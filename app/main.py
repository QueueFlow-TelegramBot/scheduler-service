import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.logging_config import setup_logging
from app.rabbitmq import rabbitmq_manager
from app.routers import health, room, analytics

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await rabbitmq_manager.connect()
        logger.info("RabbitMQ connected on startup")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ on startup: {e}")
    yield
    await rabbitmq_manager.disconnect()


app = FastAPI(
    title="SmartCampus Scheduling Service",
    description="Manages queue rooms for the SmartCampus secretary queue system. Handles room creation, queue joining, and next-in-line notifications via RabbitMQ.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)
    logger.info(
        "Request processed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


app.include_router(health.router)
app.include_router(room.router)
app.include_router(analytics.router)
