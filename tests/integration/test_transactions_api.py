import pytest


async def _make_user(client, email: str) -> dict:
    r = await client.post("/users", json={"email": email})
    assert r.status_code == 201
    return r.json()


@pytest.mark.asyncio
async def test_create_transaction_deposit(client):
    u = await _make_user(client, "tx@example.com")
    r = await client.post(f"/{u['id']}/transactions", json={"currency": "USD", "amount": 100})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "PROCESSED"
    assert body["amount"] == 100.0
    assert body["currency"] == "USD"
    assert body["user_id"] == u["id"]


@pytest.mark.asyncio
async def test_create_transaction_withdraw(client):
    u = await _make_user(client, "wd@example.com")
    await client.post(f"/{u['id']}/transactions", json={"currency": "USD", "amount": 100})
    r = await client.post(f"/{u['id']}/transactions", json={"currency": "USD", "amount": -30})
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_create_transaction_negative_balance_400(client):
    u = await _make_user(client, "neg@example.com")
    r = await client.post(f"/{u['id']}/transactions", json={"currency": "USD", "amount": -10})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_create_transaction_zero_amount_422(client):
    u = await _make_user(client, "zero@example.com")
    r = await client.post(f"/{u['id']}/transactions", json={"currency": "USD", "amount": 0})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_transaction_unknown_currency_422(client):
    u = await _make_user(client, "cur@example.com")
    r = await client.post(f"/{u['id']}/transactions", json={"currency": "XYZ", "amount": 10})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_transaction_user_not_found_404(client):
    r = await client.post("/9999/transactions", json={"currency": "USD", "amount": 10})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_transaction_blocked_user_400(client):
    u = await _make_user(client, "blk@example.com")
    await client.patch(f"/users/{u['id']}", json={"status": "BLOCKED"})
    r = await client.post(f"/{u['id']}/transactions", json={"currency": "USD", "amount": 10})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_rollback_transaction(client):
    u = await _make_user(client, "rb@example.com")
    t = (await client.post(f"/{u['id']}/transactions", json={"currency": "USD", "amount": 50})).json()
    r = await client.patch(f"/{u['id']}/transactions/{t['id']}")
    assert r.status_code == 200
    assert r.json()["status"] == "ROLLBACKED"


@pytest.mark.asyncio
async def test_rollback_already_rollbacked_400(client):
    u = await _make_user(client, "rbd@example.com")
    t = (await client.post(f"/{u['id']}/transactions", json={"currency": "USD", "amount": 50})).json()
    await client.patch(f"/{u['id']}/transactions/{t['id']}")
    r = await client.patch(f"/{u['id']}/transactions/{t['id']}")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_rollback_not_belonging_400(client):
    u1 = await _make_user(client, "a@example.com")
    u2 = await _make_user(client, "b@example.com")
    t = (await client.post(f"/{u1['id']}/transactions", json={"currency": "USD", "amount": 50})).json()
    r = await client.patch(f"/{u2['id']}/transactions/{t['id']}")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_list_transactions_filter(client):
    u = await _make_user(client, "lt@example.com")
    await client.post(f"/{u['id']}/transactions", json={"currency": "USD", "amount": 10})
    r = await client.get("/transactions", params={"user_id": u["id"]})
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_rollback_blocked_user_400(client):
    u = await _make_user(client, "rbb@example.com")
    t = (await client.post(f"/{u['id']}/transactions", json={"currency": "USD", "amount": 50})).json()
    await client.patch(f"/users/{u['id']}", json={"status": "BLOCKED"})
    r = await client.patch(f"/{u['id']}/transactions/{t['id']}")
    assert r.status_code == 400
