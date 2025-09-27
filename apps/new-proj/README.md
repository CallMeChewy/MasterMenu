# Launch Project Startup

Launches the external Project_Startup PySide application after searching for the repository in several common locations (inside `MasterMenu`, as a sibling directory, or on the Desktop).

## Usage

1. Enable Maintenance Mode if you need to adjust the command, otherwise just launch the tool.
2. When prompted, provide optional CLI arguments (leave blank for the default workflow).
3. The script locates Project_Startup and opens a terminal to run `python src/main.py`.

## Troubleshooting

- If the repository cannot be located, you’ll see an error dialog. Move or symlink Project_Startup into one of the expected locations and rerun.
- Add new search paths by editing `apps/new-proj/run.sh` once you settle on a permanent directory layout.
