#!/bin/bash

__DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# Configuration
REPO_DIR="$__DIR/.."
VENV_DIR="$REPO_DIR/.venv"

# Ensure the virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Setting up Python environment (one-time setup)..."
    cd "$REPO_DIR" || exit 1
    python3 -m venv "$VENV_DIR"
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate" || exit 1
    pip install -e .
    deactivate
fi

# Activate the virtual environment and run the command
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate" || exit 1

# Determine which script to run
case "$1" in
    create-release)
        shift
        python -m src.create_release "$@"
        ;;
    delete-release)
        shift
        python -m src.delete_release "$@"
        ;;
    rollback-release)
        shift
        python -m src.rollback_release "$@"
        ;;
    update-params-release-tag)
        shift
        python -m src.update_params_release_tag "$@"
        ;;
    demo-release-pipeline)
        shift
        python -m src.demo_release_pipeline "$@"
        ;;
    *)
        echo "Usage: pipeline-helpers COMMAND [ARGS]"
        echo ""
        echo "Available commands:"
        echo "  create-release"
        echo "  delete-release"
        echo "  rollback-release"
        echo "  update-params-release-tag"
        echo "  demo-release-pipeline"
        ;;
esac

# Deactivate the virtual environment
deactivate