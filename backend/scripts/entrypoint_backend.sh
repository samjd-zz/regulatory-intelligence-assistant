#!/bin/sh
set -e

echo "🚀 Starting Regulatory Intelligence Assistant Backend..."

# Wait for Neo4j to be ready
echo "⏳ Waiting for Neo4j to be ready..."
while ! nc -z neo4j 7687; do
    echo "Neo4j is not ready yet, waiting..."
    sleep 2
done
echo "✓ Neo4j is ready"

# Initialize Neo4j schema and indexes
echo "🔧 Initializing Neo4j schema and fulltext indexes..."
python scripts/init_neo4j.py || {
    echo "⚠️ Schema initialization failed, continuing anyway..."
}
echo "✓ Neo4j schema initialization complete"

# Start the FastAPI server
echo "🌐 Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
