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
export QT_QPA_PLATFORM=${QT_QPA_PLATFORM:-xcb}

APP_SCRIPT="$SCRIPT_DIR/Finder.py"

if [[ ! -f "$APP_SCRIPT" ]]; then
  printf 'Finder script missing at %s\n' "$APP_SCRIPT" >&2
  exit 1
fi

exec "$PYTHON_BIN" "$APP_SCRIPT" "$@"
