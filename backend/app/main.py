"""VideoNote 后端 - FastAPI 应用入口"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import video, transcribe, note, qa, download, settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    # 启动时
    print("🚀 VideoNote 后端启动中...")
    yield
    # 关闭时
    print("👋 VideoNote 后端已关闭")


app = FastAPI(
    title="VideoNote API",
    description="视频转笔记 API 服务",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 中间件（开发环境允许所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(video.router, prefix="/api/video", tags=["视频"])
app.include_router(transcribe.router, prefix="/api/transcribe", tags=["转录"])
app.include_router(note.router, prefix="/api/note", tags=["笔记"])
app.include_router(qa.router, prefix="/api/qa", tags=["问答"])
app.include_router(download.router, prefix="/api/download", tags=["下载"])
app.include_router(settings.router, prefix="/api/settings", tags=["设置"])


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """健康检查"""
    return {"status": "ok", "service": "videonote-backend"}
