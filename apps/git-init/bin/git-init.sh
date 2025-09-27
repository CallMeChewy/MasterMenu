#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR=${1:-}

if [[ -z "$TARGET_DIR" ]]; then
  echo "Usage: git-init.sh <target_directory>"
  exit 1
fi

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Directory does not exist: $TARGET_DIR" >&2
  exit 1
fi

cd "$TARGET_DIR"

git init
git branch -M main

touch README.md .gitignore

echo "Git repository initialized at $TARGET_DIR"
