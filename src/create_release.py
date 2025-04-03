#!/usr/bin/env python3

import argparse
import os
import subprocess

from helpers.git_helper import GitHelper
from helpers.release_helper import ReleaseHelper
from helpers.concourse import ConcourseClient
from helpers.logger import default_logger as logger


class CustomHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom help formatter to modify the help output."""

    def format_help(self):
        help_text = super().format_help()
        # Remove the default options section
        help_text = help_text.split("\n\n")[0] + "\n\n" + help_text.split("\n\n")[-1]
        # Change "usage:" to "Usage:"
        help_text = help_text.replace("usage:", "Usage:")
        return help_text


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
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
        "-h",
        "--help",
        action="help",
        help="display usage",
    )
    return parser.parse_args()


def main() -> None:
    """Main function to create a new release."""
    args = parse_args()

    repo = args.repo
    params_repo = args.params_repo
    release_pipeline = f"tkgi-{repo}-release"

    if args.owner != "Utilities-tkgieng":
        repo = f"{repo}-{args.owner}"
        params_repo = f"{args.params_repo}-{args.owner}"
        release_pipeline = f"tkgi-{repo}-release"

    # Initialize helpers
    git_helper = GitHelper(repo=repo)
    if not git_helper.check_git_repo():
        logger.error("Git is not installed or not in PATH")
        return
    release_helper = ReleaseHelper(repo=repo, owner=args.owner, params_repo=params_repo)
    concourse_client = ConcourseClient()

    try:
        # Change to the repo's ci directory
        ci_dir = os.path.expanduser(f"~/git/{repo}/ci")
        if not os.path.exists(ci_dir):
            logger.error(f"CI directory not found at {ci_dir}")
            return

        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            logger.info(f"Would change to directory: {ci_dir}")
        else:
            os.chdir(ci_dir)

        # Run release pipeline
        if args.dry_run:
            logger.info(f"Would run release pipeline: {release_pipeline}")
            logger.info(f"Foundation: {args.foundation}")
            if args.message:
                logger.info(f"Release message: {args.message}")
        else:
            if not release_helper.run_release_pipeline(args.foundation, args.message):
                logger.error("Failed to run release pipeline")
                return

        # Update git release tag
        if args.dry_run:
            logger.info("Would update git release tag")
        else:
            if not release_helper.update_params_git_release_tag():
                logger.error("Failed to update git release tag")
                return

        # Run set pipeline
        if args.dry_run:
            logger.info(f"Would run set pipeline for foundation: {args.foundation}")
        else:
            if not release_helper.run_set_pipeline(args.foundation):
                logger.error("Failed to run set pipeline")
                return

        # Ask if user wants to run the prepare-kustomizations job
        if not args.dry_run:
            user_input = input(
                f"Do you want to run the tkgi-{repo}-{args.foundation} pipeline? [yN] "
            )
            if user_input.lower().startswith("y"):
                concourse_client.trigger_job(
                    args.foundation,
                    f"tkgi-{repo}-{args.foundation}/prepare-kustomizations",
                    watch=True,
                )
        else:
            logger.info(f"Would prompt to run tkgi-{repo}-{args.foundation} pipeline")

        # Get current branch
        branch = git_helper.get_current_branch()

        # Ask if user wants to refly the pipeline
        if not args.dry_run:
            pipeline_name = f"tkgi-{repo}-{args.foundation}"
            prompt = (
                f"Do you want to refly the {pipeline_name} pipeline "
                f"back to latest code on branch: {branch}? [yN] "
            )
            user_input = input(prompt)
            if user_input.lower().startswith("y"):
                # Find the fly.sh script in the current directory
                fly_script = os.path.join(os.getcwd(), "fly.sh")
                if os.path.isfile(fly_script) and os.access(fly_script, os.X_OK):
                    # Use ConcourseClient to run the script
                    try:
                        subprocess.run(
                            [fly_script, "-f", args.foundation, "-b", branch],
                            input=b"y\n",
                            check=True,
                        )
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to run fly.sh: {e}")
                else:
                    logger.error(f"Fly script not found or not executable at {fly_script}")
        else:
            logger.info(f"Would prompt to refly pipeline on branch: {branch}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}: {e}")
        return
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return


if __name__ == "__main__":
    main()
