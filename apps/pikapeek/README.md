# PikaPeek Backup Explorer

## Overview
Launch the PikaPeek Borg backup explorer UI for browsing repositories and restoring files.

## Setup
- Requires the external `PikaPeek` project at `/home/herb/Desktop/PikaPeek` with its scripts intact.
- No virtualenv is used here; the project manages its own dependencies.

## Storage & Output
- MasterMenu directs run artifacts to `~/.local/share/mastermenu/pikapeek/<timestamp>/` when launched from the UI; nothing is written there by default.
- Temporary files created by PikaPeek remain under its own project directory.

## CLI Usage
- Launch from the menu or run `bin/pikapeek` after adding `$(pwd)/bin` to your PATH.
- Optional arguments are forwarded to `run-backup-explorer.sh` if needed.
