import sys
import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.rollback_release import CustomHelpFormatter, parse_args

# Create an undecorated version of the main function for testing
def main_test_function():
    """
    This is a copy of the main function without the wrapper for testing purposes.
    Must be kept in sync with the original in src/rollback_release.py
    """
    from src.rollback_release import GitHelper, ReleaseHelper
    import os
    import subprocess
    
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
        release_helper.print_valid_params_release_tags()
        raise ValueError(f"Release [-r {args.release}] must be a valid release tagged on the params repo")

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


def test_parse_args():
    # Test with required arguments
    with patch("sys.argv", ["rollback_release.py", "-f", "foundation1", "-r", "v1.0.0"]):
        args = parse_args()
        assert args.foundation == "foundation1"
        assert args.release == "v1.0.0"
        assert args.params_repo == "params"  # Default value

    # Test with custom params repo
    with patch(
        "sys.argv",
        ["rollback_release.py", "-f", "foundation1", "-r", "v1.0.0", "-p", "custom-params"],
    ):
        args = parse_args()
        assert args.params_repo == "custom-params"

    # Test missing required argument (foundation)
    with patch("sys.argv", ["rollback_release.py", "-r", "v1.0.0"]):
        with pytest.raises(SystemExit):
            parse_args()

    # Test missing required argument (release)
    with patch("sys.argv", ["rollback_release.py", "-f", "foundation1"]):
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


@patch("src.rollback_release.GitHelper")
@patch("src.rollback_release.ReleaseHelper")
@patch("os.path.exists")
@patch("os.path.expanduser")
@patch("os.chdir")
def test_main_ci_dir_not_found(
    mock_chdir,
    mock_expanduser,
    mock_exists,
    mock_release_helper,
    mock_git_helper,
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_exists.return_value = False
    
    # Mock expanduser to avoid file system errors
    mock_ci_dir = "/home/user/git/ns-mgmt/ci"
    mock_expanduser.return_value = mock_ci_dir

    # Run with required arguments
    with patch("sys.argv", ["rollback_release.py", "-f", "foundation1", "-r", "v1.0.0"]):
        with pytest.raises(ValueError) as excinfo:
            main_test_function()
        
        # Verify the error message
        assert "CI directory not found" in str(excinfo.value)

    # Verify chdir was not called
    mock_chdir.assert_not_called()


@patch("src.rollback_release.GitHelper")
@patch("src.rollback_release.ReleaseHelper")
@patch("os.path.exists")
@patch("os.path.expanduser")
@patch("os.chdir")
def test_main_invalid_release_tag(
    mock_chdir,
    mock_expanduser,
    mock_exists,
    mock_release_helper,
    mock_git_helper,
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_exists.return_value = True
    
    # Mock expanduser to avoid file system errors
    mock_ci_dir = "/home/user/git/ns-mgmt/ci"
    mock_expanduser.return_value = mock_ci_dir
    
    # Make validate_params_release_tag return False
    mock_release_helper.return_value.validate_params_release_tag.return_value = False

    # Run with required arguments
    with patch("sys.argv", ["rollback_release.py", "-f", "foundation1", "-r", "v1.0.0"]):
        with pytest.raises(ValueError) as excinfo:
            main_test_function()
        
        # Verify the error message
        assert "must be a valid release tagged on the params repo" in str(excinfo.value)

    # Verify method was called
    mock_release_helper.return_value.validate_params_release_tag.assert_called_once_with(
        "ns-mgmt-v1.0.0"
    )
    # Verify print valid tags was called
    mock_release_helper.return_value.print_valid_params_release_tags.assert_called_once()


@patch("src.rollback_release.GitHelper")
@patch("src.rollback_release.ReleaseHelper")
@patch("os.path.exists")
@patch("os.path.expanduser")
@patch("os.chdir")
def test_main_set_pipeline_fails(
    mock_chdir,
    mock_expanduser,
    mock_exists,
    mock_release_helper,
    mock_git_helper,
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_exists.return_value = True
    
    # Mock expanduser to avoid file system errors
    mock_ci_dir = "/home/user/git/ns-mgmt/ci"
    mock_expanduser.return_value = mock_ci_dir
    
    # Make methods return appropriate values
    mock_release_helper.return_value.validate_params_release_tag.return_value = True
    mock_release_helper.return_value.run_set_pipeline.return_value = False

    # Run with required arguments
    with patch("sys.argv", ["rollback_release.py", "-f", "foundation1", "-r", "v1.0.0"]):
        with pytest.raises(ValueError) as excinfo:
            main_test_function()
        
        # Verify the error message
        assert "Failed to run set pipeline" in str(excinfo.value)

    # Verify set pipeline was called
    mock_release_helper.return_value.run_set_pipeline.assert_called_once_with("foundation1")


@patch("src.rollback_release.GitHelper")
@patch("src.rollback_release.ReleaseHelper")
@patch("os.path.exists")
@patch("os.path.expanduser")
@patch("os.chdir")
@patch("builtins.input")
@patch("subprocess.run")
def test_main_trigger_pipeline_user_accepts(
    mock_subprocess_run,
    mock_input,
    mock_chdir,
    mock_expanduser,
    mock_exists,
    mock_release_helper,
    mock_git_helper,
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_exists.return_value = True
    
    # Mock expanduser to avoid file system errors
    mock_ci_dir = "/home/user/git/ns-mgmt/ci"
    mock_expanduser.return_value = mock_ci_dir
    
    # Make methods return appropriate values
    mock_release_helper.return_value.validate_params_release_tag.return_value = True
    mock_release_helper.return_value.run_set_pipeline.return_value = True
    
    # Mock user input to accept running pipeline
    mock_input.return_value = "yes"

    # Run with required arguments
    with patch("sys.argv", ["rollback_release.py", "-f", "foundation1", "-r", "v1.0.0"]):
        main_test_function()

    # Verify trigger job was called
    mock_subprocess_run.assert_called_once_with(
        [
            "fly",
            "-t",
            "foundation1",
            "trigger-job",
            "tkgi-ns-mgmt-foundation1/prepare-kustomizations",
            "-w",
        ],
        check=True,
    )


@patch("src.rollback_release.GitHelper")
@patch("src.rollback_release.ReleaseHelper")
@patch("os.path.exists")
@patch("os.path.expanduser")
@patch("os.chdir")
@patch("builtins.input")
@patch("subprocess.run")
def test_main_trigger_pipeline_user_declines(
    mock_subprocess_run,
    mock_input,
    mock_chdir,
    mock_expanduser,
    mock_exists,
    mock_release_helper,
    mock_git_helper,
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_exists.return_value = True
    
    # Mock expanduser to avoid file system errors
    mock_ci_dir = "/home/user/git/ns-mgmt/ci"
    mock_expanduser.return_value = mock_ci_dir
    
    # Make methods return appropriate values
    mock_release_helper.return_value.validate_params_release_tag.return_value = True
    mock_release_helper.return_value.run_set_pipeline.return_value = True
    
    # Mock user input to decline running pipeline
    mock_input.return_value = "no"

    # Run with required arguments
    with patch("sys.argv", ["rollback_release.py", "-f", "foundation1", "-r", "v1.0.0"]):
        main_test_function()

    # Verify trigger job was not called
    mock_subprocess_run.assert_not_called()


@patch("src.rollback_release.GitHelper")
@patch("src.rollback_release.ReleaseHelper")
@patch("os.path.exists")
@patch("os.path.expanduser")
@patch("os.chdir")
@patch("builtins.input")
@patch("subprocess.run")
def test_main_trigger_pipeline_subprocess_error(
    mock_subprocess_run,
    mock_input,
    mock_chdir,
    mock_expanduser,
    mock_exists,
    mock_release_helper,
    mock_git_helper,
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_exists.return_value = True
    
    # Mock expanduser to avoid file system errors
    mock_ci_dir = "/home/user/git/ns-mgmt/ci"
    mock_expanduser.return_value = mock_ci_dir
    
    # Make methods return appropriate values
    mock_release_helper.return_value.validate_params_release_tag.return_value = True
    mock_release_helper.return_value.run_set_pipeline.return_value = True
    
    # Mock user input to accept running pipeline
    mock_input.return_value = "yes"
    
    # Make subprocess.run raise an error
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "fly")

    # Run with required arguments
    with patch("sys.argv", ["rollback_release.py", "-f", "foundation1", "-r", "v1.0.0"]):
        with pytest.raises(ValueError) as excinfo:
            main_test_function()
        
        # Verify the error message
        assert "Failed to trigger pipeline job" in str(excinfo.value)


@patch("src.rollback_release.GitHelper")
@patch("src.rollback_release.ReleaseHelper")
@patch("os.path.exists")
def test_main_unexpected_error(
    mock_exists, mock_release_helper, mock_git_helper
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    
    # Make os.path.exists raise an unexpected error
    mock_exists.side_effect = Exception("Unexpected test error")

    # Run with required arguments
    with patch("sys.argv", ["rollback_release.py", "-f", "foundation1", "-r", "v1.0.0"]):
        with pytest.raises(Exception) as excinfo:
            main_test_function()
        
        # Verify it's our test error that was raised
        assert "Unexpected test error" in str(excinfo.value)


@patch("src.rollback_release.GitHelper")
@patch("src.rollback_release.ReleaseHelper")
@patch("os.path.exists")
@patch("os.path.expanduser")
@patch("os.chdir")
def test_main_with_custom_owner(
    mock_chdir, mock_expanduser, mock_exists, mock_release_helper, mock_git_helper
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_exists.return_value = True
    
    # Mock expanduser to avoid file system errors
    mock_ci_dir = "/home/user/git/ns-mgmt-custom-owner/ci"
    mock_expanduser.return_value = mock_ci_dir
    
    # Make methods return appropriate values
    mock_release_helper.return_value.validate_params_release_tag.return_value = True
    mock_release_helper.return_value.run_set_pipeline.return_value = True

    # Set args.owner to a custom value
    with patch("sys.argv", ["rollback_release.py", "-f", "foundation1", "-r", "v1.0.0", "-o", "custom-owner"]):
        # Mock user input to decline running pipeline
        with patch("builtins.input", return_value="no"):
            main_test_function()

    # Verify GitHelper was initialized with the correct repo
    mock_git_helper.assert_called_once_with(repo="ns-mgmt-custom-owner")
    # Verify ReleaseHelper was initialized with the correct parameters
    mock_release_helper.assert_called_once_with(
        repo="ns-mgmt-custom-owner", owner="custom-owner", params_repo="params-custom-owner"
    )