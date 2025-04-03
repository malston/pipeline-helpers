import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, "../src")  # This ensures src directory is in path

from src.create_release import CustomHelpFormatter, main, parse_args


def test_parse_args():
    # Test required arguments
    with patch("sys.argv", ["create_release.py"]):
        with pytest.raises(SystemExit):
            parse_args()

    with patch("sys.argv", ["create_release.py", "-f", "foundation"]):
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


@patch("src.create_release.GitHelper")
@patch("src.create_release.ReleaseHelper")
@patch("src.create_release.ConcourseClient")
@patch("os.path.exists")
def test_main_with_dry_run(mock_exists, mock_concourse, mock_release_helper, mock_git_helper):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_git_helper.return_value.get_current_branch.return_value = "develop"
    mock_exists.return_value = True

    # Mock args
    with patch(
        "sys.argv", ["create_release.py", "-f", "foundation", "-r", "repo", "--dry-run"]
    ), patch("src.create_release.logger") as mock_logger:
        # Run the function
        main()

        # Verify logger calls to confirm dry run behavior
        assert mock_logger.info.call_count >= 5
        mock_logger.info.assert_any_call("DRY RUN MODE - No changes will be made")
        mock_logger.info.assert_any_call("Would run release pipeline: tkgi-repo-release")
        mock_logger.info.assert_any_call("Would update git release tag")

        # Verify no actual operations were performed
        mock_release_helper.return_value.run_release_pipeline.assert_not_called()
        mock_release_helper.return_value.update_params_git_release_tag.assert_not_called()
        mock_release_helper.return_value.run_set_pipeline.assert_not_called()


@patch("src.create_release.GitHelper")
@patch("src.create_release.ReleaseHelper")
@patch("src.create_release.ConcourseClient")
@patch("os.path.exists")
@patch("os.chdir")
def test_main_success_flow(
    mock_chdir, mock_exists, mock_concourse, mock_release_helper, mock_git_helper
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
            # Run the function
            main()

            # Verify the workflow
            mock_chdir.assert_called_once()
            mock_release_helper.return_value.run_release_pipeline.assert_called_once_with(
                "foundation", "Test release"
            )
            mock_release_helper.return_value.update_params_git_release_tag.assert_called_once()
            mock_release_helper.return_value.run_set_pipeline.assert_called_once_with("foundation")

            # Check concourse client not used (since we mock user input to 'n')
            mock_concourse.return_value.trigger_job.assert_not_called()


@patch("src.create_release.GitHelper")
@patch("src.create_release.ReleaseHelper")
@patch("src.create_release.ConcourseClient")
@patch("os.path.exists")
def test_main_ci_dir_not_found(mock_exists, mock_concourse, mock_release_helper, mock_git_helper):
    # Setup mocks - CI directory doesn't exist
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_exists.return_value = False

    with patch("sys.argv", ["create_release.py", "-f", "foundation", "-r", "repo"]), patch(
        "src.create_release.logger"
    ) as mock_logger:
        # Run the function
        main()

        # Verify error was logged
        mock_logger.error.assert_called_once()
        assert "CI directory not found" in mock_logger.error.call_args[0][0]

        # Verify no operations were performed
        mock_release_helper.return_value.run_release_pipeline.assert_not_called()


@patch("src.create_release.GitHelper")
@patch("src.create_release.ReleaseHelper")
@patch("src.create_release.ConcourseClient")
@patch("os.path.exists")
@patch("os.chdir")
def test_main_pipeline_failure(
    mock_chdir, mock_exists, mock_concourse, mock_release_helper, mock_git_helper
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_exists.return_value = True
    # Make run_release_pipeline fail
    mock_release_helper.return_value.run_release_pipeline.return_value = False

    with patch("sys.argv", ["create_release.py", "-f", "foundation", "-r", "repo"]), patch(
        "src.create_release.logger"
    ) as mock_logger:
        # Run the function
        main()

        # Verify error was logged
        mock_logger.error.assert_called_once_with("Failed to run release pipeline")

        # Verify no further operations were performed
        mock_release_helper.return_value.update_params_git_release_tag.assert_not_called()
        mock_release_helper.return_value.run_set_pipeline.assert_not_called()


@patch("src.create_release.GitHelper")
@patch("src.create_release.ReleaseHelper")
@patch("src.create_release.ConcourseClient")
@patch("os.path.exists")
@patch("os.chdir")
@patch("subprocess.run")
def test_main_with_fly_script(
    mock_subprocess, mock_chdir, mock_exists, mock_concourse, mock_release_helper, mock_git_helper
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_git_helper.return_value.get_current_branch.return_value = "develop"
    mock_exists.return_value = True
    mock_release_helper.return_value.run_release_pipeline.return_value = True
    mock_release_helper.return_value.update_params_git_release_tag.return_value = True
    mock_release_helper.return_value.run_set_pipeline.return_value = True

    # Mock path operations for fly.sh script
    with patch("os.path.isfile", return_value=True), patch("os.access", return_value=True), patch(
        "os.getcwd", return_value="/tmp/repo/ci"
    ):

        # Mock user input to say 'yes' to running fly script
        with patch("builtins.input", side_effect=["n", "y"]):
            with patch("sys.argv", ["create_release.py", "-f", "foundation", "-r", "repo"]):
                # Run the function
                main()

                # Verify subprocess was called with right params
                mock_subprocess.assert_called_once()
                call_args = mock_subprocess.call_args[0][0]
                assert call_args[0] == "/tmp/repo/ci/fly.sh"
                assert "-f" in call_args
                assert "foundation" in call_args
                assert "-b" in call_args
                assert "develop" in call_args


@patch("src.create_release.GitHelper")
@patch("src.create_release.ReleaseHelper")
@patch("src.create_release.ConcourseClient")
@patch("os.path.exists")
@patch("os.chdir")
def test_main_with_concourse_trigger(
    mock_chdir, mock_exists, mock_concourse, mock_release_helper, mock_git_helper
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
            # Run the function
            main()

            # Verify Concourse client was called to trigger the job
            mock_concourse.return_value.trigger_job.assert_called_once_with(
                "foundation", "tkgi-repo-foundation/prepare-kustomizations", watch=True
            )


@patch("helpers.git_helper.GitHelper")
def test_main_git_error(mock_git_helper):
    # Setup mock to simulate git not available
    mock_git_helper.return_value.check_git_repo.return_value = False

    with patch("sys.argv", ["create_release.py", "-f", "foundation", "-r", "repo"]), patch(
        "src.create_release.logger"
    ) as mock_logger:
        # Run the function
        main()

        # Verify error was logged and execution stopped
        mock_logger.error.assert_called_once_with("Git is not installed or not in PATH")


@patch("src.create_release.GitHelper")
@patch("src.create_release.ReleaseHelper")
@patch("src.create_release.ConcourseClient")
@patch("os.path.exists")
@patch("os.chdir")
def test_main_with_custom_owner(
    mock_chdir, mock_exists, mock_concourse, mock_release_helper, mock_git_helper
):
    # Setup mocks
    mock_git_helper.return_value.check_git_repo.return_value = True
    mock_exists.return_value = True

    with patch(
        "sys.argv", ["create_release.py", "-f", "foundation", "-r", "repo", "-o", "custom-owner"]
    ):
        # Run the function
        main()

        # Verify GitHelper was called with the correct repo name
        mock_git_helper.assert_called_with(repo="repo-custom-owner")

        # Verify ReleaseHelper was called with the correct parameters
        # The actual repo parameter follows the logic in the main function
        mock_release_helper.assert_called_with(
            repo="repo-custom-owner", owner="custom-owner", params_repo="params-custom-owner"
        )
