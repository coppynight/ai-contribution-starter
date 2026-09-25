"""Run one controlled gate demonstration and preserve its real exit code."""

import argparse
import os
from pathlib import Path
import sys

from _demo_support import inject_fault, run_check, source_hashes, temporary_demo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", choices=("before", "after"), required=True)
    parser.add_argument("--inject-fault", choices=("true", "false"), default="false")
    parser.add_argument(
        "--verify-expectation", action="store_true",
        help="Verify the teaching scenario; without this flag return the raw gate exit code.",
    )
    args = parser.parse_args()
    original_hashes = source_hashes()
    with temporary_demo(args.version) as project:
        if args.inject_fault == "true":
            inject_fault(project)
        result = run_check(project)
    print(result["stdout"], end="")
    print(result["stderr"], end="", file=sys.stderr)
    print(f'Gate demo: version={args.version}, controlled_fault={args.inject_fault}, '
          f'test_failures={result["test_failures"]}, exit={result["exit_code"]}', flush=True)
    if source_hashes() != original_hashes:
        print("ERROR: source files changed", file=sys.stderr)
        return 2
    print("Source files unchanged; temporary copy removed.", flush=True)
    if args.verify_expectation:
        fault = args.inject_fault == "true"
        expected_exit = 1 if args.version == "after" and fault else 0
        expected_failures = 2 if fault else 0
        matches = (
            result["exit_code"] == expected_exit
            and result["tests_run"] == 3
            and result["test_failures"] == expected_failures
            and result["tests_passed"] == (not fault)
        )
        summary = (
            "## Teaching scenario verification\n\n"
            f"Version: `{args.version}`; controlled fault: `{args.inject_fault}`.\n\n"
            "| Observation | Expected | Actual |\n"
            "| --- | --- | --- |\n"
            f"| Gate exit code | {expected_exit} | {result['exit_code']} |\n"
            f"| Tests run | 3 | {result['tests_run']} |\n"
            f"| Test failures | {expected_failures} | {result['test_failures']} |\n\n"
            f"Scenario verification: **{'PASS' if matches else 'FAIL'}**.\n\n"
            "This workflow checks whether the teaching scenario behaved as expected. "
            "It does not approve the faulty example for use. The raw gate command still "
            "returns its real exit code when --verify-expectation is omitted.\n"
        )
        print(summary, flush=True)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as stream:
                stream.write(summary)
        return 0 if matches else 1
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
