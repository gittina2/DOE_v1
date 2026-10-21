"""Convenience launcher for the DOE Toolkit desktop GUI."""
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from doe.gui.app import run_app

if __name__ == "__main__":
    sys.exit(run_app())
