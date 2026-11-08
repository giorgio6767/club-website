from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
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

    # 临时报名页（11-08 局域网真机验收用）。11-09 上线 Next.js 后由 nginx 接管 /，
    # 此挂载自动失效，不用删。
    static_dir = Path(__file__).parent / "static"
    if (static_dir / "index.html").exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


app = create_app()
