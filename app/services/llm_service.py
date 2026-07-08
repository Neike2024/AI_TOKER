import requests
import json
import time
import logging
from app.core.config import load_providers, MAX_RETRIES
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = {
    "role": "system",
    "content": "你是一个可爱的狐娘，你说话非常可爱软糯，你很会说话，说话语气俏皮，人性化。"
}

_providers = None

_memory_history = {}


def get_providers():
    global _providers
    if _providers is None:
        _providers = load_providers()
    return _providers


def get_chat_history_messages(user_id: int):
    if SessionLocal is None:
        logger.warning("数据库未连接，使用内存存储")
        return _memory_history.get(user_id, [])
    
    try:
        db = SessionLocal()
        messages = db.query(__import__('app.models.message', fromlist=['ChatMessage']).ChatMessage)\
            .filter(__import__('app.models.message', fromlist=['ChatMessage']).ChatMessage.user_id == user_id)\
            .order_by(__import__('app.models.message', fromlist=['ChatMessage']).ChatMessage.created_at.asc())\
            .limit(100)\
            .all()
        history = []
        for msg in messages:
            history.append({"role": msg.role, "content": msg.content})
        return history
    except Exception as e:
        logger.error(f"数据库查询失败，使用内存存储: {e}")
        return _memory_history.get(user_id, [])
    finally:
        db.close()


def save_user_message(user_id: int, content: str):
    if SessionLocal is None:
        logger.warning("数据库未连接，消息保存到内存")
        if user_id not in _memory_history:
            _memory_history[user_id] = []
        _memory_history[user_id].append({"role": "user", "content": content})
        return
    
    try:
        from app.crud.message import create_message
        from app.schemas.message import MessageCreate
        db = SessionLocal()
        create_message(db, MessageCreate(user_id=user_id, role="user", content=content))
    except Exception as e:
        logger.error(f"数据库保存失败，消息保存到内存: {e}")
        if user_id not in _memory_history:
            _memory_history[user_id] = []
        _memory_history[user_id].append({"role": "user", "content": content})
    finally:
        db.close()


def save_assistant_message(user_id: int, content: str):
    if SessionLocal is None:
        logger.warning("数据库未连接，消息保存到内存")
        if user_id not in _memory_history:
            _memory_history[user_id] = []
        _memory_history[user_id].append({"role": "assistant", "content": content})
        return
    
    try:
        from app.crud.message import create_message
        from app.schemas.message import MessageCreate
        db = SessionLocal()
        create_message(db, MessageCreate(user_id=user_id, role="assistant", content=content))
    except Exception as e:
        logger.error(f"数据库保存失败，消息保存到内存: {e}")
        if user_id not in _memory_history:
            _memory_history[user_id] = []
        _memory_history[user_id].append({"role": "assistant", "content": content})
    finally:
        db.close()


def call_api(provider, messages):
    headers = {
        "Authorization": f"Bearer {provider.api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": provider.model,
        "messages": messages,
        "temperature": 0.8,
        "stream": True
    }

    resp = requests.post(provider.url, headers=headers, json=payload, stream=True, timeout=60)
    resp.raise_for_status()

    full_content = ""
    for line in resp.iter_lines(decode_unicode=True):
        if not line.startswith("data: "):
            continue
        data = line[6:]
        if data == "[DONE]":
            break
        try:
            chunk = json.loads(data)
            delta = chunk["choices"][0]["delta"]
            if "content" in delta:
                content = delta["content"]
                full_content += content
                yield content
        except json.JSONDecodeError:
            continue
    
    return full_content


def stream_chat(user_id: int, user_input: str):
    save_user_message(user_id, user_input)
    
    messages = get_chat_history_messages(user_id)
    
    if not messages or messages[0]["role"] != "system":
        messages.insert(0, SYSTEM_PROMPT)
    
    messages.append({"role": "user", "content": user_input})

    providers = get_providers()
    if not providers:
        yield "【错误】未配置任何API提供商"
        return

    available_providers = [p for p in providers if p.is_available()]
    if not available_providers:
        yield "【错误】所有API提供商都处于冷却状态，请稍后再试"
        return

    full_content = ""
    last_error = None

    for attempt in range(MAX_RETRIES):
        for provider in available_providers:
            try:
                logger.info(f"尝试调用API提供商: {provider.name} (第{attempt + 1}次尝试)")
                
                chunks_generator = call_api(provider, messages)
                for chunk in chunks_generator:
                    full_content += chunk
                    yield chunk
                
                save_assistant_message(user_id, full_content)
                logger.info(f"API调用成功，提供商: {provider.name}")
                return
                
            except requests.exceptions.RequestException as e:
                last_error = f"API请求失败: {str(e)}"
                logger.error(f"提供商 {provider.name} 调用失败: {last_error}")
                provider.mark_failed()
                time.sleep(1)
            except Exception as e:
                last_error = f"未知错误: {str(e)}"
                logger.error(f"提供商 {provider.name} 调用失败: {last_error}")
                provider.mark_failed()
                time.sleep(1)

    if full_content:
        save_assistant_message(user_id, full_content)
    
    yield f"【错误】所有API提供商均调用失败: {last_error}"