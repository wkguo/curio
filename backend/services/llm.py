"""Provider-agnostic LLM client (spec §16).

`LLMClient.generate(messages, schema=...)` returns either text or a validated
Pydantic object. The OpenAI-compatible implementation covers OpenAI, Qwen,
DeepSeek, Gemini's OpenAI endpoint, vLLM, Ollama and most gateways.

Failure contract (spec §25): structured output is retried once with the
validation error fed back; after that `LLMError` is raised and the harness
switches to its deterministic rule path. Raw errors never reach the student.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from config import Settings, get_settings

log = logging.getLogger("curio.llm")

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    """Any failure to obtain a usable model response."""


class LLMClient:
    name = "abstract"

    @property
    def available(self) -> bool:
        return False

    async def generate(self, messages: list[dict[str, str]], schema: type[T] | None = None) -> T | str:
        raise NotImplementedError


class DisabledLLMClient(LLMClient):
    name = "disabled"

    async def generate(self, messages, schema=None):
        raise LLMError("LLM disabled (rules mode or no API key)")


def extract_json(text: str) -> Any:
    """Fallback parser: tolerate ```json fences and leading/trailing prose."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


class OpenAICompatibleClient(LLMClient):
    name = "openai-compatible"

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.llm_base_url.rstrip("/"),
            timeout=settings.llm_timeout_s,
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
        )

    @property
    def available(self) -> bool:
        return True

    async def _chat(self, messages: list[dict[str, str]], json_mode: bool) -> str:
        body: dict[str, Any] = {
            "model": self.settings.llm_model,
            "messages": messages,
            "temperature": self.settings.llm_temperature,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        try:
            resp = await self._client.post("/chat/completions", json=body)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"] or ""
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            log.warning("LLM call failed: %s", exc)
            raise LLMError(str(exc)) from exc

    async def generate(self, messages, schema=None):
        if schema is None:
            return await self._chat(messages, json_mode=False)

        schema_hint = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        convo = [
            *messages,
            {"role": "system", "content": f"Respond with ONE JSON object matching this JSON schema:\n{schema_hint}"},
        ]
        last_error: Exception | None = None
        for attempt in range(2):  # spec §25: retry once
            raw = await self._chat(convo, json_mode=True)
            try:
                return schema.model_validate(extract_json(raw))
            except (ValidationError, json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                log.info("structured output invalid (attempt %d): %s", attempt + 1, exc)
                convo = [
                    *convo,
                    {"role": "assistant", "content": raw[:4000]},
                    {"role": "user", "content": f"That JSON was invalid: {str(exc)[:800]}. Return corrected JSON only."},
                ]
        raise LLMError(f"structured output failed after retry: {last_error}")


_client: LLMClient | None = None


def get_llm() -> LLMClient:
    global _client
    if _client is None:
        s = get_settings()
        _client = OpenAICompatibleClient(s) if s.llm_enabled else DisabledLLMClient()
    return _client


def set_llm(client: LLMClient | None) -> None:
    """Override the client (tests, or swapping providers at runtime)."""
    global _client
    _client = client
