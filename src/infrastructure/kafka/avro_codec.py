import json
from io import BytesIO
from pathlib import Path

from fastavro import parse_schema, schemaless_reader, schemaless_writer

from src.infrastructure.schemas.kafka import TransactionEvent, UserRegisteredEvent

_SCHEMAS_DIR = Path(__file__).parent / "avro_schemas"


def _load_schema(name: str) -> dict:
    raw = (_SCHEMAS_DIR / name).read_text(encoding="utf-8")
    return parse_schema(json.loads(raw))


_USER_EVENT_SCHEMA = _load_schema("user_registered.avsc")
_TRANSACTION_EVENT_SCHEMA = _load_schema("transaction_event.avsc")


def _serialize(schema: dict, record: dict) -> bytes:
    buffer = BytesIO()
    schemaless_writer(buffer, schema, record)
    return buffer.getvalue()


def _deserialize(schema: dict, payload: bytes) -> dict:
    return schemaless_reader(BytesIO(payload), schema)


def serialize_user_event(event: UserRegisteredEvent) -> bytes:
    return _serialize(_USER_EVENT_SCHEMA, event.model_dump(mode="python"))


def deserialize_user_event(payload: bytes) -> UserRegisteredEvent:
    return UserRegisteredEvent.model_validate(_deserialize(_USER_EVENT_SCHEMA, payload))


def serialize_transaction_event(event: TransactionEvent) -> bytes:
    return _serialize(_TRANSACTION_EVENT_SCHEMA, event.model_dump(mode="python"))


def deserialize_transaction_event(payload: bytes) -> TransactionEvent:
    return TransactionEvent.model_validate(_deserialize(_TRANSACTION_EVENT_SCHEMA, payload))
