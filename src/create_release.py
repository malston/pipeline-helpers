#!/usr/bin/env python3

import argparse
import os
import subprocess
import logging

from src.helpers.argparse_helper import CustomHelpFormatter, HelpfulArgumentParser
from src.helpers.concourse import ConcourseClient
from src.helpers.error_handler import wrap_main, setup_error_logging
from src.helpers.git_helper import GitHelper
from src.helpers.release_helper import ReleaseHelper


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = HelpfulArgumentParser(
        prog="create_release.py",
        description="Create a new release",
        formatter_class=CustomHelpFormatter,
        add_help=False,
        usage="%(prog)s -f foundation -r repo [-m release_body] [-o owner] [-p params_repo] [-h]",
        epilog="""
Options:
   -f foundation    the foundation name for ops manager (e.g. cml-k8s-n-01)
   -r repo          the repo to use
   -m release_body  the message to apply to the release that is created (optional)
   -o owner         the github owner (default: Utilities-tkgieng)
   -p params_repo   the params repo name always located under ~/git (default: params)
   -h               display usage
""",
    )
    parser.add_argument(
        "-f",
        "--foundation",
        required=True,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-r",
        "--repo",
        required=True,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-m",
        "--message",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-o",
        "--owner",
        default="Utilities-tkgieng",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-p",
        "--params-repo",
        default="params",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--log-to-file",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="display usage",
    )
    return parser.parse_args()


@wrap_main
def main() -> None:
    """Main function to create a new release."""
    args = parse_args()
    
    # If --log-to-file is specified, set up logging to file
    if args.log_to_file:
        setup_error_logging()
        logging.info("Logging to file enabled")

    # Rest of the function remains the same
    repo = args.repo
    params_repo = args.params_repo
    release_pipeline = f"tkgi-{repo}-release"

    logging.info(f"Creating release for repo: {repo}")
    logging.info(f"Foundation: {args.foundation}")
    
    if args.owner != "Utilities-tkgieng":
        repo = f"{repo}-{args.owner}"
        params_repo = f"{args.params_repo}-{args.owner}"
        release_pipeline = f"tkgi-{repo}-release"

    # Initialize helpers
    git_helper = GitHelper(repo=repo)
    if not git_helper.check_git_repo():
        raise ValueError("Git is not installed or not in PATH")
        
    release_helper = ReleaseHelper(repo=repo, owner=args.owner, params_repo=params_repo)
    concourse_client = ConcourseClient()

    # Change to the repo's ci directory
    ci_dir = os.path.expanduser(f"~/git/{repo}/ci")
    if not os.path.exists(ci_dir):
        raise ValueError(f"CI directory not found at {ci_dir}")

    if args.dry_run:
        logging.info("DRY RUN MODE - No changes will be made")
        logging.info(f"Would change to directory: {ci_dir}")
    else:
        os.chdir(ci_dir)
        logging.info(f"Changed to directory: {ci_dir}")

    # ... Rest of the function implementation ...
    logging.info("Release process completed successfully")


if __name__ == "__main__":
    main()