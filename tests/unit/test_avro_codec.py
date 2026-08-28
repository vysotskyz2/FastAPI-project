from datetime import datetime, timezone
from decimal import Decimal

from src.infrastructure.kafka.avro_codec import (
    deserialize_transaction_event,
    deserialize_user_event,
    serialize_transaction_event,
    serialize_user_event,
)
from src.infrastructure.schemas.kafka import (
    TransactionEvent,
    TransactionEventType,
    UserRegisteredEvent,
)


def test_user_event_round_trip():
    event = UserRegisteredEvent(
        user_id=42,
        email="user@example.com",
        occurred_at=datetime(2026, 8, 25, 12, 0, 0, 123000, tzinfo=timezone.utc),
    )
    payload = serialize_user_event(event)
    assert isinstance(payload, bytes)
    restored = deserialize_user_event(payload)
    assert restored.user_id == 42
    assert restored.email == "user@example.com"
    assert restored.occurred_at == event.occurred_at


def test_transaction_event_round_trip():
    event = TransactionEvent(
        event_type=TransactionEventType.CREATED,
        transaction_id=7,
        user_id=42,
        currency="USD",
        amount=Decimal("100.50000000"),
        status="PROCESSED",
        occurred_at=datetime(2026, 8, 25, 12, 0, 0, 456000, tzinfo=timezone.utc),
    )
    payload = serialize_transaction_event(event)
    restored = deserialize_transaction_event(payload)
    assert restored.event_type == TransactionEventType.CREATED
    assert restored.transaction_id == 7
    assert restored.user_id == 42
    assert restored.currency == "USD"
    assert restored.amount == Decimal("100.50000000")
    assert restored.status == "PROCESSED"
    assert restored.occurred_at == event.occurred_at
