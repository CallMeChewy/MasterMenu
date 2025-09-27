# MasterMenu

MasterMenu consolidates local helper scripts and mini-apps into a PySide6 desktop launcher with maintenance tooling.

## Quick Start

1. **Install dependencies**
   ```bash
   cd MasterMenu
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Launch the UI**
   ```bash
   ./launch_mastermenu.sh
   ```
   The script prefers `.venv/bin/python`, falls back to `python3`, and surfaces desktop notifications if startup fails.
3. Explore tools from the **Launcher** tab. Toggle **Maintenance Mode** to edit metadata, categories, and ordering in-app.

## Features

- YAML-driven manifests (`apps/<tool>/app.yaml`, `menu_config.yaml`) keep ordering predictable and editable in code or UI.
- Standardised tool scaffold (`apps/_template`) with symlink-safe `run.sh`, storage conventions, and README placeholders.
- Automation helpers under `scripts/`: `new-tool.sh` clones the template, `update-wrappers.sh` regenerates PATH wrappers, and `doctor.sh` validates manifests/run scripts.
- CLI wrappers in `bin/` mirror menu tools when tagged `cli`, so a subset of utilities can be invoked directly from any shell.
- Automatic backups of manifests/configs (`backups/`) and per-run work directories under `~/.local/share/mastermenu` (trim via `bin/mastermenu-clean`).

## Structure

```
MasterMenu/
├── apps/                # Individual tool folders + `_template`
├── assets/              # Shared icons and placeholders
├── bin/                 # Generated CLI wrappers + maintenance utilities
├── scripts/             # Repo tooling (doctor, scaffolding, wrapper sync)
├── backups/             # Manifest/config snapshots
├── menu_config.yaml     # Tab/category definitions for the launcher UI
├── launch_mastermenu.sh # Preferred entry point for the UI
├── requirements.txt     # PySide6 + PyYAML deps
└── src/                 # PySide6 application code
```

## Maintenance Notes

- Prefer `scripts/new-tool.sh <tool-id> [--with-wrapper]` when adding entries; it updates manifests and optional `bin/` wrappers automatically.
- Run `scripts/doctor.sh` before committing to catch missing icons, non-executable `run.sh`, or syntax errors.
- If you expose wrappers system-wide, add `$(pwd)/bin` to your `PATH` and re-run `scripts/update-wrappers.sh` whenever manifests change.
- Use **Reload Configuration** in the UI after editing YAML by hand; backups are created automatically under `backups/`.
- Periodically prune run artifacts with `bin/mastermenu-clean --dry-run` to preview deletions, then schedule it (cron/anacron) with an appropriate `--keep-days` value.
