import io
import edge_tts
import asyncio
from app.core.config import VOICE


async def text_to_speech_edge(text: str) -> io.BytesIO:
    communicate = edge_tts.Communicate(text, VOICE)
    mp3_data = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            mp3_data.write(chunk["data"])
    mp3_data.seek(0)
    return mp3_data