import json
import os
import platform
import re
from typing import Callable

from ..core.message import Message, Role
from ..core.provider import Provider
from ..tools.registry import ToolRegistry


SYSTEM_PROMPT = """Ты — NeuroCore, автономный агент. Решаешь задачи через инструменты.

ОКРУЖЕНИЕ:
{environment}

ПРАВИЛА РАБОТЫ:
- Если ОС = Windows — используй команды Windows (dir, type, copy, del). НЕ используй ls, cat, grep, find, rm, chmod, ~/. Они не работают.
- Пути указывай в формате текущей ОС. На Windows избегай ~, используй абсолютные пути из блока ОКРУЖЕНИЕ (home) или относительные.
- Когда задача решена — ответь обычным текстом БЕЗ вызова инструментов.
- Не выдумывай результаты — жди реального вывода инструмента.
- Если инструмент вернул ошибку — проанализируй и попробуй иначе. Не повторяй один и тот же вызов.
- Файлы скриншотов (screen.png, _see_tmp.png, browser.png и т.п.) УДАЛЯЙ через `desktop_cleanup_screenshots()` после того как посмотрел.
- Если пользователь НЕ указал путь — сохраняй файл БЕЗ пути, только имя (например `test.py`). Файл автоматически попадёт в папку по умолчанию из настроек. НЕ выдумывай полные пути.
- ЗАПРЕЩЕНО делать более 2 попыток поиска по одной задаче. Если поиск не дал результат — отвечай сразу с тем что есть.
- Если `deepseek_search` вернул ошибку или пусто — НЕ пробуй ещё раз, переходи к ответу текстом.
- СКОРОСТЬ ВАЖНЕЕ ПОЛНОТЫ. Максимум 3-5 вызовов тулов на задачу, потом ОТВЕЧАЙ.
- Для открытия сайта используй `desktop_open_url(url)` — ОДИН вызов, без shell/start.
- НЕ вызывай `desktop_windows` / `desktop_focus_window` больше 1 раза.
- `desktop_wait` максимум 1 секунда. Не ставь 5, 7, 8 секунд.
- Если делаешь скриншот — используй `desktop_screenshot`, потом `desktop_read_clipboard` если нужен текст со страницы.
- Для поиска в интернете — `deepseek_search` (5 секунд), НЕ desktop-манипуляции.
- Если задача не получается за 3 шага — отвечай с тем что есть.

КАК ВЫЗЫВАТЬ ИНСТРУМЕНТЫ:
Используй встроенный tool-call механизм DeepSeek. Пример правильного вызова:

<|DSML|invoke name="shell">
{"command": "dir"}


Можно вызывать несколько инструментов подряд — отдельными блоками .

ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
{tools}
"""


# --- Парсер 1: нативный DSML DeepSeek ---
_INVOKE_OPEN = re.compile(
    r"<[\|\uFF5C]+\s*DSML\s*[\|\uFF5C]+\s*invoke\s+name\s*=\s*[\"']([^\"']+)[\"']\s*>",
    re.IGNORECASE,
)
_DSML_TAG = re.compile(
    r"</?[\|\uFF5C]+\s*DSML\s*[\|\uFF5C]+\s*\w+\s*>",
    re.IGNORECASE,
)

# --- Парсер 2: наш JSON формат ---
_TOOL_CALL_RE = re.compile(r"<tool_call>\s*\n?(.*?)\n?</tool_call>", re.DOTALL)
_CODE_BLOCK_RE = re.compile(r"```(?:tool|json)\s*\n?(.*?)\n?```", re.DOTALL)


def _extract_json_object(text: str):
    """Находит первый валидный JSON-объект, учитывая строки и экранирование."""
    depth = 0
    start = -1
    in_str = False
    esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    obj = json.loads(text[start:i + 1])
                    if isinstance(obj, dict):
                        return obj
                except json.JSONDecodeError:
                    pass
                start = -1
    return None


def strip_dsml(text: str) -> str:
    """Убирает из текста все блоки и теги DSML (для показа пользователю)."""
    if not text:
        return text
    # вырезаем полные блоки <|DSML|invoke ...>...
    text = re.sub(
        r"<[\|\uFF5C]+\s*DSML\s*[\|\uFF5C]+\s*invoke\b.*?(?:</[\|\uFF5C]+\s*DSML\s*[\|\uFF5C]+\s*invoke\s*>|$)",
        "", text, flags=re.DOTALL | re.IGNORECASE,
    )
    # остатки одиночных тегов
    text = _DSML_TAG.sub("", text)
    return text.strip()


class Agent:
    def __init__(
        self,
        provider: Provider,
        tools: ToolRegistry,
        system_prompt: str = SYSTEM_PROMPT,
        max_iterations: int = 6,
        on_event: Callable[..., None] | None = None,
        should_stop: Callable[[], bool] | None = None,
    ):
        self.provider = provider
        self.tools = tools
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.on_event = on_event or (lambda *a, **k: None)
        self.should_stop = should_stop or (lambda: False)
        self.messages: list[Message] = []
        self._call_cache = {}  # {signature: результат} — антиповтор
        self._search_attempts = 0  # сколько раз подряд искали

    def _emit(self, event: str, **data):
        self.on_event(event, **data)

    def _environment(self) -> str:
        return (
            "OS: " + platform.system() + " " + platform.release() + "\n"
            "cwd: " + os.getcwd() + "\n"
            "home: " + os.path.expanduser("~")
        )

    def _system(self) -> Message:
        prompt = self.system_prompt.replace("{environment}", self._environment())
        prompt = prompt.replace("{tools}", self.tools.describe())
        return Message(Role.SYSTEM, prompt)

    # ---------------- парсинг ----------------

    def _parse_tool_calls(self, text: str) -> list[dict]:
        calls = self._parse_dsml(text)
        if calls:
            return calls

        for m in _TOOL_CALL_RE.finditer(text):
            obj = _extract_json_object(m.group(1))
            if obj and "name" in obj:
                calls.append(obj)
        if calls:
            return calls

        for m in _CODE_BLOCK_RE.finditer(text):
            obj = _extract_json_object(m.group(1))
            if obj and "name" in obj:
                calls.append(obj)
        return calls

    def _parse_dsml(self, text: str) -> list[dict]:
        calls = []
        openings = list(_INVOKE_OPEN.finditer(text))
        for i, m in enumerate(openings):
            name = m.group(1).strip()
            start = m.end()
            end = openings[i + 1].start() if i + 1 < len(openings) else len(text)
            body = text[start:end]
            body = _DSML_TAG.sub("", body).strip()

            args = self._extract_dsml_args(body)
            calls.append({"name": name, "arguments": args})
        return calls

    def _extract_dsml_args(self, body: str) -> dict:
        obj = _extract_json_object(body)
        if obj is not None:
            return obj

        args = {}
        for pm in re.finditer(
            r"<[\|\uFF5C]+\s*DSML\s*[\|\uFF5C]+\s*parameter\s+name\s*=\s*"
            r"[\"']([^\"']+)[\"']\s*>(.*?)</[\|\uFF5C]+\s*DSML\s*[\|\uFF5C]+\s*parameter\s*>",
            body, re.DOTALL | re.IGNORECASE,
        ):
            key = pm.group(1).strip()
            val = pm.group(2).strip()
            try:
                val = json.loads(val)
            except json.JSONDecodeError:
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
            args[key] = val
        return args

    # ---------------- исполнение ----------------

    def _execute(self, name: str, arguments: dict) -> str:
        tool = self.tools.get(name)
        if not tool:
            return "[error] неизвестный инструмент: " + name
        try:
            return tool.run(**arguments)
        except TypeError as e:
            return "[error] неверные аргументы для " + name + ": " + str(e)
        except Exception as e:
            return "[error] " + type(e).__name__ + ": " + str(e)

    def _tool_result_message(self, name: str, result: str) -> Message:
        body = (
            "<|DSML|tool_result name=\"" + name + "\">\n"
            + result
            + "\n"
        )
        return Message(Role.TOOL, body, name=name)

    def run(self, user_input: str, attachments=None) -> str:
        if attachments and hasattr(self.provider, "set_pending_files"):
            self.provider.set_pending_files(attachments)

        self.messages.append(Message(Role.USER, user_input))
        self._call_cache = {}
        self._search_attempts = 0
        last_assistant_text = ""

        for iteration in range(1, self.max_iterations + 1):
            if self.should_stop():
                return last_assistant_text or "[остановлено]"

            self._emit("thinking", iteration=iteration)

            response = self.provider.chat([self._system(), *self.messages])
            self.messages.append(response)
            self._emit("assistant", text=response.content)
            if response.content and response.content.strip():
                last_assistant_text = response.content

            calls = self._parse_tool_calls(response.content)
            if not calls:
                if "DSML" in response.content:
                    self._emit("parse_error", error="raw DSML in text")
                    hint = (
                        "Твой вызов инструмента не распознан. "
                        "Ответь ЕЩЁ РАЗ, соблюдая правила: "
                        "1) только ОДИН закрывающий тег </|DSML|invoke>; "
                        "2) пути пиши через forward slash "
                        "(C:/Users/rolan/Downloads), а не через backslash; "
                        "3) JSON должен быть валидным."
                    )
                    self.messages.append(Message(Role.USER, hint))
                    continue
                return response.content

            had_progress = False
            for call in calls:
                if self.should_stop():
                    return last_assistant_text or "[остановлено]"

                name = call.get("name", "?")
                args = call.get("arguments", {}) or {}
                self._emit("tool_call", name=name, arguments=args)

                import json as _json
                try:
                    sig = name + ":" + _json.dumps(args, sort_keys=True, ensure_ascii=False)
                except Exception:
                    sig = name + ":" + str(args)

                if sig in self._call_cache:
                    result = ("[BLOCKED] Уже вызывалось. НЕ повторяй, "
                              "ответь текстом или попробуй другой метод.")
                    self._emit("tool_result", name=name, result=result)
                    self.messages.append(self._tool_result_message(name, result))
                    continue

                result = self._execute(name, args)
                self._call_cache[sig] = result
                self._emit("tool_result", name=name, result=result)
                self.messages.append(self._tool_result_message(name, result))
                had_progress = True

                # отдельный счётчик для search-тулов
                if "search" in name.lower() or "web" in name.lower():
                    self._search_attempts += 1
                    if self._search_attempts >= 3 and "не удал" in result.lower():
                        return (last_assistant_text +
                                "\n\n(поиск не дал результатов — "
                                "используй browser_open для конкретного URL)")

            # если все вызовы были заблокированы — не тратим итерацию
            if not had_progress:
                return (last_assistant_text +
                        "\n\n[повторы заблокированы, отвечаю тем что есть]")

        # финал — возвращаем последний ассистентский текст, не ошибку
        return (last_assistant_text or
                "[задача не завершена, попробуй переформулировать]")

