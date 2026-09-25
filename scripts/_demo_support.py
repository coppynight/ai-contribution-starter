"""Shared, standard-library-only helpers for controlled CI demonstrations."""

import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager


ROOT = Path(__file__).resolve().parents[1]
FILTER = ' if not task["completed"]'


def source_hashes():
    """Hash source files, ignoring interpreter-generated caches."""
    hashes = {}
    for name in ("demo-before", "demo-after"):
        for path in sorted((ROOT / name).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
    return hashes


@contextmanager
def temporary_demo(version):
    if version not in ("before", "after"):
        raise ValueError("version must be before or after")
    with tempfile.TemporaryDirectory(prefix="ai-contribution-demo-") as directory:
        target = Path(directory) / ("demo-" + version)
        shutil.copytree(
            ROOT / ("demo-" + version), target,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        yield target


def inject_fault(project):
    """Remove exactly one filter in a temporary copy; return original bytes."""
    source = project / "tasks.py"
    original = source.read_bytes()
    decoded = original.decode("utf-8")
    if decoded.count(FILTER) != 1:
        raise RuntimeError("controlled fault requires exactly one known filter")
    source.write_text(decoded.replace(FILTER, "", 1), encoding="utf-8")
    return original


def run_check(project):
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, "-B", "check.py"], cwd=project,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=environment, check=False, timeout=30,
    )

    def portable(text):
        # unittest tracebacks include an absolute temporary path. Keep the
        # evidence portable without dropping the useful file/line information.
        for prefix in (str(project), project.as_posix(), str(ROOT), ROOT.as_posix()):
            text = text.replace(prefix, "<demo>")
        return re.sub(r'<demo>[^"\n]*', lambda match: match.group(0).replace("\\", "/"), text)

    stdout = portable(result.stdout)
    stderr = portable(result.stderr)
    transcript = stdout + stderr
    match = re.search(r"Ran (\d+) tests?", transcript)
    failures = re.search(r"FAILED \(failures=(\d+)\)", transcript)
    return {
        "exit_code": result.returncode,
        "tests_run": int(match.group(1)) if match else None,
        "test_failures": int(failures.group(1)) if failures else 0,
        "tests_passed": bool(re.search(r"^OK\s*$", transcript, re.MULTILINE)),
        "stdout": stdout,
        "stderr": stderr,
    }
