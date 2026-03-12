import pytest


ROOM_DATA = {
    "name": "Secretary Office 1",
    "creator_id": "123456789",
    "creator_name": "Maria Popescu",
}

USER1 = {"user_id": "111", "user_name": "Alice"}
USER2 = {"user_id": "222", "user_name": "Bob"}


@pytest.mark.asyncio
async def test_next_returns_first_user(client, mock_rabbitmq):
    room = (await client.post("/rooms", json=ROOM_DATA)).json()
    room_id = room["room_id"]

    await client.post(f"/rooms/{room_id}/join", json=USER1)
    await client.post(f"/rooms/{room_id}/join", json=USER2)

    mock_rabbitmq.published.clear()

    response = await client.post(f"/rooms/{room_id}/next", json={"creator_id": ROOM_DATA["creator_id"]})
    assert response.status_code == 200
    data = response.json()
    assert data["next_user_id"] == USER1["user_id"]
    assert data["remaining_in_queue"] == 1

    # Notification published
    notif = [p for p in mock_rabbitmq.published if p["routing_key"].startswith("notification.")]
    assert len(notif) == 1
    assert notif[0]["body"]["event"] == "your_turn"


@pytest.mark.asyncio
async def test_next_second_user(client):
    room = (await client.post("/rooms", json=ROOM_DATA)).json()
    room_id = room["room_id"]

    await client.post(f"/rooms/{room_id}/join", json=USER1)
    await client.post(f"/rooms/{room_id}/join", json=USER2)

    await client.post(f"/rooms/{room_id}/next", json={"creator_id": ROOM_DATA["creator_id"]})
    response = await client.post(f"/rooms/{room_id}/next", json={"creator_id": ROOM_DATA["creator_id"]})

    assert response.status_code == 200
    data = response.json()
    assert data["next_user_id"] == USER2["user_id"]
    assert data["remaining_in_queue"] == 0


@pytest.mark.asyncio
async def test_next_empty_queue(client):
    room = (await client.post("/rooms", json=ROOM_DATA)).json()
    room_id = room["room_id"]

    response = await client.post(f"/rooms/{room_id}/next", json={"creator_id": ROOM_DATA["creator_id"]})
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_next_wrong_creator(client):
    room = (await client.post("/rooms", json=ROOM_DATA)).json()
    room_id = room["room_id"]

    response = await client.post(f"/rooms/{room_id}/next", json={"creator_id": "wrongcreator"})
    assert response.status_code == 403
