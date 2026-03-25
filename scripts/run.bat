@echo off
REM Start dev dependencies and run the service
docker compose up -d
echo Waiting for services to be ready...
timeout /t 15 /nobreak >nul
.venv\Scripts\alembic upgrade head
.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
