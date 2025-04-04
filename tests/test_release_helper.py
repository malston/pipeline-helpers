#!/usr/bin/env python3

import subprocess
import unittest
from unittest.mock import MagicMock, call, patch

# Using import from package
from src.helpers.release_helper import ReleaseHelper


class TestReleaseHelper(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.patcher1 = patch("src.helpers.release_helper.GitHelper")
        self.patcher2 = patch("src.helpers.release_helper.logger")
        self.patcher3 = patch("src.helpers.release_helper.GitHubClient")

        self.mock_git_helper = self.patcher1.start()
        self.mock_logger = self.patcher2.start()
        self.mock_github_client = self.patcher3.start()

        # Setup mock GitHelper instance
        self.mock_git = self.mock_git_helper.return_value
        self.mock_git.check_git_repo.return_value = True

        # Setup mock GitHub client
        self.mock_github = self.mock_github_client.return_value

        self.helper = ReleaseHelper(
            foundation="test-foundation",
            repo="test-repo",
            owner="test-owner",
            params_repo="test-params",
            git_dir="/test/git",
            repo_dir="/test/repo",
            params_dir="/test/params",
        )

    def tearDown(self):
        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()

    def test_update_params_git_release_tag_success(self):
        """Test successful update of params git release tag."""
        # Setup mock GitHelper instance
        self.mock_git.pull_all.return_value = None

        # Create mock git tag objects
        mock_tag1 = MagicMock()
        mock_tag1.name = "release-v1.0.0"
        mock_tag2 = MagicMock()
        mock_tag2.name = "release-v1.1.0"
        self.mock_git.get_tags.return_value = [mock_tag1, mock_tag2]

        self.mock_git.confirm.side_effect = [True, True]  # Confirm both prompts
        self.mock_git.has_uncommitted_changes.return_value = False
        self.mock_git.update_release_tag_in_params.return_value = None
        self.mock_git.create_and_merge_branch.return_value = None
        self.mock_git.create_and_push_tag.return_value = None
        self.mock_git.info.return_value = None
        self.mock_git.error.return_value = None

        # Mock subprocess.run for git status and diff
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Execute the method
            result = self.helper.update_params_git_release_tag()

            # Verify the result
            self.assertTrue(result)

            # Verify all expected calls were made
            self.assertEqual(self.mock_git.pull_all.call_count, 2)
            self.mock_git.pull_all.assert_has_calls(
                [
                    call(),  # First call without repo parameter
                    call(repo="test-params"),  # Second call with params repo
                ]
            )
            self.mock_git.get_tags.assert_called_once()
            self.assertEqual(self.mock_git.confirm.call_count, 2)
            self.mock_git.has_uncommitted_changes.assert_called_once_with(repo="test-params")
            self.mock_git.update_release_tag_in_params.assert_called_once_with(
                "test-params", "test-repo", "v1.0.0", "v1.1.0"
            )
            self.mock_git.create_and_merge_branch.assert_called_once_with(
                "test-params",
                "test-repo-release-v1.1.0",
                "Update git_release_tag from release-v1.0.0 to release-v1.1.0\n\nNOTICKET",
            )
            self.mock_git.create_and_push_tag.assert_called_once_with(
                "test-params", "test-repo-release-v1.1.0", "Version test-repo-release-v1.1.0"
            )

    def test_update_params_git_release_tag_no_release_tags(self):
        """Test failure when no release tags are found."""
        # Setup mock GitHelper instance
        self.mock_git.pull_all.return_value = None
        self.mock_git.get_tags.return_value = []

        # Execute the method
        result = self.helper.update_params_git_release_tag()

        # Verify the result
        self.assertFalse(result)
        self.mock_logger.error.assert_called_with("No release tags found")

    def test_update_params_git_release_tag_uncommitted_changes(self):
        """Test failure when there are uncommitted changes in params repo."""
        # Setup mock GitHelper instance
        self.mock_git.pull_all.return_value = None

        # Create mock git tag objects
        mock_tag1 = MagicMock()
        mock_tag1.name = "release-v1.0.0"
        mock_tag2 = MagicMock()
        mock_tag2.name = "release-v1.1.0"
        self.mock_git.get_tags.return_value = [mock_tag1, mock_tag2]

        self.mock_git.confirm.return_value = True
        self.mock_git.has_uncommitted_changes.return_value = True

        # Execute the method
        result = self.helper.update_params_git_release_tag()

        # Verify the result
        self.assertFalse(result)
        self.mock_logger.error.assert_called_with("Please commit or stash your changes to params")

    def test_update_params_git_release_tag_user_cancels(self):
        """Test when user cancels the operation."""
        # Setup mock GitHelper instance
        self.mock_git.pull_all.return_value = None

        # Create mock git tag objects
        mock_tag1 = MagicMock()
        mock_tag1.name = "release-v1.0.0"
        mock_tag2 = MagicMock()
        mock_tag2.name = "release-v1.1.0"
        self.mock_git.get_tags.return_value = [mock_tag1, mock_tag2]

        self.mock_git.confirm.return_value = False
        self.mock_git.info.return_value = None

        # Execute the method
        result = self.helper.update_params_git_release_tag()

        # Verify the result
        self.assertFalse(result)

    def test_update_params_git_release_tag_git_error(self):
        """Test handling of git command errors."""
        # Setup mock GitHelper instance
        self.mock_git.pull_all.return_value = None

        # Create mock git tag objects
        mock_tag1 = MagicMock()
        mock_tag1.name = "release-v1.0.0"
        mock_tag2 = MagicMock()
        mock_tag2.name = "release-v1.1.0"
        self.mock_git.get_tags.return_value = [mock_tag1, mock_tag2]

        self.mock_git.confirm.return_value = True
        self.mock_git.has_uncommitted_changes.return_value = False
        self.mock_git.update_release_tag_in_params.side_effect = subprocess.SubprocessError(
            "Git error"
        )

        # Execute the method
        result = self.helper.update_params_git_release_tag()

        # Verify the result
        self.assertFalse(result)
        self.mock_logger.error.assert_called_with(
            "Failed to update release tag in params: Git error"
        )


if __name__ == "__main__":
    unittest.main()
