#!/usr/bin/env python3

import argparse
import os
import subprocess

from src.helpers.argparse_helper import CustomHelpFormatter, HelpfulArgumentParser
from src.helpers.concourse import ConcourseClient
from src.helpers.error_handler import setup_error_logging, wrap_main
from src.helpers.git_helper import GitHelper
from src.helpers.logger import default_logger as logger
from src.helpers.release_helper import ReleaseHelper


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = HelpfulArgumentParser(
        prog="create_release.py",
        description="Create a new release",
        formatter_class=CustomHelpFormatter,
        add_help=False,
        usage="%(prog)s -f foundation -r repo [-m release_body] [-o owner] "
               "[-p params_repo] [--dry-run] [--log-to-file] [-h]",
        epilog="""
Options:
   -f foundation    the foundation name for ops manager (e.g. cml-k8s-n-01)
   -r repo          the repo to use
   -m release_body  the message to apply to the release that is created (optional)
   -o owner         the github owner (default: Utilities-tkgieng)
   -p params_repo   the params repo name always located under ~/git (default: params)
   --dry-run        run in dry-run mode (no changes will be made)
   --log-to-file    write logs to a file in addition to console output
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
        logger.info("Logging to file enabled")

    # Process the repo and params values
    repo = args.repo
    params_repo = args.params_repo
    release_pipeline = f"tkgi-{repo}-release"

    logger.info(f"Creating release for repo: {repo}")
    logger.info(f"Foundation: {args.foundation}")

    if args.owner != "Utilities-tkgieng":
        repo = f"{repo}-{args.owner}"
        params_repo = f"{params_repo}-{args.owner}"
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
        logger.info("DRY RUN MODE - No changes will be made")
        logger.info(f"Would change to directory: {ci_dir}")
        logger.info(f"Would run release pipeline: {release_pipeline}")
        logger.info("Would update git release tag")
        return
    else:
        os.chdir(ci_dir)
        logger.info(f"Changed to directory: {ci_dir}")

    # Run release pipeline
    if not release_helper.run_release_pipeline(args.foundation, args.message):
        raise ValueError("Failed to run release pipeline")

    # Update git release tag
    if not release_helper.update_params_git_release_tag():
        raise ValueError("Failed to update git release tag")

    # Run set pipeline
    if not release_helper.run_set_pipeline(args.foundation):
        raise ValueError("Failed to run set pipeline")

    # Ask user if they want to trigger a job
    trigger_response = input("Do you want to trigger a prepare-kustomizations job? [y/N] ")
    if trigger_response.lower().startswith("y"):
        concourse_client.trigger_job(
            args.foundation, f"tkgi-{repo}-{args.foundation}/prepare-kustomizations", watch=True
        )

    # Ask user if they want to run fly.sh script
    fly_script_response = input("Do you want to run the fly.sh script? [y/N] ")
    if fly_script_response.lower().startswith("y"):
        # Get current branch
        current_branch = git_helper.get_current_branch()
        # Build the path to fly.sh
        fly_script_path = f"{ci_dir}/fly.sh"
        # Run fly.sh script
        subprocess.run(
            [
                fly_script_path,
                "-f",
                args.foundation,
                "-b",
                current_branch,
            ],
            check=True,
        )

    logger.info("Release process completed successfully")


if __name__ == "__main__":
    main()
