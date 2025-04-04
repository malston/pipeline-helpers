# Logging System

The `pipeline-helpers` package includes a customized logging system that provides structured, color-formatted logs for both console and file output.

## Key Features

1. **Colored Console Output**: 
   - Debug messages: Cyan
   - Info messages: Green
   - Warning messages: Yellow
   - Error messages: Red
   - Critical messages: Bold Red

2. **File-based Logging**:
   - Log files stored in `~/.pipeline-helpers/logs/` by default
   - Daily log files with timestamp format: `pipeline-helpers-YYYYMMDD.log`
   - More detailed format for file logs, including timestamps and log levels

3. **Environment Variable Control**:
   - Enabled by setting `PIPELINE_HELPERS_LOG_TO_FILE=1`
   - Can be disabled with `PIPELINE_HELPERS_LOG_TO_FILE=0`

4. **Log Levels**:
   - Standard Python logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
   - Additional `success()` method as a styled variant of INFO

## Usage

### Environment Variables

Control file logging system-wide:

```bash
# Enable file logging
export PIPELINE_HELPERS_LOG_TO_FILE=1

# Disable file logging
export PIPELINE_HELPERS_LOG_TO_FILE=0
# or
unset PIPELINE_HELPERS_LOG_TO_FILE
```

### Using in Code

```python
# Import default logger
from src.helpers.logger import default_logger as logger

# Log messages with different severity levels
logger.debug("Detailed debug information")
logger.info("General information message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error message")
logger.success("Operation completed successfully")  # Special styled info message

# Create a custom logger with different settings
from src.helpers.logger import get_logger
import logging

custom_logger = get_logger(
    name="my-module",             # Logger name
    level=logging.DEBUG,          # Custom log level
    log_file="/path/to/logs.log"  # Custom log file location
)
```

### Implementation Details

The logging system consists of several components:

1. **Logger Class**: A wrapper around Python's standard logging module with customized formatters and handlers

2. **ColorFormatter**: Custom formatter that adds ANSI color codes to console output

3. **Error Handler Integration**: Works with the error_handler module to capture exceptions and route them to logs

4. **Propagation Control**: Properly manages logger hierarchies to prevent duplicate log messages

## Common Tasks

### Viewing Logs

Log files are stored in `~/.pipeline-helpers/logs/` by default, with names like `pipeline-helpers-20250404.log`.

```bash
# View most recent log file
cat ~/.pipeline-helpers/logs/pipeline-helpers-$(date +%Y%m%d).log

# Search logs for errors
grep ERROR ~/.pipeline-helpers/logs/pipeline-helpers-*.log
```

### Modifying Log Behavior

To change the logging behavior for a specific module, create a custom logger:

```python
from src.helpers.logger import get_logger
import logging

# Create a more verbose logger for a specific module
debug_logger = get_logger(
    name="module-name", 
    level=logging.DEBUG
)

# Create a quiet logger that only shows errors
quiet_logger = get_logger(
    name="module-name",
    level=logging.ERROR
)
```