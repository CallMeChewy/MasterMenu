#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $(basename "$0") <tool-id> [--name "Display Name"] [--category slug] [--synopsis "Short description"] [--with-wrapper]

Creates a new tool scaffold under apps/<tool-id>/ from the template and optionally
adds a PATH-friendly wrapper in bin/.
USAGE
}

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 1
fi

TOOL_ID=""
TOOL_NAME=""
TOOL_CATEGORY=""
TOOL_SYNOPSIS=""
WITH_WRAPPER=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --name)
      TOOL_NAME=${2-}
      shift 2
      ;;
    --category)
      TOOL_CATEGORY=${2-}
      shift 2
      ;;
    --synopsis)
      TOOL_SYNOPSIS=${2-}
      shift 2
      ;;
    --with-wrapper)
      WITH_WRAPPER=1
      shift
      ;;
    --*)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
    *)
      if [[ -z "$TOOL_ID" ]]; then
        TOOL_ID=$1
        shift
      else
        echo "Unexpected argument: $1" >&2
        exit 1
      fi
      ;;
  esac
done

if [[ -z "$TOOL_ID" ]]; then
  echo "Tool ID is required." >&2
  exit 1
fi

ROOT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
TEMPLATE_DIR="$ROOT_DIR/apps/_template"
TARGET_DIR="$ROOT_DIR/apps/$TOOL_ID"

if [[ ! -d "$TEMPLATE_DIR" ]]; then
  echo "Template directory $TEMPLATE_DIR not found." >&2
  exit 1
fi

if [[ -e "$TARGET_DIR" ]]; then
  echo "Target directory $TARGET_DIR already exists." >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"
cp -R "$TEMPLATE_DIR"/. "$TARGET_DIR"/

chmod +x "$TARGET_DIR/run.sh"

if [[ -z "$TOOL_NAME" ]]; then
  TOOL_NAME=$(python3 - "$TOOL_ID" <<'PY'
import sys
slug = sys.argv[1]
words = slug.replace('_', '-').split('-')
print(' '.join(w.capitalize() for w in words if w) or slug)
PY
)
fi

if [[ -z "$TOOL_CATEGORY" ]]; then
  TOOL_CATEGORY="utilities"
fi

if [[ -z "$TOOL_SYNOPSIS" ]]; then
  TOOL_SYNOPSIS="Describe what this tool does."
fi

APP_YAML="$TARGET_DIR/app.yaml"
if [[ -f "$APP_YAML" ]]; then
  python3 "$APP_YAML" "$TOOL_ID" "$TOOL_NAME" "$TOOL_SYNOPSIS" "$TOOL_CATEGORY" <<'PY'
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    sys.exit(f"PyYAML is required to customize {sys.argv[1]}: {exc}")

app_yaml = Path(sys.argv[1])
tool_id = sys.argv[2]
tool_name = sys.argv[3]
synopsis = sys.argv[4]
category = sys.argv[5]

data = yaml.safe_load(app_yaml.read_text())
data["id"] = tool_id
data["name"] = tool_name
data["synopsis"] = synopsis
data["category"] = category

app_yaml.write_text(yaml.dump(data, sort_keys=False))
PY
fi

README_MD="$TARGET_DIR/README.md"
if [[ -f "$README_MD" ]]; then
  python3 "$README_MD" "$TOOL_NAME" <<'PY'
import sys
from pathlib import Path

readme = Path(sys.argv[1])
tool_name = sys.argv[2]

lines = readme.read_text().splitlines()
if lines:
    lines[0] = f"# {tool_name}"
readme.write_text("\n".join(lines) + "\n")
PY
fi

if [[ $WITH_WRAPPER -eq 1 ]]; then
  WRAPPER_DIR="$ROOT_DIR/bin"
  mkdir -p "$WRAPPER_DIR"
  WRAPPER_PATH="$WRAPPER_DIR/$TOOL_ID"
  cat <<WRAPPER > "$WRAPPER_PATH"
#!/usr/bin/env bash
set -euo pipefail
EXEC_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)/apps/$TOOL_ID"
exec "${EXEC_DIR}/run.sh" "\$@"
WRAPPER
  chmod +x "$WRAPPER_PATH"
fi

echo "Created $TARGET_DIR"
if [[ $WITH_WRAPPER -eq 1 ]]; then
  echo "Wrapper installed at bin/$TOOL_ID"
fi

echo "Next steps:\n  - Edit apps/$TOOL_ID/app.yaml to fine-tune metadata.\n  - Update apps/$TOOL_ID/README.md with setup/storage details.\n  - Wire the tool into menu_config.yaml."
