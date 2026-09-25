"""A reusable check entry point; an incorrect candidate exits with status 1."""

import argparse
import json
import sys

from scenarios import suite


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", choices=("before", "candidate", "after"), default="after")
    args = parser.parse_args()
    result = suite(args.version)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
