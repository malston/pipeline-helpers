#!/bin/bash
set -e

# Print architecture info for debugging
echo "System architecture information:"
uname -a
arch

# Setup logging
LOGFILE="/test-results/e2e-test-$(date +%Y%m%d-%H%M%S).log"
mkdir -p "$(dirname "$LOGFILE")"
exec > >(tee -a "$LOGFILE") 2>&1

echo "Starting end-to-end tests at $(date)"
echo "=========================="

# Setup SSH for Git operations
if [ -f "$SSH_PRIVATE_KEY_PATH" ]; then
    echo "Setting up SSH configuration..."
    
    # Set permissions on the private key
    chmod 600 "$SSH_PRIVATE_KEY_PATH"
    
    # Configure SSH to not prompt for host key verification
    cat > /root/.ssh/config << EOF
Host github.com
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
EOF
    chmod 600 /root/.ssh/config
    
    # Add GitHub's public key to known_hosts
    ssh-keyscan -t rsa github.com >> /root/.ssh/known_hosts
    
    echo "SSH configured successfully"
else
    echo "SSH private key not found at $SSH_PRIVATE_KEY_PATH"
    echo "Please mount your SSH key to enable Git cloning"
    exit 1
fi

# Configure Git
git config --global user.name "Pipeline E2E Tests"
git config --global user.email "test@example.com"

# Set up Concourse target
echo "Configuring Concourse target..."
fly -t test login -c "$CONCOURSE_URL" -n main --team-name main -u test -p test
fly -t test sync

# Clone required repositories
if [ ! -d "/root/git/${REPOS_OWNER}/params" ]; then
    echo "Cloning params repository..."
    mkdir -p "/root/git/${REPOS_OWNER}"
    cd "/root/git/${REPOS_OWNER}"
    git clone "git@github.com:${REPOS_OWNER}/params.git"
fi

if [ ! -d "/root/git/${REPOS_OWNER}/ns-mgmt" ]; then
    echo "Cloning ns-mgmt repository..."
    mkdir -p "/root/git/${REPOS_OWNER}"
    cd "/root/git/${REPOS_OWNER}"
    git clone "git@github.com:${REPOS_OWNER}/ns-mgmt.git"
fi

# Run the automated tests
echo "Running E2E tests..."
cd /app
python -m e2e_tests.test_end_to_end

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "=========================="
    echo "✅ E2E tests completed successfully!"
    exit 0
else
    echo "=========================="
    echo "❌ E2E tests failed!"
    exit 1
fi