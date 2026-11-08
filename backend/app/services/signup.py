"""报名核心逻辑：事务防超卖 + 时段冲突校验。

规则（对应需求文档与 tests/test_signup.py 的验收）：
1. 活动必须 open 且未过报名截止 → 400
2. 场次必须属于该活动 → 404
3. 名额：条件更新 booked_count，更新不到行 = 已满 → 409（并发安全）
4. 同人同场次重复报名 → 409（应用层先查，唯一约束兜底）
5. 时段重叠（与已有报名、与本次多选内部）→ 409
6. 学号不存在 → 自动建档 members
全部在一个事务里，任一失败整体回滚。
"""
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..models import Activity, Member, Shift, ShiftSignup

OVERLAP_NOTE = "时段与已报名场次冲突"


def get_or_create_member(
    db: Session, *, name: str, student_id: str, college: str, phone: str
) -> Member:
    member = db.scalar(select(Member).where(Member.student_id == student_id))
    if member is None:
        member = Member(name=name, student_id=student_id, college=college, phone=phone)
        db.add(member)
        db.flush()  # 拿到 member.id
    else:
        # 信息以最新一次报名为准（换手机号/搬学院是真实会发生的事）；
        # college 前端已不收集，传空时不覆盖旧值
        member.name, member.phone = name, phone
        if college:
            member.college = college
    return member


def check_activity_open(activity: Activity, now: datetime) -> None:
    if activity is None or activity.status != "open":
        raise SignupError(400, "活动未开放报名")
    if activity.signup_deadline is not None and now > activity.signup_deadline:
        raise SignupError(400, "已过报名截止时间")


def check_shifts_belong_to_activity(db: Session, activity_id: int, shift_ids: list[int]) -> list[Shift]:
    shifts = db.scalars(select(Shift).where(Shift.id.in_(shift_ids))).all()
    found = {s.id for s in shifts}
    missing = set(shift_ids) - found
    if missing:
        raise SignupError(404, f"场次不存在: {sorted(missing)}")
    wrong = [s.id for s in shifts if s.activity_id != activity_id]
    if wrong:
        raise SignupError(404, f"场次不属于该活动: {sorted(wrong)}")
    return shifts


def check_no_time_overlap(shifts: list[Shift], existing: list[tuple[datetime, datetime]]) -> None:
    """selected 内部两两 + 与已有 (start, end) 列表。区间半开：end==start 相邻不算冲突。"""
    intervals = [(s.start_time, s.end_time) for s in shifts] + list(existing)
    intervals.sort()
    for (s1, e1), (s2, e2) in zip(intervals, intervals[1:]):
        if s1 < e2 and s2 < e1:
            raise SignupError(409, f"时段冲突: {s1:%m-%d %H:%M}~{e1:%H:%M} 与 {s2:%m-%d %H:%M}~{e2:%H:%M}")


def existing_booked_intervals(db: Session, member_id: int) -> list[tuple[datetime, datetime]]:
    rows = db.execute(
        select(Shift.start_time, Shift.end_time)
        .join(ShiftSignup, ShiftSignup.shift_id == Shift.id)
        .where(ShiftSignup.member_id == member_id, ShiftSignup.status == "booked")
    ).all()
    return [(r[0], r[1]) for r in rows]


def book_capacities(db: Session, shift_ids: list[int]) -> None:
    """条件更新扣减名额；更新行数不足说明有人满员（或并发抢完）。"""
    for shift_id in shift_ids:
        result = db.execute(
            update(Shift)
            .where(Shift.id == shift_id, Shift.booked_count < Shift.capacity)
            .values(booked_count=Shift.booked_count + 1)
        )
        if result.rowcount != 1:
            raise SignupError(409, f"场次 {shift_id} 名额已满")


class SignupError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
