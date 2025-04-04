#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Pipeline Helpers Installer${NC}"
echo "This script will install the pipeline-helpers package."
echo

# Check if Python is installed
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}Error: Python 3 is required but not found.${NC}"
    echo "Please install Python 3 and try again."
    exit 1
fi

# Create installation directory
INSTALL_DIR="$HOME/.pipeline-helpers"
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/wheels"

VERSION="$(VERSION)"
DIST_DIR="$(DIST_DIR)"

if [ -z "$VERSION" ]; then
    VERSION=$(grep -m 1 'version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
fi

if [ -z "$DIST_DIR" ]; then
    DIST_DIR=dist
fi

# Download the wheel file
echo "Downloading pipeline-helpers wheel package..."
# WHEEL_URL="https://example.com/dist/pipeline_helpers-$VERSION-py3-none-any.whl"
WHEEL_FILE="pipeline_helpers-$VERSION-py3-none-any.whl"

# For local installation, copy the wheel instead of downloading
if [ -f "$DIST_DIR/${WHEEL_FILE}" ]; then
    cp "$DIST_DIR/${WHEEL_FILE}" "$INSTALL_DIR/wheels/"
else
    # In a real scenario, you'd download from your hosting location
    echo -e "${RED}Wheel file not found locally.${NC}"
    echo "This script is meant to be distributed with the wheel file."
    echo "Run make install-script to create the wheel file."
    echo "Then you can execute this script from the dist folder."
    exit 1
fi

# Create a virtual environment if it doesn't exist
if [ ! -d "$INSTALL_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$INSTALL_DIR/venv"
fi

# Activate virtual environment and install the package
echo "Installing dependencies and package..."
source "$INSTALL_DIR/venv/bin/activate"
pip install --upgrade pip setuptools wheel
pip install "$INSTALL_DIR/wheels/$WHEEL_FILE"
deactivate

# Create wrapper scripts in ~/.local/bin
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

echo "Creating command wrappers..."

COMMANDS=()
while read -r cmd; do
    COMMANDS+=("$cmd")
done < <(find src/ -maxdepth 1 -type f -name "*.py" ! -name "__init__.py" ! -name "helpers.py" -exec basename {} .py \; | sed 's/_/-/g')

for CMD in "${COMMANDS[@]}"; do
    cat >"$BIN_DIR/$CMD" <<'WRAPPER'
#!/bin/bash
source "$HOME/.pipeline-helpers/venv/bin/activate"
WRAPPER
    cat >>"$BIN_DIR/$CMD" <<WRAPPER
$CMD "\$@"
deactivate
WRAPPER
    chmod +x "$BIN_DIR/$CMD"
done

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${BLUE}Adding ~/.local/bin to your PATH...${NC}"

    # Determine shell type
    SHELL_NAME=$(basename "$SHELL")

    if [ "$SHELL_NAME" = "bash" ]; then
        PROFILE_FILE="$HOME/.bashrc"
    elif [ "$SHELL_NAME" = "zsh" ]; then
        PROFILE_FILE="$HOME/.zshrc"
    else
        echo -e "${RED}Unsupported shell: $SHELL_NAME${NC}"
        echo "Please add the following line to your shell profile manually:"
        echo 'export PATH="$HOME/.local/bin:$PATH"'
        PROFILE_FILE=""
    fi

    if [ -n "$PROFILE_FILE" ]; then
        if grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$PROFILE_FILE"; then
            echo "PATH already configured in $PROFILE_FILE"
        else
            echo 'export PATH="$HOME/.local/bin:$PATH"' >>"$PROFILE_FILE"
            echo "PATH updated in $PROFILE_FILE"
            echo "Please restart your terminal or run: source $PROFILE_FILE"
        fi
    fi
fi

echo -e "${GREEN}Installation complete!${NC}"
echo "The following commands are now available:"
echo "  - create-release"
echo "  - delete-release"
echo "  - rollback-release"
echo "  - update-params-release-tag"
echo "  - demo-release-pipeline"
echo
echo "If the commands are not available, please add ~/.local/bin to your PATH or restart your terminal."
