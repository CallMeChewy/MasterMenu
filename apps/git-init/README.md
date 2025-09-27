# Initialize Git Repo

## Overview
Turn an existing folder into a Git repository: run `git init`, set the default branch to `main`, and stub `README.md`/`.gitignore` files.

## Setup
- Requires Git installed and available on PATH.
- Prompts gather the target directory; no configuration files are needed.

## Storage & Output
- Operates directly on the chosen directory (creates `.git`, README, `.gitignore`).
- `OUTPUT_ROOT` defaults to `MASTERMENU_WORKDIR` or `apps/git-init/data/`; the script does not persist additional files there.

## CLI Usage
- Launch via MasterMenu or run `apps/git-init/run.sh`.
- Run headless by calling `bin/git-init.sh /path/to/project` (wrappers expose `git-init` on PATH once regenerated).

## Notes
- Existing repositories remain untouched; `git init` simply reports the current state.
- Edit the generated `.gitignore` to suit the project immediately after scaffolding.
