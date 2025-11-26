#!/bin/bash
set -e

# Custom entrypoint that handles restarts gracefully

# Clean up stale PID file from previous run (container restart scenario)
if [ -f "/var/lib/neo4j/run/neo4j.pid" ]; then
    echo "Cleaning up stale PID file from previous run..."
    rm -f /var/lib/neo4j/run/neo4j.pid
fi

# Check if Neo4j data exists (database already initialized)
if [ -d "/data/databases/neo4j" ] || [ -d "/data/databases/system" ]; then
    echo "Neo4j already initialized, skipping password setup..."
    # Unset NEO4J_AUTH to prevent password change attempt on restart
    unset NEO4J_AUTH
fi

# Call the original Neo4j entrypoint
exec /startup/docker-entrypoint.sh "$@"
