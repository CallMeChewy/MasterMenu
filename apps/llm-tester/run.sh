#!/bin/bash
# File: run.sh
# Path: /home/herb/Desktop/MasterMenu/apps/llm-tester/run.sh
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-04
# Last Modified: 2025-10-04 7:00PM

# LLM-Tester Launcher for MasterMenu Integration
# Handles virtual environment, dependencies, and path management

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] LLM-Tester:${NC} $1"
}

error() {
    echo -e "${RED}[ERROR] LLM-Tester:${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARN] LLM-Tester:${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO] LLM-Tester:${NC} $1"
}

# Resolve script directory (handles symlinks)
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

# MasterMenu environment setup
setup_mastermenu_env() {
    # Use MasterMenu work directory if available
    OUTPUT_ROOT=${OUTPUT_ROOT:-${MASTERMENU_WORKDIR:-"$PROJECT_ROOT/data"}}
    TMP_ROOT=${TMP_ROOT:-"$OUTPUT_ROOT/tmp"}
    mkdir -p "$OUTPUT_ROOT" "$TMP_ROOT"

    export OUTPUT_ROOT TMP_ROOT
    export LLM_TESTER_ROOT="$PROJECT_ROOT"

    log "MasterMenu environment initialized"
    info "Output directory: $OUTPUT_ROOT"
}

# Virtual environment management
setup_venv() {
    local venv_path="$PROJECT_ROOT/.venv"

    if [[ ! -d "$venv_path" ]]; then
        log "Creating virtual environment..."
        python3 -m venv "$venv_path"
    fi

    # Activate virtual environment
    source "$venv_path/bin/activate"

    # Upgrade pip
    pip install --upgrade pip setuptools wheel --quiet

    log "Virtual environment activated: $venv_path"
}

# Install dependencies
install_dependencies() {
    log "Installing required dependencies..."

    local requirements=(
        "PySide6"
        "matplotlib"
        "seaborn"
        "pandas"
        "numpy"
        "scipy"
        "requests"
        "pyyaml"
        "psutil"
        "pillow"
    )

    for package in "${requirements[@]}"; do
        log "Installing $package..."
        pip install "$package" --quiet
    done

    log "Dependencies installed successfully"
}

# Validate installation
validate_installation() {
    log "Validating installation..."

    local errors=0

    # Check essential files
    local essential_files=(
        "src/LLM_Tester_Enhanced.py"
        "lib/path_manager.py"
        "config/config.yaml"
    )

    for file in "${essential_files[@]}"; do
        if [[ ! -f "$PROJECT_ROOT/$file" ]]; then
            error "Missing essential file: $file"
            ((errors++))
        fi
    done

    # Check Python modules
    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/lib')
try:
    from path_manager import get_path_manager
    print('✅ Path manager module OK')
except Exception as e:
    print(f'❌ Path manager module error: {e}')
    sys.exit(1)
" 2>/dev/null || {
        error "Path manager validation failed"
        ((errors++))
    }

    if [[ $errors -gt 0 ]]; then
        error "Validation failed with $errors errors"
        return 1
    fi

    log "✅ Installation validation passed"
}

# Setup external data symlinks if needed
setup_external_links() {
    # Check if there's existing desktop data to link to
    local desktop_data="$HOME/Desktop/LLM-Tester"
    local external_data_dir="$PROJECT_ROOT/data/external"

    if [[ -d "$desktop_data" ]] && [[ ! -L "$external_data_dir" ]]; then
        info "Found existing LLM-Tester data on desktop, creating symlink..."
        mkdir -p "$PROJECT_ROOT/data"
        ln -sf "$desktop_data" "$external_data_dir"
        log "Created symlink: $external_data_dir -> $desktop_data"
    fi
}

# Initialize path manager
init_path_manager() {
    log "Initializing path manager..."

    export PYTHONPATH="$PROJECT_ROOT/lib:$PROJECT_ROOT/src:${PYTHONPATH:-}"

    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/lib')
from path_manager import get_path_manager

try:
    pm = get_path_manager()
    print('✅ Path manager initialized successfully')
    print(f'   App root: {pm.app_root}')
    print(f'   Data directory: {pm.get_path(\"data_dir\")}')
    print(f'   Results directory: {pm.get_path(\"results_dir\")}')

    # Validate installation
    issues = pm.validate_installation()
    if issues:
        print('⚠️  Installation issues found:')
        for issue in issues:
            print(f'   - {issue}')
    else:
        print('✅ Installation is valid')

except Exception as e:
    print(f'❌ Path manager initialization failed: {e}')
    sys.exit(1)
" 2>/dev/null || {
        error "Path manager initialization failed"
        return 1
    }
}

# Run the application
run_application() {
    log "Starting LLM-Tester Enhanced..."

    # Change to project directory
    cd "$PROJECT_ROOT"

    # Find Python executable
    local python_bin
    if [[ -x "/home/herb/.pyenv/shims/python" ]]; then
        python_bin="/home/herb/.pyenv/shims/python"
    elif command -v python3 >/dev/null 2>&1; then
        python_bin="python3"
    else
        error "No Python executable found"
        return 1
    fi

    # Run the enhanced application
    local app_script="$PROJECT_ROOT/src/LLM_Tester_Enhanced.py"
    if [[ ! -f "$app_script" ]]; then
        error "Application script not found: $app_script"
        return 1
    fi

    log "✅ Starting application with: $python_bin $app_script"

    # Launch in terminal if available, otherwise execute directly
    local cmd=("$python_bin" "$app_script" "$@")

    # MasterMenu integration: prefer direct execution when in MasterMenu environment
    if [[ -n "${MASTERMENU_TERMINAL:-}" ]] || [[ -n "${MASTERMENU_WORKDIR:-}" ]]; then
        # Running from MasterMenu - execute directly
        log "Launching from MasterMenu environment"
        exec "${cmd[@]}"
    elif command -v gnome-terminal >/dev/null 2>&1; then
        # Standalone execution - use terminal
        log "Launching in new terminal window"
        gnome-terminal -- bash -lc "$(printf '%q ' "${cmd[@]}")" &
    else
        # Fallback to direct execution
        log "Launching directly (no terminal available)"
        exec "${cmd[@]}"
    fi
}

# Cleanup function
cleanup() {
    # Kill any background processes
    if [[ -n "${LLM_TESTER_PID:-}" ]]; then
        kill "$LLM_TESTER_PID" 2>/dev/null || true
    fi
}

# Setup signal handlers
trap cleanup EXIT INT TERM

# Main execution
main() {
    log "🚀 Starting LLM-Tester launcher..."
    info "Project directory: $PROJECT_ROOT"

    # Setup MasterMenu environment
    setup_mastermenu_env

    # Setup environment
    setup_venv
    install_dependencies
    validate_installation

    # Setup external links
    setup_external_links

    # Initialize path manager
    init_path_manager

    # Run the application
    log "✅ All setup complete, launching application..."
    run_application "$@"
}

# Help function
show_help() {
    cat << EOF
LLM-Tester Enhanced Launcher

Usage: $0 [OPTIONS] [APPLICATION_ARGS]

Options:
    --help, -h          Show this help message
    --validate-only     Only validate installation, don't run app
    --reinstall         Force reinstallation of dependencies
    --clean             Clean virtual environment and reinstall

Examples:
    $0                              # Run with default settings
    $0 --validate-only              # Check installation only
    $0 --reinstall                  # Reinstall dependencies
    $0 --debug                      # Run with debug output

For more information, see: $PROJECT_ROOT/README.md
EOF
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --validate-only)
        log "Validation mode only"
        setup_mastermenu_env
        setup_venv
        validate_installation
        init_path_manager
        log "✅ Validation complete"
        exit 0
        ;;
    --reinstall)
        log "Reinstall mode"
        rm -rf "$PROJECT_ROOT/.venv"
        ;;
    --clean)
        log "Clean mode - removing virtual environment"
        rm -rf "$PROJECT_ROOT/.venv"
        log "Virtual environment removed. Please run again to recreate."
        exit 0
        ;;
    "")
        # Default case - run normally
        ;;
    *)
        # Pass through to application
        log "Passing arguments to application: $*"
        ;;
esac

# Run main function
main "$@"
