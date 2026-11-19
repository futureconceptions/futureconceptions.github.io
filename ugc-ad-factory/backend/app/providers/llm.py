"""LLM providers producing validated Pydantic objects.

AnthropicLLM  - Claude via the official SDK, `messages.parse(output_format=Model)`
                (structured outputs), optional base64 images for vision QA.
HeuristicLLM  - deterministic, offline. Calls the agent-supplied fallback so
                the whole pipeline runs without any API key (mock/dev mode).
"""
from __future__ import annotations

import base64
from typing import Callable, TypeVar

from pydantic import BaseModel

from app.core.config import get_settings
from app.providers.base import ImageInput, LLMUsage, ProviderError

T = TypeVar("T", bound=BaseModel)


class HeuristicLLM:
    name = "heuristic"
    supports_vision = False

    def structured(self, *, system: str, prompt: str, schema: type[T],
                   images: list[ImageInput] | None = None, task: str = "",
                   fallback: Callable[[], T] | None = None) -> tuple[T, LLMUsage]:
        if fallback is None:
            raise ProviderError(f"heuristic LLM has no fallback for task '{task}'")
        out = fallback()
        return schema.model_validate(out.model_dump()), LLMUsage(model="heuristic")


class AnthropicLLM:
    name = "anthropic"
    supports_vision = True

    def __init__(self, client=None):
        import anthropic

        s = get_settings()
        if client is None:
            if not s.anthropic_api_key:
                raise ProviderError("ANTHROPIC_API_KEY is not configured")
            client = anthropic.Anthropic(api_key=s.anthropic_api_key.get_secret_value(), max_retries=3)
        self.client = client
        self.model = s.anthropic_model
        self.fallback_model = s.anthropic_fallback_model
        self._anthropic = anthropic

    def _content(self, prompt: str, images: list[ImageInput] | None) -> list[dict]:
        content: list[dict] = []
        for img in images or []:
            if img.label:
                content.append({"type": "text", "text": f"[{img.label}]"})
            content.append({"type": "image", "source": {
                "type": "base64", "media_type": img.media_type,
                "data": base64.standard_b64encode(img.data).decode("ascii")}})
        content.append({"type": "text", "text": prompt})
        return content

    def structured(self, *, system: str, prompt: str, schema: type[T],
                   images: list[ImageInput] | None = None, task: str = "",
                   fallback: Callable[[], T] | None = None) -> tuple[T, LLMUsage]:
        a = self._anthropic
        messages = [{"role": "user", "content": self._content(prompt, images)}]
        models = [self.model] + ([self.fallback_model] if self.fallback_model else [])
        last_err: Exception | None = None
        for model in models:
            try:
                resp = self.client.messages.parse(model=model, max_tokens=16000, system=system,
                                                  messages=messages, output_format=schema)
            except a.RateLimitError as e:
                raise ProviderError(f"Anthropic rate limited: {e}", retryable=True) from e
            except a.APIStatusError as e:
                raise ProviderError(f"Anthropic API error {e.status_code}: {e.message}",
                                    retryable=e.status_code >= 500, status_code=e.status_code) from e
            except a.APIConnectionError as e:
                raise ProviderError(f"Anthropic connection error: {e}", retryable=True) from e
            if resp.stop_reason == "refusal":
                last_err = ProviderError(f"model {model} declined task '{task}'")
                continue  # client-side fallback to the next model
            if resp.stop_reason == "max_tokens":
                raise ProviderError(f"LLM output truncated for task '{task}'", retryable=True)
            parsed = resp.parsed_output
            if parsed is None:
                raise ProviderError(f"LLM returned no structured output for '{task}'", retryable=True)
            s = get_settings()
            usage = LLMUsage(input_tokens=resp.usage.input_tokens, output_tokens=resp.usage.output_tokens,
                             model=model)
            usage.cost_usd = (usage.input_tokens * s.anthropic_usd_per_mtok_in
                              + usage.output_tokens * s.anthropic_usd_per_mtok_out) / 1_000_000
            return parsed, usage
        raise last_err or ProviderError("LLM failed")
