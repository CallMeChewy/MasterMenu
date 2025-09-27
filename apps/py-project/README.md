# Bootstrap Python Project

## Overview
Scaffold a lightweight Python project (no virtualenv) with `src/`, `tests/`, docs, and boilerplate files.

## Setup
- Requires `python3` for basic scripting and standard Unix utilities (`mkdir`, `cp`, etc.).
- Prompts collect the project name and destination folder.

## Storage & Output
- Generates project files within the selected directory.
- `OUTPUT_ROOT` defaults to `MASTERMENU_WORKDIR` or `apps/py-project/data/`; no additional files are written there.

## CLI Usage
- Launch from the menu or run `apps/py-project/run.sh`.
- Use `bin/py-project.sh <parent-dir> <project-name>` for automation; wrappers will expose `py-project` on PATH after regeneration.

## Generated Files
- `README.md`, `requirements.txt`, `.gitignore` tuned for Python.
- `src/__init__.py` and `tests/__init__.py` plus placeholder directories.
