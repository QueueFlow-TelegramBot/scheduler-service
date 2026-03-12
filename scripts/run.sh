#!/bin/bash
# Start dev dependencies and run the service
docker compose up -d
sleep 3
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
