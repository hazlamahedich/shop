#!/usr/bin/env python3.11
"""Run tests with Python 3.11."""

import subprocess
import sys

def main():
    """Run pytest using Python 3.11."""
    result = subprocess.run(
        ["python3.11", "-m", "pytest"] + sys.argv[1:],
        cwd="/Users/sherwingorechomante/shop/backend"
    )
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
