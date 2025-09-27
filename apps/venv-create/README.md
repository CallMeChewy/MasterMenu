# Create Virtualenv

## Overview
Prompt for a directory and optional virtualenv name, then run `python3 -m venv` plus `pip install --upgrade pip`.

## Setup
- Requires system `python3` with the `venv` module.
- Prompts gather the target directory and folder name.

## Storage & Output
- Virtualenv is created in the destination you choose (default `.venv`).
- `OUTPUT_ROOT` defaults to `MASTERMENU_WORKDIR` or `apps/venv-create/data/`; the tool itself does not write additional files.

## CLI Usage
- Launch from MasterMenu or run `apps/venv-create/run.sh`.
- Automate with `bin/venv-create.sh <target-dir> [venv-name]`. PATH wrappers will expose `venv-create` after regeneration.

## Notes
- Re-running with the same path reuses the environment; delete it to start fresh.
- Install project dependencies manually after the virtualenv is created.
