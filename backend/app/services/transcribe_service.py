"""音频转录服务 — 使用 Faster-Whisper 本地转录"""

import asyncio
import logging
import os
import tempfile
import uuid
from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor

import yt_dlp

from app.config import settings
from app.core.whisper_client import get_whisper_model
from app.models.schemas import TranscriptionResult, TranscriptionSegment
from app.utils.ytdlp import build_ydl_opts

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)
_tasks: dict[str, dict] = {}


class TranscribeService:
    """音频转录服务"""

    def _download_audio_sync(self, url: str, output_dir: str) -> str:
        output_path = os.path.join(output_dir, "audio.%(ext)s")
        extra = {
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],
        }
        opts = build_ydl_opts(url, extra)
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        # 找到生成的 wav 文件
        for f in os.listdir(output_dir):
            if f.endswith(".wav"):
                return os.path.join(output_dir, f)

        raise FileNotFoundError("音频提取失败")

    def _transcribe_sync(self, audio_path: str, task: dict) -> TranscriptionResult:
        """Whisper 转录（同步，线程池中运行）"""
        model = get_whisper_model()

        segments_raw, info = model.transcribe(
            audio_path,
            beam_size=5,
            vad_filter=True,
        )

        segments: list[TranscriptionSegment] = []
        full_text_parts: list[str] = []
        total_duration = info.duration or 1.0

        for seg in segments_raw:
            segments.append(
                TranscriptionSegment(
                    start=round(seg.start, 2),
                    end=round(seg.end, 2),
                    text=seg.text.strip(),
                )
            )
            full_text_parts.append(seg.text.strip())
            # 更新进度（10% ~ 90%）
            progress = min(90, 10 + int((seg.end / total_duration) * 80))
            task["progress"] = progress

        return TranscriptionResult(
            text="\n".join(full_text_parts),
            segments=segments,
            language=info.language or "unknown",
            duration=round(total_duration, 2),
        )

    async def start(
        self,
        url: str | None = None,
        local_path: str | None = None,
    ) -> str:
        """开始转录任务，返回 task_id"""
        task_id = str(uuid.uuid4())[:8]

        _tasks[task_id] = {
            "status": "processing",
            "progress": 0,
            "source": url or local_path,
            "result": None,
        }

        asyncio.create_task(self._run_transcription(task_id, url, local_path))

        logger.info("转录任务已创建: %s", task_id)
        return task_id

    async def _run_transcription(
        self,
        task_id: str,
        url: str | None,
        local_path: str | None,
    ) -> None:
        """执行完整转录流程"""
        task = _tasks.get(task_id)
        if not task:
            return

        loop = asyncio.get_event_loop()
        os.makedirs(settings.temp_dir, exist_ok=True)
        tmp_dir = tempfile.mkdtemp(dir=settings.temp_dir)

        try:
            # 步骤 1: 获取音频文件
            if local_path and os.path.isfile(local_path):
                audio_path = local_path
                task["progress"] = 10
            elif url:
                task["progress"] = 2
                audio_path = await loop.run_in_executor(
                    _executor, self._download_audio_sync, url, tmp_dir
                )
                task["progress"] = 10
            else:
                raise ValueError("请提供视频 URL 或本地文件路径")

            # 步骤 2: Whisper 转录
            result = await loop.run_in_executor(
                _executor, self._transcribe_sync, audio_path, task
            )

            task["progress"] = 100
            task["status"] = "completed"
            task["result"] = result
            logger.info("转录完成: %s (%.1f秒)", task_id, result.duration)

        except Exception as e:
            logger.error("转录失败: %s - %s", task_id, e)
            task["status"] = "error"
            task["progress"] = 0
            task["error"] = str(e)

    async def get_progress(self, task_id: str) -> AsyncGenerator[dict, None]:
        """SSE 推送转录进度"""
        while True:
            task = _tasks.get(task_id)
            if not task:
                yield {"status": "error", "message": "任务不存在", "progress": 0}
                return

            msg = f"转录中... {task['progress']}%"
            if task["progress"] < 10:
                msg = "正在下载音频..."
            elif task["progress"] >= 100:
                msg = "转录完成"

            yield {
                "status": task["status"],
                "progress": task["progress"],
                "message": msg,
            }

            if task["status"] in ("completed", "error"):
                return

            await asyncio.sleep(0.5)

    async def get_result(self, task_id: str) -> TranscriptionResult | None:
        """获取转录结果"""
        task = _tasks.get(task_id)
        if not task or task["status"] != "completed":
            return None
        return task["result"]
