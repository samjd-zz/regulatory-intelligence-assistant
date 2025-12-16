#!/bin/sh
set -e

MODEL="${OLLAMA_MODEL:-llama3.2:3b}"

# Start Ollama in background
ollama serve &

# Wait for API to be ready
until curl -s http://localhost:11434/api/tags >/dev/null 2>&1; do
  sleep 1
done

# Pull model (idempotent)
ollama pull "$MODEL" || true

# Keep server running
wait
