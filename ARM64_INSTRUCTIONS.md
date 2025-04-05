# Running End-to-End Tests on ARM64 (Apple Silicon) Macs

This guide provides instructions for running the end-to-end tests natively on ARM64 architecture without requiring Rosetta 2 emulation.

## Two Options for Running Tests on Apple Silicon

You have two options for running the tests on an M1/M2 Mac:

1. **Using Rosetta 2 Emulation** (original setup)
2. **Native ARM64 Execution** (this guide)

## Native ARM64 Setup

The native ARM64 setup uses:
- ARM64-compatible PostgreSQL container
- ARM64-compatible Python test runner
- Rosetta emulation only for Concourse components that don't have official ARM64 images

### Prerequisites

1. Docker Desktop for Mac (latest version)
2. Git
3. GitHub SSH key and Personal Access Token

### Running Tests with Native ARM64 Support

1. Set your GitHub token:
   ```bash
   export GITHUB_TOKEN=your_github_personal_access_token
   ```

2. Run the ARM64-specific script:
   ```bash
   chmod +x ./run-arm64-tests.sh
   ./run-arm64-tests.sh
   ```

3. The script will:
   - Generate an SSH key if needed
   - Start Docker containers using the ARM64-compatible configuration
   - Run the tests in the container
   - Provide instructions for viewing logs

4. View the test logs in real-time:
   ```bash
   docker-compose -f docker-compose-arm64.yml logs -f test-runner
   ```

5. When finished, stop the containers:
   ```bash
   docker-compose -f docker-compose-arm64.yml down
   ```

## Comparing the Two Approaches

### Native ARM64 Approach (Recommended)
- **Pros**: Better performance for most components, less memory usage
- **Cons**: Still requires Rosetta for Concourse components

### Full Rosetta 2 Emulation
- **Pros**: Simple setup, consistent with non-ARM systems
- **Cons**: Higher memory usage, slower performance

## Troubleshooting

### "Cannot connect to the Docker daemon"
Make sure Docker Desktop is running and fully initialized.

### "Error response from daemon: pull access denied"
Check that you're logged in to Docker Hub:
```bash
docker login
```

### "The requested image's platform does not match the detected host platform"
This occurs if you try to run the regular docker-compose file without Rosetta 2. Use the ARM64-specific files instead.

### Test failures related to Concourse
Ensure Concourse components have fully started before running tests. You can check the health with:
```bash
docker-compose -f docker-compose-arm64.yml ps
```