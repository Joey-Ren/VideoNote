"""视频问答服务 — 基于转录内容的 AI 问答"""

import logging
from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)


class QAService:
    """视频问答服务"""

    async def ask(
        self,
        question: str,
        context: str,
        video_url: str,
    ) -> AsyncGenerator[str, None]:
        """基于视频内容回答问题（流式输出）"""

        # TODO: 实现真实 AI 问答
        # 1. 如果没有 context，先转录视频
        # 2. 构建 prompt（system + context + question）
        # 3. 调用 OpenAI streaming chat
        # 4. 逐 chunk yield

        logger.info("问答请求: %s (视频: %s)", question, video_url)

        # Mock 流式响应
        mock_answer = f"这是对「{question}」的模拟回答。连接 OpenAI API 后，AI 将基于视频内容给出准确回答。"
        for char in mock_answer:
            yield char
