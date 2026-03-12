#!/bin/bash
# Run all tests
pytest -v --tb=short --cov=app --cov-report=term-missing
