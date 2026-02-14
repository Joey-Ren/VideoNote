"""TTS 服务 — CosyVoice2 语音合成"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class TTSService:

    async def synthesize(
        self,
        text: str,
        speed: float | None = None,
    ) -> bytes:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.openai_base_url}/audio/speech",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.tts_model,
                    "input": text,
                    "response_format": "mp3",
                    "speed": speed or settings.tts_speed,
                },
            )
            resp.raise_for_status()
            return resp.content
