# Pipeline Helpers

A collection of Python scripts for managing GitHub releases with Concourse CI pipelines.

## Installation

```bash
pip install pipeline-helpers
```

## Scripts

The package provides several command-line utilities:

- `create-release`: Create a new release in a GitHub repository
- `delete-release`: Delete an existing release
- `rollback-release`: Rollback to a previous release
- `update-params-release-tag`: Update release tags in parameter files
- `demo-release-pipeline`: Demo tool for testing release pipelines

## Usage

### Create Release

```bash
create-release -f foundation_name [-m release_message] [-o owner] [-p params_repo]
```

Options:
- `-f foundation`: The foundation name for ops manager (required)
- `-m release_body`: The message to apply to the release (optional)
- `-o owner`: The GitHub owner (default: Utilities-tkgieng)
- `-p params_repo`: The params repo name (default: params)

### Delete Release

```bash
delete-release -f foundation_name [-o owner] [-p params_repo]
```

### Rollback Release

```bash
rollback-release -f foundation_name [-o owner] [-p params_repo] [-t tag]
```

## Development

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Run tests:
   ```bash
   pytest
   ```

4. Run linter:
   ```bash
   ruff check .
   ```

## License

MIT