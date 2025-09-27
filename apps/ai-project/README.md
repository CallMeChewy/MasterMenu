# Bootstrap AI Project

## Overview
Scaffold a PySide6/LangChain desktop starter app: creates a project folder, provisions a virtualenv with baseline dependencies, and initialises a Git repository.

## Setup
- Requires `python3`, `git`, and internet access for dependency installation.
- No configuration files needed; prompts gather project name and destination.

## Storage & Output
- Generates the project tree in the directory you select (`<parent>/<project-name>`).
- `OUTPUT_ROOT` defaults to `MASTERMENU_WORKDIR` or `apps/ai-project/data/` and currently only hosts transient logs; `$OUTPUT_ROOT/tmp` is safe to prune.
- The script itself does not modify existing repositories beyond running `git init` if invoked inside one.

## CLI Usage
- Launch from MasterMenu or call `apps/ai-project/run.sh` to walk through the prompts.
- Under the hood, `bin/ai-project.sh` accepts positional arguments: `bin/ai-project <parent-dir> <project-name>`. Wrappers will expose `ai-project` on PATH after `scripts/update-wrappers.sh` runs.

## Deliverables
- `src/main.py`, `tests/`, `docs/`, README template, and requirements file.
- `.venv` populated with PySide6, requests, langchain-ollama, langchain-core.
- Git repository with `main` as the default branch.

After provisioning, `cd` into the project and activate the environment with `source .venv/bin/activate` to continue development.
