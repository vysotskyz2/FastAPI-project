from loguru import logger

from src.infrastructure.kafka.avro_codec import deserialize_user_event
from src.infrastructure.kafka.base_consumer import BaseConsumer
from src.infrastructure.schemas.kafka import UserRegisteredEvent


class UserConsumer(BaseConsumer[UserRegisteredEvent]):
    def __init__(self, topic: str, bootstrap_servers: str, group_id: str) -> None:
        self.topic = topic
        super().__init__(bootstrap_servers=bootstrap_servers, group_id=group_id)

    @staticmethod
    def deserialize(raw: bytes) -> UserRegisteredEvent:
        return deserialize_user_event(raw)

    async def process_message(self, message: UserRegisteredEvent) -> None:
        logger.info("Received user event: {}", message.model_dump())
