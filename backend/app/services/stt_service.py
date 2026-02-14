"""STT 服务 — SenseVoice 语音识别"""

import logging

from app.config import settings
from app.core.ai_client import get_ai_client

logger = logging.getLogger(__name__)


class STTService:

    async def transcribe(self, audio_data: bytes, filename: str = "audio.webm") -> str:
        client = get_ai_client()
        response = await client.audio.transcriptions.create(
            model=settings.stt_model,
            file=(filename, audio_data),
        )
        return response.text
