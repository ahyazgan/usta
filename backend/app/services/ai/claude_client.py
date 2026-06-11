"""Claude API ince sarmalayıcı.

Sorumluluklar:
- 30s timeout
- tenacity retry(2) => toplam 3 deneme (yalnızca geçici hatalarda)
- JSON-only yanıtı ayrıştır
- token sayılarını (in/out) çağırana döndür (loglama servis katmanında)

MALİYET KURALI: vision modeli sonnet'tir; Opus YASAK (config.vision_model).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ...config import Settings, get_settings

try:  # anthropic SDK opsiyonel import — testte mock'lanır, kurulu olmayabilir.
    import anthropic
    from anthropic import APIConnectionError, APIStatusError, AsyncAnthropic

    _RETRYABLE: tuple[type[Exception], ...] = (APIConnectionError, APIStatusError)
except Exception:  # pragma: no cover - SDK yoksa
    anthropic = None  # type: ignore[assignment]
    AsyncAnthropic = None  # type: ignore[assignment]
    _RETRYABLE = (ConnectionError,)


@dataclass(slots=True)
class ClaudeResult:
    data: dict[str, Any]
    tokens_in: int
    tokens_out: int


class ClaudeClient:
    """Gerçek Claude çağrılarını yapar. Testlerde FakeClaudeClient ile değiştirilir."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = (
            AsyncAnthropic(api_key=self.settings.anthropic_api_key)
            if AsyncAnthropic is not None and self.settings.anthropic_api_key
            else None
        )

    async def complete_json(
        self,
        *,
        model: str,
        system: str,
        content: list[dict[str, Any]] | str,
        max_tokens: int | None = None,
    ) -> ClaudeResult:
        if self._client is None:
            raise RuntimeError(
                "Claude istemcisi yapılandırılmadı (ANTHROPIC_API_KEY eksik)."
            )

        max_tokens = max_tokens or self.settings.ai_max_tokens
        messages = [{"role": "user", "content": content}]

        @retry(
            reraise=True,
            stop=stop_after_attempt(1 + self.settings.ai_max_retries),
            wait=wait_exponential(multiplier=0.5, max=4),
            retry=retry_if_exception_type(_RETRYABLE),
        )
        async def _call() -> Any:
            return await self._client.with_options(
                timeout=self.settings.ai_timeout_seconds
            ).messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )

        message = await _call()
        text = "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        )
        data = _parse_json(text)
        usage = message.usage
        return ClaudeResult(
            data=data,
            tokens_in=getattr(usage, "input_tokens", 0),
            tokens_out=getattr(usage, "output_tokens", 0),
        )


def _parse_json(text: str) -> dict[str, Any]:
    """JSON-only yanıtı ayrıştır; gerekirse ilk { ... } bloğunu yakala."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


# Singleton bağımlılık — testlerde override edilir.
_client_singleton: ClaudeClient | None = None


def get_claude_client() -> ClaudeClient:
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = ClaudeClient()
    return _client_singleton
