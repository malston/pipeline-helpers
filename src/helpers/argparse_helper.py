"""Custom argparse helpers."""

import argparse
import sys
from typing import List, Optional


class CustomHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom help formatter to modify the help output."""

    def format_help(self):
        help_text = super().format_help()
        # Remove the default options section
        help_text = help_text.split("\n\n")[0] + "\n\n" + help_text.split("\n\n")[-1]
        # Change "usage:" to "Usage:"
        help_text = help_text.replace("usage:", "Usage:")
        return help_text


class HelpfulArgumentParser(argparse.ArgumentParser):
    """Custom argument parser that shows help if no arguments are provided."""

    def __init__(self, *args, **kwargs):
        # Don't print usage when an error occurs, we'll handle it ourselves
        kwargs["usage"] = kwargs.get("usage", None)
        super().__init__(*args, **kwargs)

    def parse_args(
        self, args: Optional[List[str]] = None, namespace: Optional[argparse.Namespace] = None
    ) -> argparse.Namespace:
        # If no arguments were supplied, print help and exit
        if args is None and len(sys.argv) == 1:
            self.print_help()
            sys.exit(0)
        return super().parse_args(args, namespace)

    def error(self, message):
        """Override error method to avoid printing usage twice."""
        self.print_usage = lambda file: None  # Disable automatic usage printing
        sys.stderr.write(f"Error: {message}\n\n")
        self.print_help()
        self.exit(2)
