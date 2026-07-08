from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import ALLOWED_ORIGINS
from app.routers import chat_router, voice_router
import logging

logger = logging.getLogger(__name__)

try:
    from app.core.database import engine, Base
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建成功")
except Exception as e:
    logger.error(f"数据库连接失败，服务将以降级模式运行: {e}")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(chat_router)
app.include_router(voice_router)


@app.get("/")
async def root():
    return FileResponse("templates/chat.html")