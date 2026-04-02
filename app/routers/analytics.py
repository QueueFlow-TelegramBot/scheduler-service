import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.room import Room, QueueEntry
from app.schemas.analytics import AnalyticsResponse, QueueEntryStatusCounts

router = APIRouter(prefix="/analytics", tags=["Analytics"])
logger = logging.getLogger(__name__)


@router.get(
    "",
    response_model=AnalyticsResponse,
    summary="Queue analytics",
    description=(
        "Returns key indicators for the queue system: "
        "total events processed, events by status, "
        "room counts by status, and actions per service."
    ),
    responses={200: {"description": "Analytics data"}},
)
async def get_analytics(db: AsyncSession = Depends(get_db)):
    # Events by status (waiting / notified / cancelled)
    status_rows = await db.execute(
        select(QueueEntry.status, func.count(QueueEntry.id).label("cnt"))
        .group_by(QueueEntry.status)
    )
    status_counts = {row.status: row.cnt for row in status_rows}

    events_by_status = QueueEntryStatusCounts(
        waiting=status_counts.get("waiting", 0),
        notified=status_counts.get("notified", 0),
        cancelled=status_counts.get("cancelled", 0),
    )

    total_events = events_by_status.waiting + events_by_status.notified + events_by_status.cancelled

    # Rooms by status (active / closed)
    room_rows = await db.execute(
        select(Room.status, func.count(Room.id).label("cnt"))
        .group_by(Room.status)
    )
    rooms_by_status = {row.status: row.cnt for row in room_rows}
    total_rooms = sum(rooms_by_status.values())

    # Actions per service — derived from event counts
    actions_per_service = {
        "scheduler-service": events_by_status.notified + events_by_status.cancelled + total_rooms,
        "telegram-bot-service": total_events,
    }

    logger.info("Analytics retrieved", extra={"total_events": total_events, "total_rooms": total_rooms})

    return AnalyticsResponse(
        total_events_processed=events_by_status.notified,
        events_by_status=events_by_status,
        total_rooms=total_rooms,
        rooms_by_status=rooms_by_status,
        actions_per_service=actions_per_service,
    )
