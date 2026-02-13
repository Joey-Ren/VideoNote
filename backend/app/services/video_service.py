"""视频信息服务 — 使用 yt-dlp 提取视频元数据"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import yt_dlp

from app.models.schemas import VideoInfo

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)


class VideoService:
    """视频信息提取服务"""

    def _detect_platform(self, url: str) -> str:
        """检测视频平台"""
        host = urlparse(url).hostname or ""
        if "youtube" in host or "youtu.be" in host:
            return "youtube"
        if "bilibili" in host or "b23.tv" in host:
            return "bilibili"
        return "unknown"

    def _extract_info_sync(self, url: str) -> dict:
        """同步提取视频信息（在线程池中运行）"""
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "no_playlist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    async def get_video_info(self, url: str) -> VideoInfo:
        """提取视频信息（标题、封面、时长、平台）"""
        platform = self._detect_platform(url)
        logger.info("获取视频信息: %s (平台: %s)", url, platform)

        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(_executor, self._extract_info_sync, url)

        return VideoInfo(
            title=info.get("title", "未知标题"),
            thumbnail=info.get("thumbnail"),
            duration=int(info.get("duration", 0)),
            platform=platform,
            url=url,
        )
