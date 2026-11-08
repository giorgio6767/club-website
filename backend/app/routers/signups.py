"""报名接口（公开）：志愿者多选场次一次性提交，事务内全部校验+扣名额。

验收对应 tests/test_signup.py：
1. 名额不足 → 409（条件更新，并发安全）
2. 同人同场次重复报名 → 409（应用层查重 + 唯一约束兜底）
3. 时段重叠（本次多选内部 / 与已有报名）→ 409
4. 活动非 open 或过截止 → 400
5. 学号不存在 → 自动建档 members
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Activity, ShiftSignup
from ..services.signup import (
    SignupError,
    book_capacities,
    check_activity_open,
    check_no_time_overlap,
    check_shifts_belong_to_activity,
    existing_booked_intervals,
    get_or_create_member,
)

router = APIRouter(prefix="/activities", tags=["signups"])


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    student_id: str = Field(min_length=6, max_length=20, pattern=r"^[0-9A-Za-z]+$")
    college: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=11, max_length=11, pattern=r"^1[0-9]{10}$")
    shift_ids: list[int] = Field(min_length=1)

    @field_validator("shift_ids")
    @classmethod
    def dedup(cls, v: list[int]) -> list[int]:
        ids = list(dict.fromkeys(v))  # 保序去重
        if len(ids) != len(v):
            raise ValueError("场次列表有重复")
        return ids


class SignupResponse(BaseModel):
    member_id: int
    booked_shift_ids: list[int]
    message: str = "报名成功"


@router.post("/{activity_id}/signups", response_model=SignupResponse)
def signup(activity_id: int, body: SignupRequest, db: Session = Depends(get_db)):
    activity = db.get(Activity, activity_id)
    if activity is None:
        raise HTTPException(status_code=404, detail="活动不存在")
    member = None
    try:
        check_activity_open(activity, datetime.now())
        shifts = check_shifts_belong_to_activity(db, activity_id, body.shift_ids)
        check_no_time_overlap(shifts, [])  # 先查本次多选内部

        member = get_or_create_member(
            db,
            name=body.name,
            student_id=body.student_id,
            college=body.college,
            phone=body.phone,
        )
        # 先查重再查冲突：重复报名的提示比时段冲突更准确
        mine = set(
            db.scalars(
                select(ShiftSignup.shift_id).where(
                    ShiftSignup.member_id == member.id,
                    ShiftSignup.shift_id.in_(body.shift_ids),
                    ShiftSignup.status == "booked",
                )
            ).all()
        )
        if mine:
            raise SignupError(409, f"你已报过场次 {sorted(mine)}，无需重复报名")

        check_no_time_overlap(shifts, existing_booked_intervals(db, member.id))

        book_capacities(db, body.shift_ids)
        for sid in body.shift_ids:
            db.add(ShiftSignup(shift_id=sid, member_id=member.id))
        db.commit()
    except SignupError as e:
        db.rollback()
        raise HTTPException(status_code=e.status_code, detail=e.detail) from None
    except Exception:
        db.rollback()
        raise

    return SignupResponse(member_id=member.id, booked_shift_ids=body.shift_ids)
