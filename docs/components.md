# Concourse Pipeline Helpers

This Python package provides utilities for managing GitHub releases with Concourse CI pipelines. The package is designed for DevOps engineers working with Concourse CI in a specific environment where repositories follow certain naming conventions.

## Key Components

1. **Core Functionality**:
   - Create, delete, and rollback GitHub releases
   - Update release tags in parameter files
   - Trigger Concourse pipelines for releases
   - Manage repository versioning

2. **Main Scripts**:
   - `create_release.py`: Creates a new release in a GitHub repository
   - `delete_release.py`: Deletes an existing release
   - `rollback_release.py`: Rolls back to a previous release
   - `update_params_release_tag.py`: Updates release tags in parameter files
   - `demo_release_pipeline.py`: Demo tool for testing release pipelines

3. **Helper Modules**:
   - `git_helper.py`: Manages Git operations (checkout, tag, branch, etc.)
   - `release_helper.py`: Handles release-specific logic
   - `concourse.py`: Interacts with Concourse CI through the fly CLI
   - `github.py`: Communicates with the GitHub API
   - `logger.py`: Provides structured and color-formatted logging (see [logging.md](logging.md))
   - `error_handler.py`: Manages exception handling and error reporting

4. **Architecture**:
   - The package follows a modular design with clear separation of concerns
   - Scripts use helper classes that encapsulate related functionality
   - Error handling is consistent across components
   - Command-line interfaces use standardized argument parsing

5. **Build System**:
   - Uses a modern Python package structure with pyproject.toml
   - Includes a comprehensive Makefile for development tasks
   - Has testing infrastructure with pytest
   - Supports code formatting and linting

The system appears designed for managing infrastructure as code in an enterprise environment, specifically for TKGI (Tanzu Kubernetes Grid Integrated) deployments, with a focus on managing releases across multiple foundational environments.
