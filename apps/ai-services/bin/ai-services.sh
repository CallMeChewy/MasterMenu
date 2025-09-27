#!/usr/bin/env bash
set -euo pipefail

echo "=== Running AI Services ==="
if pgrep -x "ollama" > /dev/null; then
    echo "✓ Ollama is running"
else
    echo "✗ Ollama is not running"
fi

if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "✓ Ollama API is accessible"
else
    echo "✗ Ollama API is not accessible"
fi
