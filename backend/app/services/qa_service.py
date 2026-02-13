"""视频问答服务 — 基于转录内容的 AI 问答"""

import logging
from collections.abc import AsyncGenerator

from app.config import settings
from app.core.ai_client import get_ai_client

logger = logging.getLogger(__name__)

QA_SYSTEM_PROMPT = """你是一个视频内容问答助手。用户会提供视频的转录文本作为上下文，然后基于这些内容提问。

要求：
1. 只根据提供的视频内容回答，不要编造信息
2. 如果视频内容中没有相关信息，明确告知用户
3. 回答简洁准确，必要时引用视频中的原话
4. 使用中文回答"""


class QAService:
    """视频问答服务"""

    async def ask(
        self,
        question: str,
        context: str,
        video_url: str,
    ) -> AsyncGenerator[str, None]:
        """基于视频内容回答问题（流式输出）"""
        logger.info("问答请求: %s (视频: %s)", question, video_url)

        client = get_ai_client()

        messages: list[dict[str, str]] = [
            {"role": "system", "content": QA_SYSTEM_PROMPT},
        ]

        if context:
            messages.append(
                {"role": "user", "content": f"以下是视频的转录内容：\n\n{context}"}
            )
            messages.append(
                {"role": "assistant", "content": "好的，我已经阅读了视频内容。请问你有什么问题？"}
            )

        messages.append({"role": "user", "content": question})

        stream = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=0.5,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
