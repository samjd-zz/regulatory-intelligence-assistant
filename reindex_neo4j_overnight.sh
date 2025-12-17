#!/bin/bash

# Neo4j Overnight Re-indexing Script (Docker version)
# Run this script to safely re-populate Neo4j with the full regulatory dataset

set -e

echo "🌙 Neo4j Overnight Re-indexing Started at $(date)"
echo "=================================================="

# Configuration
BATCH_SIZE=${BATCH_SIZE:-50}
MAX_RETRIES=${MAX_RETRIES:-3}
DRY_RUN=${DRY_RUN:-false}
RESUME=${RESUME:-false}

# Build arguments
ARGS="--batch-size $BATCH_SIZE --max-retries $MAX_RETRIES"
if [ "$DRY_RUN" = "true" ]; then
    ARGS="$ARGS --dry-run"
fi
if [ "$RESUME" = "true" ]; then
    ARGS="$ARGS --resume"
fi

echo "⚙️  Configuration:"
echo "   Batch Size: $BATCH_SIZE"
echo "   Max Retries: $MAX_RETRIES"
echo "   Dry Run: $DRY_RUN"
echo "   Resume: $RESUME"
echo ""

# Check if services are running
echo "🔍 Checking service status..."
docker compose ps | grep -E "(neo4j|postgres)"

# Run the re-indexing script
echo "🚀 Starting re-indexing process..."
docker compose exec backend python scripts/reindex_neo4j_overnight.py $ARGS

EXIT_CODE=$?

echo ""
echo "=================================================="
echo "🌅 Neo4j Re-indexing Completed at $(date)"
echo "Exit Code: $EXIT_CODE"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ SUCCESS: Neo4j has been successfully re-indexed!"
    echo ""
    echo "📊 You can check the results:"
    echo "   - Log file: neo4j_reindex.log" 
    echo "   - Results: neo4j_reindex_results.json"
    echo "   - Progress: neo4j_reindex_progress.json"
    echo ""
    echo "🔍 Test the updated Neo4j:"
    echo "   curl -X POST http://localhost:8000/api/rag/ask \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"question\": \"What personal information can the government collect?\"}'"
else
    echo "❌ FAILED: Re-indexing encountered errors (code: $EXIT_CODE)"
    echo ""
    echo "📋 Check logs for details:"
    echo "   docker compose logs backend | tail -50"
    echo "   cat neo4j_reindex.log | tail -50"
fi

exit $EXIT_CODE