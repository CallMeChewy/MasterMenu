# Desktop Exact Finder

Prompts for a file or folder name and scans the Desktop directory tree for exact matches. Results appear in a terminal window.

## Usage

1. Launch the tool and enter the exact name you are looking for (case-sensitive).
2. The script runs `find ~/Desktop -name "<term>" -print` and streams any matches.
3. Close the terminal or press `Ctrl+C` after reviewing the output.

## Notes

- If Zenity is unavailable, a Tk input dialog is used as a fallback.
- Use shell wildcards by editing `apps/ff/bin/ff.sh` if you need pattern matching; the default is exact search.
