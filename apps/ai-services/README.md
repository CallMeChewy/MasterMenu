# AI Services Status

Runs a pair of quick checks to confirm the Ollama daemon is active and its HTTP API is responding. Useful for verifying the local AI stack before launching dependent tools.

## What It Does

- Uses `pgrep` to ensure the `ollama` process is alive
- Calls `curl http://localhost:11434/api/tags` to verify the REST endpoint
- Prints a concise ✓/✗ summary in a terminal window

## Notes

- No configuration is required, but the script assumes Ollama listens on the default port.
- If the API check fails, inspect the terminal logs for network or authentication errors.
