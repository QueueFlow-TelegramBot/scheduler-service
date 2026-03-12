import pytest


ROOM_DATA = {
    "name": "Secretary Office 1",
    "creator_id": "123456789",
    "creator_name": "Maria Popescu",
}


@pytest.mark.asyncio
async def test_create_room(client):
    response = await client.post("/rooms", json=ROOM_DATA)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == ROOM_DATA["name"]
    assert data["creator_id"] == ROOM_DATA["creator_id"]
    assert data["status"] == "active"
    assert len(data["room_id"]) == 5


@pytest.mark.asyncio
async def test_create_room_missing_name(client):
    response = await client.post("/rooms", json={"creator_id": "123", "creator_name": "Test"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_room_missing_creator_id(client):
    response = await client.post("/rooms", json={"name": "Office", "creator_name": "Test"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_room(client):
    create_resp = await client.post("/rooms", json=ROOM_DATA)
    room_id = create_resp.json()["room_id"]

    response = await client.get(f"/rooms/{room_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["room_id"] == room_id
    assert data["people_in_queue"] == 0


@pytest.mark.asyncio
async def test_get_room_not_found(client):
    response = await client.get("/rooms/XXXXX")
    assert response.status_code == 404
    assert response.json()["detail"] == "Room not found"


@pytest.mark.asyncio
async def test_list_rooms_by_creator(client):
    await client.post("/rooms", json={**ROOM_DATA, "creator_id": "creatorA"})
    await client.post("/rooms", json={**ROOM_DATA, "creator_id": "creatorA"})
    await client.post("/rooms", json={**ROOM_DATA, "creator_id": "creatorB"})

    response = await client.get("/rooms?creator_id=creatorA")
    assert response.status_code == 200
    assert len(response.json()["rooms"]) == 2


@pytest.mark.asyncio
async def test_list_rooms_empty(client):
    response = await client.get("/rooms?creator_id=nobody")
    assert response.status_code == 200
    assert response.json()["rooms"] == []
