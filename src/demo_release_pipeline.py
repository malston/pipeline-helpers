#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from src.helpers.argparse_helper import CustomHelpFormatter, HelpfulArgumentParser
from src.helpers.concourse import ConcourseClient
from src.helpers.error_handler import wrap_main
from src.helpers.git_helper import GitHelper
from src.helpers.logger import default_logger as logger
from src.helpers.path_helper import RepositoryPathHelper
from src.helpers.release_helper import ReleaseHelper


class DemoReleasePipeline:
    """Class to handle the demo release pipeline."""

    def __init__(
        self,
        git_helper: GitHelper,
        release_helper: ReleaseHelper,
        concourse_client: ConcourseClient,
        foundation: str,
        repo: str,
        repo_dir: str,
        owner: str,
        branch: str,
        params_repo: str,
        params_dir: str,
        params_branch: str,
        release_tag: str,
        release_body: str,
        dry_run: bool = False,
    ):
        self.git_helper = git_helper
        self.release_helper = release_helper
        self.concourse_client = concourse_client
        self.foundation = foundation
        self.branch = branch
        self.params_branch = params_branch
        self.release_tag = release_tag
        self.release_body = release_body
        self.dry_run = dry_run
        self.owner = owner
        self.repo = repo
        self.repo_dir = repo_dir
        self.params_repo = params_repo
        self.params_dir = params_dir

        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN env must be set before executing this script")

    def is_semantic_version(self, version: str) -> bool:
        """Check if a string is a valid semantic version number.

        Args:
            version: The version string to validate

        Returns:
            bool: True if the version is a valid semantic version, False otherwise
        """
        pattern = r"^\d+\.\d+\.\d+$"
        return bool(re.match(pattern, version))

    def run_git_command(
        self,
        command: list,
        repo_dir: Optional[str] = None,
        dry_run: Optional[bool] = None,
        **kwargs,
    ) -> Optional[subprocess.CompletedProcess]:
        """Run a git command in the repo directory.

        Args:
           command: List of command arguments
           dry_run: Whether to run in dry-run mode (defaults to self.dry_run if not specified)
           **kwargs: Additional arguments to pass to subprocess.run

        Returns:
           Optional[subprocess.CompletedProcess]: The result of running the command,
           or None if dry-run
        """
        repo_dir = repo_dir if repo_dir else self.repo_dir
        dry_run = self.dry_run if dry_run is None else dry_run
        if dry_run:
            logger.info(f'[DRY RUN] Would run git command: {" ".join(command)}')
            return None

        # Set check=False by default unless overridden in kwargs
        if "check" not in kwargs:
            kwargs["check"] = False
        return subprocess.run(command, cwd=repo_dir, **kwargs)

    def validate_git_tag(self, version: str) -> bool:
        """Check if a git tag exists for the given version."""
        try:
            # Check if the tag exists
            result = self.run_git_command(
                ["git", "tag", "-l", f"release-v{version}"],
                check=True,
                capture_output=True,
                text=True,
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return False

    def get_valid_version_input(self) -> Optional[str]:
        """Get and validate version input from the user.

        Returns:
            Optional[str]: The validated version number or None if validation fails
        """
        while True:
            version = input("Enter the version you want to revert to: ").strip()

            if not self.is_semantic_version(version):
                logger.error(f"Invalid version format: {version}")
                logger.info("Version must be in semantic version format (e.g., 1.2.3)")
                retry = input("Would you like to try again? [yN] ")
                if not retry.lower().startswith("y"):
                    return None
                continue

            if not self.validate_git_tag(version):
                logger.error(f"No git tag found for version: release-v{version}")
                logger.info("Available release tags:")
                # Show available tags for reference
                subprocess.run(
                    ["git", "tag", "-l", "|", "sort", "-V", "|", "grep", "release-v*"],
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=self.repo_dir,
                )
                retry = input("Would you like to try again? [yN] ")
                if not retry.lower().startswith("y"):
                    return None
                continue

            return version

    def get_latest_release_tag(self) -> str:
        """Get the latest release tag from git."""
        print(f"Getting latest release tag from {self.repo_dir}...")
        try:
            # Pull all branches and tags
            self.run_git_command(["git", "pull", "-q", "--all"], dry_run=False, check=True)
            result = self.run_git_command(
                ["git", "rev-list", "--tags", "--max-count=1"],
                dry_run=False,
                check=True,
                text=True,
                capture_output=True,
            )
            tag = result.stdout.strip()
            print(f"Latest tag: {tag}")
            # Get latest tag
            result = self.run_git_command(
                ["git", "describe", "--tags", tag],
                dry_run=False,
                check=True,
                text=True,
                capture_output=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            logger.info(f"No release tags found in {self.repo_dir}.")
            return None
            # raise ValueError(f"No release tags found in {self.repo_dir}") from err

    def delete_github_release(
        self, repo: str, owner: str, tag: str, non_interactive: bool = False
    ) -> None:
        """Delete a GitHub release."""

        try:
            # Get all releases to find the one with matching tag
            release = self.release_helper.get_github_release_by_tag(tag)
        except (ConnectionError, ValueError, RuntimeError, IOError) as e:
            logger.error(f"Error fetching releases: {str(e)}")
            return

        if not release:
            return

        release_id = release.get("id")

        if not non_interactive:
            response = input(f"Do you want to delete github release: {tag}? [yN] ")
            if not response.lower().startswith("y"):
                return
        try:
            if self.dry_run:
                logger.info(
                    f"[DRY RUN] Would delete GitHub release {tag} for {owner}/{repo} "
                    f"(release_id: {release_id})"
                )
                return

            # Delete the release
            if self.release_helper.delete_github_release(release_id):
                logger.info(f"Successfully deleted GitHub release {tag} for {owner}/{repo}")
            else:
                logger.error(f"Failed to delete GitHub release {tag}")

        except (ValueError, KeyError, ConnectionError) as e:
            logger.error(f"Error deleting GitHub release: {str(e)}")

    def revert_version(self, previous_version: str) -> None:
        """Revert to a previous version."""
        logger.info(f"Reverting to version: {previous_version}")

        if self.dry_run:
            logger.info("[DRY RUN] Would perform the following actions:")
            logger.info("1. Checkout and pull version branch")
            logger.info(f"2. Update version file to {previous_version}")
            logger.info("3. Commit and push changes")
            logger.info("4. Recreate release branch")
            return

        try:
            # Change to version branch
            self.run_git_command(
                ["git", "checkout", "version"],
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )
            self.run_git_command(["git", "pull", "-q", "origin", "version"], check=True)

            # Update version file
            version_file = os.path.join(self.repo_dir, "version")
            with open(version_file, "w", encoding="utf-8") as f:
                f.write(previous_version)

            # Commit changes
            self.run_git_command(["git", "add", "."], check=True)
            self.run_git_command(
                ["git", "commit", "-m", f"Revert version back to {previous_version} NOTICKET"],
                check=True,
            )
            self.run_git_command(["git", "push", "origin", "version"], check=True)

            # Recreate release branch
            self.run_git_command(["git", "checkout", "master"], check=True)
            self.run_git_command(["git", "pull", "-q", "origin", "version"], check=True)
            self.run_git_command(["git", "branch", "-D", "release"], check=True)
            self.run_git_command(["git", "push", "--delete", "origin", "release"], check=True)
            self.run_git_command(["git", "checkout", "-b", "release"], check=True)
            self.run_git_command(["git", "push", "-u", "origin", "release"], check=True)

        except subprocess.CalledProcessError as e:
            logger.error(f"Git operation failed: {e.cmd}")
            logger.error(f"Exit code: {e.returncode}")
            if e.output:
                logger.error(f"Output: {e.output.decode()}")
            logger.error(
                "Version reversion failed. Please check the git status and resolve any issues."
            )
            return
        except Exception as e:
            logger.error(f"Unexpected error during version reversion: {str(e)}")
            return

    def run_fly_script(self, args: list) -> None:
        """Run the fly.sh script in the repo's ci directory.

        Args:
            args: List of arguments to pass to fly.sh
        """
        if self.dry_run:
            logger.info(f'[DRY RUN] Would run fly.sh with args: {" ".join(args)}')
            return

        ci_dir = os.path.join(self.repo_dir, "ci")
        if not os.path.isdir(ci_dir):
            logger.error(f"CI directory not found at {ci_dir}")
            return

        # Use ConcourseClient to find the fly script
        fly_scripts = self.concourse_client.find_fly_script(ci_dir)

        # Handle the result based on its type
        if fly_scripts is None:
            logger.error(f"No fly script found in {ci_dir}")
            return

        # If a list of scripts was returned, let the user choose one
        if isinstance(fly_scripts, list):
            if len(fly_scripts) == 1:
                fly_script = fly_scripts[0]
            else:
                logger.info("Multiple fly scripts found. Please choose one:")
                for i, script in enumerate(fly_scripts, 1):
                    logger.info(f"{i}. {os.path.basename(script)}")

                while True:
                    try:
                        choice = int(input("Enter the number of the script to use: "))
                        if 1 <= choice <= len(fly_scripts):
                            fly_script = fly_scripts[choice - 1]
                            break
                        logger.error(f"Please enter a number between 1 and {len(fly_scripts)}")
                    except ValueError:
                        logger.error("Please enter a valid number")
        else:
            # Single script path was returned
            fly_script = fly_scripts

        try:
            # Use ConcourseClient to run the fly script
            self.concourse_client.run_fly_script(fly_script, args, cwd=ci_dir)
        except ValueError as e:
            logger.error(str(e))
            return
        except subprocess.CalledProcessError as e:
            logger.error(f"Fly script failed: {e.cmd}")
            logger.error(f"Exit code: {e.returncode}")
            if hasattr(e, "output") and e.output:
                logger.error(f"Output: {e.output.decode()}")
            raise

    def run_release_pipeline(self) -> None:
        """Run the release pipeline."""
        release_pipeline = f"tkgi-{self.repo}-release"
        if self.owner != "Utilities-tkgieng":
            release_pipeline = f"tkgi-{self.repo}-{self.owner}-release"

        if self.dry_run:
            logger.info("[DRY RUN] Would perform the following actions:")
            logger.info(f"1. Ask to recreate release pipeline: {release_pipeline}")
            logger.info("2. Run fly.sh with parameters:")
            logger.info(f"   - foundation: {self.foundation}")
            logger.info(f"   - release body: {self.release_body}")
            logger.info(f"   - owner: {self.owner}")
            logger.info(f"   - pipeline: {release_pipeline}")
            logger.info(f"3. Ask to run pipeline: {release_pipeline}")
            logger.info("4. Update git release tag")
            return

        # Recreate release pipeline if needed
        response = input("Do you want to recreate the release pipeline? [yN] ")
        if response.lower().startswith("y"):
            # Using our ConcourseClient to destroy pipeline
            cmd = ["-t", "tkgi-pipeline-upgrade", "dp", "-p", release_pipeline, "-n"]
            self.concourse_client._run_fly_command(cmd)

        # Run fly.sh script
        self.run_fly_script(
            [
                "-f",
                self.foundation,
                "-r",
                self.release_body,
                "-o",
                self.owner,
                "-p",
                release_pipeline,
            ]
        )

        # Run pipeline if requested
        response = input(f"Do you want to run the {release_pipeline} pipeline? [yN] ")
        if response.lower().startswith("y"):
            # Using our ConcourseClient to unpause, trigger and watch the pipeline
            self.concourse_client.unpause_pipeline("tkgi-pipeline-upgrade", release_pipeline)
            self.concourse_client.trigger_job(
                "tkgi-pipeline-upgrade", f"{release_pipeline}/create-final-release"
            )
            self.concourse_client.watch_job(
                "tkgi-pipeline-upgrade", f"{release_pipeline}/create-final-release"
            )

    def run_set_release_pipeline(self) -> None:
        """Run the set release pipeline."""
        mgmt_pipeline = f"tkgi-{self.repo}-{self.foundation}"
        if self.owner != "Utilities-tkgieng":
            mgmt_pipeline = f"tkgi-{self.repo}-{self.owner}-{self.foundation}"
        set_release_pipeline = f"{mgmt_pipeline}-set-release-pipeline"

        if self.dry_run:
            logger.info("[DRY RUN] Would perform the following actions:")
            logger.info(f"1. Ask to run pipeline: {set_release_pipeline}")
            logger.info("2. Run fly.sh with parameters:")
            logger.info(f"   - foundation: {self.foundation}")
            logger.info(f"   - set pipeline: {set_release_pipeline}")
            logger.info(f"   - branch: {self.branch}")
            logger.info(f"   - params branch: {self.params_branch}")
            logger.info(f"   - owner: {self.owner}")
            logger.info(f"   - pipeline: {mgmt_pipeline}")
            logger.info("3. Unpause and trigger set-release-pipeline job")
            logger.info(f"4. Ask to run pipeline: {mgmt_pipeline}")
            logger.info("5. Unpause and trigger prepare-kustomizations job")
            return

        response = input(f"Do you want to run the {set_release_pipeline} pipeline? [yN] ")
        if response.lower().startswith("y"):
            self.run_fly_script(
                [
                    "-f",
                    self.foundation,
                    "-s",
                    set_release_pipeline,
                    "-b",
                    self.branch,
                    "-d",
                    self.params_branch,
                    "-o",
                    self.owner,
                    "-p",
                    mgmt_pipeline,
                ]
            )

            # Using our ConcourseClient to unpause pipeline and trigger job
            self.concourse_client.unpause_pipeline(self.foundation, set_release_pipeline)
            self.concourse_client.trigger_job(
                self.foundation, f"{set_release_pipeline}/set-release-pipeline", watch=True
            )

            response = input(f"Do you want to run the {mgmt_pipeline} pipeline? [yN] ")
            if response.lower().startswith("y"):
                # Using our ConcourseClient to unpause pipeline and trigger job
                self.concourse_client.unpause_pipeline(self.foundation, mgmt_pipeline)
                self.concourse_client.trigger_job(
                    self.foundation, f"{mgmt_pipeline}/prepare-kustomizations", watch=True
                )

    def refly_pipeline(self) -> None:
        """Refly the pipeline back to latest code."""
        mgmt_pipeline = f"tkgi-{self.repo}-{self.foundation}"
        if self.owner != "Utilities-tkgieng":
            mgmt_pipeline = f"tkgi-{self.repo}-{self.owner}-{self.foundation}"

        if self.dry_run:
            logger.info("[DRY RUN] Would perform the following actions:")
            logger.info(
                f"1. Ask to refly the {mgmt_pipeline} pipeline "
                f"back to latest code on branch: {self.branch}"
            )
            return

        response = input(
            f"Do you want to refly the {mgmt_pipeline} pipeline "
            f"back to latest code on branch: {self.branch}? [yN] "
        )
        if response.lower().startswith("y"):
            self.run_fly_script(["-f", self.foundation, "-b", self.branch, "-p", mgmt_pipeline])

            response = input(f"Do you want to rerun the {mgmt_pipeline} pipeline? [yN] ")
            if response.lower().startswith("y"):
                # Using our ConcourseClient to unpause pipeline and trigger job
                self.concourse_client.unpause_pipeline(self.foundation, mgmt_pipeline)
                self.concourse_client.trigger_job(
                    self.foundation, f"{mgmt_pipeline}/prepare-kustomizations", watch=True
                )

    def handle_version_reversion(self) -> None:
        """Handle checking current version and potential reversion to an older version."""
        if self.dry_run:
            logger.info("[DRY RUN] Would perform the following actions:")
            logger.info("1. Checkout and pull version branch")
            logger.info("2. Read current version from version file")
            logger.info("3. Ask if you want to revert to an older version")
            logger.info("4. If yes, validate and prompt for previous version")
            logger.info("5. If valid, revert to the specified version")
            return

        try:
            # Check current version
            self.run_git_command(["git", "checkout", "version"], check=True)
            self.run_git_command(["git", "pull", "-q", "origin", "version"], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Git operation failed: {e.cmd}")
            logger.error(f"Exit code: {e.returncode}")
            if e.output:
                logger.error(f"Output: {e.output.decode()}")
            return

        version_file = os.path.join(self.repo_dir, "version")
        if not os.path.exists(version_file):
            logger.error(f"Version file not found at {version_file}")
            self.run_git_command(["git", "checkout", self.branch], check=True)
            return

        try:
            with open(version_file, "r", encoding="utf-8") as f:
                current_version = f.read().strip()
        except Exception as e:
            logger.error(f"Error reading version file: {str(e)}")
            self.run_git_command(
                ["git", "checkout", self.branch],
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )
            return

        logger.info(f"The current version is: {current_version}")

        # Handle version reversion if requested
        response = input("Do you want to revert to an older version? [yN] ")
        if response.lower().startswith("y"):
            previous_version = self.get_valid_version_input()
            if previous_version:
                self.revert_version(previous_version)
            else:
                logger.info("Version reversion cancelled")

        # Checkout the original branch
        if self.branch == "version":
            self.branch = "develop"
        self.run_git_command(
            ["git", "checkout", self.branch],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
        self.run_git_command(["git", "pull", "-q"], dry_run=False, check=True)

    def run(self) -> None:
        """Run the complete demo release pipeline."""
        # Check for uncommitted changes
        result = self.run_git_command(
            ["git", "status", "--porcelain"],
            dry_run=False,
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            logger.error("Please commit or stash your changes before running this script")
            return

        # Get current branch if not specified
        if not self.branch:
            try:
                # Check if the tag exists
                result = self.run_git_command(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    dry_run=False,
                    check=True,
                    text=True,
                    capture_output=True,
                )
                if result is None:
                    logger.error("Failed to get current branch")
                    return
                # Get the current branch name
                self.branch = result.stdout.strip()
                print(f"Current branch: {self.branch}")
            except subprocess.CalledProcessError:
                return False

        # Get latest release tag if not specified
        if not self.release_tag:
            self.release_tag = self.get_latest_release_tag()

        if self.release_tag is not None:
            # Delete GitHub release if requested and a release is found
            self.delete_github_release(self.repo, self.owner, self.release_tag)

        # Handle version checking and potential reversion
        self.handle_version_reversion()

        # Run the pipeline steps
        self.run_release_pipeline()

        input("Press enter to continue")

        if not self.release_helper.update_params_git_release_tag():
            logger.error("Failed to update git release tag")
            response = input(
                "Failed to update params git release tag. Do you want to continue anyway? [yN] "
            )
            if not response.lower().startswith("y"):
                logger.info("Exiting the pipeline process.")
                sys.exit(1)

        self.run_set_release_pipeline()
        self.refly_pipeline()


@wrap_main
def main():
    """Main function to parse arguments and run the demo release pipeline."""
    parser = HelpfulArgumentParser(
        prog="demo_release_pipeline.py",
        description="Demo release pipeline script",
        formatter_class=CustomHelpFormatter,
        add_help=False,
        usage="%(prog)s -f foundation -r repo [-o owner] [-b branch] "
        "[-p params_repo] [-d params_branch] [-t tag] [-m message] "
        "[--dry-run] [--git-dir dir] [-h]",
        epilog="""
Options:
   -f foundation     the foundation name for ops manager (e.g. cml-k8s-n-01)
   -r repo           the repo to use
   -o owner          the repo owner to use (default: current user)
   -b branch         the branch to use (default: current branch)
   -p params_repo    the params repo to use (default: params)
   -d params_branch  the params branch to use (default: master)
   -t tag            the release tag (default: latest)
   -m message        the message to apply to the release that is created
   -w dir            the base directory containing git repositories (default: $GIT_WORKSPACE)
   --dry-run         run in dry-run mode (no actual changes will be made)
   -h                display usage
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
        "-o",
        "--owner",
        default="Utilities-tkgieng",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-b",
        "--branch",
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-p",
        "--params-repo",
        default="params",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-d",
        "--params-branch",
        default="master",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-t",
        "--tag",
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-m",
        "--message",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--dry-run",
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

    args = parser.parse_args()
    repo = args.repo
    params_repo = args.params_repo
    owner = args.owner
    git_dir = args.git_dir
    foundation = args.foundation
    message = args.message
    dry_run = args.dry_run
    branch = args.branch
    params_branch = args.params_branch
    release_tag = args.tag

    if not os.path.isdir(git_dir):
        raise ValueError(f"Could not find git directory: {git_dir}")
    if not os.path.isdir(os.path.join(git_dir, repo)):
        raise ValueError(f"Could not find repo directory: {git_dir}/{repo}")

    logger.info(f"Creating release for repo: {repo}")
    logger.info(f"Foundation: {foundation}")

    repo_dir = os.path.join(git_dir, repo)
    params_dir = os.path.join(git_dir, params_repo)
    path_helper = RepositoryPathHelper(git_dir=git_dir, owner=owner)
    repo, repo_dir, params_repo, params_dir = path_helper.adjust_paths(repo, params_repo)

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

    pipeline = DemoReleasePipeline(
        git_helper=git_helper,
        release_helper=release_helper,
        concourse_client=ConcourseClient(),
        foundation=foundation,
        repo=repo,
        repo_dir=repo_dir,
        owner=owner,
        branch=branch,
        params_repo=params_repo,
        params_dir=params_dir,
        params_branch=params_branch,
        release_tag=release_tag,
        release_body=message,
        dry_run=dry_run,
    )

    pipeline.run()


if __name__ == "__main__":
    main()
