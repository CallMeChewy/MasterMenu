# Finder Utility

## Overview
Finder is now bundled directly inside MasterMenu. It provides multi-variable
logical searches across files, inline formula validation (with green/yellow
visual feedback), test-suite driven examples, and per-variable case controls.

## Setup
- Optional virtualenv: create `apps/finder/.venv` and `pip install -r apps/finder/requirements.txt`.
- Otherwise ensure the root `.venv` or system Python includes `PySide6` and the
  few helper packages listed in `requirements.txt`.

## Storage & Output
- `OUTPUT_ROOT` / `TMP_ROOT` default to `~/.local/share/mastermenu/finder/<ts>`
  like other tools; Finder mostly writes to stdout/GUI.
- The educational suites generate content in-memory only. No Desktop checkout is
  required anymore.

## CLI Usage
- Launch from MasterMenu or run `bin/finder` once `$(pwd)/bin` is on your PATH`.
- All CLI arguments are forwarded to the underlying `Finder.py` script.
