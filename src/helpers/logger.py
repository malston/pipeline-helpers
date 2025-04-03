#!/usr/bin/env python3

"""Logging utility for pipeline helpers."""

import logging
import os
import sys
from typing import Optional


class ColorFormatter(logging.Formatter):
    """Formatter for colored log output."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[0;36m",  # Cyan
        "INFO": "\033[0;32m",  # Green
        "WARNING": "\033[0;33m",  # Yellow
        "ERROR": "\033[0;31m",  # Red
        "CRITICAL": "\033[1;31m",  # Bold Red
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        """Format the log record with color."""
        # Get the original formatted message
        log_message = super().format(record)

        # Add color based on level
        level_name = record.levelname
        color = self.COLORS.get(level_name, self.COLORS["RESET"])
        return f"{color}{log_message}{self.COLORS['RESET']}"


class Logger:
    """Logger class for pipeline helpers.

    This class provides standardized logging capabilities for the pipeline helpers,
    supporting both console and file logging with configurable log levels.
    """

    def __init__(
        self,
        name: str = "pipeline-helpers",
        level: int = logging.INFO,
        log_file: Optional[str] = None,
        console: bool = True,
    ):
        """Initialize the logger.

        Args:
            name: The name of the logger
            level: The log level (e.g., logging.DEBUG, logging.INFO)
            log_file: Optional path to a log file
            console: Whether to log to console
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers = []  # Clear any existing handlers

        # Create formatters
        console_formatter = ColorFormatter("%(message)s")
        file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Add console handler if requested
        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # Add file handler if a log file is specified
        if log_file:
            # Create log directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """Log a critical message."""
        self.logger.critical(message)

    def success(self, message: str) -> None:
        """Log a success message (uses INFO level with special formatting)."""
        # Use info level but with success formatting
        self.logger.info(message)


# Create a default logger instance
default_logger = Logger()


# Convenience functions that use the default logger
def debug(message: str) -> None:
    """Log a debug message using the default logger."""
    default_logger.debug(message)


def info(message: str) -> None:
    """Log an info message using the default logger."""
    default_logger.info(message)


def warning(message: str) -> None:
    """Log a warning message using the default logger."""
    default_logger.warning(message)


def warn(message: str) -> None:
    """Alias for warning using the default logger."""
    default_logger.warning(message)


def error(message: str) -> None:
    """Log an error message using the default logger."""
    default_logger.error(message)


def critical(message: str) -> None:
    """Log a critical message using the default logger."""
    default_logger.critical(message)


def success(message: str) -> None:
    """Log a success message using the default logger."""
    default_logger.success(message)


def configure(
    name: str = "pipeline-helpers",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True,
) -> None:
    """Configure the default logger.

    Args:
        name: The name of the logger
        level: The log level (e.g., logging.DEBUG, logging.INFO)
        log_file: Optional path to a log file
        console: Whether to log to console
    """
    global default_logger
    default_logger = Logger(name=name, level=level, log_file=log_file, console=console)


def get_logger(
    name: str = "pipeline-helpers",
    level: Optional[int] = None,
    log_file: Optional[str] = None,
    console: Optional[bool] = None,
) -> Logger:
    """Get a new logger instance with the specified configuration.

    Args:
        name: The name of the logger
        level: The log level (e.g., logging.DEBUG, logging.INFO).
            If None, uses default_logger's level.
        log_file: Optional path to a log file. If None, no file logging.
        console: Whether to log to console. If None, uses default_logger's setting.

    Returns:
        A new Logger instance
    """
    # Use default values if not specified
    if level is None:
        level = default_logger.logger.level
    if console is None:
        console = any(isinstance(h, logging.StreamHandler) for h in default_logger.logger.handlers)

    return Logger(name=name, level=level, log_file=log_file, console=console)
