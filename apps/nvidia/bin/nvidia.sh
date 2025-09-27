#!/usr/bin/env bash
set -euo pipefail

INTERVAL=${NVIDIA_INTERVAL_SECONDS:-1}
exec watch -n "$INTERVAL" nvidia-smi
