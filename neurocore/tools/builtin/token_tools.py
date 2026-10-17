"""Управление токеном через UI."""
from ...token_manager import clear_token, load_token
from ..base import Tool


class TokenStatusTool(Tool):
    name = "token_status"
    description = "Показать статус токена DeepSeek (задан или нет)."
    parameters = {}

    def run(self) -> str:
        t = load_token()
        if not t:
            return "[!] Токен НЕ задан. Открой настройки → DeepSeek."
        return f"[ok] Токен задан (первые 20): {t[:20]}... длина {len(t)}"


class TokenClearTool(Tool):
    name = "token_clear"
    description = "Удалить сохранённый токен."
    parameters = {}

    def run(self) -> str:
        clear_token()
        return "[ok] Токен удалён"


ALL_TOKEN_TOOLS = [TokenStatusTool, TokenClearTool]
