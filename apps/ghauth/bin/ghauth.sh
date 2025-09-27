#!/usr/bin/env bash
set -euo pipefail

echo "GitHub CLI authentication"
exec gh auth login
