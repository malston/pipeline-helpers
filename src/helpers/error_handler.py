"""Error handling utilities for pipeline helpers."""

import os
import sys
import traceback
from typing import Optional

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
    
    # Determine the log file location
    if log_file is None:
        log_dir = os.path.expanduser("~/.pipeline-helpers/logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "pipeline-helpers-error.log")
    
    # Log the full stack trace to the log file
    with open(log_file, "a") as f:
        f.write(f"\n--- New Error ---\n")
        f.write(f"Error message: {str(error)}\n")
        f.write(f"Stack trace:\n{stack_trace}\n")
    
    # Log the error message
    logger.error(str(error))
    
    # Display user-friendly message
    print(f"\nAn error occurred. See {log_file} for detailed information.\n")
    
    # Exit with the specified exit code
    sys.exit(exit_code)


def wrap_main(main_func):
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
    
    return wrapped_main