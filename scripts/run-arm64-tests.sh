#!/bin/bash
set -e

# Print system information
echo "System architecture: $(uname -m)"
echo "Using ARM64-compatible configuration"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN environment variable must be set"
    echo "Please run: export GITHUB_TOKEN=your_github_token"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running or not accessible"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Create necessary directories
mkdir -p test-ssh test-results

# Check if SSH key exists
if [ ! -f "test-ssh/id_rsa" ]; then
    echo "SSH key not found. Generating a new one..."
    ssh-keygen -t rsa -b 4096 -f test-ssh/id_rsa -N "" -C "pipeline-helpers-e2e-tests"
    
    echo ""
    echo "Important: Add this public key to your GitHub account before continuing:"
    cat test-ssh/id_rsa.pub
    echo ""
    
    read -p "Press Enter once you've added the key to GitHub..." nothing
fi

./keys/generate
# Start the containers using the ARM64-compatible compose file
echo "Starting Concourse and test runner containers..."
docker-compose -f docker-compose-arm64.yml up -d

# Display instructions
echo ""
echo "Tests are now running in the test-runner container"
echo "To view the test logs in real-time, run:"
echo "  docker logs -f $(docker-compose -f docker-compose-arm64.yml ps -q test-runner)"
echo ""
echo "When tests are complete, you can view results in the test-results directory"
echo "To stop all containers, press Ctrl+C and then run:"
echo "  docker-compose -f docker-compose-arm64.yml down"

# Wait for user to press Ctrl+C
echo "Press Ctrl+C to exit this script (containers will continue running)"
tail -f /dev/null