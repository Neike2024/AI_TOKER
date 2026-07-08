from sqlalchemy.orm import Session
from app.models.message import ChatMessage
from app.schemas.message import MessageCreate


def create_message(db: Session, message: MessageCreate):
    db_message = ChatMessage(
        user_id=message.user_id,
        role=message.role,
        content=message.content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_messages_by_user_id(db: Session, user_id: int, limit: int = 100):
    return db.query(ChatMessage)\
        .filter(ChatMessage.user_id == user_id)\
        .order_by(ChatMessage.created_at.asc())\
        .limit(limit)\
        .all()


def get_all_messages(db: Session):
    return db.query(ChatMessage).order_by(ChatMessage.created_at.desc()).all()