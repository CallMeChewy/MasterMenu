#!/usr/bin/env bash
set -euo pipefail

INTERVAL=${NUDGE_INTERVAL_MINUTES:-30}
INTERVAL_SECONDS=$((INTERVAL * 60))

while true; do
    sleep "$INTERVAL_SECONDS"
    echo
    echo "--- REMINDER: Consider saving session state to Restart.md ---"
    echo "--- Current time: $(date) ---"
    echo
done
