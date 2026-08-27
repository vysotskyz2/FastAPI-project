import pytest


@pytest.mark.asyncio
async def test_create_user(client):
    r = await client.post("/users", json={"email": "api@example.com"})
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "api@example.com"
    assert body["status"] == "ACTIVE"
    assert body["id"] > 0


@pytest.mark.asyncio
async def test_create_duplicate_user_409(client):
    await client.post("/users", json={"email": "dup@example.com"})
    r = await client.post("/users", json={"email": "dup@example.com"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_create_user_invalid_email_422(client):
    r = await client.post("/users", json={"email": "not-an-email"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_list_users(client):
    await client.post("/users", json={"email": "list@example.com"})
    r = await client.get("/users")
    assert r.status_code == 200
    assert any(u["email"] == "list@example.com" for u in r.json())


@pytest.mark.asyncio
async def test_list_users_filter_by_email(client):
    await client.post("/users", json={"email": "filter@example.com"})
    r = await client.get("/users", params={"email": "filter@example.com"})
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["email"] == "filter@example.com"


@pytest.mark.asyncio
async def test_patch_user_block(client):
    create = (await client.post("/users", json={"email": "patch@example.com"})).json()
    r = await client.patch(f"/users/{create['id']}", json={"status": "BLOCKED"})
    assert r.status_code == 200
    assert r.json()["status"] == "BLOCKED"


@pytest.mark.asyncio
async def test_patch_user_unblock(client):
    create = (await client.post("/users", json={"email": "unblk@example.com"})).json()
    await client.patch(f"/users/{create['id']}", json={"status": "BLOCKED"})
    r = await client.patch(f"/users/{create['id']}", json={"status": "ACTIVE"})
    assert r.status_code == 200
    assert r.json()["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_patch_user_not_found_404(client):
    r = await client.patch("/users/9999", json={"status": "BLOCKED"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_patch_user_invalid_status_422(client):
    create = (await client.post("/users", json={"email": "inv@example.com"})).json()
    r = await client.patch(f"/users/{create['id']}", json={"status": "WHATEVER"})
    assert r.status_code == 422
