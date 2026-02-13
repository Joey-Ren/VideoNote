import logging
import os
from urllib.parse import urlparse

from app.config import settings

logger = logging.getLogger(__name__)


def _is_bilibili(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return "bilibili" in host or "b23.tv" in host


def build_ydl_opts(url: str, extra_opts: dict | None = None) -> dict:
    opts: dict = {
        "quiet": True,
        "no_warnings": True,
    }

    if settings.cookies_file and os.path.isfile(settings.cookies_file):
        opts["cookiefile"] = settings.cookies_file
    elif settings.cookies_from_browser:
        opts["cookiesfrombrowser"] = (settings.cookies_from_browser,)

    if _is_bilibili(url):
        opts["http_headers"] = {
            "Referer": "https://www.bilibili.com/",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        }

    if extra_opts:
        opts.update(extra_opts)

    return opts
