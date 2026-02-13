"""Whisper 模型客户端，懒加载单例"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

from app.config import settings

logger = logging.getLogger(__name__)


class WhisperClient:
    """Whisper 模型管理器，首次使用时才加载模型"""

    _model: WhisperModel | None = None
    _model_size: str = ""

    @classmethod
    def get_model(cls) -> WhisperModel:
        """获取 Whisper 模型实例"""
        target_size = settings.whisper_model_size

        if cls._model is None or cls._model_size != target_size:
            logger.info("加载 Whisper 模型: %s ...", target_size)
            from faster_whisper import WhisperModel

            cls._model = WhisperModel(
                target_size,
                device="auto",
                compute_type="auto",
            )
            cls._model_size = target_size
            logger.info("Whisper 模型加载完成")

        return cls._model

    @classmethod
    def reset(cls) -> None:
        """释放模型"""
        cls._model = None
        cls._model_size = ""


def get_whisper_model() -> WhisperModel:
    """获取 Whisper 模型的快捷方法"""
    return WhisperClient.get_model()
