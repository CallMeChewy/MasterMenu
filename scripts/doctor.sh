#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
APPS_DIR="$ROOT_DIR/apps"
EXIT_CODE=0

check_run_scripts() {
  while IFS= read -r -d '' run_script; do
    if [[ "$run_script" == *"/_template/"* ]]; then
      continue
    fi
    if [[ ! -x "$run_script" ]]; then
      echo "[FAIL] run.sh not executable: ${run_script#$ROOT_DIR/}" >&2
      EXIT_CODE=1
    fi
  done < <(find "$APPS_DIR" -maxdepth 2 -type f -name run.sh -print0)
}

check_app_manifests() {
  if ! python3 - "$APPS_DIR" <<'PY'
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:
    sys.exit(f"PyYAML is required for doctor checks: {exc}")

root = Path(sys.argv[1])
failed = False

for app_yaml in sorted(root.glob('*/app.yaml')):
    if app_yaml.parent.name == '_template':
        continue
    try:
        data = yaml.safe_load(app_yaml.read_text()) or {}
    except yaml.YAMLError as exc:
        print(f"[FAIL] cannot parse {app_yaml.relative_to(root.parent)}: {exc}")
        failed = True
        continue
    required = ['id', 'name', 'command']
    missing = [key for key in required if key not in data or data[key] in (None, '')]
    if missing:
        print(f"[FAIL] {app_yaml.relative_to(root.parent)} missing fields: {', '.join(missing)}")
        failed = True
    icon = data.get('icon')
    if icon:
        icon_path = app_yaml.parent / icon
        if not icon_path.exists():
            print(f"[FAIL] icon not found for {data.get('id', app_yaml.parent.name)}: {icon_path}")
            failed = True
    tags = data.get('tags')
    if tags is not None and not isinstance(tags, (list, tuple)):
        print(f"[FAIL] tags must be a list in {app_yaml.relative_to(root.parent)}")
        failed = True

if failed:
    sys.exit(1)
PY
  then
    EXIT_CODE=1
  fi
}

check_launch_script() {
  if ! bash -n "$ROOT_DIR/launch_mastermenu.sh"; then
    echo "[FAIL] launch_mastermenu.sh failed shellcheck parsing" >&2
    EXIT_CODE=1
  fi
}

check_run_scripts
check_app_manifests
check_launch_script

if [[ $EXIT_CODE -eq 0 ]]; then
  echo "All checks passed."
fi

exit "$EXIT_CODE"
