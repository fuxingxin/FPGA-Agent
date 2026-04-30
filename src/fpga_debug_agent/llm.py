from __future__ import annotations

import os
from typing import Protocol


class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str:
        ...


class RuleBasedLLM:
    """Deterministic fallback used when no API key is available.

    The project is intentionally runnable on a normal machine without cloud access.
    In production, replace this with OpenAIClient or any internal LLM provider.
    """

    def complete(self, system: str, user: str) -> str:
        return (
            "No external LLM is configured. The rule-based analyzers generated the main report. "
            "Set OPENAI_API_KEY to enable natural-language synthesis and deeper code reasoning."
        )


class OpenAIClient:
    def __init__(self, model: str = "gpt-4.1") -> None:
        try:
            from openai import OpenAI  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Install with `pip install -e .[llm]` to enable OpenAI support") from exc
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._model = model

    def complete(self, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.1,
        )
        return response.choices[0].message.content or ""


def build_llm(model: str = "gpt-4.1") -> LLMClient:
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIClient(model=model)
    return RuleBasedLLM()
