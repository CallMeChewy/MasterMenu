# Repository Guidelines

## Project Structure & Module Organization
Source code for the launcher lives in `src/`, with Qt UI logic centralized in `main_window.py`. Tool definitions sit under `apps/<tool-id>/`, each owning its `run.sh`, manifest, README, and optional `.venv/`. Shared icons remain in `assets/`, while `bin/` hosts PATH-exposed wrappers and `scripts/` contains maintenance utilities. Persistent backups of manifests land in `backups/`, and MasterMenu-managed run artifacts default to `~/.local/share/mastermenu/<tool-id>/`.

## Build, Test, and Development Commands
Create a fresh virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Launch the GUI with `./launch_mastermenu.sh` or `python src/main.py`. Use `scripts/doctor.sh` for a quick sanity check, `scripts/new-tool.sh <tool-id> [--with-wrapper]` to scaffold a tool, and `scripts/update-wrappers.sh` to regenerate CLI wrappers from manifests.
Expose wrappers by adding the repo bin directory to PATH:
```bash
export PATH="$(pwd)/bin:$PATH"
```
Re-run `scripts/update-wrappers.sh` whenever manifests change or you toggle the `cli` tag.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation and snake_case for Python. Keep per-tool scripts self-contained: the template `run.sh` resolves symlinks, activates local `.venv` instances, and honors `MASTERMENU_WORKDIR`/`OUTPUT_ROOT`. Document each tool in its README using the provided sections (setup, storage, CLI usage). Icons should live alongside the tool or in `assets/icons/` and be referenced relatively in `app.yaml`.

## Testing & Verification
Formal tests are pending; rely on manual runs plus `scripts/doctor.sh`, which verifies manifest structure, icon presence, run.sh executability, and `launch_mastermenu.sh` syntax. When adding automated tests, place them under `tests/` and wire them into the doctor script.

## Commit & Pull Request Guidelines
Write present-tense commits focused on observable behavior (e.g., `Add CLI wrapper generator`). Group related changes and keep diffs scoped. Pull requests should include: short summary, screenshots/GIFs for UI updates, manual test notes (GUI launch, script invocations), and links to issues or design docs. Mention any new scripts, env vars, or cleanup steps so reviewers can reproduce the workflow quickly.

## Maintenance & Ops Tips
Run `bin/mastermenu-clean` to prune timestamped workdirs (defaults to 14-day retention); add `--dry-run` or `--keep-days` as needed and consider a cron entry for routine cleanup. Tag CLI-friendly tools with `cli` in `app.yaml` so wrappers stay in sync. Store sensitive data outside the repo and reference via environment variables. When retiring a tool, remove its folder, wrapper, and `menu_config.yaml` references, then run `scripts/doctor.sh` to confirm a clean slate.
