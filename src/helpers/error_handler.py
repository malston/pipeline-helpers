"""Error handling utilities for pipeline helpers."""

import os
import sys
import traceback
import logging
from datetime import datetime
from typing import Optional, Callable

from src.helpers.logger import default_logger as logger, configure


def setup_error_logging(log_file: Optional[str] = None, console_level: int = logging.INFO) -> str:
    """Set up logging to write to both console and file.

    Args:
        log_file: Optional path to log file. If None, a default is used.
        console_level: Logging level for console output (default: INFO)

    Returns:
        The path to the log file
    """
    # Determine the log file location if not provided
    if log_file is None:
        log_dir = os.path.expanduser("~/.pipeline-helpers/logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"pipeline-helpers-{timestamp}.log")

    # Get the root logger
    root_logger = logging.getLogger()

    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set the base logging level
    root_logger.setLevel(logging.DEBUG)

    # Create file handler for all detailed logs
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    # Create console handler with higher level and no error messages
    # (we'll handle errors separately with colored output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(console_level)

    # Add a filter to prevent error messages and stack traces in console
    class ConsoleFilter(logging.Filter):
        def filter(self, record):
            # Skip error messages, stack traces or multi-line messages
            if (
                record.levelno >= logging.ERROR
                or record.getMessage().startswith("Stack trace:")
                or record.getMessage().startswith("Error occurred:")
                or "\n" in record.getMessage()
            ):
                return False
            return True

    console_handler.addFilter(ConsoleFilter())
    root_logger.addHandler(console_handler)

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
    logging.error(f"Error occurred: {str(error)}")
    logging.error(f"Stack trace:\n{stack_trace}")

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

    Args:
        main_func: The main function to wrap

    Returns:
        A wrapped function with error handling
    """

    def wrapped_main(*args, **kwargs):
        # Set up logging to file for the entire script execution
        log_file = setup_error_logging()

        try:
            return main_func(*args, **kwargs)
        except ValueError as e:
            handle_error(e, log_file=log_file)
        except Exception as e:
            # For other exceptions, still log them but re-raise
            logging.error(f"Unexpected error: {str(e)}")
            logging.error(f"Stack trace:\n{traceback.format_exc()}")
            raise

    # Preserve the original function's name and docstring
    wrapped_main.__name__ = main_func.__name__
    wrapped_main.__doc__ = main_func.__doc__

    return wrapped_main
