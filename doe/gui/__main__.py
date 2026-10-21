"""CLI entry point for running the GUI via python -m doe.gui."""
import sys
from doe.gui.app import run_app

if __name__ == "__main__":
    sys.exit(run_app())
