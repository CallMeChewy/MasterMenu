# GPU Monitor

## Overview
Open a terminal running `watch nvidia-smi` to monitor GPU utilisation, memory, and active processes.

## Setup
- Requires NVIDIA drivers and the `nvidia-smi` CLI.
- Optional: set `NVIDIA_INTERVAL_SECONDS` to change the refresh rate (default 1s).

## Storage & Output
- No files are created; output streams live in the terminal.
- `OUTPUT_ROOT`/`TMP_ROOT` directories are initialised but unused.

## CLI Usage
- Launch from MasterMenu or run `apps/nvidia/run.sh`.
- Execute `bin/nvidia.sh` directly (wrappers expose `nvidia` on PATH after regeneration) to start the monitor from any shell.

## Notes
- Falls back to the current shell when `gnome-terminal` is unavailable—tune the launcher if you prefer a different terminal emulator.
- Stop monitoring with `Ctrl+C` or by closing the window.
