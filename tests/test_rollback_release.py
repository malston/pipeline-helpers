import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, "../src")  # This ensures src directory is in path

from src.rollback_release import main, parse_args


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
    from helpers.argparse_helper import CustomHelpFormatter

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
@patch("helpers.logger.default_logger.error")
def test_main_ci_dir_not_found(
    mock_logger_error,
    mock_chdir,
    mock_expanduser,
    mock_exists,
    mock_release_helper,
    mock_git_helper,
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_exists.return_value = False
    mock_expanduser.return_value = "/home/user/git/ns-mgmt/ci"

    # Run with required arguments
    with patch("sys.argv", ["rollback_release.py", "-f", "foundation1", "-r", "v1.0.0"]):
        # Mock the parse_args function to include the owner attribute
        with patch("src.rollback_release.parse_args") as mock_parse_args:
            mock_args = MagicMock()
            mock_args.foundation = "foundation1"
            mock_args.release = "v1.0.0"
            mock_args.params_repo = "params"
            mock_args.owner = "Utilities-tkgieng"  # Add owner attribute
            mock_parse_args.return_value = mock_args

            main()

    # Verify error was logged for missing CI directory
    mock_logger_error.assert_called_once_with("CI directory not found at /home/user/git/ns-mgmt/ci")
    # Verify chdir was not called
    mock_chdir.assert_not_called()


@patch("src.rollback_release.GitHelper")
@patch("src.rollback_release.ReleaseHelper")
@patch("os.path.exists")
@patch("os.path.expanduser")
@patch("os.chdir")
@patch("helpers.logger.default_logger.error")
@patch("helpers.logger.default_logger.info")
def test_main_invalid_release_tag(
    mock_logger_info,
    mock_logger_error,
    mock_chdir,
    mock_expanduser,
    mock_exists,
    mock_release_helper,
    mock_git_helper,
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_exists.return_value = True
    mock_expanduser.return_value = "/home/user/git/ns-mgmt/ci"
    mock_release_helper.return_value.validate_params_release_tag.return_value = False

    # Run with required arguments
    with patch("sys.argv", ["rollback_release.py", "-f", "foundation1", "-r", "v1.0.0"]):
        # Mock the parse_args function to include the owner attribute
        with patch("src.rollback_release.parse_args") as mock_parse_args:
            mock_args = MagicMock()
            mock_args.foundation = "foundation1"
            mock_args.release = "v1.0.0"
            mock_args.params_repo = "params"
            mock_args.owner = "Utilities-tkgieng"  # Add owner attribute
            mock_parse_args.return_value = mock_args

            main()

    # Verify validation was called
    mock_release_helper.return_value.validate_params_release_tag.assert_called_once_with(
        "ns-mgmt-v1.0.0"
    )
    # Verify error was logged
    mock_logger_error.assert_called_once_with(
        "Release [-r v1.0.0] must be a valid release tagged on the params repo"
    )
    # Verify info was logged
    mock_logger_info.assert_called_once_with("Valid tags are:")
    # Verify print valid tags was called
    mock_release_helper.return_value.print_valid_params_release_tags.assert_called_once()


@patch("src.rollback_release.GitHelper")
@patch("src.rollback_release.ReleaseHelper")
@patch("os.path.exists")
@patch("os.path.expanduser")
@patch("os.chdir")
@patch("helpers.logger.default_logger.error")
def test_main_set_pipeline_fails(
    mock_logger_error,
    mock_chdir,
    mock_expanduser,
    mock_exists,
    mock_release_helper,
    mock_git_helper,
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_exists.return_value = True
    mock_expanduser.return_value = "/home/user/git/ns-mgmt/ci"
    mock_release_helper.return_value.validate_params_release_tag.return_value = True
    mock_release_helper.return_value.run_set_pipeline.return_value = False

    # Run with required arguments
    with patch("sys.argv", ["rollback_release.py", "-f", "foundation1", "-r", "v1.0.0"]):
        # Mock the parse_args function to include the owner attribute
        with patch("src.rollback_release.parse_args") as mock_parse_args:
            mock_args = MagicMock()
            mock_args.foundation = "foundation1"
            mock_args.release = "v1.0.0"
            mock_args.params_repo = "params"
            mock_args.owner = "Utilities-tkgieng"  # Add owner attribute
            mock_parse_args.return_value = mock_args

            main()

    # Verify set pipeline was called
    mock_release_helper.return_value.run_set_pipeline.assert_called_once_with("foundation1")
    # Verify error was logged
    mock_logger_error.assert_called_once_with("Failed to run set pipeline")


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
    mock_expanduser.return_value = "/home/user/git/ns-mgmt/ci"
    mock_release_helper.return_value.validate_params_release_tag.return_value = True
    mock_release_helper.return_value.run_set_pipeline.return_value = True
    mock_input.return_value = "yes"

    # Run with required arguments
    with patch("sys.argv", ["rollback_release.py", "-f", "foundation1", "-r", "v1.0.0"]):
        # Mock the parse_args function to include the owner attribute
        with patch("src.rollback_release.parse_args") as mock_parse_args:
            mock_args = MagicMock()
            mock_args.foundation = "foundation1"
            mock_args.release = "v1.0.0"
            mock_args.params_repo = "params"
            mock_args.owner = "Utilities-tkgieng"  # Add owner attribute
            mock_parse_args.return_value = mock_args

            main()

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
    mock_expanduser.return_value = "/home/user/git/ns-mgmt/ci"
    mock_release_helper.return_value.validate_params_release_tag.return_value = True
    mock_release_helper.return_value.run_set_pipeline.return_value = True
    mock_input.return_value = "no"

    # Run with required arguments
    with patch("sys.argv", ["rollback_release.py", "-f", "foundation1", "-r", "v1.0.0"]):
        # Mock the parse_args function to include the owner attribute
        with patch("src.rollback_release.parse_args") as mock_parse_args:
            mock_args = MagicMock()
            mock_args.foundation = "foundation1"
            mock_args.release = "v1.0.0"
            mock_args.params_repo = "params"
            mock_args.owner = "Utilities-tkgieng"  # Add owner attribute
            mock_parse_args.return_value = mock_args

            main()

    # Verify trigger job was not called
    mock_subprocess_run.assert_not_called()


@patch("src.rollback_release.GitHelper")
@patch("src.rollback_release.ReleaseHelper")
@patch("os.path.exists")
@patch("os.path.expanduser")
@patch("os.chdir")
@patch("builtins.input")
@patch("subprocess.run")
@patch("helpers.logger.default_logger.error")
def test_main_trigger_pipeline_subprocess_error(
    mock_logger_error,
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
    mock_expanduser.return_value = "/home/user/git/ns-mgmt/ci"
    mock_release_helper.return_value.validate_params_release_tag.return_value = True
    mock_release_helper.return_value.run_set_pipeline.return_value = True
    mock_input.return_value = "yes"
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "fly")

    # Run with required arguments
    with patch("sys.argv", ["rollback_release.py", "-f", "foundation1", "-r", "v1.0.0"]):
        # Mock the parse_args function to include the owner attribute
        with patch("src.rollback_release.parse_args") as mock_parse_args:
            mock_args = MagicMock()
            mock_args.foundation = "foundation1"
            mock_args.release = "v1.0.0"
            mock_args.params_repo = "params"
            mock_args.owner = "Utilities-tkgieng"  # Add owner attribute
            mock_parse_args.return_value = mock_args

            main()

    # Verify error was logged
    mock_logger_error.assert_called_once()
    assert "Failed to trigger pipeline job" in mock_logger_error.call_args[0][0]


@patch("src.rollback_release.GitHelper")
@patch("src.rollback_release.ReleaseHelper")
@patch("os.path.exists")
@patch("helpers.logger.default_logger.error")
def test_main_unexpected_error(
    mock_logger_error, mock_exists, mock_release_helper, mock_git_helper
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_exists.side_effect = Exception("Unexpected test error")

    # Run with required arguments
    with patch("sys.argv", ["rollback_release.py", "-f", "foundation1", "-r", "v1.0.0"]):
        # Mock the parse_args function to include the owner attribute
        with patch("src.rollback_release.parse_args") as mock_parse_args:
            mock_args = MagicMock()
            mock_args.foundation = "foundation1"
            mock_args.release = "v1.0.0"
            mock_args.params_repo = "params"
            mock_args.owner = "Utilities-tkgieng"  # Add owner attribute
            mock_parse_args.return_value = mock_args

            main()

    # Verify error was logged
    mock_logger_error.assert_called_once_with("Unexpected error: Unexpected test error")


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
    mock_expanduser.return_value = "/home/user/git/ns-mgmt-custom-owner/ci"
    mock_release_helper.return_value.validate_params_release_tag.return_value = True
    mock_release_helper.return_value.run_set_pipeline.return_value = True

    # Set args.owner to a custom value
    with patch("src.rollback_release.parse_args") as mock_parse_args:
        mock_args = MagicMock()
        mock_args.foundation = "foundation1"
        mock_args.release = "v1.0.0"
        mock_args.params_repo = "params"
        mock_args.owner = "custom-owner"  # Set custom owner
        mock_parse_args.return_value = mock_args

        main()

    # Verify GitHelper was initialized with the correct repo
    mock_git_helper.assert_called_once_with(repo="ns-mgmt-custom-owner")
    # Verify ReleaseHelper was initialized with the correct parameters
    mock_release_helper.assert_called_once_with(
        repo="ns-mgmt-custom-owner", owner="custom-owner", params_repo="params-custom-owner"
    )
