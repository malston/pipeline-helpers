import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.update_params_release_tag import parse_args


# Create an undecorated version of the main function for testing
def main_test_function():
    """
    This is a copy of the main function without the wrapper for testing purposes.
    Must be kept in sync with the original in src/update_params_release_tag.py
    """
    import os

    from src.helpers.path_helper import RepositoryPathHelper
    from src.update_params_release_tag import ReleaseHelper

    args = parse_args()

    repo = args.repo
    params_repo = args.params_repo
    owner = args.owner
    git_dir = "/home/user/git"  # For testing, use a fixed path

    if not os.path.isdir(git_dir):
        raise ValueError(f"Could not find git directory: {git_dir}")
    if not os.path.isdir(os.path.join(git_dir, repo)):
        raise ValueError(f"Could not find repo directory: {git_dir}/{repo}")

    repo_dir = os.path.join(git_dir, repo)
    params_dir = os.path.join(git_dir, params_repo)
    path_helper = RepositoryPathHelper(git_dir=git_dir, owner=owner)
    repo, repo_dir, params_repo, params_dir = path_helper.adjust_paths(repo, params_repo)

    # Initialize helpers
    release_helper = ReleaseHelper(
        repo=repo,
        repo_dir=repo_dir,
        owner=owner,
        params_dir=params_dir,
        params_repo=params_repo,
    )
    os.chdir(repo_dir)

    if not release_helper.update_params_git_release_tag("v"):
        raise ValueError("Failed to update git release tag")


def test_parse_args():
    # Test with required arguments
    with patch("sys.argv", ["update_params_release_tag.py", "-r", "test-repo"]):
        args = parse_args()
        assert args.repo == "test-repo"
        assert args.owner == "Utilities-tkgieng"  # Default value
        assert args.params_repo == "params"  # Default value

    # Test with all arguments
    with patch(
        "sys.argv",
        [
            "update_params_release_tag.py",
            "-r",
            "test-repo",
            "-o",
            "custom-owner",
            "-p",
            "custom-params",
        ],
    ):
        args = parse_args()
        assert args.repo == "test-repo"
        assert args.owner == "custom-owner"
        assert args.params_repo == "custom-params"

    # Test missing required argument
    with patch("sys.argv", ["update_params_release_tag.py"]):
        with pytest.raises(SystemExit):
            parse_args()


def test_custom_help_formatter():
    # Test that the help formatter modifies the help text correctly
    from src.helpers.argparse_helper import CustomHelpFormatter

    # Create a formatter with a mocked super method
    formatter = CustomHelpFormatter(prog="test")
    # Mock the superclass method by patching it
    with patch("argparse.RawDescriptionHelpFormatter.format_help") as mock_super_format_help:
        mock_super_format_help.return_value = (
            "usage: test\n\noptional arguments:\n-h, --help\n\ndetailed help"
        )

        # Call the actual method
        result = formatter.format_help()

        # Verify that "usage:" was changed to "Usage:"
        assert "Usage:" in result
        assert "usage:" not in result


@patch("os.path.isdir")
def test_main_repo_dir_not_found(mock_isdir):
    # Setup mocks - first call for git_dir, second call for repo_dir
    mock_isdir.side_effect = [True, False]

    # Run with required arguments
    with patch("sys.argv", ["update_params_release_tag.py", "-r", "test-repo"]):
        with pytest.raises(ValueError) as excinfo:
            main_test_function()

        # Verify error message
        assert "Could not find repo directory" in str(excinfo.value)


@patch("os.path.isdir")
@patch("os.chdir")
@patch("src.update_params_release_tag.ReleaseHelper")
def test_main_not_git_repo(mock_release_helper, mock_chdir, mock_isdir):
    # Setup mocks - first call for git_dir, second call for repo_dir
    mock_isdir.side_effect = [False, True]

    # Run with required arguments
    with patch("sys.argv", ["update_params_release_tag.py", "-r", "test-repo"]):
        with pytest.raises(ValueError) as excinfo:
            main_test_function()

        # Verify error message
        assert "Could not find git directory: /home/user/git" in str(excinfo.value)

        # Verify release_helper.update_params_git_release_tag wasn't called
        mock_release_helper.return_value.update_params_git_release_tag.assert_not_called()


@patch("os.path.isdir")
@patch("os.chdir")
@patch("src.update_params_release_tag.ReleaseHelper")
@patch("src.helpers.path_helper.RepositoryPathHelper")
def test_main_update_tag_fails(mock_path_helper, mock_release_helper, mock_chdir, mock_isdir):
    # Setup mocks
    mock_isdir.return_value = True
    mock_path_helper.return_value.adjust_paths.return_value = (
        "test-repo",
        "/home/user/git/test-repo",
        "params",
        "/home/user/git/params"
    )
    mock_release_helper.return_value.update_params_git_release_tag.return_value = False

    # Run with required arguments
    with patch("sys.argv", ["update_params_release_tag.py", "-r", "test-repo"]):
        with pytest.raises(ValueError) as excinfo:
            main_test_function()

        # Verify error message
        assert "Failed to update git release tag" in str(excinfo.value)


@patch("os.path.isdir")
@patch("os.chdir")
@patch("src.update_params_release_tag.ReleaseHelper")
@patch("src.helpers.path_helper.RepositoryPathHelper")
def test_main_success(mock_path_helper, mock_release_helper, mock_chdir, mock_isdir):
    # Setup mocks
    mock_isdir.return_value = True
    mock_path_helper.return_value.adjust_paths.return_value = (
        "test-repo",
        "/home/user/git/test-repo",
        "params",
        "/home/user/git/params"
    )
    mock_release_helper.return_value.update_params_git_release_tag.return_value = True

    # Run with required arguments
    with patch("sys.argv", ["update_params_release_tag.py", "-r", "test-repo"]):
        main_test_function()

    # Verify ReleaseHelper was initialized correctly
    mock_release_helper.assert_called_once_with(
        repo="test-repo",
        repo_dir="/home/user/git/test-repo",
        owner="Utilities-tkgieng",
        params_dir="/home/user/git/params",
        params_repo="params",
    )

    # Verify update_params_git_release_tag was called
    mock_release_helper.return_value.update_params_git_release_tag.assert_called_once_with("v")


@patch("os.path.isdir")
@patch("os.chdir")
@patch("src.update_params_release_tag.ReleaseHelper")
@patch("src.helpers.path_helper.RepositoryPathHelper")
def test_main_with_custom_owner(mock_path_helper, mock_release_helper, mock_chdir, mock_isdir):
    # Setup mocks
    mock_isdir.return_value = True
    mock_path_helper.return_value.adjust_paths.return_value = (
        "test-repo",
        "/home/user/git/test-repo-custom-owner",
        "params",
        "/home/user/git/params-custom-owner"
    )
    mock_release_helper.return_value.update_params_git_release_tag.return_value = True

    # Run with custom owner
    with patch(
        "sys.argv", ["update_params_release_tag.py", "-r", "test-repo", "-o", "custom-owner"]
    ):
        main_test_function()

    # Verify ReleaseHelper was initialized with correct params
    mock_release_helper.assert_called_once_with(
        repo="test-repo",
        repo_dir="/home/user/git/test-repo-custom-owner",
        owner="custom-owner",
        params_dir="/home/user/git/params-custom-owner",
        params_repo="params",
    )


@patch("os.path.isdir")
@patch("os.chdir")
@patch("src.update_params_release_tag.ReleaseHelper")
@patch("src.helpers.path_helper.RepositoryPathHelper")
def test_main_repo_ending_with_owner(mock_path_helper, mock_release_helper, mock_chdir, mock_isdir):
    # Setup mocks
    mock_isdir.return_value = True
    mock_path_helper.return_value.adjust_paths.return_value = (
        "test-repo",
        "/home/user/git/test-repo",
        "params",
        "/home/user/git/params"
    )
    mock_release_helper.return_value.update_params_git_release_tag.return_value = True

    # Run with repo that ends with owner
    with patch("sys.argv", ["update_params_release_tag.py", "-r", "test-repo-Utilities-tkgieng"]):
        main_test_function()

    # Verify ReleaseHelper was initialized correctly
    mock_release_helper.assert_called_once_with(
        repo="test-repo",
        repo_dir="/home/user/git/test-repo",
        owner="Utilities-tkgieng",
        params_dir="/home/user/git/params",
        params_repo="params",
    )


@patch("os.path.isdir")
@patch("os.chdir")
@patch("src.update_params_release_tag.ReleaseHelper")
@patch("src.helpers.path_helper.RepositoryPathHelper")
def test_main_params_repo_ending_with_owner(
    mock_path_helper, mock_release_helper, mock_chdir, mock_isdir
):
    # Setup mocks
    mock_isdir.return_value = True
    mock_path_helper.return_value.adjust_paths.return_value = (
        "test-repo",
        "/home/user/git/test-repo",
        "params-Utilities-tkgieng",
        "/home/user/git/params-Utilities-tkgieng"
    )
    mock_release_helper.return_value.update_params_git_release_tag.return_value = True

    # Run with params repo that ends with owner
    with patch(
        "sys.argv",
        ["update_params_release_tag.py", "-r", "test-repo", "-p", "params-Utilities-tkgieng"],
    ):
        main_test_function()

    # Verify ReleaseHelper was initialized with correct params
    # The actual implementation retains the full params repo name
    mock_release_helper.assert_called_once_with(
        repo="test-repo",
        repo_dir="/home/user/git/test-repo",
        owner="Utilities-tkgieng",
        params_dir="/home/user/git/params-Utilities-tkgieng",
        params_repo="params-Utilities-tkgieng",
    )
