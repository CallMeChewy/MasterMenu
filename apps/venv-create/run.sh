#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SCRIPT="$SCRIPT_DIR/bin/venv-create.sh"

select_directory() {
  if command -v zenity >/dev/null 2>&1; then
    zenity --file-selection --directory --title="Select target directory" --filename="$HOME/" 2>/dev/null || echo ""
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
path = filedialog.askdirectory(title="Select target directory")
if path:
    print(path)
PY
  fi
}

prompt_name() {
  if command -v zenity >/dev/null 2>&1; then
    zenity --entry --title="Virtualenv Name" --text="Enter virtualenv folder name:" --entry-text=".venv" 2>/dev/null || echo ""
  else
    python3 - <<'PY'
import sys
try:
    import tkinter as tk
    from tkinter import simpledialog
except Exception:
    sys.exit(0)
root = tk.Tk()
root.withdraw()
value = simpledialog.askstring("Virtualenv Name", "Enter virtualenv folder name:", initialvalue=".venv")
if value:
    print(value)
PY
  fi
}

TARGET_DIR=$(select_directory)
if [[ -z "$TARGET_DIR" ]]; then
  exit 0
fi

VENV_NAME=$(prompt_name)
if [[ -z "$VENV_NAME" ]]; then
  VENV_NAME=.venv
fi

CMD=$(printf '%q ' "$TARGET_SCRIPT" "$TARGET_DIR" "$VENV_NAME")

exec bash -lc "$CMD"
