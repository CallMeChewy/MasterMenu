# Launch Project Startup

## Overview
Locate the external `Project_Startup` repository and launch its PySide application, optionally forwarding command-line arguments.

## Setup
- Requires the `Project_Startup` project cloned locally; the script checks common paths but you can update them in `run.sh`.
- Depends on system `python3` and whatever packages `Project_Startup` requires.

## Storage & Output
- No artifacts are written under `OUTPUT_ROOT`; the launched app handles its own storage.
- Error dialogs surface when the repository cannot be found.

## CLI Usage
- Launch from MasterMenu or run `apps/new-proj/run.sh`.
- To bypass prompts, call `bin/new-proj.sh -- <args>` once wrappers are regenerated; optional CLI arguments are forwarded to the downstream app.

## Troubleshooting
- If the repository path changes, add it to the search list near the top of `run.sh`.
- Ensure `Project_Startup` dependencies are installed before launching.
