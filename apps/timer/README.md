# Desktop Reminder Timer

## Overview
Launch the bundled Tk reminder app in the background so MasterMenu stays available.

## Setup
- Optional: install `playsound` into the tool’s `.venv` for audio alerts.
- Configure interval, message, and audio file inside the GUI.

## Storage & Output
- The app stores preferences in memory only; no files are created.
- When run from MasterMenu, `OUTPUT_ROOT`/`TMP_ROOT` resolve to the run directory but remain unused.

## CLI Usage
- Launch from MasterMenu or call `apps/timer/run.sh` to open the GUI.
- This tool is not exposed as a CLI wrapper by default since it requires user interaction.

## Usage Tips
- Click **Start Reminder** to begin; reminders show as dialogs and optional sounds.
- Stop via **Stop Reminder** or close the window when finished.
