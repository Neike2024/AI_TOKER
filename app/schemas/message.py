from pydantic import BaseModel
from datetime import datetime
from typing import List


class MessageCreate(BaseModel):
    user_id: int
    role: str
    content: str


class MessageResponse(BaseModel):
    id: int
    user_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        orm_mode = True


class ChatHistoryResponse(BaseModel):
    messages: List[MessageResponse]


class ChatRequest(BaseModel):
    user_id: int
    message: str


class VoiceChatRequest(BaseModel):
    user_id: int
    message: str