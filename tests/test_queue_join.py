import pytest


ROOM_DATA = {
    "name": "Secretary Office 1",
    "creator_id": "123456789",
    "creator_name": "Maria Popescu",
}

USER1 = {"user_id": "111", "user_name": "Alice"}
USER2 = {"user_id": "222", "user_name": "Bob"}


@pytest.mark.asyncio
async def test_join_room(client, mock_rabbitmq):
    room = (await client.post("/rooms", json=ROOM_DATA)).json()
    room_id = room["room_id"]

    response = await client.post(f"/rooms/{room_id}/join", json=USER1)
    assert response.status_code == 200
    data = response.json()
    assert data["position"] == 1
    assert data["people_in_front"] == 0
    assert data["room_id"] == room_id

    # RabbitMQ publish called
    assert len(mock_rabbitmq.published) == 1
    pub = mock_rabbitmq.published[0]
    assert pub["routing_key"] == f"room.{room_id}"
    assert pub["body"]["user_id"] == USER1["user_id"]
    assert pub["body"]["event"] == "user_joined"


@pytest.mark.asyncio
async def test_join_room_twice(client):
    room = (await client.post("/rooms", json=ROOM_DATA)).json()
    room_id = room["room_id"]

    await client.post(f"/rooms/{room_id}/join", json=USER1)
    response = await client.post(f"/rooms/{room_id}/join", json=USER1)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_join_nonexistent_room(client):
    response = await client.post("/rooms/NOPE0/join", json=USER1)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_join_closed_room(client):
    room = (await client.post("/rooms", json=ROOM_DATA)).json()
    room_id = room["room_id"]
    await client.patch(f"/rooms/{room_id}/close", json={"creator_id": ROOM_DATA["creator_id"]})

    response = await client.post(f"/rooms/{room_id}/join", json=USER1)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_multiple_users_positions(client):
    room = (await client.post("/rooms", json=ROOM_DATA)).json()
    room_id = room["room_id"]

    r1 = (await client.post(f"/rooms/{room_id}/join", json=USER1)).json()
    r2 = (await client.post(f"/rooms/{room_id}/join", json=USER2)).json()

    assert r1["position"] == 1
    assert r2["position"] == 2
