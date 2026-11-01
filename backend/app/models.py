"""六张表，对应 docs/数据库设计.md 的 ER 图。

约定：
- 时间一律存 naive UTC，由调用方负责转换
- 场次名额扣减走条件更新（见 services/signup.py，M1 实现）
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    """后台账号（干事/管理员）。志愿者不登录，见 members。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    display_name: Mapped[str] = mapped_column(String(50))
    role: Mapped[str] = mapped_column(String(20), default="staff")  # staff/admin
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Member(Base):
    """志愿者档案。首次报名时若学号不存在则自动建档。"""

    __tablename__ = "members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    student_id: Mapped[str] = mapped_column(String(20), unique=True)
    college: Mapped[str] = mapped_column(String(100), default="")
    phone: Mapped[str] = mapped_column(String(20), default="")
    served_seconds: Mapped[int] = mapped_column(Integer, default=0)  # 结算回写
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    cover_image: Mapped[str] = mapped_column(String(255), default="")
    signup_deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft/open/closed/archived
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    shifts: Mapped[list["Shift"]] = relationship(back_populates="activity")


class Shift(Base):
    """场次 = 电商 SKU：时间段 + 地点 + 岗位 + 名额（库存）。"""

    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), index=True)
    post_name: Mapped[str] = mapped_column(String(50))
    location: Mapped[str] = mapped_column(String(100), default="")
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)
    capacity: Mapped[int] = mapped_column(Integer)
    booked_count: Mapped[int] = mapped_column(Integer, default=0)

    activity: Mapped["Activity"] = relationship(back_populates="shifts")


class ShiftSignup(Base):
    __tablename__ = "shift_signups"
    __table_args__ = (UniqueConstraint("shift_id", "member_id", name="uq_shift_member"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shift_id: Mapped[int] = mapped_column(ForeignKey("shifts.id"), index=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="booked")  # booked/attended/absent/cancelled
    remark: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class SignRecord(Base):
    """签到签退记录。桂志愿导出与纸质录入共用一张表，source 区分来源。

    member_id 可空：导入时按学号/姓名匹配不上就留空，靠 raw_row 人工对账。
    """

    __tablename__ = "sign_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), index=True)
    member_id: Mapped[int | None] = mapped_column(ForeignKey("members.id"), nullable=True)
    member_name: Mapped[str] = mapped_column(String(50))
    check_in: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    check_out: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source: Mapped[str] = mapped_column(String(20))  # guizhiyuan/paper
    import_batch: Mapped[str] = mapped_column(String(50), index=True)
    raw_row: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    content_md: Mapped[str] = mapped_column(Text, default="")
    cover_image: Mapped[str] = mapped_column(String(255), default="")
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
