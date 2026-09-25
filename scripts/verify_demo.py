"""Reproduce the comparison with real subprocesses, then write evidence."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from _demo_support import ROOT, inject_fault, run_check, source_hashes, temporary_demo


def verify_case(name, project, expected_exit, expected_failures):
    result = run_check(project)
    result.update({
        "case": name,
        "expected_exit_code": expected_exit,
        "expected_test_failures": expected_failures,
    })
    result["matches_expectation"] = (
        result["exit_code"] == expected_exit
        and result["tests_run"] == 3
        and result["test_failures"] == expected_failures
        and result["tests_passed"] == (expected_failures == 0)
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="evidence/verification.json")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if ROOT not in output.parents:
        parser.error("output must be inside this repository")

    before_hashes = source_hashes()
    cases = []
    restored = False
    for version, fault_exit in (("before", 0), ("after", 1)):
        with temporary_demo(version) as project:
            cases.append(verify_case(version + "_baseline", project, 0, 0))
            original = inject_fault(project)
            try:
                cases.append(verify_case(version + "_controlled_fault", project, fault_exit, 2))
            finally:
                (project / "tasks.py").write_bytes(original)
            if version == "after":
                restored = (project / "tasks.py").read_bytes() == original
                cases.append(verify_case("after_restored", project, 0, 0))

    after_hashes = source_hashes()
    unchanged = before_hashes == after_hashes
    passed = all(case["matches_expectation"] for case in cases) and unchanged and restored
    evidence = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "command": "python scripts/verify_demo.py",
        "controlled_fault": "remove completed-task filter in temporary copies only",
        "cases": cases,
        "temporary_after_source_restored": restored,
        "source_files_unchanged": unchanged,
        "source_hashes_before": before_hashes,
        "source_hashes_after": after_hashes,
        "verified": passed,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for case in cases:
        marker = "PASS" if case["matches_expectation"] else "FAIL"
        print(f'{marker} {case["case"]}: tests={case["tests_run"]}, '
              f'failures={case["test_failures"]}, exit={case["exit_code"]}')
    print(f"Source files unchanged: {unchanged}; temporary after restored: {restored}")
    print("Evidence: " + output.relative_to(ROOT).as_posix())
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
