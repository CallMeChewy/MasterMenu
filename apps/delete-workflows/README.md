# Purge GitHub Workflow Runs

## Overview
Bulk delete GitHub Actions workflow runs for a specified repository using the GitHub CLI.

## Setup
- Requires GitHub CLI (`gh`) installed and authenticated (`gh auth login`).
- Provide the `owner/repo` string when prompted.

## Storage & Output
- No local files are created; all output streams to the terminal.
- `OUTPUT_ROOT`/`TMP_ROOT` directories are initialised but unused and can be pruned.

## CLI Usage
- Launch from MasterMenu or run `apps/delete-workflows/run.sh`.
- Direct invocation: `bin/delete-workflows.sh <owner/repo>` with optional flags for dry runs. Wrappers will expose `delete-workflows` on PATH after regeneration.

## Safety
- The script loops until GitHub reports no remaining runs. Abort the terminal if you selected the wrong repository.
- Export audit data before purging if you need historical metrics.
