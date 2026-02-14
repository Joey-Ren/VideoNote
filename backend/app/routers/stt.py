"""STT 语音识别路由"""

from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

from app.services.stt_service import STTService

router = APIRouter()
stt_service = STTService()


class STTResponse(BaseModel):
    text: str


@router.post("/transcribe", response_model=STTResponse)
async def speech_to_text(file: UploadFile = File(...)) -> STTResponse:
    audio_data = await file.read()
    text = await stt_service.transcribe(
        audio_data=audio_data,
        filename=file.filename or "audio.webm",
    )
    return STTResponse(text=text)
