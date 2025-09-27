# AI Services Status

## Overview
Performs quick health checks against the Ollama stack: confirms the daemon process is running and the REST API responds to `/api/tags`.

## Setup
- Requires `pgrep`, `curl`, and a locally installed Ollama service.
- No configuration files; the endpoint defaults to `http://localhost:11434`.

## Storage & Output
- Writes status output to the invoking terminal only; no files persist under `OUTPUT_ROOT`.
- `OUTPUT_ROOT`/`TMP_ROOT` directories are still created for consistency when launching via MasterMenu or CLI.

## CLI Usage
- Launch from the menu or execute `apps/ai-services/run.sh`.
- Direct access to the core logic is available via `bin/ai-services.sh`; PATH wrappers will expose `ai-services` once generated.

## Notes
- If the API check fails, inspect the terminal logs for HTTP status codes or network errors.
- Update the endpoint in `bin/ai-services.sh` if your daemon listens on a different port.
