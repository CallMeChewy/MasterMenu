# MasterMenu Developer Toolkit Blueprint

## Goals & Operating Principles

- Provide a single, organized surface for heterogeneous tools (from one-line scripts to full GUIs) while keeping each self-contained.
- Ensure every tool remains runnable both from the MasterMenu GUI and directly via shell/IDE without behavioral drift.
- Keep onboarding lean: predictable folder contracts, scripted scaffolding, and concise documentation per tool.

## Repository Layout & Ownership

```
MasterMenu/
├── src/            # PySide6 launcher
├── apps/           # One folder per tool (plus `_template` scaffold)
├── assets/         # Shared icons and placeholders
├── backups/        # Auto-saved manifests/config snapshots
├── bin/            # Optional CLI wrappers exposed on PATH
├── launch_mastermenu.sh
├── MasterMenu.desktop
└── AGENTS.md, DESIGN.md
```

- Each `apps/<tool-id>/` folder owns its runtime, assets, venv, docs, and output policy.
- `_template/` defines the canonical scaffold: `run.sh`, `app.yaml`, `README.md`, `icon.png`, `.gitignore`.

## Tool Lifecycle

1. **Create**: `./scripts/new-tool.sh <tool-id>` copies `_template`, nudges metadata edits, and optionally adds a `bin/` wrapper.
2. **Configure**: Update `app.yaml` (command, synopsis, category). Link the tool in `menu_config.yaml`.
3. **Develop**: Keep logic in `run.sh` or language-specific modules inside the tool folder; rely on `settings.py` only when interacting with launcher-level assets.
4. **Document**: Capture setup notes, external dependencies, and storage behavior in `apps/<tool-id>/README.md`.
5. **Retire**: Remove the folder and associated entries from `menu_config.yaml`; prune wrappers and stale data directories.

## Runtime Modes & Entry Points

- **MasterMenu** launches `run.sh` directly. The Qt launcher sets `MASTERMENU_WORKDIR` per run (see Storage Strategy).
- **CLI/IDE** usage relies on PATH-exposed wrappers under `bin/` (export with `export PATH="$(pwd)/bin:$PATH"`):
  
  ```bash
  #!/usr/bin/env bash
  exec /home/herb/Desktop/MasterMenu/apps/nudge/run.sh "$@"
  ```
- All `run.sh` scripts use a symlink-safe resolver to normalize relative paths:
  
  ```bash
  resolve_script_dir() {
    local source="${BASH_SOURCE[0]}"
    while [ -h "$source" ]; do
      local dir="$(cd -P "$(dirname "$source")" && pwd)"
      source="$(readlink "$source")"
      [[ $source != /* ]] && source="$dir/$source"
    done
    cd -P "$(dirname "$source")" && pwd
  }
  SCRIPT_DIR="$(resolve_script_dir)"
  cd "$SCRIPT_DIR"
  ```

## Environment & Execution Policy

- Repository-level `.venv` powers the launcher (`launch_mastermenu.sh` auto-falls back to `python3`/`python`).
- Tool-specific dependencies belong in `apps/<tool>/.venv` and activate conditionally inside `run.sh` to keep isolation when run from Terminal or GUI.
- Commands in `app.yaml` must route through `run.sh` even for trivial scripts, preserving consistent startup behavior and logging.

## Storage Strategy

- Default output roots:
  
  ```bash
  OUTPUT_ROOT=${MASTERMENU_WORKDIR:-"$SCRIPT_DIR/data"}
  TMP_ROOT=$OUTPUT_ROOT/tmp
  mkdir -p "$OUTPUT_ROOT" "$TMP_ROOT"
  ```
- **MasterMenu launches** set `MASTERMENU_WORKDIR="$HOME/.local/share/mastermenu/<tool-id>/<timestamp>"` via the Qt launcher (`MainWindow.launch_tool`). A scheduled sweeper prunes stale timestamped folders.
- **Standalone launches** default to the tool’s local `data/`. Tools can accept overrides (`--output`, `OUTPUT_ROOT=...`) for project-specific runs.
- Document whether artifacts are ephemeral (Purge after N days) or persistent (Version-controlled). Place cleanup helpers under `bin/mastermenu-clean` to automate temp pruning.

## Maintenance & Automation

- Continuous hygiene: `bin/mastermenu-clean` (default 14-day retention with dry-run flag), backup rotation in `backups/`, and a `scripts/doctor.sh` that validates manifests, icons, and executable bits.
- Add CI hooks (even simple shell scripts) to lint `app.yaml` schemas, verify `run.sh` executability, and ensure `launch_mastermenu.sh` still boots.
- Encourage a quarterly review: audit tool usefulness, delete stale folders, update icons, refresh READMEs.

## Presentation & Future Enhancements

- UI surfaces metadata directly; keep names/synopsis short and actionable. Provide icons per tool for quick scanning.
- Potential roadmap: drag-and-drop ordering, manifest diff viewer, environment diagnostics, and one-click log access for failed runs.
- Iterate on this blueprint as tooling grows; keep the philosophy of “consistent shells, independent runtimes” intact.
