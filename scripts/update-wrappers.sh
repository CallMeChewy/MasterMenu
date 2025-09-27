#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
APPS_DIR="$ROOT_DIR/apps"
WRAPPER_DIR="$ROOT_DIR/bin"

mkdir -p "$WRAPPER_DIR"
python3 "$ROOT_DIR/scripts/update_wrappers.py" "$APPS_DIR" "$WRAPPER_DIR"
