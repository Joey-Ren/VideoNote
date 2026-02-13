"""笔记生成服务 — 使用 AI 将转录文本生成结构化笔记"""

import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator

from app.config import settings
from app.core.ai_client import get_ai_client
from app.models.schemas import NoteResult
from app.utils.text import chunk_text

logger = logging.getLogger(__name__)

_tasks: dict[str, dict] = {}

NOTE_SYSTEM_PROMPT = """你是一个专业的视频笔记助手。请根据视频转录文本生成结构化的 Markdown 笔记。

要求：
1. 提取核心要点，用简洁的语言总结
2. 使用清晰的层级结构（标题、小标题、列表）
3. 保留关键数据、引用和重要细节
4. 最后给出简短总结
5. 使用中文输出

输出格式：
# 视频标题（根据内容推断）

## 核心要点
- 要点1
- 要点2
...

## 详细内容
### 主题1
...

### 主题2
...

## 总结
..."""


class NoteService:
    """AI 笔记生成服务"""

    async def generate(self, text: str, language: str = "zh") -> str:
        """生成笔记，返回 task_id"""
        task_id = str(uuid.uuid4())[:8]

        _tasks[task_id] = {
            "status": "processing",
            "progress": 0,
            "result": None,
            "markdown_chunks": [],
        }

        asyncio.create_task(self._run_generate(task_id, text, language))

        logger.info("笔记生成任务已创建: %s", task_id)
        return task_id

    async def _run_generate(
        self, task_id: str, text: str, language: str
    ) -> None:
        """执行 AI 笔记生成"""
        task = _tasks.get(task_id)
        if not task:
            return

        try:
            client = get_ai_client()
            chunks = chunk_text(text, chunk_size=8000, overlap=200)

            # 如果文本较短，直接一次性生成
            if len(chunks) == 1:
                content = chunks[0]
            else:
                # 长文本：先分块摘要，再合并
                summaries: list[str] = []
                for i, chunk in enumerate(chunks):
                    task["progress"] = int((i / len(chunks)) * 60)
                    resp = await client.chat.completions.create(
                        model=settings.openai_model,
                        messages=[
                            {"role": "system", "content": "请简洁总结以下视频转录片段的核心内容，保留关键信息："},
                            {"role": "user", "content": chunk},
                        ],
                        temperature=0.3,
                    )
                    summaries.append(resp.choices[0].message.content or "")
                content = "\n\n".join(summaries)

            # 生成最终笔记（流式）
            task["progress"] = 70
            markdown_parts: list[str] = []

            stream = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": NOTE_SYSTEM_PROMPT},
                    {"role": "user", "content": f"请根据以下视频内容生成笔记：\n\n{content}"},
                ],
                temperature=0.3,
                stream=True,
            )

            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    markdown_parts.append(delta)
                    task["markdown_chunks"].append(delta)

            full_markdown = "".join(markdown_parts)
            task["progress"] = 100
            task["status"] = "completed"

            # 提取大纲（从 markdown 标题中提取）
            outline = [
                line.lstrip("#").strip()
                for line in full_markdown.split("\n")
                if line.startswith("## ")
            ]

            task["result"] = NoteResult(
                title=outline[0] if outline else "视频笔记",
                markdown=full_markdown,
                outline=outline,
            )
            logger.info("笔记生成完成: %s", task_id)

        except Exception as e:
            logger.error("笔记生成失败: %s - %s", task_id, e)
            task["status"] = "error"
            task["error"] = str(e)

    async def stream_result(self, task_id: str) -> AsyncGenerator[dict, None]:
        """流式推送笔记生成过程"""
        sent_index = 0
        while True:
            task = _tasks.get(task_id)
            if not task:
                yield {"status": "error", "message": "任务不存在"}
                return

            # 推送新的 markdown 片段
            chunks = task.get("markdown_chunks", [])
            if sent_index < len(chunks):
                new_content = "".join(chunks[sent_index:])
                sent_index = len(chunks)
                yield {"status": "streaming", "content": new_content}

            if task["status"] == "completed":
                yield {"status": "completed"}
                return

            if task["status"] == "error":
                yield {"status": "error", "message": task.get("error", "未知错误")}
                return

            await asyncio.sleep(0.2)

    async def get_result(self, task_id: str) -> NoteResult | None:
        """获取笔记结果"""
        task = _tasks.get(task_id)
        if not task or task["status"] != "completed":
            return None
        return task["result"]
