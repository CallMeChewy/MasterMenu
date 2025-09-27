#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

notify_failure() {
  local message=$1
  if command -v zenity >/dev/null 2>&1; then
    zenity --error --title="MasterMenu" --text="$message" || true
  elif command -v notify-send >/dev/null 2>&1; then
    notify-send "MasterMenu" "$message" || true
  else
    printf '%s\n' "$message" >&2
  fi
}

PYTHON_BIN=""
if [[ -x .venv/bin/python ]]; then
  PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
  # shellcheck disable=SC1091
  source .venv/bin/activate
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
fi

if [[ -z "$PYTHON_BIN" ]]; then
  notify_failure "Python interpreter not found. Run 'python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt' from the MasterMenu folder to set up the environment."
  exit 1
fi

if ! "$PYTHON_BIN" "$SCRIPT_DIR/src/main.py" "$@"; then
  notify_failure "MasterMenu failed to start. Open a terminal in $SCRIPT_DIR and run './launch_mastermenu.sh' to view the error output."
  exit 1
fi
