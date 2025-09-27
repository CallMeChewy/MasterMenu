# Save State Nudge

## Overview
Start a loop that periodically prints a reminder message to save work. Choose the interval in minutes at launch.

## Setup
- No dependencies beyond standard shell utilities. Optional Zenity or Tk prompts improve the UX.
- The interval defaults to 30 minutes but can be overridden via prompt or `NUDGE_INTERVAL_MINUTES` env var.

## Storage & Output
- Emits reminders to the terminal; no files are written.
- `OUTPUT_ROOT`/`TMP_ROOT` directories are initialised and can be cleared if unused.

## CLI Usage
- Launch via MasterMenu or run `apps/nudge/run.sh`.
- For scripting, set `NUDGE_INTERVAL_MINUTES` and call `bin/nudge.sh`; wrappers will expose `nudge` on PATH after regeneration.

## Tips
- Redirect stdout to a log file if you want an audit trail (`bin/nudge.sh >> reminders.log`).
- Stop the loop with `Ctrl+C` or by closing the terminal.
