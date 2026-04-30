from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1"
    vivado_bin: str | None = None

    @staticmethod
    def from_env() -> "Settings":
        return Settings(
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
            vivado_bin=os.getenv("VIVADO_BIN") or None,
        )
