from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.services.llm_service import stream_chat

router = APIRouter()


@router.post("/chat-stream")
async def chat_stream(request: Request):
    body = await request.json()
    user_input = body.get("message", "")
    user_id = body.get("user_id", 1)

    def generate():
        try:
            for text_piece in stream_chat(user_id, user_input):
                yield text_piece
        except Exception as e:
            yield f"【错误】{e}"

    return StreamingResponse(generate(), media_type="text/plain")