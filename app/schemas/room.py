from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class RoomCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Room name", examples=["Secretary Office 1"])
    creator_id: str = Field(..., min_length=1, description="Telegram user ID of the creator", examples=["123456789"])
    creator_name: str = Field(..., min_length=1, description="Display name of the creator", examples=["Maria Popescu"])

    model_config = {"json_schema_extra": {"example": {"name": "Secretary Office 1", "creator_id": "123456789", "creator_name": "Maria Popescu"}}}


class RoomResponse(BaseModel):
    room_id: str = Field(..., description="Unique 5-char room ID")
    name: str
    creator_id: str
    creator_name: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RoomListItem(BaseModel):
    room_id: str
    name: str
    status: str
    created_at: datetime
    people_in_queue: int

    model_config = {"from_attributes": True}


class RoomListResponse(BaseModel):
    rooms: List[RoomListItem]


class RoomDetailResponse(BaseModel):
    room_id: str
    name: str
    creator_id: str
    creator_name: str
    status: str
    created_at: datetime
    people_in_queue: int

    model_config = {"from_attributes": True}


class JoinRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="Telegram user ID of the joiner", examples=["987654321"])
    user_name: str = Field(..., min_length=1, description="Display name of the joiner", examples=["Ion Studentul"])

    model_config = {"json_schema_extra": {"example": {"user_id": "987654321", "user_name": "Ion Studentul"}}}


class JoinResponse(BaseModel):
    room_id: str
    room_name: str
    creator_name: str
    position: int
    people_in_front: int


class NextRequest(BaseModel):
    creator_id: str = Field(..., min_length=1, description="Telegram user ID of the creator", examples=["123456789"])

    model_config = {"json_schema_extra": {"example": {"creator_id": "123456789"}}}


class NextResponse(BaseModel):
    room_id: str
    room_name: str
    next_user_id: str
    next_user_name: str
    position_served: int
    remaining_in_queue: int


class CloseRequest(BaseModel):
    creator_id: str = Field(..., min_length=1, description="Telegram user ID of the creator", examples=["123456789"])

    model_config = {"json_schema_extra": {"example": {"creator_id": "123456789"}}}


class CloseResponse(BaseModel):
    room_id: str
    status: str


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
    rabbitmq: str
