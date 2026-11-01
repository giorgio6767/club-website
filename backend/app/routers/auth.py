"""占位：鉴权 M1 实现。验收：JWT 登录、角色依赖注入（staff/admin）。"""
from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
def me():
    """M1：解码 JWT 返回当前用户，未登录返回 401。"""
    return {"detail": "M1 实现"}
