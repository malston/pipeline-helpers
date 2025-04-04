#!/usr/bin/env python3

import argparse
import os
from pathlib import Path

from src.helpers.command_helper import CommandHelper
from src.helpers.argparse_helper import CustomHelpFormatter, HelpfulArgumentParser
from src.helpers.error_handler import wrap_main
from src.helpers.git_helper import GitHelper
from src.helpers.logger import default_logger as logger
from src.helpers.release_helper import ReleaseHelper


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = HelpfulArgumentParser(
        prog="update_params_release_tag.py",
        description="Create a new release",
        formatter_class=CustomHelpFormatter,
        add_help=False,
        usage="%(prog)s -r repo [-o owner] [-p params_repo] [-w dir] [--log-to-file] [-h]",
        epilog="""
Options:
  -r repo          the repo to use
  -p params_repo   the params repo name always located under ~/git (default: params)
  -o owner         the github owner (default: Utilities-tkgieng)
  -w dir           the base directory containing git repositories (default: $GIT_WORKSPACE or ~/git)
  -h, --help       display this help message and exit
""",
    )
    parser.add_argument(
        "-r",
        "--repo",
        required=True,
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
        "-h",
        "--help",
        action="help",
        help="display usage",
    )
    return parser.parse_args()


@wrap_main
def main() -> None:
    """Main function to update the release tag in the params repo."""
    args = parse_args()

    repo = args.repo
    params_repo = args.params_repo
    owner = args.owner
    git_dir = args.git_dir
    # repo_dir = os.path.join(git_dir, args.repo)
    # params_dir = os.path.join(git_dir, args.params_repo)

    if not os.path.isdir(git_dir):
        raise ValueError(f"Could not find git directory: {git_dir}")
    if not os.path.isdir(os.path.join(git_dir, repo)):
        raise ValueError(f"Could not find repo directory: {git_dir}/{repo}")

    logger.info(f"Updating release for repo: {repo}, params_repo: {params_repo}")

    repo_dir = os.path.join(git_dir, repo)
    params_dir = os.path.join(git_dir, params_repo)
    command_helper = CommandHelper(git_dir=git_dir, owner=owner)
    repo, repo_dir, params_repo, params_dir = command_helper.adjust_repo_and_params_paths(
        repo, params_repo
    )

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
    os.chdir(repo_dir)

    if not release_helper.update_params_git_release_tag("v"):
        raise ValueError("Failed to update git release tag")


if __name__ == "__main__":
    main()
