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

if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

OUTPUT_ROOT=${OUTPUT_ROOT:-${MASTERMENU_WORKDIR:-"$SCRIPT_DIR/data"}}
TMP_ROOT=${TMP_ROOT:-"$OUTPUT_ROOT/tmp"}
mkdir -p "$OUTPUT_ROOT" "$TMP_ROOT"

export OUTPUT_ROOT TMP_ROOT

PYTHON_BIN="/home/herb/.pyenv/shims/python"
APP_ROOT="/home/herb/Desktop/LLM-Tester"
APP_SCRIPT="$APP_ROOT/LLM-Tester.py"

if [[ ! -x "$PYTHON_BIN" ]]; then
  printf 'Python shim not found at %s\n' "$PYTHON_BIN" >&2
  exit 1
fi

if [[ ! -f "$APP_SCRIPT" ]]; then
  printf 'LLM Tester script missing at %s\n' "$APP_SCRIPT" >&2
  exit 1
fi

cd "$APP_ROOT"

CMD=("$PYTHON_BIN" "$APP_SCRIPT" "$@")

if command -v gnome-terminal >/dev/null 2>&1; then
  gnome-terminal -- bash -lc "$(printf '%q ' "${CMD[@]}")"
else
  exec "${CMD[@]}"
fi
