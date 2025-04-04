# Makefile for pipeline-helpers development

.PHONY: setup venv install dev test lint format clean build build-wheel build-sdist publish activate security check-env update-tools install-package help install-script

PYTHON_VERSION ?= 3.11
SRC_DIR = src
TEST_DIR = tests
SCRIPT_DIR = scripts
DIST_DIR = dist
BUILD_DIR = build

# Detect Python executable (prefer python3 if available)
PYTHON := $(shell which python3 2>/dev/null || which python 2>/dev/null)
# Check if the Python version is 3.x
PYTHON_IS_3 := $(shell $(PYTHON) -c "import sys; print(sys.version_info[0]==3)" 2>/dev/null)

ifeq ($(PYTHON_IS_3),)
$(error Python 3 not found. Please install Python 3 and try again.)
endif

ifeq ($(PYTHON_IS_3),False)
$(error Python 3 required but Python 2 detected. Please use Python 3.)
endif

# Project version from pyproject.toml (using grep and sed)
VERSION := $(shell grep -m 1 'version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

# Default target when just running 'make'
help:
	@echo "Available commands:"
	@echo "  make setup           - Check Python environment and development tools"
	@echo "  make venv            - Create a virtual environment (uses uv if available)"
	@echo "  make install         - Install dependencies and package in development mode"
	@echo "  make dev             - Complete development setup (venv + install)"
	@echo "  make activate        - Show instructions to activate virtual environment"
	@echo "  make test            - Run tests"
	@echo "  make lint            - Run linting checks (ruff)"
	@echo "  make format          - Format code (black)"
	@echo "  make clean           - Remove build artifacts and cache directories"
	@echo "  make build           - Build package distribution files (wheel and sdist)"
	@echo "  make build-wheel     - Build wheel package only"
	@echo "  make build-sdist     - Build source distribution only"
	@echo "  make install-script  - Create installer script for end users"
	@echo "  make publish         - Publish package to PyPI (requires credentials)"
	@echo "  make check-env       - Check if development environment is properly set up"
	@echo "  make security        - Check dependencies for security vulnerabilities"
	@echo "  make update-tools    - Update pip, setuptools, and wheel to latest versions"
	@echo "  make install-package - Install the published pipeline-helpers package"

# Set up the development environment with pythonenv and uv
setup:
	@echo "Checking Python environment setup..."
	@echo "Python version: $$($(PYTHON) --version 2>&1)"
	@if command -v mise >/dev/null 2>&1; then \
		echo "mise found, you can use it to manage Python versions"; \
		echo "To install Python $(PYTHON_VERSION) with mise:"; \
		echo "  mise install python@$(PYTHON_VERSION)"; \
	elif command -v pyenv >/dev/null 2>&1; then \
		echo "pyenv found, you can use it to manage Python versions"; \
		echo "To install Python $(PYTHON_VERSION) with pyenv:"; \
		echo "  pyenv install $(PYTHON_VERSION)"; \
	else \
		echo "No version manager found. You can install one:"; \
		echo "  mise: curl https://mise.run | sh"; \
		echo "  pyenv: https://github.com/pyenv/pyenv#installation"; \
	fi
	@echo ""
	@echo "Checking for uv installation..."
	@if command -v uv >/dev/null 2>&1; then \
		echo "✓ uv is already installed"; \
	else \
		echo "uv not found. You can install it with:"; \
		echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"; \
	fi
	@echo ""
	@echo "Setup check complete. Next step: run 'make dev'"

# Create a virtual environment using uv
venv:
	@echo "Setting up virtual environment..."
	@if [ -d ".venv" ]; then \
		echo "✓ Virtual environment already exists in .venv"; \
	else \
		echo "Creating virtual environment..."; \
		if command -v uv >/dev/null 2>&1; then \
			uv venv; \
		else \
			echo "uv not found. Creating venv with standard tools..."; \
			if command -v python3 >/dev/null 2>&1; then \
				python3 -m venv .venv; \
			else \
				$(PYTHON) -m venv .venv; \
			fi; \
		fi; \
		echo "✓ Virtual environment created in .venv directory"; \
	fi

# Install dependencies and the package in development mode
install:
	@echo "Installing development dependencies and package..."
	@if [ ! -d ".venv" ]; then \
		echo "Virtual environment not found. Please run 'make venv' first."; \
		exit 1; \
	fi
	@echo "Installing dependencies..."
	@if command -v uv >/dev/null 2>&1; then \
		uv pip install -e ".[dev]" || { \
			echo "uv installation failed, trying standard pip..."; \
			. .venv/bin/activate && pip install -e ".[dev]"; \
		}; \
	else \
		. .venv/bin/activate && pip install -e ".[dev]"; \
	fi
	@echo "✓ Installation complete"

# Update pip, setuptools, and wheel to latest versions
update-tools:
	@echo "Updating pip, setuptools, and wheel to latest versions..."
	@if [ ! -d ".venv" ]; then \
		echo "Virtual environment not found. Please run 'make venv' first."; \
		exit 1; \
	fi
	@if command -v uv >/dev/null 2>&1; then \
		uv pip install --upgrade pip setuptools wheel build || { \
			echo "uv upgrade failed, trying standard pip..."; \
			. .venv/bin/activate && pip install --upgrade pip setuptools wheel build; \
		}; \
	else \
		. .venv/bin/activate && pip install --upgrade pip setuptools wheel build; \
	fi
	@echo "✓ Core tools successfully updated"

# Complete development setup
dev: venv update-tools install
	@echo "Development environment setup complete"
	@make activate

# Add a special target for activating the virtual environment
activate:
	@echo "To activate the virtual environment, run:"
	@echo "source .venv/bin/activate"
	@echo ""
	@echo "To deactivate, simply run:"
	@echo "deactivate"

# Run linting
lint:
	@echo "Running linting checks..."
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && ruff check $(SRC_DIR) $(TEST_DIR) --fix; \
	else \
		echo "Virtual environment not found. Please run 'make venv' first."; \
		exit 1; \
	fi

# Format code
format:
	@echo "Formatting code..."
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && black $(SRC_DIR) $(TEST_DIR); \
	else \
		echo "Virtual environment not found. Please run 'make venv' first."; \
		exit 1; \
	fi

# Run tests
test:
	@echo "Running tests..."
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python -m pytest $(TEST_DIR) -v; \
	else \
		echo "Virtual environment not found. Please run 'make venv' first."; \
		exit 1; \
	fi

# Clean build artifacts and cache directories
clean:
	@echo "Cleaning build artifacts and cache directories..."
	@rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage .ruff_cache/ .black_cache/
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@echo "Cleaned"

# Build package wheel distribution
build-wheel: clean
	@echo "Building wheel package..."
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python -m build --wheel; \
	else \
		echo "Virtual environment not found. Please run 'make venv' first."; \
		exit 1; \
	fi
	@echo "Wheel package built. Check the dist/ directory."

# Build source distribution
build-sdist: clean
	@echo "Building source distribution package..."
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python -m build --sdist; \
	else \
		echo "Virtual environment not found. Please run 'make venv' first."; \
		exit 1; \
	fi
	@echo "Source distribution built. Check the dist/ directory."

# Build both wheel and source distribution
build: clean
	@echo "Building package distribution files..."
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python -m build; \
	else \
		echo "Virtual environment not found. Please run 'make venv' first."; \
		exit 1; \
	fi
	@echo "Build complete. Distribution files in dist/"

# Create installer script for end users
install-script: build-wheel
	@echo "Creating installer script..."
	@mkdir -p $(DIST_DIR)
	@cp $(SCRIPT_DIR)/install-pipeline-helpers.sh $(DIST_DIR)/install-pipeline-helpers.sh
	@sed -i.bak 's/\$$(VERSION)/$(VERSION)/g' $(DIST_DIR)/install-pipeline-helpers.sh
	@sed -i.bak 's/\$$(DIST_DIR)/$(DIST_DIR)/g' $(DIST_DIR)/install-pipeline-helpers.sh
	@rm $(DIST_DIR)/install-pipeline-helpers.sh.bak
	@echo "Installer script created at $(DIST_DIR)/install-pipeline-helpers.sh"
	@echo "For distribution to users, include this script along with the wheel file from dist/"

# Publish to PyPI
publish: build
	@echo "Publishing to PyPI..."
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python -m twine upload dist/*; \
	else \
		echo "Virtual environment not found. Please run 'make venv' first."; \
		exit 1; \
	fi
	@echo "Package published to PyPI"

# Check dev environment status
check-env:
	@echo "Checking development environment..."
	@echo "Python version: $$($(PYTHON) --version 2>&1)"
	@if [ -d ".venv" ]; then \
		echo "✓ Virtual environment found"; \
		if [ -f ".venv/bin/activate" ]; then \
			echo "  Checking installed packages..."; \
			. .venv/bin/activate && pip list | grep -e pytest -e ruff -e black > /dev/null && \
			echo "✓ Development dependencies installed" || \
			echo "✗ Some development dependencies missing. Run 'make install'"; \
		else \
			echo "✗ Virtual environment appears corrupted. Run 'rm -rf .venv && make venv'"; \
		fi; \
	else \
		echo "✗ Virtual environment not found. Run 'make venv'"; \
	fi
	@if command -v mise >/dev/null 2>&1 || command -v pyenv >/dev/null 2>&1; then \
		echo "✓ Python version manager installed"; \
	else \
		echo "ℹ️ No Python version manager found. Consider installing mise or pyenv"; \
	fi
	@if command -v uv >/dev/null 2>&1; then \
		echo "✓ uv installed"; \
	else \
		echo "ℹ️ uv not found. Using standard pip (uv recommended for faster installs)"; \
	fi
	@if [ -f "pyproject.toml" ]; then \
		echo "✓ pyproject.toml found"; \
	else \
		echo "✗ pyproject.toml missing"; \
		exit 1; \
	fi
	@echo "Environment check complete!"

# Check all dependencies for security vulnerabilities
security:
	@echo "Checking dependencies for security vulnerabilities..."
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python -m pip_audit; \
	else \
		echo "Virtual environment not found. Please run 'make venv' first."; \
		exit 1; \
	fi

# Install the published pipeline-helpers package
install-package:
	@echo "Installing pipeline-helpers package from PyPI..."
	@if [ ! -d ".venv" ]; then \
		echo "Virtual environment not found. Creating one first..."; \
		make venv; \
	fi
	@if command -v uv >/dev/null 2>&1; then \
		uv pip install pipeline-helpers || { \
			echo "uv installation failed, trying standard pip..."; \
			. .venv/bin/activate && pip install pipeline-helpers; \
		}; \
	else \
		. .venv/bin/activate && pip install pipeline-helpers; \
	fi
	@echo "✓ pipeline-helpers package successfully installed"

executable:
	@echo "Creating executable scripts..."
	@if [ ! -d ".venv" ]; then \
		echo "Virtual environment not found. Please run 'make venv' first."; \
		exit 1; \
	fi
	@if ! command -v pyinstaller >/dev/null 2>&1; then \
		echo "pyinstaller not found. Installing it now..."; \
		if command -v uv >/dev/null 2>&1; then \
			uv pip install pyinstaller || { \
				echo "uv installation failed, trying standard pip..."; \
				. .venv/bin/activate && pip install pyinstaller; \
			}; \
		else \
			. .venv/bin/activate && pip install pyinstaller || { \
				echo "Failed to install pyinstaller. Please check your environment."; \
				exit 1; \
			}; \
		fi \
	fi
	@echo "Creating executables..."
	@for script in create_release delete_release rollback_release update_params_release_tag demo_release_pipeline; do \
		. .venv/bin/activate && pyinstaller --onefile src/$$script.py || { \
			echo "Failed to create executable for $$script.py"; \
			exit 1; \
		}; \
	done
	@cp dist/* ~/.local/bin/
	@echo "✓ All executables created successfully"
