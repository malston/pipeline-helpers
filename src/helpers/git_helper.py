#!/usr/bin/env python3

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import git

from src.helpers.logger import default_logger as logger


class GitHelper:
    """Helper class for git operations used in release pipeline scripts."""

    def __init__(
        self,
        git_dir: str,
        repo_dir: Optional[str] = None,
        repo: Optional[str] = None,
        params: str = "params",
        params_dir: Optional[str] = None,
    ):
        self.git_dir = (
            git_dir if git_dir else os.environ.get("GIT_WORKSPACE", str(Path.home() / "git"))
        )
        self.repo = repo
        self.repo_dir = repo_dir if repo_dir else os.path.join(self.git_dir, self.repo)
        self.params = params
        self.params_dir = params_dir if params_dir else os.path.join(self.git_dir, self.params)

    # Logging methods removed - use logger directly

    def get_repo_info(self, repo: Optional[str] = None) -> Tuple[str, str]:
        """Extract owner and repo name from git remote URL."""
        repo_dir = self.repo_dir if repo is None else os.path.join(self.git_dir, repo)
        try:
            repo_obj = git.Repo(repo_dir)
            for remote in repo_obj.remotes:
                if remote.name == "origin":
                    url = next(remote.urls)
                    # Handle SSH or HTTPS URL formats
                    match = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", url)
                    if match:
                        return match.group(1), match.group(2)

            raise ValueError("Not a GitHub repository or missing origin remote")
        except (git.InvalidGitRepositoryError, git.NoSuchPathError) as err:
            raise ValueError("Current directory is not a git repository") from err

    def check_git_repo(self, repo: Optional[str] = None) -> bool:
        """Check if repo is a git repository."""
        repo_dir = self.repo_dir if repo is None else os.path.join(self.git_dir, repo)
        try:
            git.Repo(repo_dir)
            return True
        except (git.InvalidGitRepositoryError, git.NoSuchPathError):
            return False

    def _get_repo(self, repo: Optional[str] = None) -> git.Repo:
        """Get a git.Repo object for the specified repository."""
        repo_dir = self.repo_dir if repo is None else os.path.join(self.git_dir, repo)
        try:
            return git.Repo(repo_dir)
        except (git.InvalidGitRepositoryError, git.NoSuchPathError) as e:
            logger.error(f"Failed to get repository '{repo_dir}': {e}")
            raise

    def pull(self, repo: Optional[str] = None) -> None:
        """Pull changes from remote."""
        try:
            repo_obj = self._get_repo(repo)
            origin = repo_obj.remotes.origin
            origin.pull(quiet=True)
        except Exception as e:
            logger.error(f"Failed to pull changes: {e}")

    def pull_all(self, repo: Optional[str] = None) -> None:
        """Pull all changes from all remotes."""
        try:
            repo_obj = self._get_repo(repo)
            for remote in repo_obj.remotes:
                remote.pull(quiet=True)
        except Exception as e:
            logger.error(f"Failed to pull changes: {e}")

    def get_current_branch(self, repo: Optional[str] = None) -> str:
        """Get the current branch name."""
        try:
            repo_obj = self._get_repo(repo)
            return repo_obj.active_branch.name
        except Exception as e:
            logger.error(f"Failed to get current branch: {e}")
            return ""

    def get_tags(self, repo: Optional[str] = None) -> Union[List[git.Tag], Dict[str, git.Tag]]:
        """Get all git tags."""
        try:
            repo_obj = self._get_repo(repo)
            return repo_obj.tags
        except (git.InvalidGitRepositoryError, git.NoSuchPathError, Exception):
            return []

    def delete_tag(self, tag: str, repo: Optional[str] = None) -> bool:
        """Delete a git tag locally and remotely."""
        try:
            repo_obj = self._get_repo(repo)
            # Delete locally
            repo_obj.delete_tag(tag)
            # Delete remotely
            origin = repo_obj.remotes.origin
            origin.push(refspec=f":refs/tags/{tag}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete tag: {e}")
            return False

    def has_uncommitted_changes(self, repo: Optional[str] = None) -> bool:
        """Check if there are any uncommitted changes."""
        try:
            repo_obj = self._get_repo(repo)
            return repo_obj.is_dirty()
        except Exception as e:
            logger.error(f"Failed to check git status: {e}")
            return True

    def reset_changes(self, repo: Optional[str] = None) -> None:
        """Reset all changes in the working directory."""
        try:
            repo_obj = self._get_repo(repo)
            repo_obj.head.reset(index=True, working_tree=True)
        except Exception as e:
            logger.error(f"Failed to reset changes: {e}")

    def update_release_tag_in_params(
        self, params_repo: str, repo: str, from_version: str, to_version: str
    ) -> None:
        """Update the release tag in params files."""
        params_dir = self.params_dir if params_repo is None else os.path.join(self.git_dir, repo)
        try:
            # Find and update files
            for root, _, files in os.walk(params_dir):
                for file in files:
                    if file.endswith(f"-{repo}.yml") or file.endswith(f".{repo}.yaml"):
                        file_path = os.path.join(root, file)
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        if f"git_release_tag: release-{from_version}" in content:
                            new_content = content.replace(
                                f"git_release_tag: release-{from_version}",
                                f"git_release_tag: release-{to_version}",
                            )
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(new_content)
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Failed to update release tag in params: {e}")

    def create_and_merge_branch(self, repo: str, branch_name: str, commit_message: str) -> bool:
        """Create a new branch, commit changes, and merge it into master."""
        try:
            repo_obj = self._get_repo(repo)

            # Create and checkout new branch
            new_branch = repo_obj.create_head(branch_name)
            new_branch.checkout()

            # Add all changes
            repo_obj.git.add(A=True)

            # Commit changes
            repo_obj.index.commit(commit_message)

            # Checkout master branch
            master = repo_obj.heads.master
            master.checkout()

            # Pull latest changes from origin/master
            origin = repo_obj.remotes.origin
            origin.pull("master")

            # Rebase changes onto master
            repo_obj.git.rebase(branch_name)

            # Push to remote
            origin.push("master")

            # Delete the branch
            repo_obj.delete_head(branch_name, force=True)

            return True
        except Exception as e:
            logger.error(f"Failed to create and merge branch: {e}")
            return False

    def create_and_push_tag(self, repo: str, tag_name: str, tag_message: str) -> bool:
        """Create and push a git tag."""
        try:
            repo_obj = self._get_repo(repo)

            # Create tag
            repo_obj.create_tag(tag_name, message=tag_message)

            # Push tag to remote
            origin = repo_obj.remotes.origin
            origin.push(tag_name)

            return True
        except Exception as e:
            logger.error(f"Failed to create and push tag: {e}")
            return False

    def confirm(self, message: str) -> bool:
        """Ask for user confirmation."""
        response = input(f"{message} (y/N): ")
        return response.lower().startswith("y")

    def tag_exists(self, tag: str, repo: Optional[str] = None) -> bool:
        """Check if a git tag exists."""
        try:
            repo_obj = self._get_repo(repo)
            for existing_tag in repo_obj.tags:
                if existing_tag.name == tag:
                    return True
            return False
        except Exception:
            return False
