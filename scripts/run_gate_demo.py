"""Run one controlled gate demonstration and preserve its real exit code."""

import argparse
import sys

from _demo_support import inject_fault, run_check, source_hashes, temporary_demo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", choices=("before", "after"), required=True)
    parser.add_argument("--inject-fault", choices=("true", "false"), default="false")
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
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
