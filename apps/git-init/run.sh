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
