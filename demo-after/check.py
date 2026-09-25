"""Run the existing checks and return their exit status to the caller."""
import subprocess
import sys
from pathlib import Path


result = subprocess.run(
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
    cwd=Path(__file__).resolve().parent,
    check=False,
)
sys.exit(result.returncode)
