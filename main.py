import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from API_call.api_call import stream_chat 
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import edge_tts
import asyncio


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 新增依赖
VOICE = "zh-CN-XiaoxiaoNeural"   # 微软小晓，可爱女声，适合狐娘

load_dotenv()
api_key = os.getenv('API_KEY')
model = os.getenv('glm_model')
url = os.getenv('url')

#user_input = input("你：")

async def text_to_speech_edge(text: str) -> io.BytesIO:
    """将文本转成语音，返回内存中的 MP3 字节流"""
    communicate = edge_tts.Communicate(text, VOICE)
    mp3_data = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            mp3_data.write(chunk["data"])
    mp3_data.seek(0)
    return mp3_data

@app.get("/")
async def root():
    return FileResponse("templets\chat.html")

@app.post("/chat-stream")
async def chat_stream(request: Request):
    body = await request.json()
    user_input = body.get("message", "")

    # 生成器函数，每次 yield 一个文本片段
    def generate():
        try:
            # 调用 api_call 中的流式生成器
            for text_piece in stream_chat(user_input, model, api_key, url):
                yield text_piece  # FastAPI 会逐步发送这些字节
        except Exception as e:
            yield f"【错误】{e}"

    return StreamingResponse(generate(), media_type="text/plain")


@app.post("/chat-voice")
async def chat_voice(request: Request):
    body = await request.json()
    user_input = body.get("message", "")

    # 1. 获取 AI 完整回复（收集流式输出）
    full_reply = ""
    try:
        for text_piece in stream_chat(user_input, model, api_key, url):
            full_reply += text_piece
    except Exception as e:
        full_reply = f"对不起，我出了点问题：{e}"

    # 2. 调用 Edge TTS 生成音频（注意 stream_chat 是同步生成器，需在线程中运行避免阻塞异步）
    #    由于 edge_tts 需要async，这里直接 await
    try:
        mp3_stream = await text_to_speech_edge(full_reply)
    except Exception as e:
        # TTS 失败则返回错误文字
        return {"error": f"TTS 失败：{e}"}

    return StreamingResponse(mp3_stream, media_type="audio/mpeg")