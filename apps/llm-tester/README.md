# LLM Tester

## Overview
Open the local LLM Tester interface for exercising models served on your machine.

## Setup
- Requires the external LLM-Tester project at `/home/herb/Desktop/LLM-Tester`.
- Depends on the `~/.pyenv/shims/python` interpreter and whatever packages that project needs.

## Storage & Output
- MasterMenu launches the app with `MASTERMENU_WORKDIR` pointing to `~/.local/share/mastermenu/llm-tester/<timestamp>/`, though the tester typically writes logs/configs inside its own repo.
- Terminal output appears in a dedicated window (via `gnome-terminal` when available).

## CLI Usage
- Run from MasterMenu or execute `bin/llm-tester`; supply any additional arguments you normally pass to `LLM-Tester.py`.
- Without `gnome-terminal`, the process runs in your current shell.
