# PikaPeek Backup Explorer

## Overview
PikaPeek is a Qt UI for browsing Borg backup archives and restoring either individual files or entire directory trees. This copy ships inside MasterMenu so the launcher no longer depends on the external Desktop checkout.

## Setup
- Ensure the MasterMenu virtualenv has PySide6 available (run `pip install -r requirements.txt` from the repo root).
- Optionally bootstrap an app-scoped environment:
  ```bash
  python3 -m venv apps/pikapeek/.venv
  source apps/pikapeek/.venv/bin/activate
  pip install PySide6 borgbackup
  ```
- Point the explorer at your Borg repository with one of the following:
  - Export `PIKAPEEK_REPO_PATH=/path/to/repo` for a fixed location, or
  - Leave it unset and let the launcher search under `PIKAPEEK_REPO_ROOT` (defaults to `/media`).

## Storage & Output
- MasterMenu seeds `OUTPUT_ROOT` to `~/.local/share/mastermenu/pikapeek/<timestamp>/` when launched from the UI; recovery copies land in `$OUTPUT_ROOT/recovered` by default and previews in `$TMP_ROOT/preview`.
- Override the destinations with `PIKAPEEK_RECOVERY_PATH` and `PIKAPEEK_TEMP_PATH` if you prefer another workspace.

## Environment Controls
- `PIKAPEEK_REPO_PATH` – explicit Borg repository (takes precedence over scanning).
- `PIKAPEEK_REPO_ROOT` – directory tree to scan for candidate Pika repositories when none are set.
- `PIKAPEEK_HOME_PREFIX` – archive root to present in the quick-access list (defaults to `home/<username>`).
- `PIKAPEEK_RECOVERY_PATH` / `PIKAPEEK_TEMP_PATH` – override the final and preview copy locations.
- `PIKAPEEK_LIST_TIMEOUT` / `PIKAPEEK_EXTRACT_TIMEOUT` – optional timeouts (seconds) passed to Borg commands.

## CLI Usage
- Launch from MasterMenu or run `bin/pikapeek` after exporting `PATH="$(pwd)/bin:$PATH"`.
- When multiple dated repositories are discovered you will be prompted to pick one before the UI opens.
- Use the quick-access list to jump directly into common folders; the **Full Restore** panel can rebuild any subtree into the configured destination with live progress output.
