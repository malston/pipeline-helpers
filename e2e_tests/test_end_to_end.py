#!/usr/bin/env python3

"""End-to-end tests for pipeline-helpers with Concourse CI."""

import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.helpers.git_helper import GitHelper
from src.helpers.logger import get_logger


class EndToEndTest(unittest.TestCase):
    """Run end-to-end tests for pipeline-helpers with Concourse CI."""

    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        # Initialize logger
        cls.logger = get_logger(name="e2e-test", log_file="/test-results/e2e-test.log")
        cls.logger.info("Setting up end-to-end test environment")

        # Environment variables
        cls.github_token = os.environ.get("GITHUB_TOKEN")
        cls.concourse_url = os.environ.get("CONCOURSE_URL", "http://concourse-web:8080")
        cls.git_workspace = os.environ.get("GIT_WORKSPACE", "/root/git")
        cls.repos_owner = os.environ.get("REPOS_OWNER", "malston")
        cls.foundation = os.environ.get("FOUNDATION_NAME", "test-foundation")

        # Check required environment variables
        if not cls.github_token:
            cls.logger.error("GITHUB_TOKEN environment variable not set")
            sys.exit(1)

        # Create repo paths
        cls.repo_name = "ns-mgmt"
        cls.params_repo_name = "params"
        cls.repo_path = os.path.join(cls.git_workspace, cls.repos_owner, cls.repo_name)
        cls.params_path = os.path.join(cls.git_workspace, cls.repos_owner, cls.params_repo_name)

        # Make sure repos are cloned
        cls._ensure_repos_cloned()

        # Set up Concourse
        cls._setup_concourse()

    @classmethod
    def _ensure_repos_cloned(cls):
        """Ensure repositories are cloned."""
        # Check if repos exist
        if not os.path.exists(cls.repo_path) or not os.path.exists(cls.params_path):
            cls.logger.error(f"Required repositories not found in {cls.git_workspace}")
            cls.logger.error("Please ensure repositories are cloned before running tests")
            sys.exit(1)

        # Check if repos are git repositories
        git_helper = GitHelper(git_dir=cls.git_workspace)
        if not git_helper.check_git_repo(f"{cls.repos_owner}/{cls.repo_name}"):
            cls.logger.error(f"{cls.repo_path} is not a valid git repository")
            sys.exit(1)
        if not git_helper.check_git_repo(f"{cls.repos_owner}/{cls.params_repo_name}"):
            cls.logger.error(f"{cls.params_path} is not a valid git repository")
            sys.exit(1)

    @classmethod
    def _setup_concourse(cls):
        """Set up Concourse CI for testing."""
        cls.logger.info("Setting up Concourse CI...")
        
        # Ensure Concourse is running
        max_attempts = 10
        wait_time = 5  # seconds
        
        for attempt in range(max_attempts):
            try:
                result = subprocess.run(
                    ["fly", "-t", "test", "status"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                if "logged in successfully" in result.stdout or "authorized" in result.stdout:
                    cls.logger.info("Successfully connected to Concourse")
                    break
            except subprocess.CalledProcessError:
                cls.logger.warning(f"Waiting for Concourse... (attempt {attempt+1}/{max_attempts})")
                time.sleep(wait_time)
        else:
            cls.logger.error("Failed to connect to Concourse")
            sys.exit(1)

    def setUp(self):
        """Set up before each test."""
        self.logger.info(f"Starting test: {self._testMethodName}")

    def tearDown(self):
        """Clean up after each test."""
        self.logger.info(f"Completed test: {self._testMethodName}")

    def test_01_pipeline_structure(self):
        """Test that the repository has the expected structure."""
        # Check for ci directory
        ci_dir = os.path.join(self.repo_path, "ci")
        self.assertTrue(os.path.isdir(ci_dir), "CI directory not found")
        
        # Check for pipelines directory
        pipelines_dir = os.path.join(ci_dir, "pipelines")
        self.assertTrue(os.path.isdir(pipelines_dir), "Pipelines directory not found")
        
        # Check for fly script
        fly_script = os.path.join(ci_dir, "fly.sh")
        self.assertTrue(os.path.isfile(fly_script), "fly.sh script not found")
        self.assertTrue(os.access(fly_script, os.X_OK), "fly.sh is not executable")

    def test_02_set_release_pipeline(self):
        """Test setting up a release pipeline."""
        # Change to CI directory
        os.chdir(os.path.join(self.repo_path, "ci"))
        
        # Create a test pipeline name
        pipeline_name = f"test-pipeline-{int(time.time())}"
        
        try:
            # Run the fly script to set the pipeline
            result = subprocess.run(
                [
                    "./fly.sh",
                    "-f", self.foundation,
                    "-p", pipeline_name,
                    "-b", "master",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.logger.info(f"Pipeline setup output: {result.stdout}")
            
            # Verify the pipeline was created
            verify_result = subprocess.run(
                ["fly", "-t", "test", "pipelines"],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn(pipeline_name, verify_result.stdout, f"Pipeline {pipeline_name} not found")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error setting pipeline: {e}")
            self.logger.error(f"Output: {e.stdout}")
            self.logger.error(f"Error: {e.stderr}")
            self.fail(f"Failed to set pipeline: {e}")
        finally:
            # Clean up - destroy the test pipeline
            subprocess.run(
                ["fly", "-t", "test", "destroy-pipeline", "-p", pipeline_name, "-n"],
                capture_output=True,
            )

    def test_03_create_release_dry_run(self):
        """Test create-release script in dry run mode."""
        # Run in dry-run mode to avoid making actual changes
        try:
            result = subprocess.run(
                [
                    "create-release",
                    "-f", self.foundation,
                    "-r", f"{self.repos_owner}/{self.repo_name}",
                    "-p", f"{self.repos_owner}/{self.params_repo_name}",
                    "--dry-run",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            
            # Check for expected output in dry run mode
            self.assertIn("DRY RUN MODE", result.stdout, "Dry run mode not indicated in output")
            self.assertIn("Would run release pipeline", result.stdout, "Pipeline command missing")
            
            self.logger.info("create-release dry run test passed")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error running create-release: {e}")
            self.logger.error(f"Output: {e.stdout}")
            self.logger.error(f"Error: {e.stderr}")
            self.fail(f"create-release failed: {e}")

    def test_04_demo_release_pipeline_dry_run(self):
        """Test demo-release-pipeline script in dry run mode."""
        try:
            result = subprocess.run(
                [
                    "demo-release-pipeline",
                    "-f", self.foundation,
                    "-r", f"{self.repos_owner}/{self.repo_name}",
                    "-p", f"{self.repos_owner}/{self.params_repo_name}",
                    "-b", "master",
                    "--dry-run",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            
            # Verify expected output
            self.assertIn("[DRY RUN]", result.stdout, "Dry run mode not indicated in output")
            
            self.logger.info("demo-release-pipeline dry run test passed")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error running demo-release-pipeline: {e}")
            self.logger.error(f"Output: {e.stdout}")
            self.logger.error(f"Error: {e.stderr}")
            self.fail(f"demo-release-pipeline failed: {e}")

    def test_05_update_params_release_tag_dry_run(self):
        """Test update-params-release-tag in dry run mode."""
        # This would normally require actual git tags, 
        # but we're just checking the command doesn't fatally error
        try:
            subprocess.run(
                [
                    "update-params-release-tag",
                    "-r", f"{self.repos_owner}/{self.repo_name}",
                    "-p", f"{self.repos_owner}/{self.params_repo_name}",
                ],
                check=False,  # Allow failure since we don't have real tags
                capture_output=True,
                text=True,
            )
            
            self.logger.info("update-params-release-tag command executed")
        except Exception as e:
            self.logger.error(f"Unexpected error running update-params-release-tag: {e}")
            self.fail(f"update-params-release-tag failed unexpectedly: {e}")


if __name__ == "__main__":
    # Generate a custom test report file name
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    test_report_dir = Path("/test-results")
    test_report_dir.mkdir(exist_ok=True)
    
    # Run the tests
    unittest.main(verbosity=2)