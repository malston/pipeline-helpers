"""Error handling utilities for pipeline helpers."""

import os
import sys
import traceback
import logging
from datetime import datetime
from typing import Optional, Callable

from src.helpers.logger import default_logger as logger, configure


def setup_error_logging(log_file: Optional[str] = None) -> str:
    """Set up logging to write to both console and file.
    
    Args:
        log_file: Optional path to log file. If None, a default is used.
        
    Returns:
        The path to the log file
    """
    # Determine the log file location if not provided
    if log_file is None:
        log_dir = os.path.expanduser("~/.pipeline-helpers/logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"pipeline-helpers-{timestamp}.log")
    
    # Configure the logger to write to both console and file
    configure(
        name="pipeline-helpers",
        level=logging.INFO,
        log_file=log_file,
        console=True
    )
    
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
    
    # Set up logging to file
    log_file = setup_error_logging(log_file)
    
    # Log the error and stack trace
    logger.error(f"Error occurred: {str(error)}")
    logger.error(f"Stack trace:\n{stack_trace}")
    
    # Display user-friendly message with the error first
    # Using ANSI color codes: Red for "Error:", Yellow for the message, Cyan for log file path
    RED = "\033[31m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    RESET = "\033[0m"
    
    # Print error message to terminal
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
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(f"Stack trace:\n{traceback.format_exc()}")
            raise
    
    # Preserve the original function's name and docstring
    wrapped_main.__name__ = main_func.__name__
    wrapped_main.__doc__ = main_func.__doc__
    
    return wrapped_main