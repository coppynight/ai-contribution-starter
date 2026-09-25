"""Exercise the CI contracts with real processes in disposable repository copies."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CIContractTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="ci-contract-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in ("scripts", "demo-before", "demo-after", "registration-demo"):
            shutil.copytree(
                ROOT / name,
                self.root / name,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )

    def replace_once(self, relative_path, original, replacement):
        path = self.root / relative_path
        source = path.read_text(encoding="utf-8")
        self.assertEqual(source.count(original), 1, f"Mutation anchor: {relative_path}")
        path.write_text(source.replace(original, replacement, 1), encoding="utf-8")

    def run_script(self, relative_path, *arguments):
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"
        # Negative fixtures must not publish their intentional failures to the
        # parent workflow's user-facing summary.
        environment.pop("GITHUB_STEP_SUMMARY", None)
        return subprocess.run(
            [sys.executable, "-B", str(self.root / relative_path), *arguments],
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=30,
        )

    def registration(self):
        return self.run_script(
            "registration-demo/verify.py", "--output", "registration-demo/ci-evidence.json"
        )

    def gate(self, verify=False):
        arguments = ["--version", "after", "--inject-fault", "true"]
        if verify:
            arguments.append("--verify-expectation")
        return self.run_script("scripts/run_gate_demo.py", *arguments)

    def assert_succeeded(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_rejected(self, result, reason):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(reason, result.stdout + result.stderr)

    def test_registration_accepts_complete_expected_demonstration(self):
        self.assert_succeeded(self.registration())

    def test_registration_rejects_empty_check_report(self):
        self.replace_once(
            "registration-demo/check.py",
            "    result = suite(args.version)\n",
            '    result = suite(args.version)\n    result["checks"] = []\n',
        )
        self.assert_rejected(self.registration(), "before: missing or unexpected checks")

    def test_registration_rejects_removed_family_regression(self):
        self.replace_once(
            "registration-demo/scenarios.py",
            '    if version in ("candidate", "after"):',
            '    if version == "candidate":',
        )
        self.assert_rejected(self.registration(), "after: missing or unexpected checks")

    def test_registration_rejects_swallowed_candidate_failure(self):
        self.replace_once(
            "registration-demo/check.py",
            '    return 0 if result["passed"] else 1',
            "    return 0",
        )
        self.assert_rejected(self.registration(), "candidate: expected exit 1, got 0")

    def test_registration_rejects_failure_for_the_wrong_reason(self):
        self.replace_once(
            "registration-demo/check.py",
            "    result = suite(args.version)\n",
            "    result = suite(args.version)\n"
            '    if args.version == "candidate":\n'
            '        result["checks"][0].update(actual=6, passed=False)\n'
            '        result["checks"][-1].update(actual=8, passed=True)\n',
        )
        self.assert_rejected(self.registration(), "candidate: unexpected check result")

    def test_registration_rejects_broken_correction(self):
        self.replace_once(
            "registration-demo/model.py",
            "remaining=event.remaining + booking.people,",
            "remaining=event.remaining + 1,",
        )
        self.assert_rejected(self.registration(), "Unexpected result in after")

    def test_gate_preserves_raw_failure_and_verifies_expected_failure(self):
        raw = self.gate()
        self.assertEqual(raw.returncode, 1, raw.stdout + raw.stderr)
        self.assert_succeeded(self.gate(verify=True))

    def test_gate_rejects_swallowed_failure(self):
        self.replace_once("demo-after/check.py", "sys.exit(result.returncode)", "sys.exit(0)")
        self.assert_rejected(self.gate(verify=True), "Scenario verification: **FAIL**")

    def test_gate_rejects_missing_tests(self):
        (self.root / "demo-after/tests/test_tasks.py").unlink()
        self.assert_rejected(self.gate(verify=True), "Scenario verification: **FAIL**")


if __name__ == "__main__":
    unittest.main(verbosity=2)
