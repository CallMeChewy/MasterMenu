# GPU Monitor

Launches a terminal window that runs `watch -n 1 nvidia-smi` so you can track GPU utilisation, memory pressure, and active processes.

## Usage

- Run the tool to open a dedicated terminal displaying the `nvidia-smi` output.
- Press `Ctrl+C` or close the terminal window when finished.
- Set `NVIDIA_INTERVAL_SECONDS` to change the refresh cadence (e.g., `export NVIDIA_INTERVAL_SECONDS=5`).

## Notes

- Requires NVIDIA drivers plus the `nvidia-smi` CLI bundled with them.
- Falls back to the current shell if `gnome-terminal` is unavailable; adjust the launcher script if you prefer another terminal emulator.
