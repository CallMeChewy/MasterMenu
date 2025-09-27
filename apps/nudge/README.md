# Save State Nudge

Runs a simple timer that reminds you to save your session notes. Set the interval in minutes when launching from the menu.

## Usage

1. Enter the desired interval (default 30 minutes) when prompted.
2. A terminal window prints a reminder message after each interval along with the current timestamp.
3. Close the terminal or press `Ctrl+C` to stop the loop.

## Tips

- Predefine the interval by exporting `NUDGE_INTERVAL_MINUTES` before launching.
- Point the terminal output to a log file if you want an audit trail of reminders.
