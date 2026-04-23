from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from typing import Any

import requests
from flask import current_app


@dataclass
class KeywordMetrics:
    search_volume: int


class DataForSEOClient:
    """
    Real DataForSEO client with deterministic mock fallback.
    Only implements what's needed for this assessment (keyword search volume).
    """

    def __init__(
        self,
        login: str | None = None,
        password: str | None = None,
        timeout_s: int | None = None,
    ):
        cfg = current_app.config if current_app else {}
        self.login = login if login is not None else cfg.get("DATAFORSEO_LOGIN")
        self.password = password if password is not None else cfg.get("DATAFORSEO_PASSWORD")
        self.timeout_s = int(timeout_s if timeout_s is not None else cfg.get("DATAFORSEO_TIMEOUT_S", 30))

        self.base_url = "https://api.dataforseo.com/v3"

    def get_search_volume(self, query_text: str, *, location_code: int = 2840, language_code: str = "en") -> KeywordMetrics:
        if not self.login or not self.password:
            return KeywordMetrics(search_volume=_mock_volume(query_text))

        try:
            url = f"{self.base_url}/keywords_data/google_ads/search_volume/live"
            payload = [
                {
                    "keywords": [query_text],
                    "location_code": location_code,
                    "language_code": language_code,
                }
            ]
            resp = requests.post(
                url,
                headers={
                    "Authorization": _basic_auth_header(self.login, self.password),
                    "Content-Type": "application/json",
                },
                data=json.dumps(payload),
                timeout=self.timeout_s,
            )
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()

            # Best-effort parse. DataForSEO schema can vary by endpoint/version.
            volume = _extract_volume(data)
            if volume is None:
                volume = _mock_volume(query_text)
            return KeywordMetrics(search_volume=int(volume))
        except Exception:
            return KeywordMetrics(search_volume=_mock_volume(query_text))


def _basic_auth_header(login: str, password: str) -> str:
    token = base64.b64encode(f"{login}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def _extract_volume(data: dict[str, Any]) -> int | None:
    try:
        tasks = data.get("tasks") or []
        if not tasks:
            return None
        result = (tasks[0].get("result") or [])
        if not result:
            return None
        items = result[0].get("items") or result[0].get("keyword_data") or []
        if isinstance(items, dict):
            items = [items]
        if not items:
            return None
        first = items[0]
        # common fields
        for k in ("search_volume", "volume", "monthly_searches"):
            if k in first and first[k] is not None:
                return int(first[k])
        # nested
        if "keyword_info" in first and isinstance(first["keyword_info"], dict):
            ki = first["keyword_info"]
            if ki.get("search_volume") is not None:
                return int(ki["search_volume"])
        return None
    except Exception:
        return None


def _mock_volume(query_text: str) -> int:
    """
    Deterministic fallback volume (0..5000) so scoring stays stable in tests.
    """
    h = hashlib.sha256(query_text.strip().lower().encode("utf-8")).digest()
    return int.from_bytes(h[:2], "big") % 5001

