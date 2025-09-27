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
