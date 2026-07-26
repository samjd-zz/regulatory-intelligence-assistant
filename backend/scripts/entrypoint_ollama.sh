#!/bin/sh
set -e

MODEL="${OLLAMA_MODEL:-llama3.2:3b}"
LLM_PROVIDER="${LLM_PROVIDER:-gemini}"

# Start Ollama in background
ollama serve &

# Wait for API to be ready
until curl -s http://localhost:11434/api/tags >/dev/null 2>&1; do
  sleep 1
done

# Only pull model if LLM_PROVIDER is set to ollama
if [ "$LLM_PROVIDER" = "ollama" ]; then
    echo "🤖 LLM_PROVIDER is 'ollama' - downloading model: $MODEL"
    ollama pull "$MODEL" || true
else
    echo "ℹ️ LLM_PROVIDER is '$LLM_PROVIDER' - skipping Ollama model download"
    echo "   Model will be downloaded when first accessed via API"
fi

# Keep server running
wait
