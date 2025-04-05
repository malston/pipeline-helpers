# End-to-End Testing

This project includes end-to-end tests that verify the pipeline-helpers scripts work correctly with a real Concourse CI instance and actual GitHub repositories.

## Prerequisites

- Docker and Docker Compose
- SSH key with access to your private GitHub repositories
- GitHub personal access token with appropriate permissions

## Running the Tests

1. Set up the environment:
   ```bash
   export GITHUB_TOKEN=your_github_personal_access_token
   make -f Makefile.e2e setup
   ```

2. Add the generated SSH key to your GitHub account

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

See [e2e_tests/README.md](e2e_tests/README.md) for more details on the end-to-end testing framework.