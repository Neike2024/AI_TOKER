from dotenv import load_dotenv
import os
import json

load_dotenv()

VOICE = os.getenv("VOICE", "zh-CN-XiaoxiaoNeural")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "ai_chat")

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
PROVIDER_COOLDOWN = int(os.getenv("PROVIDER_COOLDOWN", "300"))


class APIProvider:
    def __init__(self, name: str, api_key: str, model: str, url: str, priority: int = 1):
        self.name = name
        self.api_key = api_key
        self.model = model
        self.url = url
        self.priority = priority
        self.last_fail_time = 0

    def is_available(self):
        import time
        return time.time() - self.last_fail_time > PROVIDER_COOLDOWN

    def mark_failed(self):
        import time
        self.last_fail_time = time.time()


def load_providers() -> list:
    providers = []
    
    provider_config = os.getenv("API_PROVIDERS")
    if provider_config:
        try:
            config_list = json.loads(provider_config)
            for idx, config in enumerate(config_list):
                providers.append(APIProvider(
                    name=config.get("name", f"provider_{idx}"),
                    api_key=config.get("api_key", ""),
                    model=config.get("model", "glm-4"),
                    url=config.get("url", "https://open.bigmodel.cn/api/paas/v4/chat/completions"),
                    priority=config.get("priority", idx + 1)
                ))
        except json.JSONDecodeError:
            pass
    
    if not providers:
        api_key = os.getenv("API_KEY")
        model = os.getenv("glm_model", "glm-4")
        url = os.getenv("url", "https://open.bigmodel.cn/api/paas/v4/chat/completions")
        if api_key:
            providers.append(APIProvider(name="default", api_key=api_key, model=model, url=url))
    
    return sorted(providers, key=lambda p: p.priority)