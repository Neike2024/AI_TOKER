import requests
from dotenv import load_dotenv
import os
import json
from pathlib import Path
#初始化更新聊天记录
messages_load = [
    {
        "role": "system",
        "content": "你是一个可爱的狐娘，你说话非常可爱软糯，你很会说话，说话语气俏皮，人性化。"
    }
]

'''
该文件功能为调用大模型api并生成回复,
'''

# # 全局消息历史（按需使用）
# messages = [{"role": "system","content": "你是一个可爱的狐娘，你说话非常可爱软糯，你很会说话，说话语气俏皮，人性化。"}]

def stream_chat(user_input: str, model: str, api_key: str, url: str):
    """
    返回一个生成器，逐块 yield 大模型回复的文本
    """
    with open(r"Chat_history\message.json",'r',encoding='utf-8') as f:
        messages = json.load(f)

    messages.append({"role": "user", "content": user_input})

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.8,
        "stream": True
    }

    resp = requests.post(url, headers=headers, json=payload, stream=True)
    resp.raise_for_status()  # 出错会抛异常

    full_content = ""
    for line in resp.iter_lines(decode_unicode=True):
        if not line.startswith("data: "):
            continue
        data = line[6:]  # 去掉 "data: "
        if data == "[DONE]":
            break
        try:
            chunk = json.loads(data)
            delta = chunk["choices"][0]["delta"]
            if "content" in delta:
                content = delta["content"]
                full_content += content
                yield content       # 逐字产出
        except json.JSONDecodeError:
            continue

    # 把完整回复保存到消息历史，实现多轮对话
    messages.append({"role": "assistant", "content": full_content})

    #常态化
    file_path = r"Chat_history\message.json"
    with open(file=file_path,mode='w',encoding='utf-8') as f:
        json.dump(messages,f,indent=4,ensure_ascii=False)