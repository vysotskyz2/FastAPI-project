from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from aiokafka import AIOKafkaConsumer
from loguru import logger
from pydantic import BaseModel

MessageT = TypeVar("MessageT", bound=BaseModel)


class BaseConsumer(ABC, Generic[MessageT]):
    topic: str

    def __init__(self, bootstrap_servers: str, group_id: str) -> None:
        self._consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=self._safe_deserialize,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        )

    @staticmethod
    def deserialize(raw: bytes) -> MessageT:
        raise NotImplementedError

    def _safe_deserialize(self, raw: bytes) -> MessageT | None:
        try:
            return self.deserialize(raw)
        except Exception:
            logger.exception("Failed to deserialize message on topic '{}'", self.topic)
            return None

    async def run(self) -> None:
        await self._consumer.start()
        logger.info("Consumer started for topic '{}'", self.topic)
        try:
            async for msg in self._consumer:
                await self._handle(msg.value)
        finally:
            await self._consumer.stop()
            logger.info("Consumer stopped for topic '{}'", self.topic)

    async def stop(self) -> None:
        await self._consumer.stop()

    async def _handle(self, message: MessageT | None) -> None:
        if message is None:
            return
        try:
            await self.process_message(message)
        except Exception:
            logger.exception("Failed to process message on topic '{}'", self.topic)

    @abstractmethod
    async def process_message(self, message: MessageT) -> None:
        pass
