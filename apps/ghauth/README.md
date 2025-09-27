# GitHub CLI Login

## Overview
Launch `gh auth login` in a terminal to refresh GitHub CLI credentials quickly.

## Setup
- Requires GitHub CLI installed and available on PATH.
- Needs internet access for the login device/web flow.

## Storage & Output
- The GitHub CLI stores credentials in its standard config location; this tool does not write additional files.
- `OUTPUT_ROOT`/`TMP_ROOT` directories are created but unused.

## CLI Usage
- Launch from MasterMenu or run `apps/ghauth/run.sh`.
- To skip the menu, execute `bin/ghauth.sh` directly or, after wrapper generation, call `ghauth` from PATH.

## Notes
- Choose the authentication method (web, device, token) when prompted by `gh`.
- Close the terminal when the login flow completes.
