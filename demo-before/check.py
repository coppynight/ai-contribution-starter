"""Existing local check entry point, intentionally incomplete for the exercise."""
import subprocess
import sys
from pathlib import Path


subprocess.run(
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
    cwd=Path(__file__).resolve().parent,
    check=False,
)
