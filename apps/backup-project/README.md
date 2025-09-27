# Project Backup

Choose a project directory and copy it into `~/Desktop/Projects_Backup` with a timestamp suffix. Use this for manual checkpoints before risky changes.

## Usage

1. Launch the tool and select the project folder you want to snapshot.
2. The script mirrors the directory into `~/Desktop/Projects_Backup/<name>_<timestamp>`.
3. A terminal window prints the destination path when the copy completes.

## Notes

- Backups are full copies, so large projects take longer and consume disk space. Prune the backup folder periodically.
- Pass a path argument when launching from the CLI (`bash run.sh /path/to/project`) to automate backups for scripts.
