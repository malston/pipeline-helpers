"""Test configuration for pytest."""

import os
import sys
from pathlib import Path

# Add the project root to the Python path for tests
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add the src directory to the Python path
src_dir = os.path.join(project_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)