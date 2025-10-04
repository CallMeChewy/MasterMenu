#!/bin/bash
# File: run.sh
# Path: /home/herb/Desktop/MasterMenu/apps/image-browser/run.sh
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 04:20PM

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies if needed
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the application
echo "Starting Image Browser..."
python3 app.py