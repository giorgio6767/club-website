"""管理后台接口：全部挂 require_admin。

今天（11-08）交付：创建活动+场次、活动列表、开关报名、报名名单。
11-10 交付：Excel 导出。
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Activity, Member, Shift, ShiftSignup, User
from ..security import require_admin
from ..schemas import ActivityOut, ActivityWithShifts

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


class ShiftIn(BaseModel):
    post_name: str = Field(min_length=1, max_length=50)
    location: str = Field(default="", max_length=100)
    start_time: datetime
    end_time: datetime
    capacity: int = Field(gt=0, le=999)

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v: datetime, info):
        start = info.data.get("start_time")
        if start and v <= start:
            raise ValueError("结束时间必须晚于开始时间")
        return v


class ActivityCreate(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=5000)
    signup_deadline: datetime | None = None
    status: str = Field(default="draft", pattern="^(draft|open|closed)$")
    shifts: list[ShiftIn] = Field(min_length=1)


class StatusUpdate(BaseModel):
    status: str = Field(pattern="^(draft|open|closed|archived)$")


@router.post("/activities", response_model=ActivityWithShifts, status_code=201)
def create_activity(body: ActivityCreate, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    activity = Activity(
        title=body.title,
        description=body.description,
        signup_deadline=body.signup_deadline,
        status=body.status,
        created_by=user.id,
    )
    db.add(activity)
    db.flush()
    for s in body.shifts:
        db.add(
            Shift(
                activity_id=activity.id,
                post_name=s.post_name,
                location=s.location,
                start_time=s.start_time,
                end_time=s.end_time,
                capacity=s.capacity,
            )
        )
    db.commit()
    return db.scalar(
        select(Activity).options(selectinload(Activity.shifts)).where(Activity.id == activity.id)
    )


@router.get("/activities", response_model=list[ActivityWithShifts])
def list_all_activities(db: Session = Depends(get_db)):
    """后台列表：含草稿/关闭，全量倒序。"""
    return db.scalars(
        select(Activity).options(selectinload(Activity.shifts)).order_by(Activity.id.desc())
    ).all()


@router.post("/activities/{activity_id}/status", response_model=ActivityOut)
def update_status(activity_id: int, body: StatusUpdate, db: Session = Depends(get_db)):
    activity = db.get(Activity, activity_id)
    if activity is None:
        raise HTTPException(status_code=404, detail="活动不存在")
    activity.status = body.status
    db.commit()
    db.refresh(activity)
    return activity


@router.get("/activities/{activity_id}/roster")
def roster(activity_id: int, db: Session = Depends(get_db)):
    """报名名单：按场次分组，含志愿者联系方式，供现场核对。"""
    activity = db.get(Activity, activity_id)
    if activity is None:
        raise HTTPException(status_code=404, detail="活动不存在")
    shifts = db.scalars(select(Shift).where(Shift.activity_id == activity_id)).all()
    result = []
    for s in shifts:
        rows = db.execute(
            select(ShiftSignup, Member)
            .join(Member, Member.id == ShiftSignup.member_id)
            .where(ShiftSignup.shift_id == s.id)
            .order_by(ShiftSignup.created_at)
        ).all()
        result.append(
            {
                "shift_id": s.id,
                "post_name": s.post_name,
                "location": s.location,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat(),
                "capacity": s.capacity,
                "booked_count": s.booked_count,
                "signups": [
                    {
                        "signup_id": su.id,
                        "name": m.name,
                        "student_id": m.student_id,
                        "college": m.college,
                        "phone": m.phone,
                        "status": su.status,
                        "remark": su.remark,
                        "created_at": su.created_at.isoformat(),
                    }
                    for su, m in rows
                ],
            }
        )
    return {"activity_id": activity.id, "title": activity.title, "status": activity.status, "shifts": result}
