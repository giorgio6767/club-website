"""占位：后段核对结算 M5 实现。

验收（M5）：
- POST /import：上传桂志愿导出 Excel，解析/校验/幂等（import_batch 去重）
- GET /diff/{activity_id}：桂志愿 vs 纸质 差集 → 异常清单
- GET /report/monthly：窗口函数月度时长报表
"""
from fastapi import APIRouter

router = APIRouter(prefix="/settlement", tags=["settlement"])
