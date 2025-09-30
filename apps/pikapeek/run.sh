#!/usr/bin/env bash
set -euo pipefail

resolve_script_dir() {
  local source="${BASH_SOURCE[0]}"
  while [[ -h "$source" ]]; do
    local dir
    dir="$(cd -P "$(dirname "$source")" && pwd)"
    source="$(readlink "$source")"
    [[ $source != /* ]] && source="$dir/$source"
  done
  cd -P "$(dirname "$source")" && pwd
}

SCRIPT_DIR="$(resolve_script_dir)"
cd "$SCRIPT_DIR"

activate_venv() {
  local candidate="$1"
  if [[ -x "$candidate/bin/python" ]]; then
    # shellcheck disable=SC1091
    source "$candidate/bin/activate"
    printf '%s' "$candidate/bin/python"
    return 0
  fi
  return 1
}

PYTHON_BIN=""
if python_candidate="$(activate_venv "$SCRIPT_DIR/.venv" 2>/dev/null)"; then
  PYTHON_BIN="$python_candidate"
elif python_candidate="$(activate_venv "$SCRIPT_DIR/../../.venv" 2>/dev/null)"; then
  PYTHON_BIN="$python_candidate"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  printf 'python3 not found. Create a virtualenv or install system Python.\n' >&2
  exit 1
fi

OUTPUT_ROOT=${OUTPUT_ROOT:-${MASTERMENU_WORKDIR:-"$SCRIPT_DIR/data"}}
TMP_ROOT=${TMP_ROOT:-"$OUTPUT_ROOT/tmp"}
mkdir -p "$OUTPUT_ROOT" "$TMP_ROOT"
export OUTPUT_ROOT TMP_ROOT

# Default working folders used by the explorer UI
RECOVERY_ROOT=${PIKAPEEK_RECOVERY_PATH:-"$OUTPUT_ROOT/recovered"}
TEMP_ROOT=${PIKAPEEK_TEMP_PATH:-"$TMP_ROOT/preview"}
mkdir -p "$RECOVERY_ROOT" "$TEMP_ROOT"
export PIKAPEEK_RECOVERY_PATH="$RECOVERY_ROOT"
export PIKAPEEK_TEMP_PATH="$TEMP_ROOT"

# Home prefix inside Borg archives (usually home/<user>)
HOME_PREFIX=${PIKAPEEK_HOME_PREFIX:-${HOME#/}}
export PIKAPEEK_HOME_PREFIX="$HOME_PREFIX"

# Discover Borg repositories if none specified
REPO_ENV_VAR=PIKAPEEK_REPO_PATH
REPO_ROOT=${PIKAPEEK_REPO_ROOT:-/media}
if [[ -z "${!REPO_ENV_VAR:-}" && -d "$REPO_ROOT" ]]; then
  mapfile -t candidate_paths < <(
    PIKA_ROOT="$REPO_ROOT" "$PYTHON_BIN" - <<'PY'
import os
import re
import sys

root = os.environ.get('PIKA_ROOT', '/media')
if not os.path.isdir(root):
    sys.exit(0)

date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}$")
choices = set()
for current_root, dirnames, _ in os.walk(root):
    depth = os.path.relpath(current_root, root).count(os.sep)
    if depth > 4:
        dirnames[:] = []
        continue
    for dirname in list(dirnames):
        full_path = os.path.join(current_root, dirname)
        if 'pika' not in full_path.lower():
            continue
        if date_pattern.search(dirname) and os.path.isdir(full_path):
            choices.add(os.path.normpath(full_path))

for path in sorted(choices):
    print(path)
PY
  )

  if [[ ${#candidate_paths[@]} -eq 1 ]]; then
    export "$REPO_ENV_VAR"="${candidate_paths[0]}"
  elif [[ ${#candidate_paths[@]} -gt 1 ]]; then
    printf 'Multiple backup repositories detected under %s.\n' "$REPO_ROOT"
    PS3="Select repository: "
    select selected_path in "${candidate_paths[@]}"; do
      if [[ -n "$selected_path" ]]; then
        export "$REPO_ENV_VAR"="$selected_path"
        break
      fi
    done
  fi
fi

EXPLORER_SCRIPT="$SCRIPT_DIR/explorer/SimplePikaExplorer.py"
if [[ ! -f "$EXPLORER_SCRIPT" ]]; then
  printf 'Explorer script missing at %s\n' "$EXPLORER_SCRIPT" >&2
  exit 1
fi

export QT_QPA_PLATFORM=${QT_QPA_PLATFORM:-xcb}

exec "$PYTHON_BIN" "$EXPLORER_SCRIPT" "$@"
