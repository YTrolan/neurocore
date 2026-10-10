"""OpenDeep provider — stateless, без серверной памяти."""
import opendeep
from opendeep import GenerativeModel

from ..token_manager import load_token
from .message import Message, Role
from .provider import Provider


class OpenDeepProvider(Provider):
    """
    Stateless-провайдер. Каждый chat() — независимый запрос.

    ВАЖНО: НЕ используем start_chat() — он держит серверную сессию,
    которая общая на весь токен. Из-за этого сессии NeuroCore путались.

    Вся история передаётся в промпте каждый раз (Agent это делает сам).
    """

    def __init__(
        self,
        token: str,
        model: str = "deepseek-v4-pro",
        thinking: bool = False,
    ):
        if not token:
            token = load_token()
        opendeep.configure(api_key=token)
        self._model = GenerativeModel(model)
        self._thinking = thinking

    def chat(self, messages: list[Message]) -> Message:
        # Собираем ВСЮ историю в один промпт
        prompt_parts = []
        for m in messages:
            if m.role == Role.SYSTEM:
                prompt_parts.append(m.content)
            elif m.role == Role.USER:
                prompt_parts.append("Пользователь: " + m.content)
            elif m.role == Role.ASSISTANT:
                prompt_parts.append("Ассистент: " + m.content)
            elif m.role == Role.TOOL:
                prompt_parts.append(
                    "[результат " + (m.name or "tool") + "]:\n" + m.content
                )

        prompt = "\n\n".join(prompt_parts)

        # stateless — каждый раз новый запрос, без истории на сервере
        response = self._model.generate_content(prompt)
        return Message(role=Role.ASSISTANT, content=response.text)

    def reset(self) -> None:
        # ничего не кэшируем — сбрасывать нечего
        pass
