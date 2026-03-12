import logging
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room, QueueEntry
from app.schemas.room import RoomCreate
from app.utils import generate_room_id

logger = logging.getLogger(__name__)


async def create_room(db: AsyncSession, data: RoomCreate) -> Room:
    for attempt in range(5):
        room_id = generate_room_id()
        existing = await db.get(Room, room_id)
        if existing is None:
            break
    else:
        raise RuntimeError("Failed to generate unique room ID after 5 attempts")

    room = Room(
        id=room_id,
        name=data.name,
        creator_id=data.creator_id,
        creator_name=data.creator_name,
        status="active",
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)
    logger.info("Room created", extra={"room_id": room_id, "creator_id": data.creator_id})
    return room


async def get_room(db: AsyncSession, room_id: str) -> Optional[Room]:
    return await db.get(Room, room_id)


async def count_waiting(db: AsyncSession, room_id: str) -> int:
    result = await db.execute(
        select(func.count(QueueEntry.id)).where(
            QueueEntry.room_id == room_id,
            QueueEntry.status == "waiting",
        )
    )
    return result.scalar_one()


async def list_rooms_by_creator(db: AsyncSession, creator_id: str) -> list:
    result = await db.execute(
        select(Room).where(Room.creator_id == creator_id, Room.status == "active")
    )
    rooms = result.scalars().all()
    return rooms


async def close_room(db: AsyncSession, room: Room) -> Room:
    room.status = "closed"
    # Cancel all waiting entries
    result = await db.execute(
        select(QueueEntry).where(QueueEntry.room_id == room.id, QueueEntry.status == "waiting")
    )
    entries = result.scalars().all()
    for entry in entries:
        entry.status = "cancelled"
    await db.commit()
    await db.refresh(room)
    logger.info("Room closed", extra={"room_id": room.id})
    return room
