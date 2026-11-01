"""冒烟测试：应用能起、健康检查连库、活动接口基本可用。"""
from datetime import datetime


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_activity_crud_min(client, db):
    from app.models import Activity, Shift

    activity = Activity(title="十月无偿献血志愿服务", status="open")
    db.add(activity)
    db.flush()
    db.add(
        Shift(
            activity_id=activity.id,
            post_name="引导岗",
            location="校医院门口",
            start_time=datetime(2026, 11, 8, 9, 0),
            end_time=datetime(2026, 11, 8, 12, 0),
            capacity=3,
        )
    )
    db.commit()

    resp = client.get("/api/activities")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1 and body[0]["title"].startswith("十月")

    detail = client.get(f"/api/activities/{activity.id}")
    assert detail.status_code == 200
    assert detail.json()["shifts"][0]["post_name"] == "引导岗"

    assert client.get("/api/activities/9999").status_code == 404
