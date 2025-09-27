#!/usr/bin/env bash
set -euo pipefail

PROJECT_PATH=${1:-}

if [[ -z "$PROJECT_PATH" ]]; then
  echo "Usage: ai-project.sh <absolute_project_path>"
  exit 1
fi

PROJECT_NAME=$(basename "$PROJECT_PATH")
TARGET_DIR=$(dirname "$PROJECT_PATH")

mkdir -p "$PROJECT_PATH"/{src,tests,docs}

touch "$PROJECT_PATH/README.md"

cat > "$PROJECT_PATH/requirements.txt" <<'EOL'
PySide6
requests
langchain-ollama
langchain-core
EOL

cat > "$PROJECT_PATH/.gitignore" <<'EOL'
__pycache__/
*.py[cod]
*$py.class
.env
.venv
*.log
.DS_Store
EOL

cat > "$PROJECT_PATH/src/main.py" <<'EOL'
from PySide6.QtWidgets import QApplication, QMainWindow
import sys

def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
EOL

echo "Created AI project structure in $PROJECT_PATH"

(
  cd "$PROJECT_PATH"
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install PySide6 requests langchain-ollama langchain-core
  git init
  git branch -M main
)

echo "Project initialized and ready for development"
if command -v tree >/dev/null 2>&1; then
  tree "$PROJECT_PATH"
fi
