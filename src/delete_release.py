#!/usr/bin/env python3

import argparse
import os
from pathlib import Path

from src.helpers.argparse_helper import CustomHelpFormatter, HelpfulArgumentParser
from src.helpers.git_helper import GitHelper
from src.helpers.logger import default_logger as logger
from src.helpers.path_helper import RepositoryPathHelper
from src.helpers.release_helper import ReleaseHelper


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = HelpfulArgumentParser(
        prog="delete_release.py",
        description="Delete a GitHub release",
        formatter_class=CustomHelpFormatter,
        add_help=False,
        usage="%(prog)s -r repo -t tag [-o owner] [-x] [-n] [-h]",
        epilog="""
Options:
  -r repo          the repo to use
  -t tag           the release tag (e.g.: v1.0.0)
  -o owner         the github owner (default: Utilities-tkgieng)
  -x               do not delete the git tag
  -n               non-interactive
  -w dir           the base directory containing git repositories (default: $GIT_WORKSPACE or ~/git)
  -h               display usage
""",
    )
    parser.add_argument(
        "-r",
        "--repo",
        required=True,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-t",
        "--tag",
        "--release-tag",
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
        "-x",
        "--no-tag-deletion",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-n",
        "--non-interactive",
        action="store_true",
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


def delete_git_tag(
    git_helper: GitHelper, release_helper: ReleaseHelper, tag: str, non_interactive: bool = False
) -> None:
    """Delete a git tag with user confirmation if needed."""
    if not git_helper.tag_exists(tag):
        logger.error(f"Git tag {tag} not found in repository")
        return

    if not non_interactive:
        user_input = input(f"Would you like to delete the git tag: {tag}? [yN] ")
        if not user_input.lower().startswith("y"):
            return
    release_helper.delete_release_tag(tag)


def print_available_releases(releases: list) -> None:
    """Print a list of available GitHub releases."""
    print("Available Github Releases:")
    for release in releases:
        print(f"{release['tag_name']} - {release['name']}")


def main() -> None:
    """Main function to delete a GitHub release."""
    args = parse_args()
    repo = args.repo
    owner = args.owner
    release_tag = args.tag
    git_dir = args.git_dir

    path_helper = RepositoryPathHelper(git_dir=git_dir, owner=owner)
    repo, repo_dir = path_helper.adjust_path(repo)

    # Initialize helpers
    release_helper = ReleaseHelper(
        repo=repo,
        git_dir=git_dir,
        repo_dir=repo_dir,
        owner=owner,
    )
    git_helper = GitHelper(git_dir=git_dir, repo=repo, repo_dir=repo_dir)
    if not git_helper.check_git_repo():
        logger.error(f"{repo} is not a git repository")
        return

    release = release_helper.get_github_release_by_tag(release_tag)

    if not release:
        releases = release_helper.get_releases()
        if not releases:
            logger.info("No releases found")
            if not args.no_tag_deletion:
                delete_git_tag(git_helper, release_helper, release_tag, args.non_interactive)
            return
        logger.error(f"Release {release_tag} not found")
        print_available_releases(releases)
        if not args.no_tag_deletion:
            delete_git_tag(git_helper, release_helper, release_tag, args.non_interactive)
        return

    if not args.non_interactive:
        user_input = input(f"Are you sure you want to delete github release: {release_tag}? [yN] ")
        if not user_input.lower().startswith("y"):
            return

    if not release_helper.delete_github_release(release.get("id")):
        logger.error("Failed to delete GitHub release")

    if not args.no_tag_deletion:
        delete_git_tag(git_helper, release_helper, release_tag, args.non_interactive)

    logger.info(f"Deleted GitHub release: {release_tag}")


if __name__ == "__main__":
    main()
