# 红十字会学生分会网站

校红十字会学生分会官方网站 + 业务系统：场次制活动报名（防超卖/防时段冲突）、桂志愿数据核对与时长结算、RAG 智能问答（QQ/Web 双入口）。

- 需求与系统边界：`docs/需求文档.md`
- 数据库设计（ER 图 + 6 张表）：`docs/数据库设计.md`
- 技术栈：FastAPI + SQLAlchemy + SQLite(→PostgreSQL)；Next.js + Tailwind

## 快速启动

后端（需已安装 [uv](https://docs.astral.sh/uv/)）：

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload   # 接口文档 http://127.0.0.1:8000/docs
uv run pytest                          # 测试
```

前端：

```bash
cd frontend
npm install
npm run dev                            # http://localhost:3000
```

## 目录结构

```
backend/          FastAPI 后端
  app/models.py     六张表（users/members/activities/shifts/shift_signups/sign_records/news 中 users+news 属辅助）
  app/routers/      接口路由（activities 已可用，signups/auth/settlement 为 M1/M5 占位）
  tests/            pytest（conftest 用内存 SQLite）
frontend/         Next.js 前端（M0 仅占位首页）
docs/             需求文档、数据库设计
```

## 路线图

M0 骨架 ✓ → M1 后端 API（W02–W03）→ M2 前端（W04–W05）→ M3 部署（W06）→ M4 问答（W07–W08）→ M5 核对结算/向量检索（W09+）
