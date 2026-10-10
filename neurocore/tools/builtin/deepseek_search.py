"""Поиск через встроенный DeepSeek Search (только Flash)."""
import os
import time

from ...token_manager import load_token
from ..base import Tool


class DeepSeekSearchTool(Tool):
    """Встроенный веб-поиск DeepSeek. Работает только на Flash-модели."""

    name = "deepseek_search"
    description = (
        "Найти информацию в интернете через встроенный поиск DeepSeek. "
        "Возвращает свежий ответ со ссылками. Используй для актуальных "
        "данных: новости, погода, курсы, свежая документация."
    )
    parameters = {
        "query": "поисковый запрос (можно на русском)",
    }

    def __init__(self, token: str | None = None):
        self._token = token or load_token()

    def run(self, query: str) -> str:
        if not self._token:
            return ("[error] DEEPSEEK_TOKEN не задан, "
                    "используй web_search как fallback")
        try:
            import opendeep
            from opendeep import GenerativeModel

            opendeep.configure(api_key=self._token)
            m = GenerativeModel("deepseek-v4-flash")

            t0 = time.time()
            resp = m.generate_content(query, search_enabled=True)
            dt = time.time() - t0
            text = (resp.text or "").strip()
            if not text:
                return "[error] Flash+search вернул пусто"
            return f"[search {dt:.1f}s]\n{text}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


__all__ = ["DeepSeekSearchTool"]
