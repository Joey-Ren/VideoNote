"""Pydantic 数据模型"""

from pydantic import BaseModel


# ============================================
# 请求模型
# ============================================

class VideoPreviewRequest(BaseModel):
    """视频预览请求"""
    url: str


class TranscribeRequest(BaseModel):
    """转录请求"""
    url: str | None = None
    local_path: str | None = None


class NoteGenerateRequest(BaseModel):
    """笔记生成请求"""
    transcription_text: str
    language: str = "zh"


class QARequest(BaseModel):
    """视频问答请求"""
    video_url: str
    question: str
    context: str | None = None


class DownloadRequest(BaseModel):
    """视频下载请求"""
    url: str
    format: str = "mp4"
    quality: str = "best"


# ============================================
# 响应模型
# ============================================

class VideoInfo(BaseModel):
    """视频信息"""
    title: str
    thumbnail: str | None = None
    duration: int  # 秒
    platform: str
    url: str


class TranscriptionSegment(BaseModel):
    """转录片段"""
    start: float
    end: float
    text: str


class TranscriptionResult(BaseModel):
    """转录结果"""
    text: str
    segments: list[TranscriptionSegment]
    language: str
    duration: float


class NoteResult(BaseModel):
    """笔记结果"""
    markdown: str
    title: str
    outline: list[str]


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: str
    message: str
