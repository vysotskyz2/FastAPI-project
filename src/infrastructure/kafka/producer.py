from aiokafka import AIOKafkaProducer
from loguru import logger

from src.infrastructure.kafka.avro_codec import (
    serialize_transaction_event,
    serialize_user_event,
)
from src.infrastructure.schemas.kafka import TransactionEvent, UserRegisteredEvent


class EventProducer:
    def __init__(
        self,
        bootstrap_servers: str,
        topic_user_events: str,
        topic_transaction_events: str,
    ) -> None:
        self._producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
        self._topic_user_events = topic_user_events
        self._topic_transaction_events = topic_transaction_events
        self._started = False

    async def start(self) -> None:
        try:
            await self._producer.start()
            self._started = True
            logger.info("Kafka producer started")
        except Exception:
            logger.exception("Failed to start Kafka producer; events will be skipped")

    async def stop(self) -> None:
        if self._started:
            await self._producer.stop()
            logger.info("Kafka producer stopped")

    async def publish_user_registered(self, event: UserRegisteredEvent) -> None:
        await self._safe_publish(self._topic_user_events, serialize_user_event(event))

    async def publish_transaction_event(self, event: TransactionEvent) -> None:
        await self._safe_publish(self._topic_transaction_events, serialize_transaction_event(event))

    async def _safe_publish(self, topic: str, value: bytes) -> None:
        if not self._started:
            logger.warning("Kafka producer is not started; skipping event for topic '{}'", topic)
            return
        try:
            await self._producer.send_and_wait(topic, value)
            logger.debug("Event published to topic '{}'", topic)
        except Exception:
            logger.exception("Failed to publish event to topic '{}'", topic)
