import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, "../src")  # This ensures src directory is in path

from src.delete_release import delete_git_tag, main, parse_args, print_available_releases
from src.helpers.release_helper import ReleaseHelper


def test_parse_args():
    # Test required arguments
    with patch("sys.argv", ["delete_release.py"]):
        with pytest.raises(SystemExit):
            parse_args()

    # Test with required -t tag argument missing
    with patch("sys.argv", ["delete_release.py", "-r", "repo"]):
        with pytest.raises(SystemExit):
            parse_args()

    # Test with valid arguments
    with patch("sys.argv", ["delete_release.py", "-r", "repo", "-t", "v1.0.0"]):
        args = parse_args()
        assert args.repo == "repo"
        assert args.tag == "v1.0.0"
        assert args.owner == "Utilities-tkgieng"
        assert not args.no_tag_deletion
        assert not args.non_interactive

    # Test with custom owner
    test_args = ["delete_release.py", "-r", "repo", "-t", "v1.0.0", "-o", "custom-owner"]
    with patch("sys.argv", test_args):
        args = parse_args()
        assert args.owner == "custom-owner"

    # Test with no tag deletion
    with patch("sys.argv", ["delete_release.py", "-r", "repo", "-t", "v1.0.0", "-x"]):
        args = parse_args()
        assert args.no_tag_deletion

    # Test non-interactive mode
    with patch("sys.argv", ["delete_release.py", "-r", "repo", "-t", "v1.0.0", "-n"]):
        args = parse_args()
        assert args.non_interactive


def test_print_available_releases(capsys):
    releases = [
        {"tag_name": "v1.0.0", "name": "Release 1.0.0"},
        {"tag_name": "v2.0.0", "name": "Release 2.0.0"},
    ]
    print_available_releases(releases)
    captured = capsys.readouterr()
    assert (
        captured.out
        == "Available Github Releases:\nv1.0.0 - Release 1.0.0\nv2.0.0 - Release 2.0.0\n"
    )


def test_delete_git_tag():
    mock_git_helper = MagicMock()
    mock_git_helper.tag_exists = MagicMock()
    mock_release_helper = MagicMock(spec=ReleaseHelper)

    non_interactive = False
    tag = "v1.0.0"

    # Test when tag exists and user confirms
    mock_git_helper.tag_exists.return_value = True
    with patch("builtins.input", return_value="y"):
        delete_git_tag(mock_git_helper, mock_release_helper, tag, non_interactive)
        mock_release_helper.delete_release_tag.assert_called_once_with(tag)

    # Test when tag exists but user cancels
    mock_release_helper.reset_mock()
    with patch("builtins.input", return_value="n"):
        delete_git_tag(mock_git_helper, mock_release_helper, tag, non_interactive)
        mock_release_helper.delete_release_tag.assert_not_called()

    # Test when tag doesn't exist
    mock_git_helper.tag_exists.return_value = False
    with patch("src.helpers.logger.default_logger.error") as mock_logger_error:
        delete_git_tag(mock_git_helper, mock_release_helper, tag, non_interactive)
        mock_release_helper.delete_release_tag.assert_not_called()
        mock_logger_error.assert_called_once_with(f"Git tag {tag} not found in repository")

    # Test in non-interactive mode
    non_interactive = True
    mock_git_helper.tag_exists.return_value = True
    mock_git_helper.reset_mock()
    mock_release_helper.reset_mock()
    delete_git_tag(mock_git_helper, mock_release_helper, tag, non_interactive)
    mock_release_helper.delete_release_tag.assert_called_once_with(tag)


@pytest.mark.parametrize(
    "input_args,expected_repo",
    [
        (["-r", "ns-mgmt", "-t", "v1.0.0"], "ns-mgmt"),
        (["-r", "ns-mgmt", "-t", "v1.0.0", "-o", "custom-owner"], "ns-mgmt-custom-owner"),
    ],
)
def test_repo_name_construction(input_args, expected_repo):
    git_dir = os.path.expanduser("~/git")

    with patch("src.helpers.git_helper.GitHelper") as mock_git_helper, patch(
        "src.helpers.release_helper.ReleaseHelper"
    ) as mock_release_helper, patch("os.path.isdir", return_value=True), patch(
        "src.delete_release.GitHelper", mock_git_helper
    ), patch(
        "src.delete_release.ReleaseHelper", mock_release_helper
    ):

        mock_git_helper.return_value.check_git_repo.return_value = True
        mock_release_helper.return_value.get_github_release_by_tag.return_value = {
            "tag_name": "v1.0.0"
        }
        mock_release_helper.return_value.delete_github_release.return_value = True
        mock_git_helper.return_value.tag_exists.return_value = True

        with patch("sys.argv", ["delete_release.py"] + input_args), patch(
            "builtins.input", return_value="y"
        ):
            # Run main without storing args
            main()

            mock_git_helper.assert_called_once_with(
                git_dir=git_dir, repo="ns-mgmt", repo_dir=os.path.join(git_dir, expected_repo)
            )


def test_release_not_found():
    repo = "ns-mgmt"

    with patch("src.helpers.git_helper.GitHelper") as mock_git_helper, patch(
        "src.helpers.release_helper.ReleaseHelper"
    ) as mock_release_helper, patch("os.path.isdir", return_value=True), patch(
        "src.delete_release.GitHelper", mock_git_helper
    ), patch(
        "src.delete_release.ReleaseHelper", mock_release_helper
    ), patch(
        "src.helpers.logger.default_logger.error"
    ) as mock_logger_error:

        mock_git_helper.return_value.check_git_repo.return_value = True
        mock_release_helper.return_value.get_github_release_by_tag.return_value = None
        mock_release_helper.return_value.get_releases.return_value = [
            {"tag_name": "v1.0.0", "name": "Release 1.0.0"},
            {"tag_name": "v2.0.0", "name": "Release 2.0.0"},
        ]
        mock_git_helper.return_value.tag_exists.return_value = True

        with patch("sys.argv", ["delete_release.py", "-r", repo, "-t", "v3.0.0"]), patch(
            "builtins.input", return_value="y"
        ):
            # Run main without storing args
            main()

            mock_logger_error.assert_any_call("Release v3.0.0 not found")


def test_no_releases_found():
    repo = "ns-mgmt"
    tag = "v1.0.0"

    with patch("src.helpers.git_helper.GitHelper") as mock_git_helper, patch(
        "src.helpers.release_helper.ReleaseHelper"
    ) as mock_release_helper, patch("os.path.isdir", return_value=True), patch(
        "src.delete_release.GitHelper", mock_git_helper
    ), patch(
        "src.delete_release.ReleaseHelper", mock_release_helper
    ), patch(
        "src.helpers.logger.default_logger.info"
    ) as mock_logger_info:

        mock_git_helper.return_value.check_git_repo.return_value = True
        mock_release_helper.return_value.get_github_release_by_tag.return_value = None
        mock_release_helper.return_value.get_releases.return_value = []
        mock_git_helper.return_value.tag_exists.return_value = True

        with patch("sys.argv", ["delete_release.py", "-r", repo, "-t", tag]), patch(
            "builtins.input", return_value="y"
        ):
            # Run main without storing args
            main()

            # Check that info was called with "No releases found"
            mock_logger_info.assert_any_call("No releases found")
            mock_release_helper.return_value.delete_release_tag.assert_called_once_with(tag)


def test_successful_deletion():
    repo = "ns-mgmt"
    tag = "v1.0.0"

    with patch("src.helpers.git_helper.GitHelper") as mock_git_helper, patch(
        "src.helpers.release_helper.ReleaseHelper"
    ) as mock_release_helper, patch("os.path.isdir", return_value=True), patch(
        "src.delete_release.GitHelper", mock_git_helper
    ), patch(
        "src.delete_release.ReleaseHelper", mock_release_helper
    ):
        mock_release = {
            "tag_name": tag,
            "name": "Release 1.0.0",
            "id": 12345,
        }
        mock_git_helper.return_value.check_git_repo.return_value = True
        mock_release_helper.return_value.get_github_release_by_tag.return_value = mock_release
        mock_release_helper.return_value.delete_github_release.return_value = True
        mock_git_helper.return_value.tag_exists.return_value = True

        with patch("sys.argv", ["delete_release.py", "-r", repo, "-t", tag]), patch(
            "builtins.input", return_value="y"
        ):
            # Run main without storing args
            main()

            mock_release_helper.return_value.delete_github_release.assert_called_once_with(
                mock_release.get("id")
            )
            mock_release_helper.return_value.delete_release_tag.assert_called_once_with(tag)


def test_deletion_cancelled():
    repo = "ns-mgmt"
    tag = "v1.0.0"

    with patch("src.helpers.git_helper.GitHelper") as mock_git_helper, patch(
        "src.helpers.release_helper.ReleaseHelper"
    ) as mock_release_helper, patch("os.path.isdir", return_value=True), patch(
        "src.delete_release.GitHelper", mock_git_helper
    ), patch(
        "src.delete_release.ReleaseHelper", mock_release_helper
    ):

        mock_git_helper.return_value.check_git_repo.return_value = True
        mock_release_helper.return_value.get_github_release_by_tag.return_value = {"tag_name": tag}
        mock_git_helper.return_value.tag_exists.return_value = True

        with patch("sys.argv", ["delete_release.py", "-r", repo, "-t", tag]), patch(
            "builtins.input", return_value="n"
        ):
            # Run main without storing args
            main()

            mock_release_helper.return_value.delete_github_release.assert_not_called()
            mock_release_helper.return_value.delete_release_tag.assert_not_called()
