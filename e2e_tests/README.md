# End-to-End Tests for Pipeline Helpers

This directory contains end-to-end tests that verify the pipeline-helpers scripts work correctly
with a real Concourse CI instance and GitHub repositories.

## Requirements

- Docker and Docker Compose
- GitHub SSH key for repo access
- GitHub personal access token with repo scope
- Access to the following private repositories:
  - github.com/malston/ns-mgmt
  - github.com/malston/params

## Test Environment

The tests run inside a Docker container alongside a complete Concourse CI instance:

- **Concourse Web**: The Concourse web UI and API
- **Concourse Worker**: The worker that runs tasks
- **PostgreSQL**: The database for Concourse
- **Test Runner**: The container that runs the E2E tests

## Running the Tests

1. Set up the environment:
   ```bash
   export GITHUB_TOKEN=your_github_personal_access_token
   make -f Makefile.e2e setup
   ```

2. Add the generated SSH key to your GitHub account
   (the key will be displayed in the console after running setup)

3. Run the tests:
   ```bash
   make -f Makefile.e2e run-tests
   ```

4. View test logs:
   ```bash
   make -f Makefile.e2e logs
   ```

5. Clean up when done:
   ```bash
   make -f Makefile.e2e clean
   ```

## Test Cases

The end-to-end tests verify:

1. Repository structure validation
2. Setting up a release pipeline in Concourse
3. Creating a release (dry run mode)
4. Testing the demo release pipeline (dry run mode)
5. Updating params release tags (with validation)

## Customization

You can customize the test environment by setting these environment variables:

- `GITHUB_TOKEN`: Your GitHub personal access token (required)
- `REPOS_OWNER`: GitHub owner of the repositories (default: malston)
- `FOUNDATION_NAME`: Name to use for the foundation (default: test)

Example:
```bash
export GITHUB_TOKEN=ghp_abcdef123456
export REPOS_OWNER=your-github-username
export FOUNDATION_NAME=custom-foundation

make -f Makefile.e2e run-tests
```

## Troubleshooting

If tests fail, check:

1. SSH key is properly added to your GitHub account
2. GitHub token has sufficient permissions
3. Docker containers are running correctly
4. Network connectivity to GitHub

Detailed logs are available in the `test-results` directory.