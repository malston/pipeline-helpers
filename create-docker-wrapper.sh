#!/bin/bash

# Create a directory for wrapper scripts
mkdir -p ~/.local/bin

WORKSPACE=$(pwd)/..

# Create wrapper script for each command
for CMD in create-release delete-release rollback-release update-params-release-tag demo-release-pipeline; do
    cat > ~/.local/bin/$CMD << EOF
#!/bin/bash
docker run --rm -it -v $WORKSPACE:/root/git -e GITHUB_TOKEN="\$GITHUB_TOKEN" pipeline-helpers $CMD "\$@"
EOF
    chmod +x ~/.local/bin/$CMD
done

echo "Wrapper scripts created in ~/.local/bin"
echo "Make sure this directory is in your PATH"
