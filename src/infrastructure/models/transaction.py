from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.models.base import Base
from src.infrastructure.models.enums import TransactionStatusEnum


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=TransactionStatusEnum.PROCESSED.value,
        server_default=TransactionStatusEnum.PROCESSED.value,
    )
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint("amount <> 0", name="ck_transactions_amount_non_zero"),
        CheckConstraint(
            "status IN ('PROCESSED', 'ROLLBACKED')",
            name="ck_transactions_status",
        ),
        Index("ix_transactions_user_id", "user_id"),
        Index("ix_transactions_created", "created"),
    )

    user: Mapped["User"] = relationship(back_populates="transactions")
