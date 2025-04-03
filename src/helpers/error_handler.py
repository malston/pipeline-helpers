"""Error handling utilities for pipeline helpers."""

import os
import sys
import traceback
import logging
from datetime import datetime
from typing import Optional, Callable

from src.helpers.logger import default_logger as logger


def handle_error(error: Exception, exit_code: int = 1, log_file: Optional[str] = None) -> None:
    """Handle an exception by logging the stack trace and displaying a user-friendly message.
    
    Args:
        error: The exception that was raised
        exit_code: Exit code to use when terminating (default: 1)
        log_file: Optional path to log file. If None, uses default logging location
    """
    # Get the full stack trace
    stack_trace = traceback.format_exc()
    
    # Determine the log file location if not provided
    if log_file is None:
        log_dir = os.path.expanduser("~/.pipeline-helpers/logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"pipeline-helpers-{timestamp}.log")
    
    # Write error information directly to the log file
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"\n--- New Error at {timestamp} ---\n")
        f.write(f"Error message: {str(error)}\n")
        f.write(f"Stack trace:\n{stack_trace}\n")
    
    # Display user-friendly message with the error first
    # Using ANSI color codes: Red for "Error:", Yellow for the message, Cyan for log file path
    RED = "\033[31m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    RESET = "\033[0m"
    
    # Print error message to terminal only (not stack trace)
    print(f"\n{RED}Error:{RESET} {YELLOW}{str(error)}{RESET}\n")
    print(f"See {CYAN}{log_file}{RESET} for detailed information.\n")
    
    # Exit with the specified exit code
    sys.exit(exit_code)


def configure_file_logger(log_file: str) -> None:
    """Configure the logger to write to the specified file.
    
    Args:
        log_file: Path to the log file
    """
    # Check if we already have a file handler
    has_file_handler = False
    for handler in logger.logger.handlers:
        if isinstance(handler, logging.FileHandler):
            has_file_handler = True
            break
    
    # If no file handler exists, add one
    if not has_file_handler:
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.logger.addHandler(file_handler)


def wrap_main(main_func: Callable) -> Callable:
    """Decorator to wrap main functions with error handling.
    
    This decorator catches ValueError exceptions, logs them, and provides a user-friendly message.
    
    Args:
        main_func: The main function to wrap
        
    Returns:
        A wrapped function with error handling
    """
    def wrapped_main(*args, **kwargs):
        try:
            return main_func(*args, **kwargs)
        except ValueError as e:
            handle_error(e)
        except Exception as e:
            # For other exceptions, we'll still log them but re-raise
            # This lets the standard Python error handling show them
            logger.error(f"Unexpected error: {str(e)}")
            raise
    
    # Preserve the original function's name and docstring
    wrapped_main.__name__ = main_func.__name__
    wrapped_main.__doc__ = main_func.__doc__
    
    return wrapped_main