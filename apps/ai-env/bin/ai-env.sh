#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR=${1:-}
VENV_NAME=${2:-.venv}

if [[ -z "$TARGET_DIR" ]]; then
  echo "Usage: ai-env.sh <target_directory> [venv_name]"
  exit 1
fi

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Target directory does not exist: $TARGET_DIR" >&2
  exit 1
fi

cd "$TARGET_DIR"

python3 -m venv "$VENV_NAME"
source "$VENV_NAME/bin/activate"
pip install --upgrade pip
pip install PySide6 requests langchain-ollama langchain-core

echo "AI environment created at $TARGET_DIR/$VENV_NAME"
echo "Virtual environment activated; run 'deactivate' to exit."
