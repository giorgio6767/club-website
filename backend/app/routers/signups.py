"""占位：报名接口 M1 实现，核心规则先落在这里做验收标准。

POST /shifts/{shift_id}/signups 的验收（M1）：
1. 库存不足 → 409
2. 同人同场次重复报名 → 409（唯一约束兜底）
3. 同人时段重叠 → 409
4. 活动非 open 或过截止 → 400
5. 学号不存在 → 自动建档 members
"""
from fastapi import APIRouter

router = APIRouter(prefix="/shifts", tags=["signups"])


@router.get("/{shift_id}/signups")
def list_signups(shift_id: int):
    """各场次报名名单（M1：干事鉴权后开放）。"""
    return {"shift_id": shift_id, "signups": []}
