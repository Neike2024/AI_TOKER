from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.services.llm_service import stream_chat
from app.services.tts_service import text_to_speech_edge

router = APIRouter()


@router.post("/chat-voice")
async def chat_voice(request: Request):
    body = await request.json()
    user_input = body.get("message", "")
    user_id = body.get("user_id", 1)

    full_reply = ""
    try:
        for text_piece in stream_chat(user_id, user_input):
            full_reply += text_piece
    except Exception as e:
        full_reply = f"对不起，我出了点问题：{e}"

    try:
        mp3_stream = await text_to_speech_edge(full_reply)
    except Exception as e:
        return {"error": f"TTS 失败：{e}"}

    return StreamingResponse(mp3_stream, media_type="audio/mpeg")