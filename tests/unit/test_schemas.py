from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.infrastructure.models.enums import CurrencyEnum
from src.infrastructure.schemas import TransactionCreate


def test_transaction_create_rejects_zero_amount():
    with pytest.raises(ValidationError):
        TransactionCreate(currency=CurrencyEnum.USD, amount=Decimal("0"))


def test_transaction_create_rejects_unknown_currency():
    with pytest.raises(ValidationError):
        TransactionCreate(currency="XXX", amount=Decimal("10"))
