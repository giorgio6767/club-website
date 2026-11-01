"""全局配置。秘密信息一律走环境变量，不进仓库。"""
from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # 开发期 SQLite；上线前切 PostgreSQL，只改这一个变量
    database_url: str = f"sqlite:///{BASE_DIR / 'club.db'}"

    # JWT；生产环境必须用环境变量覆盖
    jwt_secret: str = "dev-only-change-me"
    jwt_expire_minutes: int = 12 * 60

    # 智谱问答（M4 接入暖暖抽离的问答服务时使用）
    zhipu_api_key: str = ""

    model_config = {"env_file": BASE_DIR / ".env", "extra": "ignore"}


settings = Settings()
