@echo off
REM Run all tests
.venv\Scripts\pytest -v --tb=short --cov=app --cov-report=term-missing
