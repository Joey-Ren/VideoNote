"""转录路由"""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import TranscribeRequest, TranscriptionResult, TaskResponse
from app.services.transcribe_service import TranscribeService

router = APIRouter()
transcribe_service = TranscribeService()


@router.post("/start", response_model=TaskResponse)
async def start_transcription(request: TranscribeRequest) -> TaskResponse:
    """开始转录任务"""
    if not request.url and not request.local_path:
        raise HTTPException(status_code=400, detail="请提供视频 URL 或本地路径")
    try:
        task_id = await transcribe_service.start(
            url=request.url,
            local_path=request.local_path,
        )
        return TaskResponse(task_id=task_id, status="processing", message="转录已开始")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/{task_id}")
async def transcription_progress(task_id: str) -> StreamingResponse:
    """SSE 实时推送转录进度"""

    async def event_stream():
        async for progress in transcribe_service.get_progress(task_id):
            yield f"data: {json.dumps(progress, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Content-Type": "text/event-stream; charset=utf-8"},
    )


@router.get("/result/{task_id}", response_model=TranscriptionResult)
async def get_transcription_result(task_id: str) -> TranscriptionResult:
    """获取转录结果"""
    result = await transcribe_service.get_result(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="任务不存在或未完成")
    return result
