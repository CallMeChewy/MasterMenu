#!/usr/bin/env bash
set -euo pipefail

resolve_script_dir() {
  local source="${BASH_SOURCE[0]}"
  while [[ -h "$source" ]]; do
    local dir
    dir="$(cd -P "$(dirname "$source")" && pwd)"
    source="$(readlink "$source")"
    [[ $source != /* ]] && source="$dir/$source"
  done
  cd -P "$(dirname "$source")" && pwd
}

SCRIPT_DIR="$(resolve_script_dir)"
cd "$SCRIPT_DIR"

if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

OUTPUT_ROOT=${OUTPUT_ROOT:-${MASTERMENU_WORKDIR:-"$SCRIPT_DIR/data"}}
TMP_ROOT=${TMP_ROOT:-"$OUTPUT_ROOT/tmp"}
mkdir -p "$OUTPUT_ROOT" "$TMP_ROOT"

export OUTPUT_ROOT TMP_ROOT

TARGET_SCRIPT="$SCRIPT_DIR/bin/py-project.sh"

prompt_name() {
  if command -v zenity >/dev/null 2>&1; then
    zenity --entry --title="New Python Project" --text="Project name:" 2>/dev/null || echo ""
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
value = simpledialog.askstring("New Python Project", "Project name:")
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
