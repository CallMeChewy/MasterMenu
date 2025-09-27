#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SCRIPT="$SCRIPT_DIR/bin/ff.sh"

prompt_with_tk() {
  python3 - <<'PY'
import sys
try:
    import tkinter as tk
    from tkinter import simpledialog
except Exception:
    sys.exit(0)
root = tk.Tk()
root.withdraw()
value = simpledialog.askstring("Desktop Exact Match Search", "Enter file or folder name:")
if value:
    print(value)
PY
}

if command -v zenity >/dev/null 2>&1; then
  SEARCH_PHRASE=$(zenity --entry --title="Desktop Exact Match Search" --text="Enter file or folder name:" 2>/dev/null || true)
else
  SEARCH_PHRASE=$(prompt_with_tk)
fi

if [[ -z "${SEARCH_PHRASE}" ]]; then
  exit 0
fi

exec bash "$TARGET_SCRIPT" "$SEARCH_PHRASE"
