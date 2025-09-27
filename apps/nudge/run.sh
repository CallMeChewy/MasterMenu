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

TARGET_SCRIPT="$SCRIPT_DIR/bin/nudge.sh"

prompt_interval() {
  if command -v zenity >/dev/null 2>&1; then
    zenity --entry --title="Nudge Interval" --text="Minutes between reminders:" --entry-text="30" 2>/dev/null || echo ""
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
value = simpledialog.askstring("Nudge Interval", "Minutes between reminders:", initialvalue="30")
if value:
    print(value)
PY
  fi
}

RAW_INTERVAL=$(prompt_interval)
if [[ -z "$RAW_INTERVAL" ]]; then
  RAW_INTERVAL=30
fi

if ! [[ "$RAW_INTERVAL" =~ ^[0-9]+$ ]]; then
  RAW_INTERVAL=30
fi

if command -v gnome-terminal >/dev/null 2>&1; then
  NUDGE_INTERVAL_MINUTES="$RAW_INTERVAL" gnome-terminal -- bash -lc "'$TARGET_SCRIPT'"
else
  NUDGE_INTERVAL_MINUTES="$RAW_INTERVAL" bash "$TARGET_SCRIPT" &
fi
