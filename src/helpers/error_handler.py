"""Error handling utilities for pipeline helpers."""

import logging
import os
import sys
import traceback
from datetime import datetime
from typing import Callable, Optional

from src.helpers.logger import default_logger as logger


def setup_error_logging(log_file: Optional[str] = None, console_level: int = logging.INFO) -> str:
    """Set up logging to write to both console and file.

    Args:
        log_file: Optional path to log file. If None, a default is used.
        console_level: Logging level for console output (default: INFO)

    Returns:
        The path to the log file or None if file logging is disabled
    """
    # Check if file logging is enabled via environment variable
    # If PIPELINE_HELPERS_LOG_TO_FILE is not set or set to 0/false/no, file logging is disabled
    env_log_to_file = os.environ.get("PIPELINE_HELPERS_LOG_TO_FILE", "").lower()
    file_logging_enabled = env_log_to_file not in ("", "0", "false", "no", "off")

    # If file logging is disabled, return None
    if not file_logging_enabled and log_file is None:
        return None

    # Determine the log file location if not provided
    if log_file is None:
        log_dir = os.path.expanduser("~/.pipeline-helpers/logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"pipeline-helpers-{timestamp}.log")

    # Configure the logger module to use the file
    # but don't add handlers to the root logger to avoid duplicate console output
    pipeline_logger = logger.logger

    # Don't add a file handler if one already exists
    has_file_handler = any(isinstance(h, logging.FileHandler) for h in pipeline_logger.handlers)

    if not has_file_handler and log_file:
        # Create file handler for detailed logs
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        pipeline_logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")

    return log_file


def handle_error(error: Exception, exit_code: int = 1, log_file: Optional[str] = None) -> None:
    """Handle an exception by logging the stack trace and displaying a user-friendly message.

    Args:
        error: The exception that was raised
        exit_code: Exit code to use when terminating (default: 1)
        log_file: Optional path to log file. If None, uses default logging location
    """
    # Get the full stack trace
    stack_trace = traceback.format_exc()

    # Set up logging to file only for error handling
    log_file = setup_error_logging(log_file, console_level=logging.ERROR)

    # Log the error and stack trace to file
    logger.error(f"Error occurred: {str(error)}")
    logger.error(f"Stack trace:\n{stack_trace}")

    # Using ANSI color codes: Red for "Error:", Yellow for the message, Cyan for log file path
    RED = "\033[31m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    RESET = "\033[0m"

    # Print error message to terminal directly (not through logger)
    print(f"\n{RED}Error:{RESET} {YELLOW}{str(error)}{RESET}\n")
    print(f"See {CYAN}{log_file}{RESET} for detailed information.\n")

    # Exit with the specified exit code
    sys.exit(exit_code)


def wrap_main(main_func: Callable) -> Callable:
    """Decorator to wrap main functions with error handling.

    This decorator catches ValueError exceptions, logs them, and provides a user-friendly message.

    File logging can be enabled by setting the PIPELINE_HELPERS_LOG_TO_FILE environment variable
    to any value except 0, false, no, or off.

    Args:
        main_func: The main function to wrap

    Returns:
        A wrapped function with error handling
    """

    def wrapped_main(*args, **kwargs):
        # Set up logging to file for the entire script execution based on environment variable
        log_file = setup_error_logging()

        try:
            return main_func(*args, **kwargs)
        except ValueError as e:
            handle_error(e, log_file=log_file)
        except Exception as e:
            # For other exceptions, still log them but re-raise
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(f"Stack trace:\n{traceback.format_exc()}")
            raise

    # Preserve the original function's name and docstring
    wrapped_main.__name__ = main_func.__name__
    wrapped_main.__doc__ = main_func.__doc__

    return wrapped_main
