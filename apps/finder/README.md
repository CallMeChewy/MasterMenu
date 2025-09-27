# Finder Utility

## Overview
Launch the Finder desktop search utility implemented in Python.

## Setup
- Depends on the external Finder project at `/home/herb/Desktop/Finder` and the `~/.pyenv/shims/python` interpreter.
- No virtualenv is managed here; the Finder project supplies its own dependencies.

## Storage & Output
- MasterMenu sets `OUTPUT_ROOT` to `~/.local/share/mastermenu/finder/<timestamp>/`, though the tool does not write to that directory by default.
- Finder itself handles any caching/logs inside its project folder.

## CLI Usage
- Launch from MasterMenu or run `bin/finder` once `$(pwd)/bin` is on your PATH.
- Additional arguments are forwarded to `Finder.py` if the script supports them.
