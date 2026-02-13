from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings
from app.core.ai_client import AIClient

router = APIRouter()


class SettingsData(BaseModel):
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    whisper_model_size: str = "base"
    youtube_api_key: str = ""


def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


@router.get("", response_model=SettingsData)
async def get_settings() -> SettingsData:
    return SettingsData(
        openai_api_key=_mask_key(settings.openai_api_key) if settings.openai_api_key else "",
        openai_base_url=settings.openai_base_url,
        openai_model=settings.openai_model,
        whisper_model_size=settings.whisper_model_size,
        youtube_api_key=_mask_key(settings.youtube_api_key) if settings.youtube_api_key else "",
    )


@router.put("")
async def update_settings(data: SettingsData) -> dict:
    changed = False

    if data.openai_api_key and "*" not in data.openai_api_key:
        settings.openai_api_key = data.openai_api_key
        changed = True
    if data.openai_base_url:
        settings.openai_base_url = data.openai_base_url
        changed = True
    if data.openai_model:
        settings.openai_model = data.openai_model
    if data.whisper_model_size:
        settings.whisper_model_size = data.whisper_model_size
    if data.youtube_api_key and "*" not in data.youtube_api_key:
        settings.youtube_api_key = data.youtube_api_key

    if changed:
        AIClient.reset()

    return {"status": "ok", "message": "设置已更新"}
