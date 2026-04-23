from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from flask import current_app

from app.utils.json_parser import safe_json_parse


@dataclass
class LLMResult:
    text: str
    tokens_used: int | None = None
    raw: dict[str, Any] | None = None


class OpenAILLMClient:
    """
    Simple OpenAI wrapper (no LangChain).
    Uses real API if OPENAI_API_KEY is set, otherwise deterministic mock.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None, timeout_s: int | None = None):
        cfg = current_app.config if current_app else {}
        self.api_key = api_key if api_key is not None else cfg.get("OPENAI_API_KEY")
        self.model = model if model is not None else cfg.get("OPENAI_MODEL", "gpt-4o")
        self.timeout_s = int(timeout_s if timeout_s is not None else cfg.get("OPENAI_TIMEOUT_S", 30))

    def chat(self, *, system: str, user: str, response_format_json: bool = False) -> LLMResult:
        if not self.api_key:
            return self._mock(system=system, user=user)

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key, timeout=self.timeout_s)
            kwargs: dict[str, Any] = {}
            if response_format_json:
                kwargs["response_format"] = {"type": "json_object"}

            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.2,
                **kwargs,
            )
            text = resp.choices[0].message.content or ""
            tokens_used = None
            try:
                tokens_used = int(getattr(resp, "usage", None).total_tokens)  # type: ignore[union-attr]
            except Exception:
                tokens_used = None

            return LLMResult(text=text, tokens_used=tokens_used, raw=_safe_dump(resp))
        except Exception:
            return self._mock(system=system, user=user)

    def chat_json(self, *, system: str, user: str) -> tuple[Any, LLMResult]:
        res = self.chat(system=system, user=user, response_format_json=False)
        parsed = safe_json_parse(res.text)
        return parsed, res

    def _mock(self, *, system: str, user: str) -> LLMResult:
        seed = f"{system}\n{user}".encode("utf-8", errors="ignore")
        # deterministic-ish "token estimate" without depending on provider
        tokens_used = max(1, len(seed) // 20)
        # Small delay to mimic network latency a bit (keeps pipeline realistic in demos)
        time.sleep(0.05)
        return LLMResult(
            text=json.dumps({"mock": True, "note": "OPENAI_API_KEY missing or call failed"}),
            tokens_used=tokens_used,
            raw=None,
        )


def _safe_dump(resp: Any) -> dict[str, Any]:
    try:
        return json.loads(resp.model_dump_json())  # type: ignore[attr-defined]
    except Exception:
        try:
            return resp.model_dump()  # type: ignore[attr-defined]
        except Exception:
            return {"raw": str(resp)}

