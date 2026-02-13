"""OpenAI 客户端单例"""

from openai import AsyncOpenAI

from app.config import settings


class AIClient:
    """OpenAI 客户端，懒加载单例"""

    _instance: AsyncOpenAI | None = None

    @classmethod
    def get_client(cls) -> AsyncOpenAI:
        """获取 OpenAI 客户端实例"""
        if cls._instance is None:
            cls._instance = AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """重置客户端（配置变更时调用）"""
        cls._instance = None


def get_ai_client() -> AsyncOpenAI:
    """获取 AI 客户端的快捷方法"""
    return AIClient.get_client()
