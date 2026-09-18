from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


class AIProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class AIConfig:
    provider: str
    base_url: str
    api_key: str
    model: str

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "AIConfig":
        raw = config.get("ai") if isinstance(config.get("ai"), dict) else {}
        provider = str(raw.get("provider") or "deepseek").strip()
        base_url = str(raw.get("base_url") or "https://api.deepseek.com").strip()
        api_key = str(raw.get("api_key") or "").strip()
        model = str(raw.get("model") or "deepseek-v4-flash").strip()
        if not api_key:
            raise AIProviderError("请先在配置页填写 AI 写稿 API Key。")
        return cls(provider=provider, base_url=base_url, api_key=api_key, model=model)


class OpenAICompatibleProvider:
    def __init__(self, config: AIConfig, *, timeout: int = 90) -> None:
        self.config = config
        self.timeout = timeout

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.4,
        max_tokens: int = 4096,
        thinking: bool | None = None,
    ) -> dict[str, Any]:
        content = self._chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            thinking=thinking,
        )
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIProviderError(f"AI 返回的内容不是合法 JSON：{exc}") from exc
        if not isinstance(parsed, dict):
            raise AIProviderError("AI 返回的 JSON 顶层必须是对象。")
        return parsed

    def _chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: dict[str, str],
        thinking: bool | None,
    ) -> str:
        endpoint = urljoin(self.config.base_url.rstrip("/") + "/", "chat/completions")
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            "response_format": response_format,
        }
        if thinking is not None:
            payload["thinking"] = {"type": "enabled" if thinking else "disabled"}
        request = Request(
            endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "WeChatMPWriterApp/0.1",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise AIProviderError(f"AI 接口请求失败：HTTP {exc.code} {body}") from exc
        except URLError as exc:
            raise AIProviderError(f"无法连接 AI 接口：{exc.reason}") from exc
        except TimeoutError as exc:
            raise AIProviderError("AI 接口请求超时，请稍后重试。") from exc

        try:
            data = json.loads(raw)
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise AIProviderError("AI 接口返回格式异常。") from exc
        if not str(content or "").strip():
            raise AIProviderError("AI 返回内容为空，请重试。")
        return str(content).strip()


def build_provider(config: dict[str, Any]) -> OpenAICompatibleProvider:
    ai_config = AIConfig.from_config(config)
    return OpenAICompatibleProvider(ai_config)
