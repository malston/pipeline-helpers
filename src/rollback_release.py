#!/usr/bin/env python3

import argparse
import os
import subprocess

from src.helpers.argparse_helper import CustomHelpFormatter, HelpfulArgumentParser
from src.helpers.error_handler import wrap_main
from src.helpers.git_helper import GitHelper
from src.helpers.logger import default_logger as logger
from src.helpers.release_helper import ReleaseHelper


def parse_args() -> argparse.Namespace:
    parser = HelpfulArgumentParser(
        prog="rollback_release.py",
        description="Rollback a release",
        formatter_class=CustomHelpFormatter,
        add_help=False,
        usage="%(prog)s -f foundation -r release_tag [-o owner] [-p params_repo] [-h]",
        epilog="""
Options:
   -f foundation    the foundation name for ops manager (e.g. cml-k8s-n-01)
   -r release_tag   the release tag
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
        "--release",
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
        "-h",
        "--help",
        action="help",
        help="display usage",
    )
    return parser.parse_args()


@wrap_main
def main() -> None:
    args = parse_args()
    repo = "ns-mgmt"
    params_repo = args.params_repo

    if args.owner != "Utilities-tkgieng":
        repo = f"{repo}-{args.owner}"
        params_repo = f"{args.params_repo}-{args.owner}"

    # Initialize helpers
    git_helper = GitHelper(repo=repo)
    if not git_helper.check_git_repo():
        raise ValueError(f"Git repository {repo} not found or not a valid Git repository")

    release_helper = ReleaseHelper(repo=repo, owner=args.owner, params_repo=params_repo)

    # Change to the repo's ci directory
    ci_dir = os.path.expanduser(f"~/git/{repo}/ci")
    if not os.path.exists(ci_dir):
        raise ValueError(f"CI directory not found at {ci_dir}")

    os.chdir(ci_dir)

    # Validate release tag
    release_tag = f"{repo}-{args.release}"
    if not release_helper.validate_params_release_tag(release_tag):
        logger.error(
            f"Release [-r {args.release}] must be a valid release tagged on the params repo"
        )
        logger.info("Valid tags are:")
        release_helper.print_valid_params_release_tags()
        raise ValueError(f"Invalid release tag: {args.release}")

    # Run set pipeline
    if not release_helper.run_set_pipeline(args.foundation):
        raise ValueError("Failed to run set pipeline")

    # Ask user if they want to run the pipeline
    user_input = input(f"Do you want to run the tkgi-{repo}-{args.foundation} pipeline? [yN] ")
    if user_input.lower().startswith("y"):
        try:
            subprocess.run(
                [
                    "fly",
                    "-t",
                    args.foundation,
                    "trigger-job",
                    f"tkgi-{repo}-{args.foundation}/prepare-kustomizations",
                    "-w",
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to trigger pipeline job: {e}")


if __name__ == "__main__":
    main()
