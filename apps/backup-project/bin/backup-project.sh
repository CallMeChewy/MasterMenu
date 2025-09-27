#!/usr/bin/env bash
set -euo pipefail

select_directory() {
  if command -v zenity >/dev/null 2>&1; then
    zenity --file-selection --directory --title="Select project to back up" 2>/dev/null || echo ""
  else
    python3 - <<'PY'
import sys
try:
    import tkinter as tk
    from tkinter import filedialog
except Exception:
    sys.exit(0)
root = tk.Tk()
root.withdraw()
path = filedialog.askdirectory(title="Select project to back up")
if path:
    print(path)
PY
  fi
}

SOURCE_DIR=${1:-}
if [[ -z "$SOURCE_DIR" ]]; then
  SOURCE_DIR=$(select_directory)
fi

if [[ -z "$SOURCE_DIR" ]]; then
  echo "No project selected; aborting."
  exit 0
fi

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "Directory not found: $SOURCE_DIR"
  exit 1
fi

PROJECTS_BACKUP_DIR="$HOME/Desktop/Projects_Backup"
DATESTAMP=$(date +%Y%m%d_%H%M%S)
BASENAME=$(basename "$SOURCE_DIR")
TARGET_DIR="$PROJECTS_BACKUP_DIR/${BASENAME}_${DATESTAMP}"

mkdir -p "$PROJECTS_BACKUP_DIR"
cp -a "$SOURCE_DIR" "$TARGET_DIR"

echo "Project backed up to: $TARGET_DIR"
