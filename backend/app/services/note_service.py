"""笔记生成服务 — 使用 AI 将转录文本生成结构化笔记"""

import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator

from app.models.schemas import NoteResult

logger = logging.getLogger(__name__)

_tasks: dict[str, dict] = {}


class NoteService:
    """AI 笔记生成服务"""

    async def generate(self, text: str, language: str = "zh") -> str:
        """生成笔记，返回 task_id"""
        task_id = str(uuid.uuid4())[:8]

        _tasks[task_id] = {
            "status": "processing",
            "progress": 0,
            "result": None,
        }

        # TODO: 实现真实 AI 笔记生成
        # 1. 文本分块（长文本处理）
        # 2. 调用 OpenAI 生成摘要
        # 3. 合并生成最终笔记

        asyncio.create_task(self._mock_generate(task_id, text))

        logger.info("笔记生成任务已创建: %s", task_id)
        return task_id

    async def _mock_generate(self, task_id: str, text: str) -> None:
        """模拟笔记生成（开发用）"""
        task = _tasks.get(task_id)
        if not task:
            return

        await asyncio.sleep(2)

        task["status"] = "completed"
        task["result"] = NoteResult(
            title="视频笔记",
            markdown=f"""# 视频笔记

## 核心要点

- 这是 AI 自动生成的笔记内容
- 连接 OpenAI API 后将生成真实笔记
- 支持结构化输出和 Markdown 格式

## 详细内容

{text[:200]}...

## 总结

以上是视频的主要内容总结。
""",
            outline=["核心要点", "详细内容", "总结"],
        )

    async def stream_result(self, task_id: str) -> AsyncGenerator[dict, None]:
        """流式推送笔记生成过程"""
        while True:
            task = _tasks.get(task_id)
            if not task:
                yield {"status": "error", "message": "任务不存在"}
                return

            if task["status"] == "completed" and task["result"]:
                yield {
                    "status": "completed",
                    "markdown": task["result"].markdown,
                }
                return

            yield {"status": "processing", "message": "笔记生成中..."}
            await asyncio.sleep(1)

    async def get_result(self, task_id: str) -> NoteResult | None:
        """获取笔记结果"""
        task = _tasks.get(task_id)
        if not task or task["status"] != "completed":
            return None
        return task["result"]
