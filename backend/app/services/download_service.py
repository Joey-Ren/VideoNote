"""视频下载服务 — 使用 yt-dlp 下载视频"""

import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)

_tasks: dict[str, dict] = {}


class DownloadService:
    """视频下载服务"""

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

        # TODO: 实现真实下载
        # 1. 使用 yt-dlp 下载
        # 2. 实时更新进度
        # 3. 保存到 temp 目录

        asyncio.create_task(self._mock_download(task_id))

        logger.info("下载任务已创建: %s (%s, %s)", task_id, format, quality)
        return task_id

    async def _mock_download(self, task_id: str) -> None:
        """模拟下载过程（开发用）"""
        task = _tasks.get(task_id)
        if not task:
            return

        for i in range(1, 11):
            await asyncio.sleep(0.3)
            task["progress"] = i * 10

        task["status"] = "completed"
        task["file_path"] = f"./temp/{task_id}.mp4"

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
