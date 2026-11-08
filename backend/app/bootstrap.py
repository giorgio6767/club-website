"""创建首个管理员账号（部署时在服务器上跑一次）。

用法：uv run python -m app.bootstrap <用户名> <密码>
账号已存在则重置其密码。
"""
import sys

from .database import Base, SessionLocal, engine
from .models import User
from .security import hash_password


def main() -> None:
    if len(sys.argv) != 3:
        print("用法: uv run python -m app.bootstrap <用户名> <密码>")
        raise SystemExit(1)
    username, password = sys.argv[1], sys.argv[2]
    if len(password) < 8:
        print("密码至少 8 位")
        raise SystemExit(1)

    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            db.add(User(username=username, password_hash=hash_password(password),
                        display_name=username, role="admin"))
            print(f"已创建管理员: {username}")
        else:
            user.password_hash = hash_password(password)
            user.role = "admin"
            print(f"已重置密码: {username}")
        db.commit()


if __name__ == "__main__":
    main()
