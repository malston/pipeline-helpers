# Running End-to-End Tests on Apple Silicon (M1/M2) Macs

This guide provides specific instructions for running the end-to-end tests on Apple Silicon Macs (M1, M2, etc.).

## Prerequisites

1. Install Docker Desktop for Mac (version 4.15.0 or later)
2. Enable Rosetta 2 emulation for Docker Desktop
3. Ensure you have sufficient memory allocated to Docker (at least 8GB recommended)

## Enabling Rosetta 2 for Docker

If you haven't already enabled Rosetta 2 for Docker:

1. Open Docker Desktop
2. Go to Settings > Features in development
3. Check "Use Rosetta for x86/amd64 emulation on Apple Silicon"
4. Click "Apply & Restart"

## Running the Tests

The docker-compose file and Dockerfiles have been configured with platform specifications to ensure compatibility with Apple Silicon:

1. All services use the `platform: linux/amd64` setting to ensure x86 compatibility
2. The test runner Dockerfile uses the `--platform=linux/amd64` flag

To run the tests, follow the standard instructions:

```bash
export GITHUB_TOKEN=your_github_personal_access_token
make -f Makefile.e2e setup
make -f Makefile.e2e run-tests
```

## Performance Considerations

Running x86 containers on Apple Silicon using Rosetta 2 emulation may result in:

1. Slower startup times for containers
2. Higher memory usage
3. Increased CPU utilization

For the best performance:

- Ensure Docker has sufficient memory allocated (Settings > Resources)
- Close other memory-intensive applications while running the tests
- Be patient during container startup, as emulation adds overhead

## Troubleshooting

If you encounter "exec format error" messages:

```sh
standard_init_linux.go:228: exec user process caused: exec format error
```

This means the container is trying to run ARM64 binaries on an x86 container or vice versa. Solutions:

1. Double-check that the platform flags are set correctly in docker-compose.yml
2. Verify that Rosetta 2 emulation is enabled in Docker Desktop
3. Try rebuilding the images with `docker-compose build --no-cache`

For other issues, check the Docker Desktop logs (Help > Troubleshoot > Get support).