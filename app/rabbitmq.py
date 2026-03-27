import json
import logging
from datetime import datetime, timezone
from typing import Optional

import aio_pika
from aio_pika import ExchangeType

from app.config import settings


NOTIFICATION_QUEUE_NAME = "notifications"
NOTIFICATION_ROUTING_KEY = "notification.*"

logger = logging.getLogger(__name__)


class RabbitMQManager:
    def __init__(self):
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._exchange: Optional[aio_pika.Exchange] = None

    async def connect(self):
        self._connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            settings.RABBITMQ_EXCHANGE,
            ExchangeType.TOPIC,
            durable=True,
        )
        logger.info("RabbitMQ connected", extra={"action": "connect", "success": True})

    async def disconnect(self):
        if self._connection:
            await self._connection.close()
        logger.info("RabbitMQ disconnected", extra={"action": "disconnect", "success": True})

    async def publish(self, routing_key: str, body: dict):
        if self._exchange is None:
            raise RuntimeError("RabbitMQ not connected")

        queue = await self._channel.declare_queue(routing_key, durable=True, auto_delete=False)
        await queue.bind(self._exchange, routing_key=routing_key)

        message = aio_pika.Message(
            body=json.dumps(body).encode(),
            content_type="application/json",
        )
        await self._exchange.publish(message, routing_key=routing_key)
        logger.info(
            "Message published",
            extra={"action": "publish", "routing_key": routing_key, "queue_name": routing_key, "success": True},
        )

    async def pull_one(self, queue_name: str) -> Optional[dict]:
        if self._channel is None:
            raise RuntimeError("RabbitMQ not connected")

        try:
            queue = await self._channel.declare_queue(queue_name, durable=True)
            message = await queue.get(no_ack=False)
            if message is None:
                logger.warning(
                    "No message in queue",
                    extra={"action": "consume", "routing_key": queue_name, "queue_name": queue_name, "success": False},
                )
                return None
            await message.ack()
            data = json.loads(message.body.decode())
            logger.info(
                "Message consumed",
                extra={"action": "consume", "routing_key": queue_name, "queue_name": queue_name, "success": True},
            )
            return data
        except aio_pika.exceptions.QueueEmpty:
            logger.warning(
                "Queue is empty",
                extra={"action": "consume", "routing_key": queue_name, "queue_name": queue_name, "success": False},
            )
            return None

    @property
    def is_connected(self) -> bool:
        return self._connection is not None and not self._connection.is_closed


rabbitmq_manager = RabbitMQManager()


async def get_rabbitmq() -> RabbitMQManager:
    return rabbitmq_manager
