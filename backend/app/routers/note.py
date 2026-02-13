"""笔记生成路由"""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import NoteGenerateRequest, NoteResult, TaskResponse
from app.services.note_service import NoteService

router = APIRouter()
note_service = NoteService()


@router.post("/generate", response_model=TaskResponse)
async def generate_note(request: NoteGenerateRequest) -> TaskResponse:
    """生成笔记"""
    try:
        task_id = await note_service.generate(
            text=request.transcription_text,
            language=request.language,
        )
        return TaskResponse(task_id=task_id, status="processing", message="笔记生成中")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream/{task_id}")
async def stream_note(task_id: str) -> StreamingResponse:
    """SSE 流式推送笔记生成过程"""

    async def event_stream():
        async for chunk in note_service.stream_result(task_id):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/result/{task_id}", response_model=NoteResult)
async def get_note_result(task_id: str) -> NoteResult:
    """获取笔记结果"""
    result = await note_service.get_result(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="任务不存在或未完成")
    return result
