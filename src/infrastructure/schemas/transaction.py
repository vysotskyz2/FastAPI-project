from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from src.infrastructure.models.enums import CurrencyEnum, TransactionStatusEnum


class TransactionCreate(BaseModel):
    currency: CurrencyEnum
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def amount_not_zero(cls, value: Decimal) -> Decimal:
        if value == 0:
            raise ValueError("Transaction amount cannot be zero")
        return value


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    currency: CurrencyEnum
    amount: Decimal
    status: TransactionStatusEnum
    created: datetime

    @field_serializer("amount")
    def serialize_amount(self, value: Decimal) -> float:
        return float(value)
