from loguru import logger

from src.infrastructure.kafka.avro_codec import deserialize_transaction_event
from src.infrastructure.kafka.base_consumer import BaseConsumer
from src.infrastructure.schemas.kafka import TransactionEvent


class TransactionConsumer(BaseConsumer[TransactionEvent]):
    def __init__(self, topic: str, bootstrap_servers: str, group_id: str) -> None:
        self.topic = topic
        super().__init__(bootstrap_servers=bootstrap_servers, group_id=group_id)

    @staticmethod
    def deserialize(raw: bytes) -> TransactionEvent:
        return deserialize_transaction_event(raw)

    async def process_message(self, message: TransactionEvent) -> None:
        logger.info("Received transaction event: {}", message.model_dump())
