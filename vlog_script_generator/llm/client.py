from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path
from typing import Any


class OpenAICompatibleClient:
    def __init__(self, config: dict) -> None:
        self.config = config.get("llm", config)
        self.base_url = str(self.config.get("baseURL", "")).rstrip("/")
        self.api_key = str(self.config.get("apiKey", ""))
        self.timeout = int(self.config.get("timeoutSeconds", 120))

    @property
    def enabled(self) -> bool:
        return bool(self.config.get("enabled") and self.base_url and self.api_key)

    def chat(self, messages: list[dict[str, Any]], model: str | None = None) -> str:
        if not self.enabled:
            raise RuntimeError("LLM is not enabled.")
        payload = {
            "model": model or self.config.get("textModel"),
            "messages": messages,
            "temperature": float(self.config.get("temperature", 0.7)),
            "max_tokens": int(self.config.get("maxTokens", 8000)),
        }
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

    @staticmethod
    def image_to_data_url(path: str | Path) -> str:
        target = Path(path)
        mime = "image/png" if target.suffix.lower() == ".png" else "image/jpeg"
        encoded = base64.b64encode(target.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{encoded}"

