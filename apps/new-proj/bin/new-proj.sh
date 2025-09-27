#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=${1:-}
shift || true

if [[ -z "$PROJECT_DIR" ]]; then
  echo "Usage: new-proj.sh <project_startup_dir> [args...]"
  exit 1
fi

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "Project_Startup directory not found: $PROJECT_DIR" >&2
  exit 1
fi

cd "$PROJECT_DIR"
python src/main.py "$@"
