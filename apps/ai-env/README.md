# AI Env Bootstrap

Creates a Python virtual environment in a directory you choose and installs PySide6, requests, langchain-ollama, and langchain-core. Ideal for spinning up an AI-focused interpreter inside an existing project workspace.

## Usage

1. Launch the tool from MasterMenu and pick the target folder that should contain the virtual environment.
2. Accept the default `.venv` name or supply a custom folder name when prompted.
3. A terminal window walks through `python -m venv`, `pip install --upgrade pip`, and installs the core dependencies. Watch for failures (e.g., missing internet access).

### Tips

- The script activates the environment before installing packages. Use the same terminal session to continue working, or run `source <venv>/bin/activate` later.
- Re-run to rebuild the environment if dependencies become stale; existing folders are reused.
