from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from aiokafka import AIOKafkaConsumer, TopicPartition
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
                if await self._handle(msg.value):
                    await self._commit(msg.topic, msg.partition, msg.offset)
        finally:
            await self._consumer.stop()
            logger.info("Consumer stopped for topic '{}'", self.topic)

    async def stop(self) -> None:
        await self._consumer.stop()

    async def _commit(self, topic: str, partition: int, offset: int) -> None:
        tp = TopicPartition(topic, partition)
        await self._consumer.commit({tp: offset + 1})

    async def _handle(self, message: MessageT | None) -> bool:
        if message is None:
            return True
        try:
            await self.process_message(message)
        except Exception:
            logger.exception("Failed to process message on topic '{}'", self.topic)
            return False
        return True

    @abstractmethod
    async def process_message(self, message: MessageT) -> None:
        pass
