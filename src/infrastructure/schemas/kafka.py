from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel


class TransactionEventType(StrEnum):
    CREATED = "CREATED"
    ROLLBACKED = "ROLLBACKED"


class UserRegisteredEvent(BaseModel):
    user_id: int
    email: str
    occurred_at: datetime


class TransactionEvent(BaseModel):
    event_type: TransactionEventType
    transaction_id: int
    user_id: int
    currency: str
    amount: Decimal
    status: str
    occurred_at: datetime
