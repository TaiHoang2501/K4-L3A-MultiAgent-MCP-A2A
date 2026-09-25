from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# Qwen LLM Configuration
API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1").rstrip("/")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen-3-8b")


async def chat_completion(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.0,
    response_format_json: bool = False,
    timeout: float = 60.0,
) -> str:
    """Send a chat completion request to Qwen via OpenAI-compatible endpoint.

    Uses `httpx2` which is already included in the repository dependencies.
    """
    api_key = os.getenv("API_KEY", API_KEY)
    if not api_key or api_key == "your_qwen_api_key_here":
        raise ValueError(
            "Chưa cấu hình API_KEY trong file .env! Vui lòng điền API_KEY=... vào file .env"
        )

    base_url = os.getenv("BASE_URL", BASE_URL).rstrip("/")
    model_name = model or os.getenv("MODEL_NAME", MODEL_NAME)

    # Đảm bảo tiền tố phù hợp nếu dùng OpenRouter
    if "openrouter.ai" in base_url and "/" not in model_name:
        model_name = f"qwen/{model_name}"

    payload: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
    }
    if response_format_json:
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    import httpx2

    async with httpx2.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{base_url}/chat/completions",
            json=payload,
            headers=headers,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Lỗi gọi Qwen API (HTTP {response.status_code}): {response.text}"
            )
        data = response.json()
        return data["choices"][0]["message"]["content"]
