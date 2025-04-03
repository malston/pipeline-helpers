#!/usr/bin/env python3

import argparse
import os

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
        usage="%(prog)s -r repo [-o owner] [-p params_repo] [-h]",
        epilog="""
Options:
  -r repo          the repo to use
  -p params_repo   the params repo name always located under ~/git (default: params)
  -o owner         the github owner (default: Utilities-tkgieng)
  -h               display usage
""",
    )
    parser.add_argument("-r", "--repo", required=True, help=argparse.SUPPRESS)
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

    git_dir = os.path.expanduser("~/git")
    repo_dir = os.path.join(git_dir, args.repo)
    params_dir = os.path.join(git_dir, args.params_repo)

    # Check if repo ends with the owner
    if args.repo.endswith(args.owner):
        args.repo = args.repo[: -len(args.owner) - 1]

    # Check if params_repo ends with the owner
    if args.params_repo.endswith(args.owner):
        args.params_repo = args.params_repo[: -len(args.owner) - 1]

    # Check if repo ends with the owner
    if args.owner != "Utilities-tkgieng":
        repo_dir = os.path.join(git_dir, f"{repo}-{args.owner}")
        params_dir = os.path.join(git_dir, f"{params_repo}-{args.owner}")
        params_repo = f"{params_repo}-{args.owner}"

    if not os.path.isdir(repo_dir):
        raise ValueError(f"Could not find repo directory: {repo_dir}")

    os.chdir(repo_dir)

    # Initialize helpers
    release_helper = ReleaseHelper(
        repo=repo,
        repo_dir=repo_dir,
        owner=args.owner,
        params_dir=params_dir,
        params_repo=params_repo,
    )
    git_helper = GitHelper(repo=repo, repo_dir=repo_dir)
    if not git_helper.check_git_repo():
        raise ValueError(f"{repo} is not a git repository")

    if not release_helper.update_params_git_release_tag():
        raise ValueError("Failed to update git release tag")


if __name__ == "__main__":
    main()
