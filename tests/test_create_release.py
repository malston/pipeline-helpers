import os
import sys
from unittest.mock import patch

import pytest

# Add src to the path to ensure imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import the function from the module
from src.create_release import CustomHelpFormatter, parse_args


# Create an undecorated version of the main function for testing
def main_test_function():
    """
    This is a copy of the main function without the wrapper for testing purposes.
    Must be kept in sync with the original in src/create_release.py
    """
    import os
    import subprocess

    from src.create_release import (
        ConcourseClient,
        GitHelper,
        ReleaseHelper,
        logger,
    )

    args = parse_args()

    # Setup error logging is now handled by the wrap_main decorator

    # Process the repo and params values
    repo = args.repo
    params_repo = args.params_repo
    release_pipeline = f"tkgi-{repo}-release"

    logger.info(f"Creating release for repo: {repo}")
    logger.info(f"Foundation: {args.foundation}")

    if args.owner != "Utilities-tkgieng":
        repo = f"{repo}-{args.owner}"
        params_repo = f"{params_repo}-{args.owner}"
        release_pipeline = f"tkgi-{repo}-release"

    # Initialize helpers
    git_helper = GitHelper(repo=repo)
    if not git_helper.check_git_repo():
        raise ValueError("Git is not installed or not in PATH")

    git_dir = os.path.expanduser("~/git")
    release_helper = ReleaseHelper(
        repo=repo, owner=args.owner, params_repo=params_repo, git_dir=git_dir
    )
    concourse_client = ConcourseClient()

    # Change to the repo's ci directory
    ci_dir = os.path.expanduser(f"~/git/{repo}/ci")
    if not os.path.exists(ci_dir):
        raise ValueError(f"CI directory not found at {ci_dir}")

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        logger.info(f"Would change to directory: {ci_dir}")
        logger.info(f"Would run release pipeline: {release_pipeline}")
        logger.info("Would update git release tag")
        return
    else:
        os.chdir(ci_dir)
        logger.info(f"Changed to directory: {ci_dir}")

    # Run release pipeline
    if not release_helper.run_release_pipeline(args.foundation, args.message):
        raise ValueError("Failed to run release pipeline")

    # Update git release tag
    if not release_helper.update_params_git_release_tag():
        raise ValueError("Failed to update git release tag")

    # Run set pipeline
    if not release_helper.run_set_pipeline(args.foundation):
        raise ValueError("Failed to run set pipeline")

    # Ask user if they want to trigger a job
    trigger_response = input("Do you want to trigger a prepare-kustomizations job? [y/N] ")
    if trigger_response.lower().startswith("y"):
        concourse_client.trigger_job(
            args.foundation, f"tkgi-{repo}-{args.foundation}/prepare-kustomizations", watch=True
        )

    # Ask user if they want to run fly.sh script
    fly_script_response = input("Do you want to run the fly.sh script? [y/N] ")
    if fly_script_response.lower().startswith("y"):
        # Get current branch
        current_branch = git_helper.get_current_branch()
        # Build the path to fly.sh
        fly_script_path = f"{ci_dir}/fly.sh"
        # Run fly.sh script
        subprocess.run(
            [
                fly_script_path,
                "-f",
                args.foundation,
                "-b",
                current_branch,
            ],
            check=True,
        )

    logger.info("Release process completed successfully")


def test_parse_args():
    # Test with required arguments missing
    with patch("sys.argv", ["create_release.py"]):
        with pytest.raises(SystemExit):
            parse_args()

    # Test with valid arguments
    with patch("sys.argv", ["create_release.py", "-f", "foundation1", "-r", "repo1"]):
        args = parse_args()
        assert args.foundation == "foundation1"
        assert args.repo == "repo1"
        assert args.owner == "Utilities-tkgieng"
        assert args.params_repo == "params"
        assert not args.dry_run
        assert args.message is None

    # Test with all optional arguments
    with patch(
        "sys.argv",
        [
            "create_release.py",
            "-f",
            "foundation2",
            "-r",
            "repo2",
            "-m",
            "Release message",
            "-o",
            "custom-owner",
            "-p",
            "custom-params",
            "--dry-run",
        ],
    ):
        args = parse_args()
        assert args.foundation == "foundation2"
        assert args.repo == "repo2"
        assert args.message == "Release message"
        assert args.owner == "custom-owner"
        assert args.params_repo == "custom-params"
        assert args.dry_run


def test_custom_help_formatter():
    # Create a formatter with a mocked parser
    formatter = CustomHelpFormatter("prog")

    # For a simple test, we can just verify it can be called
    formatter.format_help()

    # Just test that our class exists and is properly initialized
    assert isinstance(formatter, CustomHelpFormatter)
    assert hasattr(formatter, "format_help")


@patch("src.create_release.logger")  # Mock the logger
@patch("src.helpers.error_handler.setup_error_logging")  # Mock setup_error_logging
@patch("src.create_release.GitHelper")
@patch("src.create_release.ReleaseHelper")
@patch("src.create_release.ConcourseClient")
@patch("os.path.exists")
def test_main_with_dry_run(
    mock_exists,
    mock_concourse,
    mock_release_helper,
    mock_git_helper,
    mock_setup_logging,
    mock_logger,
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_git_helper.return_value.get_current_branch.return_value = "develop"
    mock_exists.return_value = True

    # Mock args
    with patch("sys.argv", ["create_release.py", "-f", "foundation", "-r", "repo", "--dry-run"]):
        # Run the test version of the function
        main_test_function()

        # Verify logger calls to confirm dry run behavior
        assert mock_logger.info.call_count >= 3
        mock_logger.info.assert_any_call("DRY RUN MODE - No changes will be made")

        # Verify no actual operations were performed
        mock_release_helper.return_value.run_release_pipeline.assert_not_called()
        mock_release_helper.return_value.update_params_git_release_tag.assert_not_called()
        mock_release_helper.return_value.run_set_pipeline.assert_not_called()


@patch("src.create_release.logger")  # Mock the logger
@patch("src.helpers.error_handler.setup_error_logging")  # Mock setup_error_logging
@patch("src.create_release.GitHelper")
@patch("src.create_release.ReleaseHelper")
@patch("src.create_release.ConcourseClient")
@patch("os.path.exists")
@patch("os.chdir")
def test_main_success_flow(
    mock_chdir,
    mock_exists,
    mock_concourse,
    mock_release_helper,
    mock_git_helper,
    mock_setup_logging,
    mock_logger,
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_git_helper.return_value.get_current_branch.return_value = "develop"
    mock_exists.return_value = True
    mock_release_helper.return_value.run_release_pipeline.return_value = True
    mock_release_helper.return_value.update_params_git_release_tag.return_value = True
    mock_release_helper.return_value.run_set_pipeline.return_value = True

    # Mock user input
    with patch("builtins.input", side_effect=["n", "n"]):
        with patch(
            "sys.argv",
            ["create_release.py", "-f", "foundation", "-r", "repo", "-m", "Test release"],
        ):
            # Run the test version of the function
            main_test_function()

            # Verify the workflow
            mock_chdir.assert_called_once()
            mock_release_helper.return_value.run_release_pipeline.assert_called_once_with(
                "foundation", "Test release"
            )
            mock_release_helper.return_value.update_params_git_release_tag.assert_called_once()
            mock_release_helper.return_value.run_set_pipeline.assert_called_once_with("foundation")

            # Check concourse client not used (since we mock user input to 'n')
            mock_concourse.return_value.trigger_job.assert_not_called()


@patch("src.create_release.logger")  # Mock the logger
@patch("src.helpers.error_handler.setup_error_logging")  # Mock setup_error_logging
@patch("src.create_release.GitHelper")
@patch("src.create_release.ReleaseHelper")
@patch("src.create_release.ConcourseClient")
@patch("os.path.exists")
def test_main_ci_dir_not_found(
    mock_exists,
    mock_concourse,
    mock_release_helper,
    mock_git_helper,
    mock_setup_logging,
    mock_logger,
):
    # Setup mocks - CI directory doesn't exist
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_exists.return_value = False

    with patch("sys.argv", ["create_release.py", "-f", "foundation", "-r", "repo"]):
        # We expect a ValueError to be raised
        with pytest.raises(ValueError) as excinfo:
            main_test_function()

        # Verify error message
        assert "CI directory not found" in str(excinfo.value)

        # Verify no operations were performed
        mock_release_helper.return_value.run_release_pipeline.assert_not_called()


@patch("src.create_release.logger")  # Mock the logger
@patch("src.helpers.error_handler.setup_error_logging")  # Mock setup_error_logging
@patch("src.create_release.GitHelper")
@patch("src.create_release.ReleaseHelper")
@patch("src.create_release.ConcourseClient")
@patch("os.path.exists")
@patch("os.chdir")
def test_main_pipeline_failure(
    mock_chdir,
    mock_exists,
    mock_concourse,
    mock_release_helper,
    mock_git_helper,
    mock_setup_logging,
    mock_logger,
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_exists.return_value = True
    # Make run_release_pipeline fail
    mock_release_helper.return_value.run_release_pipeline.return_value = False

    with patch("sys.argv", ["create_release.py", "-f", "foundation", "-r", "repo"]):
        with pytest.raises(ValueError) as excinfo:
            main_test_function()

        # Verify error message
        assert "Failed to run release pipeline" in str(excinfo.value)

        # Verify no further operations were performed
        mock_release_helper.return_value.update_params_git_release_tag.assert_not_called()
        mock_release_helper.return_value.run_set_pipeline.assert_not_called()


@patch("src.create_release.logger")  # Mock the logger
@patch("src.helpers.error_handler.setup_error_logging")  # Mock setup_error_logging
@patch("src.create_release.GitHelper")
@patch("src.create_release.ReleaseHelper")
@patch("src.create_release.ConcourseClient")
@patch("os.path.exists")
@patch("os.chdir")
@patch("subprocess.run")
def test_main_with_fly_script(
    mock_subprocess,
    mock_chdir,
    mock_exists,
    mock_concourse,
    mock_release_helper,
    mock_git_helper,
    mock_setup_logging,
    mock_logger,
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_git_helper.return_value.get_current_branch.return_value = "develop"
    mock_exists.return_value = True
    mock_release_helper.return_value.run_release_pipeline.return_value = True
    mock_release_helper.return_value.update_params_git_release_tag.return_value = True
    mock_release_helper.return_value.run_set_pipeline.return_value = True

    # Mock the CI directory path
    mock_ci_dir = "/tmp/repo/ci"

    # Patch expanduser to return our mock path
    with patch("os.path.expanduser", return_value=mock_ci_dir):
        # Mock user input to say 'yes' to running fly script
        with patch("builtins.input", side_effect=["n", "y"]):
            with patch("sys.argv", ["create_release.py", "-f", "foundation", "-r", "repo"]):
                # Run the test version of the function
                main_test_function()

                # Verify subprocess was called with the right params
                mock_subprocess.assert_called_once()
                call_args = mock_subprocess.call_args[0][0]
                assert call_args[0] == f"{mock_ci_dir}/fly.sh"
                assert "-f" in call_args
                assert "foundation" in call_args
                assert "-b" in call_args
                assert "develop" in call_args


@patch("src.create_release.logger")  # Mock the logger
@patch("src.helpers.error_handler.setup_error_logging")  # Mock setup_error_logging
@patch("src.create_release.GitHelper")
@patch("src.create_release.ReleaseHelper")
@patch("src.create_release.ConcourseClient")
@patch("os.path.exists")
@patch("os.chdir")
def test_main_with_concourse_trigger(
    mock_chdir,
    mock_exists,
    mock_concourse,
    mock_release_helper,
    mock_git_helper,
    mock_setup_logging,
    mock_logger,
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_git_helper.return_value.get_current_branch.return_value = "develop"
    mock_exists.return_value = True
    mock_release_helper.return_value.run_release_pipeline.return_value = True
    mock_release_helper.return_value.update_params_git_release_tag.return_value = True
    mock_release_helper.return_value.run_set_pipeline.return_value = True

    # Mock user input to say 'yes' to triggering Concourse job
    with patch("builtins.input", side_effect=["y", "n"]):
        with patch("sys.argv", ["create_release.py", "-f", "foundation", "-r", "repo"]):
            # Run the test version of the function
            main_test_function()

            # Verify Concourse client was called to trigger the job
            mock_concourse.return_value.trigger_job.assert_called_once_with(
                "foundation", "tkgi-repo-foundation/prepare-kustomizations", watch=True
            )


@patch("src.create_release.logger")  # Mock the logger
@patch("src.helpers.error_handler.setup_error_logging")  # Mock setup_error_logging
@patch("src.create_release.GitHelper")
def test_main_git_error(mock_git_helper, mock_setup_logging, mock_logger):
    # Setup mock to simulate git not available
    mock_git_helper.return_value.check_git_repo.return_value = False

    with patch("sys.argv", ["create_release.py", "-f", "foundation", "-r", "repo"]):
        with pytest.raises(ValueError) as excinfo:
            main_test_function()

        # Verify error message
        assert "Git is not installed or not in PATH" in str(excinfo.value)


@patch("src.create_release.logger")  # Mock the logger
@patch("src.helpers.error_handler.setup_error_logging")  # Mock setup_error_logging
@patch("src.create_release.GitHelper")
@patch("src.create_release.ReleaseHelper")
@patch("src.create_release.ConcourseClient")
@patch("os.path.exists")
@patch("os.chdir")
def test_main_with_custom_owner(
    mock_chdir,
    mock_exists,
    mock_concourse,
    mock_release_helper,
    mock_git_helper,
    mock_setup_logging,
    mock_logger,
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_exists.return_value = True
    mock_release_helper.return_value.run_release_pipeline.return_value = True
    mock_release_helper.return_value.update_params_git_release_tag.return_value = True
    mock_release_helper.return_value.run_set_pipeline.return_value = True

    # Need to mock input to avoid the stdin read error
    with patch("builtins.input", side_effect=["n", "n"]):
        with patch(
            "sys.argv",
            ["create_release.py", "-f", "foundation", "-r", "repo", "-o", "custom-owner"],
        ):
            # Run the test version of the function
            main_test_function()

            # Verify GitHelper was called with the correct repo name
            mock_git_helper.assert_called_with(repo="repo-custom-owner")

            # Verify ReleaseHelper was called with the correct parameters
            mock_release_helper.assert_called_with(
                repo="repo-custom-owner",
                owner="custom-owner",
                params_repo="params-custom-owner",
                git_dir=os.path.expanduser("~/git"),
            )


# Note: Environment variable based logging is now tested elsewhere
