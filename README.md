# Pipeline Helpers

A collection of Python scripts for managing GitHub releases with Concourse CI pipelines.

## Installation

```bash
pip install pipeline-helpers
```

## Scripts

The package provides several command-line utilities:

- `create-release`: Create a new release in a GitHub repository
- `delete-release`: Delete an existing release
- `rollback-release`: Rollback to a previous release
- `update-params-release-tag`: Update release tags in parameter files
- `demo-release-pipeline`: Demo tool for testing release pipelines

## Usage

### Create Release

```bash
create-release -f foundation -r repo [-m release_message] [-o owner] [-p params_repo] [--dry-run] [--log-to-file]
```

Options:
- `-f foundation`: The foundation name for ops manager (required)
- `-r repo`: The repository name (required)
- `-m release_body`: The message to apply to the release (optional)
- `-o owner`: The GitHub owner (default: Utilities-tkgieng)
- `-p params_repo`: The params repo name (default: params)
- `--dry-run`: Run in dry-run mode - no changes will be made

### Delete Release

```bash
delete-release -r repo -t tag [-o owner] [-x] [-n]
```

Options:
- `-r repo`: The repository name (required)
- `-t tag`: The release tag to delete (e.g., v1.0.0) (required)
- `-o owner`: The GitHub owner (default: Utilities-tkgieng)
- `-x`: Do not delete the git tag, only the GitHub release
- `-n`: Non-interactive mode (will not prompt for confirmation)

### Rollback Release

```bash
rollback-release -f foundation -r repo [-t tag] [-o owner] [-p params_repo]
```

Options:
- `-f foundation`: The foundation name (required)
- `-r repo`: The repository name (required)
- `-t tag`: The release tag to rollback to (optional, will prompt if not provided)
- `-o owner`: The GitHub owner (default: Utilities-tkgieng)
- `-p params_repo`: The params repo name (default: params)

### Update Params Release Tag

```bash
update-params-release-tag -r repo [-o owner] [-p params_repo] [-w git_dir] [--log-to-file]
```

Options:
- `-r repo`: The repository name (required)
- `-o owner`: The GitHub owner (default: Utilities-tkgieng)
- `-p params_repo`: The params repo name (default: params)
- `-w git_dir`: The base directory containing git repositories (default: $GIT_WORKSPACE or ~/git)

## Logging

The package uses a customized logging system that supports both console and file-based logging:

- Console output is colored by default for better readability
- File logging can be enabled with the `PIPELINE_HELPERS_LOG_TO_FILE` environment variable
- Log files are stored in `~/.pipeline-helpers/logs/` by default

Example with file logging:
```bash
export PIPELINE_HELPERS_LOG_TO_FILE=1
create-release -f foundation_name -r repo
```

To disable file logging:
```bash
export PIPELINE_HELPERS_LOG_TO_FILE=0
# or unset the variable
unset PIPELINE_HELPERS_LOG_TO_FILE
```

### Using the Logger in Code

To use the logging system in new code:

```python
# Import default logger
from src.helpers.logger import default_logger as logger

# Log messages with different levels
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message") 
logger.error("Error message")
logger.critical("Critical message")
logger.success("Success message")  # Alias for info with special formatting

# Create a custom logger with different settings
from src.helpers.logger import get_logger

custom_logger = get_logger(
    name="my-module",
    level=logging.DEBUG,
    log_file="/path/to/custom/log_file.log"
)
```

## Development

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Run tests:
   ```bash
   pytest
   ```

4. Run linter:
   ```bash
   ruff check .
   ```
   
5. Or use the Makefile:
   ```bash
   make dev && source .venv/bin/activate
   make test
   make format
   make lint
   ```

## License

MIT