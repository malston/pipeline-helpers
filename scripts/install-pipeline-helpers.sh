#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Pipeline Helpers Installer${NC}"
echo "This script will install the pipeline-helpers tools on your system."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not found.${NC}"
    echo "Please install Python 3 and try again."
    exit 1
fi

# Create installation directory
INSTALL_DIR="$HOME/.pipeline-helpers"
mkdir -p "$INSTALL_DIR"

# Clone or update the repository
if [ -d "$INSTALL_DIR/repo" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR/repo"
    git pull
else
    echo "Downloading pipeline-helpers..."
    git clone https://github.com/malston/pipeline-helpers.git "$INSTALL_DIR/repo"
    cd "$INSTALL_DIR/repo"
fi

# Create a virtual environment if it doesn't exist
if [ ! -d "$INSTALL_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$INSTALL_DIR/venv"
fi

# Activate virtual environment and install the package
echo "Installing dependencies..."
source "$INSTALL_DIR/venv/bin/activate"
pip install --upgrade pip setuptools wheel
pip install -e .

# Explicitly install required dependencies
pip install packaging gitpython requests semver pyyaml ruff tabulate
deactivate

# Create wrapper scripts in ~/.local/bin
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

echo "Creating command wrappers..."

for CMD in create-release delete-release rollback-release update-params-release-tag demo-release-pipeline; do
    cat > "$BIN_DIR/$CMD" << EOF
#!/bin/bash
source "$INSTALL_DIR/venv/bin/activate"
$CMD "\$@"
deactivate
EOF
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
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$PROFILE_FILE"
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