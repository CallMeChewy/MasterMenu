#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SCRIPT="$SCRIPT_DIR/bin/git-init.sh"

select_directory() {
  if command -v zenity >/dev/null 2>&1; then
    zenity --file-selection --directory --title="Select repository directory" --filename="$HOME/Desktop/" 2>/dev/null || echo ""
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
path = filedialog.askdirectory(title="Select repository directory")
if path:
    print(path)
PY
  fi
}

TARGET_DIR=$(select_directory)
if [[ -z "$TARGET_DIR" ]]; then
  exit 0
fi

CMD=$(printf '%q ' "$TARGET_SCRIPT" "$TARGET_DIR")

exec bash -lc "$CMD"
