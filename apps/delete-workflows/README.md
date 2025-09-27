# Purge GitHub Workflow Runs

Bulk delete GitHub Actions workflow runs for a repository. The script prompts for the target repo (defaulting to `CallMeChewy/AndyLibrary`) and asks for confirmation before removing runs via the GitHub CLI.

## Usage

1. Launch the tool and enter the `owner/repo` string when prompted.
2. Confirm the destructive action.
3. A terminal window enumerates each workflow run and deletes it via `gh api` calls.

## Requirements

- GitHub CLI (`gh`) installed and authenticated (`gh auth login`).
- Sufficient permissions to delete workflow history for the repository.

## Safety

- The script loops until no runs remain. Stop the terminal if you entered the wrong repository.
- Consider exporting metrics or audit information before wiping the history.
