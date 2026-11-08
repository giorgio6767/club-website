"""报名接口验收测试：对应需求文档与 services/signup.py 的规则清单。

统一通过 API 建活动/场次（走后台接口），再走公开报名接口，
保证测试覆盖的就是真实链路。
"""
from datetime import datetime, timedelta

import pytest

FUTURE = datetime(2026, 11, 16, 9, 0)  # 活动日：11-16


@pytest.fixture()
def admin_headers(client, db):
    from app.models import User
    from app.security import hash_password

    db.add(User(username="admin", password_hash=hash_password("admin-pass-123"),
                display_name="管理员", role="admin"))
    db.commit()
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin-pass-123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_activity(client, admin_headers, *, status="open", shifts, deadline=None):
    body = {
        "title": "十一月无偿献血志愿服务",
        "description": "校医院门口献血车引导",
        "status": status,
        "shifts": shifts,
    }
    if deadline:
        body["signup_deadline"] = deadline.isoformat()
    resp = client.post("/api/admin/activities", json=body, headers=admin_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def signup(client, activity_id, shift_ids, **kw):
    payload = {
        "name": kw.get("name", "张三"),
        "student_id": kw.get("student_id", "20230101"),
        "college": kw.get("college", "材料学院"),
        "phone": kw.get("phone", "13800000001"),
        "shift_ids": shift_ids,
    }
    return client.post(f"/api/activities/{activity_id}/signups", json=payload)


def test_signup_success_and_auto_member(client, admin_headers):
    """验收5：学号不存在 → 自动建档；正常多选场次成功。"""
    shifts = [
        {"post_name": "引导岗", "location": "校医院", "start_time": "2026-11-16T09:00:00",
         "end_time": "2026-11-16T12:00:00", "capacity": 3},
        {"post_name": "搀扶岗", "location": "校医院", "start_time": "2026-11-16T13:00:00",
         "end_time": "2026-11-16T16:00:00", "capacity": 2},
    ]
    activity = make_activity(client, admin_headers, shifts=shifts)
    resp = signup(client, activity["id"], [s["id"] for s in activity["shifts"]])
    assert resp.status_code == 200, resp.text
    assert resp.json()["booked_shift_ids"] == [s["id"] for s in activity["shifts"]]

    # 名单里能看到自动建档的成员信息
    roster = client.get(f"/api/admin/activities/{activity['id']}/roster", headers=admin_headers)
    assert roster.status_code == 200
    all_signups = [x for sh in roster.json()["shifts"] for x in sh["signups"]]
    assert len(all_signups) == 2
    assert all_signups[0]["student_id"] == "20230101"
    assert all_signups[0]["college"] == "材料学院"


def test_capacity_full_409(client, admin_headers):
    """验收1：名额不足 → 409。"""
    activity = make_activity(client, admin_headers, shifts=[
        {"post_name": "引导岗", "start_time": "2026-11-16T09:00:00",
         "end_time": "2026-11-16T12:00:00", "capacity": 1},
    ])
    sid = activity["shifts"][0]["id"]
    assert signup(client, activity["id"], [sid]).status_code == 200
    resp = signup(client, activity["id"], [sid], student_id="20230102", phone="13800000002")
    assert resp.status_code == 409
    assert "已满" in resp.json()["detail"]


def test_duplicate_signup_409(client, admin_headers):
    """验收2：同人同场次重复报名 → 409。"""
    activity = make_activity(client, admin_headers, shifts=[
        {"post_name": "引导岗", "start_time": "2026-11-16T09:00:00",
         "end_time": "2026-11-16T12:00:00", "capacity": 5},
    ])
    sid = activity["shifts"][0]["id"]
    assert signup(client, activity["id"], [sid]).status_code == 200
    assert signup(client, activity["id"], [sid]).status_code == 409


def test_overlap_within_batch_409(client, admin_headers):
    """验收3a：本次多选内部时段重叠 → 409。"""
    activity = make_activity(client, admin_headers, shifts=[
        {"post_name": "引导岗", "start_time": "2026-11-16T09:00:00",
         "end_time": "2026-11-16T12:00:00", "capacity": 5},
        {"post_name": "登记岗", "start_time": "2026-11-16T10:00:00",
         "end_time": "2026-11-16T14:00:00", "capacity": 5},
    ])
    ids = [s["id"] for s in activity["shifts"]]
    resp = signup(client, activity["id"], ids)
    assert resp.status_code == 409
    assert "时段冲突" in resp.json()["detail"]


def test_overlap_with_existing_booking_409(client, admin_headers):
    """验收3b：与已有报名时段重叠 → 409；相邻时段（12:00 结束/12:00 开始）不冲突。"""
    activity = make_activity(client, admin_headers, shifts=[
        {"post_name": "上午岗", "start_time": "2026-11-16T09:00:00",
         "end_time": "2026-11-16T12:00:00", "capacity": 5},
        {"post_name": "重叠岗", "start_time": "2026-11-16T11:00:00",
         "end_time": "2026-11-16T14:00:00", "capacity": 5},
        {"post_name": "下午岗", "start_time": "2026-11-16T12:00:00",
         "end_time": "2026-11-16T15:00:00", "capacity": 5},
    ])
    am, overlap, pm = [s["id"] for s in activity["shifts"]]
    assert signup(client, activity["id"], [am]).status_code == 200
    assert signup(client, activity["id"], [overlap]).status_code == 409
    assert signup(client, activity["id"], [am, pm]).status_code == 409  # 与已有 am 冲突
    # 单独报下午岗：相邻不冲突
    assert signup(client, activity["id"], [pm]).status_code == 200


def test_activity_not_open_or_expired_400(client, admin_headers):
    """验收4：草稿活动 / 过截止 → 400。"""
    shifts = [{"post_name": "引导岗", "start_time": "2026-11-16T09:00:00",
               "end_time": "2026-11-16T12:00:00", "capacity": 5}]
    draft = make_activity(client, admin_headers, status="draft", shifts=shifts)
    assert signup(client, draft["id"], [draft["shifts"][0]["id"]]).status_code == 400

    past = datetime.now() - timedelta(hours=1)  # 截止时间已过
    expired = make_activity(client, admin_headers, shifts=shifts, deadline=past)
    resp = signup(client, expired["id"], [expired["shifts"][0]["id"]])
    assert resp.status_code == 400
    assert "截止" in resp.json()["detail"]


def test_shift_from_other_activity_404(client, admin_headers):
    a1 = make_activity(client, admin_headers, shifts=[
        {"post_name": "A活动岗", "start_time": "2026-11-16T09:00:00",
         "end_time": "2026-11-16T12:00:00", "capacity": 5},
    ])
    a2 = make_activity(client, admin_headers, shifts=[
        {"post_name": "B活动岗", "start_time": "2026-11-16T09:00:00",
         "end_time": "2026-11-16T12:00:00", "capacity": 5},
    ])
    other = a2["shifts"][0]["id"]
    resp = signup(client, a1["id"], [other])
    assert resp.status_code == 404
    assert "不属于" in resp.json()["detail"]


def test_bad_payload_422(client, admin_headers):
    activity = make_activity(client, admin_headers, shifts=[
        {"post_name": "引导岗", "start_time": "2026-11-16T09:00:00",
         "end_time": "2026-11-16T12:00:00", "capacity": 5},
    ])
    # 手机号格式错误
    resp = signup(client, activity["id"], [activity["shifts"][0]["id"]], phone="12345")
    assert resp.status_code == 422
    # 空场次
    resp = signup(client, activity["id"], [])
    assert resp.status_code == 422
