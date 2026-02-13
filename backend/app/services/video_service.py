"""视频信息服务 — 使用 yt-dlp 提取视频元数据"""

import logging
from urllib.parse import urlparse

from app.models.schemas import VideoInfo

logger = logging.getLogger(__name__)


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

    async def get_video_info(self, url: str) -> VideoInfo:
        """提取视频信息（标题、封面、时长、平台）"""
        platform = self._detect_platform(url)

        # TODO: 实现 yt-dlp 提取
        # import yt_dlp
        # ydl_opts = {"quiet": True, "no_warnings": True}
        # with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        #     info = ydl.extract_info(url, download=False)

        # 临时 Mock 数据，方便前端联调
        logger.info("获取视频信息: %s (平台: %s)", url, platform)
        return VideoInfo(
            title=f"[Mock] 视频标题 - {platform}",
            thumbnail="https://via.placeholder.com/320x180?text=VideoNote",
            duration=600,
            platform=platform,
            url=url,
        )
