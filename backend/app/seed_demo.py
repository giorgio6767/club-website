"""生成验收用演示活动（幂等：已存在同名活动就跳过）。

用法：uv run python -m app.seed_demo
再启动：uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
手机 QQ 打开 http://<电脑局域网IP>:8000 即可验收。
"""
from datetime import datetime, timedelta

from sqlalchemy import select

from .database import Base, SessionLocal, engine
from .models import Activity, Shift


def main() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        exists = db.scalar(select(Activity).where(Activity.title == "演示·无偿献血志愿服务"))
        if exists:
            print("演示活动已存在，跳过")
            return
        base = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=7)
        activity = Activity(
            title="演示·无偿献血志愿服务",
            description="这是验收用演示活动：试试多选场次、重复提交、重叠时段，看系统怎么拦。",
            status="open",
            signup_deadline=base + timedelta(days=5),
        )
        db.add(activity)
        db.flush()
        db.add_all(
            [
                Shift(activity_id=activity.id, post_name="引导岗", location="校医院门口",
                      start_time=base + timedelta(hours=9), end_time=base + timedelta(hours=12),
                      capacity=3),
                Shift(activity_id=activity.id, post_name="登记岗", location="献血车旁",
                      start_time=base + timedelta(hours=10), end_time=base + timedelta(hours=14),
                      capacity=2),  # 与引导岗重叠，用来验证冲突拦截
                Shift(activity_id=activity.id, post_name="搀扶岗", location="献血车旁",
                      start_time=base + timedelta(hours=12), end_time=base + timedelta(hours=15),
                      capacity=2),  # 与引导岗相邻不冲突，可同时报
            ]
        )
        db.commit()
        print(f"已创建演示活动 id={activity.id}")


if __name__ == "__main__":
    main()
