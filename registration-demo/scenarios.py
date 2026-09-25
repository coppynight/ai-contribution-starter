"""Run the actual model and expose portable data for the video and checks."""

from model import Event, cancel_fixed, cancel_legacy, register


def check(label, actual, expected):
    return {"label": label, "actual": actual, "expected": expected, "passed": actual == expected}


def event(label, state):
    return {
        "label": label,
        "remaining": state.remaining,
        "bookings": [{"id": b.booking_id, "people": b.people} for b in state.bookings],
    }


def stage(stage_id, title, events, checks):
    return {
        "id": stage_id,
        "title": title,
        "remaining": events[-1]["remaining"],
        "events": events,
        "checks": checks,
        "passed": all(item["passed"] for item in checks),
    }


def build_stages():
    initial = Event()
    individual = register(initial, "single", 1)
    individual_cancelled = cancel_legacy(individual, "single")
    family = register(initial, "family", 3)
    broken = cancel_legacy(family, "family")
    fixed = cancel_fixed(family, "family")
    return [
        stage("baseline", "旧的个人报名规则", [event("开放报名", initial), event("1 人报名", individual)], [
            check("个人报名占用 1 个名额", individual.remaining, 7),
        ]),
        stage("contributor_a", "A：家庭报名，单独验证", [event("开放报名", initial), event("一家 3 人报名", family)], [
            check("家庭报名占用 3 个名额", family.remaining, 5),
            check("报名记录保留实际人数", family.bookings[0].people, 3),
        ]),
        stage("contributor_b", "B：取消报名，按旧的个人场景验证", [event("开放报名", initial), event("1 人报名", individual), event("取消 1 人报名", individual_cancelled)], [
            check("个人取消归还 1 个名额", individual_cancelled.remaining, 8),
            check("已取消的报名被移除", len(individual_cancelled.bookings), 0),
        ]),
        stage("candidate", "组合候选：家庭报名后取消", [event("开放报名", initial), event("一家 3 人报名", family), event("按旧规则取消家庭报名", broken)], [
            check("家庭报名占用 3 个名额", family.remaining, 5),
            check("取消后应恢复全部名额", broken.remaining, initial.capacity),
        ]),
        stage("after", "修正反馈后：按实际人数归还", [event("开放报名", initial), event("一家 3 人报名", family), event("按实际人数取消家庭报名", fixed)], [
            check("家庭报名占用 3 个名额", family.remaining, 5),
            check("取消后恢复全部名额", fixed.remaining, initial.capacity),
            check("已取消的报名被移除", len(fixed.bookings), 0),
            check("初始状态未被修改", initial.remaining, initial.capacity),
        ]),
    ]


def suite(version):
    """The old checks pass; adding the combined scenario exposes the defect."""
    initial = Event()
    single = register(initial, "single", 1)
    cancel = cancel_fixed if version == "after" else cancel_legacy
    checks = [
        check("个人报名保留 7 个名额", single.remaining, 7),
        check("个人取消恢复 8 个名额", cancel(single, "single").remaining, 8),
    ]
    if version in ("candidate", "after"):
        family = register(initial, "family", 3)
        checks.extend([
            check("家庭报名保留 5 个名额", family.remaining, 5),
            check("家庭取消恢复 8 个名额", cancel(family, "family").remaining, 8),
        ])
    return {"version": version, "checks": checks, "passed": all(c["passed"] for c in checks)}
