import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.rabbitmq import RabbitMQManager, get_rabbitmq
from app.schemas.room import (
    RoomCreate, RoomResponse, RoomListResponse, RoomListItem,
    RoomDetailResponse, JoinRequest, JoinResponse, NextRequest, NextResponse,
    CloseRequest, CloseResponse,
)
from app.services import room_service, queue_service

router = APIRouter(prefix="/rooms", tags=["Rooms"])
logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new queue room",
    description="Create a new active queue room. The room ID is auto-generated as a 5-char alphanumeric string.",
    responses={
        201: {"description": "Room created successfully"},
        422: {"description": "Validation error"},
    },
)
async def create_room(data: RoomCreate, db: AsyncSession = Depends(get_db)):
    room = await room_service.create_room(db, data)
    return RoomResponse(
        room_id=room.id,
        name=room.name,
        creator_id=room.creator_id,
        creator_name=room.creator_name,
        status=room.status,
        created_at=room.created_at,
    )


@router.get(
    "",
    response_model=RoomListResponse,
    summary="List active rooms by creator",
    description="Returns all active queue rooms for a given creator. Includes count of waiting entries.",
    responses={200: {"description": "List of active rooms"}},
)
async def list_rooms(creator_id: str = Query(..., description="Telegram user ID of the creator"), db: AsyncSession = Depends(get_db)):
    rooms = await room_service.list_rooms_by_creator(db, creator_id)
    items = []
    for room in rooms:
        count = await room_service.count_waiting(db, room.id)
        items.append(RoomListItem(
            room_id=room.id,
            name=room.name,
            status=room.status,
            created_at=room.created_at,
            people_in_queue=count,
        ))
    return RoomListResponse(rooms=items)


@router.get(
    "/{room_id}",
    response_model=RoomDetailResponse,
    summary="Get room details by ID",
    description="Returns full details of a specific room including current queue length.",
    responses={
        200: {"description": "Room details"},
        404: {"description": "Room not found", "content": {"application/json": {"example": {"detail": "Room not found"}}}},
    },
)
async def get_room(room_id: str, db: AsyncSession = Depends(get_db)):
    room = await room_service.get_room(db, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    count = await room_service.count_waiting(db, room.id)
    return RoomDetailResponse(
        room_id=room.id,
        name=room.name,
        creator_id=room.creator_id,
        creator_name=room.creator_name,
        status=room.status,
        created_at=room.created_at,
        people_in_queue=count,
    )


@router.post(
    "/{room_id}/join",
    response_model=JoinResponse,
    summary="Join a queue room",
    description="Join an active queue room. Returns the user's position in the queue.",
    responses={
        200: {"description": "Successfully joined the queue"},
        400: {"description": "Room is closed", "content": {"application/json": {"example": {"detail": "Room is closed"}}}},
        404: {"description": "Room not found"},
        409: {"description": "User already in queue", "content": {"application/json": {"example": {"detail": "User already in this queue"}}}},
    },
)
async def join_room(
    room_id: str,
    data: JoinRequest,
    db: AsyncSession = Depends(get_db),
    rabbitmq: RabbitMQManager = Depends(get_rabbitmq),
):
    room = await room_service.get_room(db, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.status != "active":
        raise HTTPException(status_code=400, detail="Room is closed")

    try:
        entry = await queue_service.join_queue(db, rabbitmq, room_id, data.user_id, data.user_name)
    except ValueError as e:
        if "already_in_queue" in str(e):
            raise HTTPException(status_code=409, detail="User already in this queue")
        raise

    return JoinResponse(
        room_id=room.id,
        room_name=room.name,
        creator_name=room.creator_name,
        position=entry.position,
        people_in_front=entry.position - 1,
    )


@router.post(
    "/{room_id}/next",
    summary="Get the next person in the queue",
    description="Consume the next person from the queue. Only the room creator can call this.",
    responses={
        200: {"model": NextResponse, "description": "Next user info"},
        204: {"description": "No one in queue"},
        403: {"description": "Not the room creator", "content": {"application/json": {"example": {"detail": "Forbidden"}}}},
        404: {"description": "Room not found"},
    },
)
async def next_in_queue(
    room_id: str,
    data: NextRequest,
    db: AsyncSession = Depends(get_db),
    rabbitmq: RabbitMQManager = Depends(get_rabbitmq),
):
    room = await room_service.get_room(db, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.creator_id != data.creator_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    result = await queue_service.get_next_in_queue(db, rabbitmq, room_id, room.name)
    if result is None:
        from fastapi.responses import Response
        return Response(status_code=204)

    return NextResponse(
        room_id=room.id,
        room_name=room.name,
        next_user_id=result["user_id"],
        next_user_name=result["user_name"],
        position_served=result["position_served"],
        remaining_in_queue=result["remaining_in_queue"],
    )


@router.patch(
    "/{room_id}/close",
    response_model=CloseResponse,
    summary="Close a room",
    description="Close a queue room. All waiting entries are cancelled. Only the room creator can close.",
    responses={
        200: {"description": "Room closed"},
        403: {"description": "Not the room creator"},
        404: {"description": "Room not found"},
    },
)
async def close_room(room_id: str, data: CloseRequest, db: AsyncSession = Depends(get_db)):
    room = await room_service.get_room(db, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.creator_id != data.creator_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    room = await room_service.close_room(db, room)
    return CloseResponse(room_id=room.id, status=room.status)
