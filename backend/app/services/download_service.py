"""视频下载服务 — 使用 yt-dlp 下载视频"""

import asyncio
import logging
import os
import uuid
from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor

import yt_dlp

from app.config import settings

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)
_tasks: dict[str, dict] = {}


class DownloadService:
    """视频下载服务"""

    def _build_ydl_opts(
        self, task_id: str, task: dict, output_dir: str, fmt: str, quality: str
    ) -> dict:
        """构建 yt-dlp 下载选项"""
        output_path = os.path.join(output_dir, f"{task_id}.%(ext)s")

        quality_map = {
            "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
            "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
            "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]",
        }

        opts: dict = {
            "outtmpl": output_path,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [lambda d: self._progress_hook(d, task)],
        }

        if fmt == "mp3":
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]
        else:
            opts["format"] = quality_map.get(quality, quality_map["best"])

        return opts

    def _progress_hook(self, d: dict, task: dict) -> None:
        """yt-dlp 下载进度回调"""
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                task["progress"] = min(95, int((downloaded / total) * 95))
        elif d["status"] == "finished":
            task["progress"] = 95

    def _download_sync(
        self, task_id: str, task: dict, url: str, fmt: str, quality: str
    ) -> str:
        """同步下载（线程池中运行）"""
        output_dir = os.path.join(settings.temp_dir, "downloads")
        os.makedirs(output_dir, exist_ok=True)

        opts = self._build_ydl_opts(task_id, task, output_dir, fmt, quality)

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        # 找到下载的文件
        for f in os.listdir(output_dir):
            if f.startswith(task_id):
                return os.path.join(output_dir, f)

        raise FileNotFoundError("下载文件未找到")

    async def start(self, url: str, format: str = "mp4", quality: str = "best") -> str:
        """开始下载任务，返回 task_id"""
        task_id = str(uuid.uuid4())[:8]

        _tasks[task_id] = {
            "status": "processing",
            "progress": 0,
            "url": url,
            "format": format,
            "quality": quality,
            "file_path": None,
        }

        asyncio.create_task(self._run_download(task_id))

        logger.info("下载任务已创建: %s (%s, %s)", task_id, format, quality)
        return task_id

    async def _run_download(self, task_id: str) -> None:
        """执行下载"""
        task = _tasks.get(task_id)
        if not task:
            return

        loop = asyncio.get_event_loop()

        try:
            file_path = await loop.run_in_executor(
                _executor,
                self._download_sync,
                task_id,
                task,
                task["url"],
                task["format"],
                task["quality"],
            )
            task["progress"] = 100
            task["status"] = "completed"
            task["file_path"] = file_path
            logger.info("下载完成: %s -> %s", task_id, file_path)

        except Exception as e:
            logger.error("下载失败: %s - %s", task_id, e)
            task["status"] = "error"
            task["error"] = str(e)

    async def get_progress(self, task_id: str) -> AsyncGenerator[dict, None]:
        """SSE 推送下载进度"""
        while True:
            task = _tasks.get(task_id)
            if not task:
                yield {"status": "error", "message": "任务不存在", "progress": 0}
                return

            yield {
                "status": task["status"],
                "progress": task["progress"],
                "message": f"下载中... {task['progress']}%",
            }

            if task["status"] in ("completed", "error"):
                return

            await asyncio.sleep(0.5)

    async def get_file_path(self, task_id: str) -> str | None:
        """获取下载文件路径"""
        task = _tasks.get(task_id)
        if not task or task["status"] != "completed":
            return None
        return task["file_path"]
