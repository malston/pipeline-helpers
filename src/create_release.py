#!/usr/bin/env python3

import argparse
import os
import subprocess
from pathlib import Path

from src.helpers.command_helper import CommandHelper
from src.helpers.argparse_helper import CustomHelpFormatter, HelpfulArgumentParser
from src.helpers.concourse import ConcourseClient
from src.helpers.error_handler import wrap_main
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
        "[-p params_repo] [--dry-run] [-h]",
        epilog="""
Options:
   -f foundation    the foundation name for ops manager (e.g. cml-k8s-n-01)
   -r repo          the repo to use
   -m release_body  the message to apply to the release that is created (optional)
   -o owner         the github owner (default: Utilities-tkgieng)
   -p params_repo   the params repo name always located under ~/git (default: params)
   -w dir           the base directory containing git repositories (default: $GIT_WORKSPACE or ~/git)
   --dry-run        run in dry-run mode (no changes will be made)
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
        "-w",
        "--git-dir",
        "--workspace",
        default=os.environ.get("GIT_WORKSPACE", str(Path.home() / "git")),
        type=str,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--dry-run",
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

    repo = args.repo
    params_repo = args.params_repo
    owner = args.owner
    git_dir = args.git_dir
    foundation = args.foundation
    message = args.message
    dry_run = args.dry_run

    if not os.path.isdir(git_dir):
        raise ValueError(f"Could not find git directory: {git_dir}")
    if not os.path.isdir(os.path.join(git_dir, repo)):
        raise ValueError(f"Could not find repo directory: {git_dir}/{repo}")

    logger.info(f"Creating release for repo: {repo}")
    logger.info(f"Foundation: {foundation}")

    repo_dir = os.path.join(git_dir, repo)
    params_dir = os.path.join(git_dir, params_repo)
    command_helper = CommandHelper(git_dir=git_dir, owner=owner)
    repo, repo_dir, params_repo, params_dir = command_helper.adjust_repo_and_params_paths(
        repo, params_repo
    )

    release_pipeline = f"tkgi-{repo}-release"
    logger.info(f"Using release pipeline: {release_pipeline}")
    logger.info(f"Using git directory: {git_dir}")
    logger.info(f"Using repo directory: {repo_dir}")
    logger.info(f"Using params directory: {params_dir}")
    logger.info(f"Using params repo: {params_repo}")
    logger.info(f"Using repo: {repo}")
    logger.info(f"Using owner: {owner}")

    # Initialize helpers
    release_helper = ReleaseHelper(
        repo=repo,
        git_dir=git_dir,
        repo_dir=repo_dir,
        owner=owner,
        params_dir=params_dir,
        params_repo=params_repo,
    )
    git_helper = GitHelper(
        git_dir=git_dir, repo=repo, repo_dir=repo_dir, params=params_repo, params_dir=params_dir
    )
    if not git_helper.check_git_repo():
        raise ValueError(f"{repo} is not a git repository")

    concourse_client = ConcourseClient()

    # Change to the repo's ci directory
    ci_dir = os.path.join(git_dir, repo, "ci")
    if not os.path.exists(ci_dir):
        raise ValueError(f"CI directory not found at {ci_dir}")

    if dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        logger.info(f"Would change to directory: {ci_dir}")
        logger.info(f"Would run release pipeline: {release_pipeline}")
        logger.info("Would update git release tag")
        return
    else:
        os.chdir(ci_dir)
        logger.info(f"Changed to directory: {ci_dir}")

    # Run release pipeline
    if not release_helper.run_release_pipeline(foundation, message):
        raise ValueError("Failed to run release pipeline")

    # Update git release tag
    if not release_helper.update_params_git_release_tag():
        raise ValueError("Failed to update git release tag")

    # Run set pipeline
    if not release_helper.run_set_pipeline(foundation):
        raise ValueError("Failed to run set pipeline")

    # Ask user if they want to trigger a job
    trigger_response = input("Do you want to trigger a prepare-kustomizations job? [y/N] ")
    if trigger_response.lower().startswith("y"):
        concourse_client.trigger_job(
            foundation, f"tkgi-{repo}-{foundation}/prepare-kustomizations", watch=True
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
                foundation,
                "-b",
                current_branch,
            ],
            check=True,
        )

    logger.info("Release process completed successfully")


if __name__ == "__main__":
    main()
