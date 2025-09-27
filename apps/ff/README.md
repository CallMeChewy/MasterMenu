# Desktop Exact Finder

## Overview
Prompt for an exact filename and search the Desktop tree for matches, printing any hits to the terminal.

## Setup
- Depends on standard Unix tools (`find`) and optional GUI prompts (Zenity or Tkinter fallback).
- No configuration required.

## Storage & Output
- Emits search results to the terminal only; no persistent files are generated.
- `OUTPUT_ROOT`/`TMP_ROOT` directories are created but unused.

## CLI Usage
- Launch from the menu or run `apps/ff/run.sh` for the same prompt flow.
- For automation, call `bin/ff.sh "filename"` to search without GUI prompts. Wrappers will surface `ff` on PATH after regeneration.

## Notes
- Adjust the search path or pattern behaviour in `bin/ff.sh` if you need globbing or alternate directories.
- When Zenity is absent, a Tk window collects the search term.
