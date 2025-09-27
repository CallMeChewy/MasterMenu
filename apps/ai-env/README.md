# AI Env Bootstrap

## Overview
Provision a Python virtual environment in a directory you choose, then install PySide6, requests, langchain-ollama, and langchain-core. Handy for spinning up an AI-ready sandbox inside an existing project.

## Setup
- Requires system `python3` with `venv` support and internet access for dependency installs.
- No additional configuration; the script activates the environment before performing `pip install` operations.

## Storage & Output
- Virtualenv contents live in the directory you select (default `.venv`).
- `OUTPUT_ROOT` defaults to `MASTERMENU_WORKDIR` or `apps/ai-env/data/` when run standalone; current script does not persist extra logs but the directory is created for consistency.
- Temporary work files land in `$OUTPUT_ROOT/tmp` and are safe to delete.

## CLI Usage
- Launch from the menu or run `apps/ai-env/run.sh` directly. Supply a target dir/name via prompts or pass them as arguments to `bin/ai-env.sh`.
- Once CLI wrappers are generated (`scripts/update-wrappers.sh`), invoke `bin/ai-env <target-dir> [venv-name]` from anywhere in your PATH.

## Tips
- Re-run to refresh dependencies; existing virtualenvs are reused.
- Activate the environment later with `source <venv>/bin/activate` to continue working in the same shell.
