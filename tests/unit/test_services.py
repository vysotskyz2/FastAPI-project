import pytest
import pytest_asyncio

from src.application.exceptions import (
    NegativeBalanceError,
    TransactionAlreadyRollbackedError,
    TransactionNotBelongToUserError,
    TransactionNotFoundError,
    UserAlreadyBlockedError,
    UserAlreadyExistsError,
    UserBlockedError,
    UserNotFoundError,
)
from src.application.services.transaction_service import TransactionService
from src.application.services.user_service import UserService
from src.infrastructure.models.enums import CurrencyEnum, TransactionStatusEnum, UserStatusEnum
from src.infrastructure.repositories.balance_repository import BalanceRepository
from src.infrastructure.repositories.transaction_repository import TransactionRepository
from src.infrastructure.repositories.user_repository import UserRepository


@pytest_asyncio.fixture
async def user_service(session):
    return UserService(session, UserRepository(session), BalanceRepository(session), None)


@pytest_asyncio.fixture
async def tx_service(session):
    return TransactionService(
        session,
        UserRepository(session),
        BalanceRepository(session),
        TransactionRepository(session),
        None,
    )


async def _balance(session, user_id, currency=CurrencyEnum.USD.value) -> float:
    bal = await BalanceRepository(session).get_by_user_and_currency(user_id, currency)
    return bal.amount


@pytest.mark.asyncio
async def test_register_creates_user_and_default_balances(user_service):
    user = await user_service.register("user@example.com")
    assert user.id is not None
    assert user.email == "user@example.com"
    assert user.status == UserStatusEnum.ACTIVE.value
    users = await user_service.list_users(None, None, None, 100, 0)
    assert len(users[0].balances) == len(list(CurrencyEnum))
    for b in users[0].balances:
        assert b.amount == 0


@pytest.mark.asyncio
async def test_register_duplicate_email_raises(user_service):
    await user_service.register("dup@example.com")
    with pytest.raises(UserAlreadyExistsError) as exc:
        await user_service.register("dup@example.com")
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_register_normalizes_email(user_service):
    user = await user_service.register("  User@Example.com ")
    assert user.email == "user@example.com"


@pytest.mark.asyncio
async def test_update_status_block_then_unblock(user_service):
    user = await user_service.register("b@example.com")
    blocked = await user_service.update_status(user.id, UserStatusEnum.BLOCKED)
    assert blocked.status == UserStatusEnum.BLOCKED.value
    active = await user_service.update_status(user.id, UserStatusEnum.ACTIVE)
    assert active.status == UserStatusEnum.ACTIVE.value


@pytest.mark.asyncio
async def test_update_status_already_blocked_raises(user_service):
    user = await user_service.register("bb@example.com")
    await user_service.update_status(user.id, UserStatusEnum.BLOCKED)
    with pytest.raises(UserAlreadyBlockedError):
        await user_service.update_status(user.id, UserStatusEnum.BLOCKED)


@pytest.mark.asyncio
async def test_deposit_increases_balance(user_service, tx_service, session):
    user = await user_service.register("d@example.com")
    tx = await tx_service.create_transaction(user.id, CurrencyEnum.USD.value, 100)
    assert tx.status == TransactionStatusEnum.PROCESSED.value
    assert await _balance(session, user.id) == 100


@pytest.mark.asyncio
async def test_withdraw_decreases_balance(user_service, tx_service, session):
    user = await user_service.register("w@example.com")
    await tx_service.create_transaction(user.id, CurrencyEnum.USD.value, 100)
    await tx_service.create_transaction(user.id, CurrencyEnum.USD.value, -30)
    assert await _balance(session, user.id) == 70


@pytest.mark.asyncio
async def test_withdraw_more_than_balance_raises(user_service, tx_service):
    user = await user_service.register("neg@example.com")
    await tx_service.create_transaction(user.id, CurrencyEnum.USD.value, 100)
    with pytest.raises(NegativeBalanceError) as exc:
        await tx_service.create_transaction(user.id, CurrencyEnum.USD.value, -150)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_rollback_deposit_returns_money(user_service, tx_service, session):
    user = await user_service.register("rb@example.com")
    tx = await tx_service.create_transaction(user.id, CurrencyEnum.USD.value, 100)
    rolled = await tx_service.rollback_transaction(user.id, tx.id)
    assert rolled.status == TransactionStatusEnum.ROLLBACKED.value
    assert await _balance(session, user.id) == 0


@pytest.mark.asyncio
async def test_rollback_withdraw_takes_money_back(user_service, tx_service, session):
    user = await user_service.register("rbw@example.com")
    await tx_service.create_transaction(user.id, CurrencyEnum.USD.value, 100)
    tx = await tx_service.create_transaction(user.id, CurrencyEnum.USD.value, -40)
    await tx_service.rollback_transaction(user.id, tx.id)
    assert await _balance(session, user.id) == 100


@pytest.mark.asyncio
async def test_rollback_already_rollbacked_raises(user_service, tx_service):
    user = await user_service.register("rbd@example.com")
    tx = await tx_service.create_transaction(user.id, CurrencyEnum.USD.value, 100)
    await tx_service.rollback_transaction(user.id, tx.id)
    with pytest.raises(TransactionAlreadyRollbackedError):
        await tx_service.rollback_transaction(user.id, tx.id)


@pytest.mark.asyncio
async def test_rollback_not_belonging_raises(user_service, tx_service):
    u1 = await user_service.register("a@example.com")
    u2 = await user_service.register("b@example.com")
    tx = await tx_service.create_transaction(u1.id, CurrencyEnum.USD.value, 100)
    with pytest.raises(TransactionNotBelongToUserError):
        await tx_service.rollback_transaction(u2.id, tx.id)


@pytest.mark.asyncio
async def test_blocked_user_cannot_transact(user_service, tx_service):
    user = await user_service.register("blk@example.com")
    await user_service.update_status(user.id, UserStatusEnum.BLOCKED)
    with pytest.raises(UserBlockedError):
        await tx_service.create_transaction(user.id, CurrencyEnum.USD.value, 100)


@pytest.mark.asyncio
async def test_blocked_user_cannot_rollback(user_service, tx_service):
    user = await user_service.register("blk2@example.com")
    tx = await tx_service.create_transaction(user.id, CurrencyEnum.USD.value, 100)
    await user_service.update_status(user.id, UserStatusEnum.BLOCKED)
    with pytest.raises(UserBlockedError):
        await tx_service.rollback_transaction(user.id, tx.id)


@pytest.mark.asyncio
async def test_create_transaction_nonexistent_user_raises(tx_service):
    with pytest.raises(UserNotFoundError):
        await tx_service.create_transaction(999, CurrencyEnum.USD.value, 100)


@pytest.mark.asyncio
async def test_rollback_nonexistent_transaction_raises(user_service, tx_service):
    user = await user_service.register("ne@example.com")
    with pytest.raises(TransactionNotFoundError):
        await tx_service.rollback_transaction(user.id, 999)
