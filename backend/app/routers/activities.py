from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Activity
from ..schemas import ActivityOut, ActivityWithShifts

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("", response_model=list[ActivityOut])
def list_activities(status: str = "open", db: Session = Depends(get_db)):
    """前台活动列表：默认只展示开放报名的，按创建时间倒序。"""
    stmt = select(Activity).where(Activity.status == status).order_by(Activity.id.desc())
    return db.scalars(stmt).all()


@router.get("/{activity_id}", response_model=ActivityWithShifts)
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    """活动详情（含场次）。M1 在此补报名截止判断。"""
    activity = db.get(Activity, activity_id)
    if activity is None:
        raise HTTPException(status_code=404, detail="活动不存在")
    return activity
