"""Pydantic 模型（请求/响应体）。M1 按接口逐个补全。"""
from datetime import datetime

from pydantic import BaseModel


class ShiftOut(BaseModel):
    id: int
    post_name: str
    location: str
    start_time: datetime
    end_time: datetime
    capacity: int
    booked_count: int

    model_config = {"from_attributes": True}


class ActivityOut(BaseModel):
    id: int
    title: str
    description: str
    status: str
    signup_deadline: datetime | None

    model_config = {"from_attributes": True}


class ActivityWithShifts(ActivityOut):
    shifts: list[ShiftOut] = []
