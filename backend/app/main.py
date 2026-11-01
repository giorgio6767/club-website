from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from .database import Base, engine
from .routers import api_router


def init_db() -> None:
    """开发期建表。M1 引入 Alembic 后此函数只留给测试环境。"""
    Base.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="红十字会学生分会网站", version="0.1.0", lifespan=lifespan)
    app.include_router(api_router)

    @app.get("/api/health")
    def health():
        # 连库探活：M3 部署后由监控/看门狗调用
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}

    return app


def init_db() -> None:
    """开发期建表。M1 引入 Alembic 后此函数只留给测试环境。"""
    Base.metadata.create_all(engine)


app = create_app()
