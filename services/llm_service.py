import os
import json
import httpx
from typing import Optional, AsyncGenerator


class LLMService:
    """Unified LLM API client supporting OpenAI-compatible interfaces."""

    def __init__(self):
        self.api_key = os.environ.get("LLM_API_KEY", "")
        self.base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model = os.environ.get("LLM_MODEL", "claude-sonnet-4-20250514")
        self.temperature = float(os.environ.get("LLM_TEMPERATURE", "0.3"))
        self.max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "8192"))

    def _build_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def chat(self, messages: list, system_prompt: str = "") -> str:
        """Non-streaming chat completion."""
        if not self.api_key:
            raise ValueError("LLM_API_KEY not configured. Please set it in Railway dashboard Variables.")

        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._build_headers(),
                json=payload,
            )
            if resp.status_code >= 400:
                err_body = resp.text[:500]
                print(f"[LLM ERROR] status={resp.status_code}, url={resp.request.url}, body={err_body}")
                raise httpx.HTTPStatusError(
                    f"LLM API error {resp.status_code}: {err_body}",
                    request=resp.request, response=resp
                )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: list, system_prompt: str = "") -> AsyncGenerator[str, None]:
        """Streaming chat completion."""
        if not self.api_key:
            raise ValueError("LLM_API_KEY not configured. Please set it in Railway dashboard Variables.")

        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._build_headers(),
                json=payload,
            ) as resp:
                if resp.status_code >= 400:
                    err_body = await resp.aread()
                    err_text = err_body.decode("utf-8", errors="replace")[:500]
                    print(f"[LLM ERROR] status={resp.status_code}, url={resp.request.url}, body={err_text}")
                    raise httpx.HTTPStatusError(
                        f"LLM API error {resp.status_code}: {err_text}",
                        request=resp.request, response=resp
                    )
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue


llm_service = LLMService()
