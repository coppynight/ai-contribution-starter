"""Verify the controlled teaching example and write reproducible public evidence."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from scenarios import build_stages


def verify_check_output(version, result):
    """Do not accept the expected exit code if checks were skipped or changed."""
    expected_checks = [
        ("个人报名保留 7 个名额", 7, 7),
        ("个人取消恢复 8 个名额", 8, 8),
    ]
    if version != "before":
        expected_checks.extend([
            ("家庭报名保留 5 个名额", 5, 5),
            ("家庭取消恢复 8 个名额", 6 if version == "candidate" else 8, 8),
        ])
    if result.get("version") != version:
        raise AssertionError(f"{version}: unexpected version in check output")
    checks = result.get("checks")
    if not isinstance(checks, list) or len(checks) != len(expected_checks):
        raise AssertionError(f"{version}: missing or unexpected checks")
    for actual, (label, value, expected) in zip(checks, expected_checks):
        if (
            actual.get("label") != label
            or actual.get("actual") != value
            or actual.get("expected") != expected
            or actual.get("passed") is not (value == expected)
        ):
            raise AssertionError(f"{version}: unexpected check result for {label}")
    if result.get("passed") is not (version != "candidate"):
        raise AssertionError(f"{version}: inconsistent overall check result")


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=root / "evidence.json")
    args = parser.parse_args()
    source_files = sorted(root.glob("*.py"))
    hashes_before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_files}
    stages = build_stages()
    by_id = {item["id"]: item for item in stages}
    expected_passes = {"baseline": True, "contributor_a": True, "contributor_b": True, "candidate": False, "after": True}
    for name, expected in expected_passes.items():
        if by_id[name]["passed"] is not expected:
            raise AssertionError(f"Unexpected result in {name}")

    commands = []
    for version, expected_code in (("before", 0), ("candidate", 1), ("after", 0)):
        process = subprocess.run(
            [sys.executable, str(root / "check.py"), "--version", version],
            cwd=root, text=True, encoding="utf-8", capture_output=True, check=False,
            timeout=30,
        )
        if process.returncode != expected_code:
            raise AssertionError(f"{version}: expected exit {expected_code}, got {process.returncode}")
        result = json.loads(process.stdout)
        verify_check_output(version, result)
        commands.append({
            "command": f"python registration-demo/check.py --version {version}",
            "exit_code": process.returncode,
            "checks_passed": sum(check["passed"] for check in result["checks"]),
            "checks_failed": sum(not check["passed"] for check in result["checks"]),
            "checks": result["checks"],
        })

    hashes_after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_files}
    if hashes_before != hashes_after:
        raise AssertionError("Source files changed while running the demonstration")
    evidence = {
        "schema_version": 1,
        "kind": "constructed_teaching_example",
        "description": "构造的活动报名样例。数字来自本次实际运行，不是真实用户事故或 Git 分支合并实验。",
        "visual_contract": {
            "capacity": by_id["baseline"]["events"][0]["remaining"],
            "family_size": by_id["contributor_a"]["events"][-1]["bookings"][0]["people"],
            "after_booking": by_id["contributor_a"]["remaining"],
            "broken_cancel": by_id["candidate"]["remaining"],
            "fixed_cancel": by_id["after"]["remaining"],
        },
        "stages": stages,
        "commands": commands,
        "source_unchanged": hashes_before == hashes_after,
        "source_sha256": hashes_after,
        "verification_passed": True,
        "limits": [
            "独立检查通过只证明列出的场景，不证明整个贡献正确。",
            "candidate 返回 1 是演练中预期的失败；verify 返回 0 表示这些演练结果符合预期。",
            "工作流只提供检查结果；本例没有设置禁止失败代码合入的分支保护。",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Registration demonstration verified: A and B pass their separate checks; combined candidate fails; corrected combination passes.")
    print(json.dumps(evidence["visual_contract"], ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
