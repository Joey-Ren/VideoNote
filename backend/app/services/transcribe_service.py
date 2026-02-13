"""音频转录服务 — 使用 Faster-Whisper 本地转录"""

import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator

from app.models.schemas import TranscriptionResult, TranscriptionSegment

logger = logging.getLogger(__name__)

# 内存中的任务存储（MVP 阶段）
_tasks: dict[str, dict] = {}


class TranscribeService:
    """音频转录服务"""

    async def start(
        self,
        url: str | None = None,
        local_path: str | None = None,
    ) -> str:
        """开始转录任务，返回 task_id"""
        task_id = str(uuid.uuid4())[:8]

        # TODO: 实现真实转录流程
        # 1. 下载视频 / 读取本地文件
        # 2. 提取音频 (ffmpeg)
        # 3. Whisper 转录
        # 4. 更新进度

        _tasks[task_id] = {
            "status": "processing",
            "progress": 0,
            "source": url or local_path,
            "result": None,
        }

        # 模拟异步转录过程
        asyncio.create_task(self._mock_transcribe(task_id))

        logger.info("转录任务已创建: %s", task_id)
        return task_id

    async def _mock_transcribe(self, task_id: str) -> None:
        """模拟转录过程（开发用）"""
        task = _tasks.get(task_id)
        if not task:
            return

        for i in range(1, 11):
            await asyncio.sleep(0.5)
            task["progress"] = i * 10

        task["status"] = "completed"
        task["result"] = TranscriptionResult(
            text="这是一段模拟的转录文本。当后端连接 Whisper 模型后，这里会显示真实的转录内容。",
            segments=[
                TranscriptionSegment(start=0.0, end=5.0, text="这是一段模拟的转录文本。"),
                TranscriptionSegment(start=5.0, end=10.0, text="当后端连接 Whisper 模型后，"),
                TranscriptionSegment(start=10.0, end=15.0, text="这里会显示真实的转录内容。"),
            ],
            language="zh",
            duration=15.0,
        )

    async def get_progress(self, task_id: str) -> AsyncGenerator[dict, None]:
        """SSE 推送转录进度"""
        while True:
            task = _tasks.get(task_id)
            if not task:
                yield {"status": "error", "message": "任务不存在", "progress": 0}
                return

            yield {
                "status": task["status"],
                "progress": task["progress"],
                "message": f"转录中... {task['progress']}%",
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
