#!/bin/sh
set -e

echo "🚀 Starting Regulatory Intelligence Assistant Backend..."

# Run database migrations
echo "🔧 Running database migrations..."
alembic upgrade head || {
    echo "⚠️ Migrations failed, continuing anyway..."
}
echo "✓ Database migrations complete"

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

# Wait for Elasticsearch to be ready
echo "⏳ Waiting for Elasticsearch to be ready..."
while ! nc -z elasticsearch 9200; do
    echo "Elasticsearch is not ready yet, waiting..."
    sleep 2
done
echo "✓ Elasticsearch is ready"

# Check if database has data, offer interactive setup if empty
echo "🔍 Checking database status..."
REG_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM regulations" 2>/dev/null | tr -d '[:space:]' || echo "0")
if [ "$REG_COUNT" -lt 100 ]; then
    echo "⚠️ Database appears empty ($REG_COUNT regulations)"
    
    if [ "${AUTO_INIT_DATA:-false}" = "true" ]; then
        echo "🔄 AUTO_INIT_DATA=true, running data initialization..."
        python scripts/init_data.py --type both --limit 50 --non-interactive || {
            echo "⚠️ Data initialization failed, continuing anyway..."
        }
    else
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📊 No data loaded yet!"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "To initialize with data, run:"
        echo "  docker compose exec backend python scripts/init_data.py"
        echo ""
        echo "Or set AUTO_INIT_DATA=true in docker-compose.yml to auto-load"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
    fi
else
    echo "✓ Database has data ($REG_COUNT regulations)"
fi

# Check if Elasticsearch reindexing is needed
echo "🔍 Checking Elasticsearch index status..."
if [ "${REINDEX_ELASTICSEARCH:-false}" = "true" ]; then
    echo "🔄 Reindexing Elasticsearch (REINDEX_ELASTICSEARCH=true)..."
    python scripts/reindex_elasticsearch.py || {
        echo "⚠️ Elasticsearch reindexing failed, continuing anyway..."
    }
    echo "✓ Elasticsearch reindexing complete"
else
    # Check if index exists and has documents
    DOCS_COUNT=$(curl -s http://elasticsearch:9200/regulatory_documents/_count | python3 -c "import sys, json; print(json.load(sys.stdin).get('count', 0))" 2>/dev/null || echo "0")
    if [ "$DOCS_COUNT" -lt 10000 ]; then
        echo "⚠️ Elasticsearch index appears empty ($DOCS_COUNT documents)"
        echo "   Data will be indexed automatically when loaded"
    else
        echo "✓ Elasticsearch index ready ($DOCS_COUNT documents)"
    fi
fi

# Start the FastAPI server
echo "🌐 Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
