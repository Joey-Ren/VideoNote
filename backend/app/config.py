"""VideoNote 配置管理"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，从 .env 文件读取"""

    # OpenAI
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"

    # TTS (ChatTTS — 速度最快，音质好)
    tts_model: str = "ChatTTS"
    tts_speed: float = 1.0  # 0.25 ~ 4.0

    # STT (SenseVoice)
    stt_model: str = "SenseVoice"

    # Whisper
    whisper_model_size: str = "base"

    # YouTube（可选，加速预览）
    youtube_api_key: str = ""

    # yt-dlp
    cookies_from_browser: str = "chrome"  # 浏览器名: chrome/firefox/edge/safari，留空禁用
    cookies_file: str = ""  # cookies.txt 路径，优先级高于 cookies_from_browser

    # 应用
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    temp_dir: str = "./temp"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


# 全局单例
settings = Settings()
