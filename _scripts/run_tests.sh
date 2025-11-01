#!/bin/bash
set -eo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

VENV_PATH="$PROJECT_ROOT/tests/.venv"
REQS_PATH="$PROJECT_ROOT/tests/requirements.txt"

setup_environment() {
    echo "Setting up Python virtual environment..."
    
    if ! command -v python3 &> /dev/null; then
        echo "Error: python3 is not installed or not in PATH."
        exit 1
    fi

    # Clean up old environment if it exists
    if [ -d "$VENV_PATH" ]; then
        echo "Removing existing virtual environment."
        rm -rf "$VENV_PATH"
    fi

    echo "Creating virtual environment at $VENV_PATH..."
    python3 -m venv "$VENV_PATH"

    echo "Installing dependencies from $REQS_PATH..."
    "$VENV_PATH/bin/pip" install -r "$REQS_PATH"
    echo "Setup complete."
}

if [[ "$1" == "--build" ]]; then
    setup_environment
    shift # Consume the --build argument
fi

if [ ! -d "$VENV_PATH" ]; then
    echo "Virtual environment not found. Please run with the --build flag to create it:"
    echo "  $0 --build"
    exit 1
fi

source "$VENV_PATH/bin/activate"

echo "Running integration tests..."
pytest -v "$PROJECT_ROOT/tests/" "$@"
