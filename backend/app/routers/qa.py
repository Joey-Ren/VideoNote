"""视频问答路由"""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import QARequest
from app.services.qa_service import QAService

router = APIRouter()
qa_service = QAService()


@router.post("/ask")
async def ask_question(request: QARequest) -> StreamingResponse:
    """基于视频内容回答问题（流式响应）"""

    async def event_stream():
        try:
            async for chunk in qa_service.ask(
                question=request.question,
                context=request.context or "",
                video_url=request.video_url,
            ):
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'status': 'completed'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Content-Type": "text/event-stream; charset=utf-8"},
    )
