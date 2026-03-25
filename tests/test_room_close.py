import pytest


ROOM_DATA = {
    "name": "Secretary Office 1",
    "creator_id": "123456789",
    "creator_name": "Maria Popescu",
}

USER1 = {"user_id": "111", "user_name": "Alice"}


@pytest.mark.asyncio
async def test_close_room(client):
    room = (await client.post("/rooms", json=ROOM_DATA)).json()
    room_id = room["room_id"]

    response = await client.patch(f"/rooms/{room_id}/close", json={"creator_id": ROOM_DATA["creator_id"]})
    assert response.status_code == 200
    assert response.json()["status"] == "closed"


@pytest.mark.asyncio
async def test_join_after_close(client):
    room = (await client.post("/rooms", json=ROOM_DATA)).json()
    room_id = room["room_id"]

    await client.patch(f"/rooms/{room_id}/close", json={"creator_id": ROOM_DATA["creator_id"]})
    response = await client.post(f"/rooms/{room_id}/join", json=USER1)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_close_wrong_creator(client):
    room = (await client.post("/rooms", json=ROOM_DATA)).json()
    room_id = room["room_id"]

    response = await client.patch(f"/rooms/{room_id}/close", json={"creator_id": "wrongcreator"})
    assert response.status_code == 403
