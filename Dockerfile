FROM python:3.11-slim

WORKDIR /app

# Install git and other dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the package files
COPY . /app/

# Install the package
RUN pip install --no-cache-dir -e .

# Create an entrypoint script
RUN echo '#!/bin/bash\n\
if [ "$1" = "create-release" ] || \
   [ "$1" = "delete-release" ] || \
   [ "$1" = "rollback-release" ] || \
   [ "$1" = "update-params-release-tag" ] || \
   [ "$1" = "demo-release-pipeline" ]; then\n\
    "$@"\n\
else\n\
    echo "Available commands:"\n\
    echo "  create-release"\n\
    echo "  delete-release"\n\
    echo "  rollback-release"\n\
    echo "  update-params-release-tag"\n\
    echo "  demo-release-pipeline"\n\
    echo ""\n\
    echo "Usage: docker run pipeline-helpers COMMAND [ARGS]"\n\
fi' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
