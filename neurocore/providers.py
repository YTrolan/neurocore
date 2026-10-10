"""Provider implementations: opendeep + OpenAI-compatible."""
import os
from abc import ABC, abstractmethod

from .core.message import Message, Role
from .deepseek_client import DeepSeekClient


class Provider(ABC):
    name = "provider"
    model = ""

    @abstractmethod
    def chat(self, messages: list) -> Message: ...

    def reset(self):
        pass


class OpenDeepProvider(Provider):
    name = "DeepSeek"

    def __init__(self, token: str, model: str = "deepseek-v4-pro",
                 thinking: bool = False):
        self.model = model
        self._thinking = thinking
        self._client = DeepSeekClient(token, model=model,
                                        thinking=thinking)
        self._pending_files = []  # пути картинок для следующего запроса

    def set_pending_files(self, paths):
        self._pending_files = list(paths or [])

    def _collect_prompt(self, messages):
        parts = []
        for m in messages:
            if m.role == Role.SYSTEM:
                parts.append(m.content)
            elif m.role == Role.USER:
                parts.append(m.content)
            elif m.role == Role.TOOL:
                parts.append("[tool:" + (m.name or "") + "]\n" + m.content)
        return "\n\n".join(parts)

    def chat(self, messages):
        prompt = self._collect_prompt(messages)

        # если есть отложенные картинки — загружаем и шлём с ними
        pending = self._pending_files
        self._pending_files = []

        file_ids = []
        if pending:
            print(f"[vision] загружаю {len(pending)} картинок…")
            for p in pending:
                fid = self._client.upload_and_wait(p)
                if fid:
                    file_ids.append(fid)
                    print(f"[vision] {fid} готов")

        text = self._client.send(prompt, file_ids=file_ids)
        return Message(role=Role.ASSISTANT, content=text)

    def reset(self):
        self._client.reset()



class OpenAICompatProvider(Provider):
    name = "OpenAI-compatible"

    def __init__(self, base_url, api_key, model):
        from openai import OpenAI
        self._client = OpenAI(base_url=base_url, api_key=api_key or "none")
        self.model = model
        self.name = base_url

    def chat(self, messages):
        api_msgs = []
        for m in messages:
            if m.role == Role.SYSTEM:
                api_msgs.append({"role": "system", "content": m.content})
            elif m.role == Role.USER:
                api_msgs.append({"role": "user", "content": m.content})
            elif m.role == Role.ASSISTANT:
                api_msgs.append({"role": "assistant", "content": m.content})
            elif m.role == Role.TOOL:
                api_msgs.append({"role": "user",
                                 "content": "[tool:" + (m.name or "") + "]\n" + m.content})
        r = self._client.chat.completions.create(
            model=self.model, messages=api_msgs, temperature=0.7,
        )
        return Message(role=Role.ASSISTANT,
                       content=r.choices[0].message.content or "")


def build(cfg: dict):
    """Собирает активный провайдер из конфига."""
    from . import config as cfgmod
    p = cfgmod.active_provider(cfg)
    model = cfg.get("active_model") or (p["models"][0] if p["models"] else "")
    if p["kind"] == "opendeep":
        token = p.get("api_key") or os.getenv("DEEPSEEK_TOKEN", "")
        thinking = bool(cfg.get("thinking", False))
        return OpenDeepProvider(token=token, model=model, thinking=thinking)
    elif p["kind"] == "openai_compat":
        return OpenAICompatProvider(
            base_url=p["base_url"], api_key=p["api_key"], model=model)
    raise ValueError("Неизвестный тип провайдера: " + p["kind"])
