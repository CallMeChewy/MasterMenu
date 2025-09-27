#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TARGET_SCRIPT="$SCRIPT_DIR/bin/new-proj.sh"

find_project_startup() {
  local candidates=(
    "$SCRIPT_DIR/Project_Startup"
    "$PROJECT_ROOT/Project_Startup"
    "$(dirname "$PROJECT_ROOT")/Project_Startup"
    "$HOME/Desktop/Project_Startup"
  )
  for candidate in "${candidates[@]}"; do
    if [[ -d "$candidate" ]]; then
      printf '%s\n' "$(cd "$candidate" && pwd)"
      return 0
    fi
  done
  return 1
}

show_error() {
  local message="$1"
  if command -v zenity >/dev/null 2>&1; then
    zenity --error --title="Project Startup" --text="$message" 2>/dev/null || true
  else
    python3 - <<PY
import sys
try:
    import tkinter as tk
    from tkinter import messagebox
except Exception:
    print(sys.argv[1])
    sys.exit(0)
root = tk.Tk()
root.withdraw()
messagebox.showerror("Project Startup", sys.argv[1])
PY
 "$message"
  fi
}

prompt_args() {
  if command -v zenity >/dev/null 2>&1; then
    zenity --entry --title="Project Startup" --text="Optional CLI arguments:" --entry-text="" 2>/dev/null || echo ""
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
value = simpledialog.askstring("Project Startup", "Optional CLI arguments:")
if value:
    print(value)
PY
  fi
}

PROJECT_DIR=$(find_project_startup)
if [[ -z "$PROJECT_DIR" ]]; then
  show_error "Project_Startup could not be located. Place it inside MasterMenu or as a sibling directory."
  exit 1
fi

EXTRA_INPUT=$(prompt_args)
ARGS=()
if [[ -n "$EXTRA_INPUT" ]]; then
  while IFS= read -r line; do
    ARGS+=("$line")
  done < <(python3 - <<'PY'
import shlex, sys
for token in shlex.split(sys.argv[1]):
    print(token)
PY
"$EXTRA_INPUT")
fi

CMD_PARTS=("$TARGET_SCRIPT" "$PROJECT_DIR")
CMD_PARTS+=("${ARGS[@]}")
CMD=$(printf '%q ' "${CMD_PARTS[@]}")

exec bash -lc "$CMD"
