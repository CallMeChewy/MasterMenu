# Bootstrap AI Project

Creates a new project directory with PySide6 boilerplate, LangChain-friendly dependencies, and an initialized Git repository. Run this when you want a fully provisioned desktop AI starter app.

## What You Get

- `src/main.py` with a minimal PySide6 window
- `tests/` and `docs/` folders plus README/requirements boilerplate
- `.venv` populated with PySide6, requests, langchain-ollama, langchain-core
- Git repository initialised with `main` as the default branch

## Usage

1. Launch the tool and provide the project name.
2. Choose the parent directory (Desktop is suggested by default).
3. Confirm overwriting if the folder already exists.
4. A terminal window provisions the tree, sets up the virtualenv, installs packages, runs `git init`, and prints a final `tree` listing when available.

After completion, open the new folder in your editor of choice and activate the environment with `source .venv/bin/activate`.
