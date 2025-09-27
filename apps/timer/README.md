# Desktop Reminder Timer

Launches the Tk-based reminder application that ships with this repository. The script spawns the GUI in the background so the menu remains usable.

## Usage

1. Set the interval (minutes), reminder message, and audio file path inside the GUI.
2. Click **Start Reminder** to begin the loop; you’ll receive a dialog and optional sound every interval.
3. Use **Stop Reminder** when you’re done.

## Requirements & Tips

- Install `playsound` inside `.venv` if audio cues are missing: `pip install playsound`.
- A default `Do Something.wav` lives alongside the script; swap it for any `.wav`/`.mp3` file via the browse button.
- Close the reminder window to exit entirely; the menu process stays untouched.
