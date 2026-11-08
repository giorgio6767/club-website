"""鉴权与后台接口测试。"""
from app.models import User
from app.security import hash_password


def login(client, username="admin", password="admin-pass-123"):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def admin_headers(client, db):
    db.add(User(username="admin", password_hash=hash_password("admin-pass-123"),
                display_name="管理员", role="admin"))
    db.commit()
    resp = login(client)
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_login_wrong_password_401(client, db):
    db.add(User(username="admin", password_hash=hash_password("admin-pass-123"),
                display_name="管理员", role="admin"))
    db.commit()
    assert login(client, password="wrong").status_code == 401
    assert login(client, username="nobody").status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_with_token(client, db):
    headers = admin_headers(client, db)
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"username": "admin", "role": "admin", "display_name": "管理员"}


def test_admin_requires_auth(client):
    assert client.get("/api/admin/activities").status_code == 401
    assert client.post("/api/admin/activities", json={}).status_code == 401


def test_create_activity_and_public_list(client, db):
    headers = admin_headers(client, db)
    resp = client.post("/api/admin/activities", json={
        "title": "十一月无偿献血志愿服务",
        "description": "引导",
        "status": "open",
        "shifts": [
            {"post_name": "引导岗", "location": "校医院",
             "start_time": "2026-11-16T09:00:00", "end_time": "2026-11-16T12:00:00",
             "capacity": 3},
        ],
    }, headers=headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["shifts"][0]["booked_count"] == 0

    # 草稿不出现在公开列表
    client.post("/api/admin/activities", json={
        "title": "草稿活动", "status": "draft",
        "shifts": [{"post_name": "岗", "start_time": "2026-11-16T09:00:00",
                    "end_time": "2026-11-16T12:00:00", "capacity": 1}],
    }, headers=headers)
    public = client.get("/api/activities").json()
    assert [a["title"] for a in public] == ["十一月无偿献血志愿服务"]

    # 结束时间早于开始时间 → 422
    bad = client.post("/api/admin/activities", json={
        "title": "坏活动", "status": "open",
        "shifts": [{"post_name": "岗", "start_time": "2026-11-16T12:00:00",
                    "end_time": "2026-11-16T09:00:00", "capacity": 1}],
    }, headers=headers)
    assert bad.status_code == 422
