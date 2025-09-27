#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: ff <search_phrase>"
  exit 1
fi

SEARCH_PHRASE="$1"
SEARCH_PATH="$HOME/Desktop"

echo "Searching for '$SEARCH_PHRASE' in '$SEARCH_PATH'..."
TMP_FILE=$(mktemp)
trap 'rm -f "$TMP_FILE"' EXIT

find "$SEARCH_PATH" -name "$SEARCH_PHRASE" -print | tee "$TMP_FILE"

if [[ ! -s "$TMP_FILE" ]]; then
  MESSAGE="No matches found for '$SEARCH_PHRASE'."
else
  MESSAGE="Results stored in $TMP_FILE"
fi

if command -v zenity >/dev/null 2>&1; then
  if [[ -s "$TMP_FILE" ]]; then
    zenity --text-info --title="Search results" --filename="$TMP_FILE" --width=640 --height=480 2>/dev/null || true
  else
    zenity --info --title="Search results" --text="$MESSAGE" 2>/dev/null || true
  fi
else
  python3 - "$TMP_FILE" "$MESSAGE" <<'PY'
import os
import sys
filepath, message = sys.argv[1], sys.argv[2]
try:
    import tkinter as tk
    from tkinter import messagebox, scrolledtext
except Exception:
    print(message)
    if filepath and os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as fh:
            print(fh.read())
    sys.exit()

root = tk.Tk()
root.withdraw()
if not filepath or not os.path.getsize(filepath):
    messagebox.showinfo("Search results", message)
else:
    window = tk.Toplevel(root)
    window.title("Search results")
    text = scrolledtext.ScrolledText(window, width=80, height=24)
    text.pack(fill=tk.BOTH, expand=True)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as fh:
        text.insert(tk.END, fh.read())
    text.config(state=tk.DISABLED)
    window.mainloop()
PY
fi
