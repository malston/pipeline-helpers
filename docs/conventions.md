# Conventions and Patterns

1. **File Structure and Organization**:
   - Scripts are placed directly in the `src` directory
   - Helper modules are in `src/helpers`
   - Tests mirror the source structure in the `tests` directory
   - Type hints with `py.typed` markers for static type checking support

2. **Naming Conventions**:
   - Snake_case for variables, functions, and file names (e.g., `get_current_branch`, `update_params_git_release_tag.py`)
   - PascalCase for classes (e.g., `GitHelper`, `ReleaseHelper`, `CustomHelpFormatter`)
   - Constants in UPPER_CASE (e.g., `COLORS`, `PYTHON_VERSION`)

3. **Documentation**:
   - Docstrings for classes and functions in Google style format
   - Detailed parameter descriptions with type information
   - High-level module docstrings explaining the purpose of each file

4. **Command-Line Interface**:
   - Consistent use of argparse with custom formatters for better help messages
   - Standardized argument patterns (e.g., `-f` for foundation, `-r` for repo, `-o` for owner)
   - Scripts support both interactive and non-interactive modes
   - Custom help formatting that's more readable and concise

5. **Error Handling**:
   - Centralized error handling through the `error_handler` module
   - Consistent logging of errors with color-coding
   - Proper exception chaining with `from e` syntax
   - Graceful degradation when features aren't available

6. **Testing**:
   - Test files named with `test_` prefix
   - Heavy use of mocking to isolate components
   - Parameterized tests for different scenarios
   - Fixtures for common setup operations

7. **Code Style**:
   - 100-character line length limit
   - Consistent import ordering (stdlib first, then third-party, then local)
   - Type annotations throughout the codebase
   - Comprehensive logging for operations

8. **Configuration Management**:
   - Environment variables for configurable settings (e.g., `GIT_WORKSPACE`, `GITHUB_TOKEN`, `PIPELINE_HELPERS_LOG_TO_FILE`)
   - Smart defaults that can be overridden (e.g., home directory expansion)
   - Path normalization and standardization
   - Preference for environment variables over command-line flags for global settings

9. **User Interaction**:
   - Colorized console output for better readability
   - Confirmation prompts before potentially destructive operations
   - Detailed progress messages for long-running operations

These conventions appear to be designed to create maintainable, robust code that's also user-friendly for the DevOps engineers who would be using these tools.
