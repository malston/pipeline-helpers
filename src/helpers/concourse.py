#!/usr/bin/env python3

"""Concourse CI client module for interacting with Concourse via fly CLI."""

import os
import subprocess
from typing import List, Optional


class ConcourseClient:
    """Client for interacting with Concourse CI.

    This client provides methods to interact with Concourse through the fly CLI,
    including managing pipelines, triggering jobs, and watching job output.
    """

    def __init__(self, fly_path: Optional[str] = None) -> None:
        """Initialize the Concourse client.

        Args:
            fly_path: Optional path to the fly executable. If not provided, assumes it's in PATH.
        """
        self.fly_path = fly_path or "fly"
        self._validate_fly_cli()

    def _validate_fly_cli(self) -> None:
        """Validate that the fly CLI is available and executable."""
        if self.fly_path == "fly":
            # Check if fly is in PATH
            for path in os.environ["PATH"].split(os.pathsep):
                executable = os.path.join(path, "fly")
                if os.path.isfile(executable) and os.access(executable, os.X_OK):
                    return
            raise ValueError("fly CLI not found in PATH")
        else:
            # Check if specified fly path exists and is executable
            if not os.path.isfile(self.fly_path) or not os.access(self.fly_path, os.X_OK):
                raise ValueError(f"fly CLI not found at {self.fly_path} or not executable")

    def _run_fly_command(
        self, args: List[str], cwd: Optional[str] = None, **kwargs
    ) -> subprocess.CompletedProcess:
        """Run a fly command with the given arguments.

        Args:
            args: List of arguments to pass to fly
            cwd: Working directory for the command
            **kwargs: Additional arguments to pass to subprocess.run

        Returns:
            A subprocess.CompletedProcess instance

        Raises:
            subprocess.CalledProcessError: If the command fails
        """
        cmd = [self.fly_path] + args
        return subprocess.run(cmd, cwd=cwd, check=True, **kwargs)

    def unpause_pipeline(self, target: str, pipeline: str) -> None:
        """Unpause a pipeline.

        Args:
            target: Concourse target
            pipeline: Pipeline name
        """
        self._run_fly_command(["-t", target, "unpause-pipeline", "-p", pipeline])

    def trigger_job(self, target: str, job: str, watch: bool = False) -> None:
        """Trigger a job.

        Args:
            target: Concourse target
            job: Job name in format 'pipeline/job'
            watch: Whether to watch the job output
        """
        args = ["-t", target, "trigger-job", "-j", job]
        if watch:
            args.append("-w")
        self._run_fly_command(args)

    def watch_job(self, target: str, job: str) -> None:
        """Watch a job's output.

        Args:
            target: Concourse target
            job: Job name in format 'pipeline/job'
        """
        self._run_fly_command(["-t", target, "watch", "-j", job])

    def run_fly_script(self, script_path: str, args: List[str], cwd: Optional[str] = None) -> None:
        """Run a fly script with the given arguments.

        Args:
            script_path: Path to the fly script
            args: List of arguments to pass to the script
            cwd: Working directory for the command

        Raises:
            ValueError: If the script is not executable
            subprocess.CalledProcessError: If the command fails
        """
        if not os.access(script_path, os.X_OK):
            raise ValueError(f"Fly script at {script_path} is not executable")

        cmd = [script_path] + args
        subprocess.run(cmd, cwd=cwd, check=True)

    def find_fly_script(self, directory: str) -> Optional[str]:
        """Find fly scripts in a directory.

        Args:
            directory: Directory to search in

        Returns:
            Path to the found fly script or None if not found
        """
        # Check for FLY_SCRIPT environment variable first
        fly_script = os.getenv("FLY_SCRIPT")
        if fly_script:
            if not os.path.isabs(fly_script):
                fly_script = os.path.join(directory, fly_script)
            return fly_script if os.path.isfile(fly_script) else None

        # Look for any script that starts with 'fly'
        fly_scripts = []
        for item in os.listdir(directory):
            if item.startswith("fly"):
                script_path = os.path.join(directory, item)
                if os.path.isfile(script_path):
                    fly_scripts.append(script_path)

        if not fly_scripts:
            return None

        if len(fly_scripts) == 1:
            return fly_scripts[0]

        # Multiple scripts found - in this case we'll return the first one
        # The caller should handle this situation by prompting the user
        return fly_scripts
