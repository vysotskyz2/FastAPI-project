from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer

from src.infrastructure.models.enums import CurrencyEnum, UserStatusEnum


class UserCreate(BaseModel):
    email: EmailStr


class UserUpdate(BaseModel):
    status: UserStatusEnum


class UserBalanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    currency: CurrencyEnum
    amount: Decimal

    @field_serializer("amount")
    def serialize_amount(self, value: Decimal) -> float:
        return float(value)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    status: UserStatusEnum
    created: datetime
    balances: list[UserBalanceRead] = Field(default_factory=list)


class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    status: UserStatusEnum
    created: datetime
