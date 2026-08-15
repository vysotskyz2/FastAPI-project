from fastapi import APIRouter, Body, Depends, Path, Query, status

from src.application.services.transaction_service import TransactionService
from src.infrastructure.schemas import TransactionCreate, TransactionRead
from src.interfaces.api.deps import get_transaction_service

router = APIRouter(tags=["transactions"])


@router.get("/transactions", response_model=list[TransactionRead], status_code=status.HTTP_200_OK)
async def list_transactions(
    user_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    service: TransactionService = Depends(get_transaction_service),
) -> list[TransactionRead]:
    transactions = await service.list_transactions(user_id, limit, offset)
    return [TransactionRead.model_validate(transaction) for transaction in transactions]


@router.post("/{user_id}/transactions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    user_id: int = Path(gt=0),
    payload: TransactionCreate = Body(...),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionRead:
    transaction = await service.create_transaction(user_id, payload.currency.value, payload.amount)
    return TransactionRead.model_validate(transaction)


@router.patch(
    "/{user_id}/transactions/{transaction_id}",
    response_model=TransactionRead,
    status_code=status.HTTP_200_OK,
)
async def rollback_transaction(
    user_id: int = Path(gt=0),
    transaction_id: int = Path(gt=0),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionRead:
    transaction = await service.rollback_transaction(user_id, transaction_id)
    return TransactionRead.model_validate(transaction)
