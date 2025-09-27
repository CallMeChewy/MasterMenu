#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR=${1:-}
VENV_NAME=${2:-.venv}

if [[ -z "$TARGET_DIR" ]]; then
  echo "Usage: venv-create.sh <target_directory> [venv_name]"
  exit 1
fi

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Directory does not exist: $TARGET_DIR" >&2
  exit 1
fi

cd "$TARGET_DIR"
python3 -m venv "$VENV_NAME"
source "$VENV_NAME/bin/activate"
pip install --upgrade pip

echo "Virtual environment '$VENV_NAME' created and activated in $TARGET_DIR"
