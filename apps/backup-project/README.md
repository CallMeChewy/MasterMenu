# Project Backup

## Overview
Create a timestamped copy of a project directory under `~/Desktop/Projects_Backup`. Useful for manual restore points before big changes.

## Setup
- Relies on `rsync` (or `cp -r` depending on the implementation in `bin/backup-project.sh`).
- No configuration files; prompts gather the source directory.

## Storage & Output
- Destination path: `~/Desktop/Projects_Backup/<name>_<timestamp>`.
- `OUTPUT_ROOT` defaults to `MASTERMENU_WORKDIR` or `apps/backup-project/data/` but is only used for transient logs; `$OUTPUT_ROOT/tmp` can be cleared safely.
- Backed-up data persists until you delete it manually.

## CLI Usage
- Run from the menu or execute `apps/backup-project/run.sh`.
- Non-interactive usage: `bin/backup-project.sh /path/to/project` (optionally pass a custom destination). Wrappers will expose `backup-project` on PATH after regeneration.

## Notes
- Large projects take time and disk space. Periodically trim `~/Desktop/Projects_Backup`.
- Automate routine backups via cron by calling the wrapper with explicit arguments.
