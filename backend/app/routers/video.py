"""视频预览路由"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import VideoPreviewRequest, VideoInfo
from app.services.video_service import VideoService

router = APIRouter()
video_service = VideoService()


@router.post("/preview", response_model=VideoInfo)
async def preview_video(request: VideoPreviewRequest) -> VideoInfo:
    """获取视频信息（标题、封面、时长、平台）"""
    try:
        return await video_service.get_video_info(request.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
