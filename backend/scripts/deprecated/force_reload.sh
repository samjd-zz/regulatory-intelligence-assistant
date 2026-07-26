#!/bin/bash
# Force reload of Python code in Docker

echo "Stopping backend container..."
docker compose stop backend

echo "Clearing Python cache in backend directory..."
find backend -type f -name '*.pyc' -delete
find backend -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true

echo "Starting backend container..."
docker compose start backend

echo "Waiting for backend to be ready..."
sleep 5

echo "Clearing Python cache inside Docker container..."
docker compose exec backend sh -c "find /app -type f -name '*.pyc' -delete && find /app -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true"

echo "Verifying updated code is in container..."
docker compose exec backend grep -n "Starting ingestion" /app/ingestion/data_pipeline.py

echo "✓ Force reload complete!"
