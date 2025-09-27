#!/usr/bin/env bash
set -euo pipefail

DEFAULT_REPO="CallMeChewy/AndyLibrary"

prompt_repo() {
  if command -v zenity >/dev/null 2>&1; then
    zenity --entry --title="GitHub Repo" --text="owner/repo to purge workflow runs:" --entry-text="$DEFAULT_REPO" 2>/dev/null || echo ""
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
value = simpledialog.askstring("GitHub Repo", "owner/repo to purge workflow runs:", initialvalue="CallMeChewy/AndyLibrary")
if value:
    print(value)
PY
  fi
}

confirm_action() {
  if command -v zenity >/dev/null 2>&1; then
    zenity --question --title="Delete workflow runs" --text="Delete ALL runs for $1?" --ok-label="Delete" --cancel-label="Cancel" 2>/dev/null
    return $?
  else
    python3 - "$1" <<'PY'
import sys
repo = sys.argv[1]
try:
    import tkinter as tk
    from tkinter import messagebox
except Exception:
    sys.exit(1)

root = tk.Tk()
root.withdraw()
answer = messagebox.askyesno(
    "Delete workflow runs",
    f"Delete ALL runs for {repo}?",
    icon=messagebox.WARNING,
)
sys.exit(0 if answer else 1)
PY
    return $?
  fi
}

REPO_INPUT=$(prompt_repo)
if [[ -z "$REPO_INPUT" ]]; then
  echo "No repository provided; aborting."
  exit 0
fi

if ! confirm_action "$REPO_INPUT"; then
  echo "Cancelled."
  exit 0
fi

PER_PAGE=100

echo "Deleting all workflow runs in $REPO_INPUT..."

while true; do
  RUN_IDS=$(gh api "repos/$REPO_INPUT/actions/runs?per_page=$PER_PAGE" --jq '.workflow_runs[].id')

  if [[ -z "$RUN_IDS" ]]; then
    echo "No more runs to delete."
    break
  fi

  for ID in $RUN_IDS; do
    echo "Deleting run $ID..."
    gh api -X DELETE "repos/$REPO_INPUT/actions/runs/$ID"
  done
done

echo "✅ All deletable workflow runs have been removed."
