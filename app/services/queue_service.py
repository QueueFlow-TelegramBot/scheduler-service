import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import QueueEntry
from app.rabbitmq import RabbitMQManager

logger = logging.getLogger(__name__)


async def join_queue(db: AsyncSession, rabbitmq: RabbitMQManager, room_id: str, user_id: str, user_name: str) -> QueueEntry:
    # Publish to RabbitMQ
    await rabbitmq.publish(
        routing_key=f"room.{room_id}",
        body={
            "event": "user_joined",
            "user_id": user_id,
            "user_name": user_name,
            "room_id": room_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    position = await rabbitmq.get_queue_length(f"room.{room_id}")

    entry = QueueEntry(
        room_id=room_id,
        user_id=user_id,
        user_name=user_name,
        position=position,
        status="waiting",
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    logger.info("User joined queue", extra={"room_id": room_id, "user_id": user_id, "position": position})
    return entry


async def get_next_in_queue(db: AsyncSession, rabbitmq: RabbitMQManager, room_id: str, room_name: str) -> Optional[dict]:
    message = await rabbitmq.pull_one(f"room.{room_id}")
    if message is None:
        return None

    user_id = message["user_id"]
    user_name = message["user_name"]

    # Update queue entry status
    result = await db.execute(
        select(QueueEntry).where(
            QueueEntry.room_id == room_id,
            QueueEntry.user_id == user_id,
            QueueEntry.status == "waiting",
        ).order_by(QueueEntry.position.asc())
    )

    entry = result.scalars().first()
    position_served = await rabbitmq.get_queue_length(f"room.{room_id}") + 1
    if entry:
        entry.status = "notified"
        await db.commit()

    # Count remaining
    count_result = await db.execute(
        select(func.count(QueueEntry.id)).where(
            QueueEntry.room_id == room_id,
            QueueEntry.status == "waiting",
        )
    )
    remaining = count_result.scalar_one()

    # Publish notification
    await rabbitmq.publish(
        routing_key=f"notification.{user_id}",
        body={
            "event": "your_turn",
            "user_id": user_id,
            "room_id": room_id,
            "room_name": room_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    logger.info("Next user notified", extra={"room_id": room_id, "user_id": user_id})

    return {
        "user_id": user_id,
        "user_name": user_name,
        "position_served": position_served,
        "remaining_in_queue": remaining,
    }
