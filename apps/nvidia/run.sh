#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SCRIPT="$SCRIPT_DIR/bin/nvidia.sh"

if command -v gnome-terminal >/dev/null 2>&1; then
  gnome-terminal -- bash -lc "'$TARGET_SCRIPT'"
else
  bash "$TARGET_SCRIPT"
fi
