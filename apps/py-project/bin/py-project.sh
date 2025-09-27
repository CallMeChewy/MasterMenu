#!/usr/bin/env bash
set -euo pipefail

PROJECT_PATH=${1:-}

if [[ -z "$PROJECT_PATH" ]]; then
  echo "Usage: py-project.sh <absolute_project_path>"
  exit 1
fi

mkdir -p "$PROJECT_PATH"/{src,tests,docs}

touch "$PROJECT_PATH/README.md"
touch "$PROJECT_PATH/requirements.txt"
touch "$PROJECT_PATH/src/__init__.py"
touch "$PROJECT_PATH/tests/__init__.py"

cat > "$PROJECT_PATH/.gitignore" <<'EOL'
__pycache__/
*.py[cod]
*$py.class
.env
.venv
*.log
EOL

echo "Created Python project structure in $PROJECT_PATH"
if command -v tree >/dev/null 2>&1; then
  tree "$PROJECT_PATH"
fi
