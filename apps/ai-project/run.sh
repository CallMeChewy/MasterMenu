#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SCRIPT="$SCRIPT_DIR/bin/ai-project.sh"

prompt_name() {
  if command -v zenity >/dev/null 2>&1; then
    zenity --entry --title="AI Project" --text="Project name:" 2>/dev/null || echo ""
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
value = simpledialog.askstring("AI Project", "Project name:")
if value:
    print(value)
PY
  fi
}

select_directory() {
  if command -v zenity >/dev/null 2>&1; then
    zenity --file-selection --directory --title="Select parent directory" --filename="$HOME/Desktop/" 2>/dev/null || echo ""
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
path = filedialog.askdirectory(title="Select parent directory")
if path:
    print(path)
PY
  fi
}

confirm_overwrite() {
  local path="$1"
  if command -v zenity >/dev/null 2>&1; then
    zenity --question --title="Overwrite?" --text="Directory $path already exists. Continue?" --ok-label="Continue" --cancel-label="Cancel" 2>/dev/null
    return $?
  else
    read -r -p "Directory $path already exists. Continue? [y/N] " ans
    [[ "$ans" =~ ^[Yy]$ ]]
  fi
}

PROJECT_NAME=$(prompt_name)
if [[ -z "$PROJECT_NAME" ]]; then
  exit 0
fi

PARENT_DIR=$(select_directory)
if [[ -z "$PARENT_DIR" ]]; then
  exit 0
fi

PROJECT_PATH="$PARENT_DIR/$PROJECT_NAME"

if [[ -e "$PROJECT_PATH" ]]; then
  if ! confirm_overwrite "$PROJECT_PATH"; then
    exit 0
  fi
fi

CMD=$(printf '%q ' "$TARGET_SCRIPT" "$PROJECT_PATH")

exec bash -lc "$CMD"
