"""视频下载路由"""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, FileResponse

from app.models.schemas import DownloadRequest, TaskResponse
from app.services.download_service import DownloadService

router = APIRouter()
download_service = DownloadService()


@router.post("/start", response_model=TaskResponse)
async def start_download(request: DownloadRequest) -> TaskResponse:
    """开始下载视频"""
    try:
        task_id = await download_service.start(
            url=request.url,
            format=request.format,
            quality=request.quality,
        )
        return TaskResponse(task_id=task_id, status="processing", message="下载已开始")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/{task_id}")
async def download_progress(task_id: str) -> StreamingResponse:
    """SSE 实时推送下载进度"""

    async def event_stream():
        async for progress in download_service.get_progress(task_id):
            yield f"data: {json.dumps(progress, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/file/{task_id}")
async def download_file(task_id: str) -> FileResponse:
    """下载已完成的文件"""
    file_path = await download_service.get_file_path(task_id)
    if file_path is None:
        raise HTTPException(status_code=404, detail="文件不存在或下载未完成")
    return FileResponse(file_path)
