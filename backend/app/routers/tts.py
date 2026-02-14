"""TTS 语音合成路由"""

from fastapi import APIRouter
from fastapi.responses import Response

from app.models.schemas import TTSRequest
from app.services.tts_service import TTSService

router = APIRouter()
tts_service = TTSService()


@router.post("/speak")
async def text_to_speech(request: TTSRequest) -> Response:
    audio_bytes = await tts_service.synthesize(
        text=request.text,
        speed=request.speed,
    )
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline"},
    )
