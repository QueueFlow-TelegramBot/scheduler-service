import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.rabbitmq import RabbitMQManager, get_rabbitmq
from app.schemas.room import HealthResponse

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health of the service including database and RabbitMQ connectivity.",
    responses={200: {"description": "Service is healthy"}},
)
async def health_check(
    db: AsyncSession = Depends(get_db),
    rabbitmq: RabbitMQManager = Depends(get_rabbitmq),
):
    # Check DB
    db_status = "disconnected"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error("DB health check failed", extra={"error": str(e)})

    # Check RabbitMQ
    rmq_status = "connected" if rabbitmq.is_connected else "disconnected"

    return HealthResponse(
        status="healthy",
        service="scheduling-service",
        database=db_status,
        rabbitmq=rmq_status,
    )
