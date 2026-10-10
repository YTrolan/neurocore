"""Extensions: plugins and agent presets."""
import importlib.util
import json
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path


PLUGIN_DIR = Path.home() / ".neurocore" / "plugins"
PRESET_DIR = Path.home() / ".neurocore" / "presets"
PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
PRESET_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class PluginInfo:
    name: str
    path: Path
    loaded: bool
    error: str = ""
    tools: list = None


@dataclass
class Preset:
    name: str
    model: str
    system_prompt: str
    description: str = ""
    path: Path = None


DEFAULT_PRESETS = [
    {
        "name": "Default",
        "model": "deepseek-v4-pro",
        "description": "Обычный агент, все инструменты доступны.",
        "system_prompt": "",
    },
    {
        "name": "Code Reviewer",
        "model": "deepseek-v4-pro",
        "description": "Строгий ревьюер Python-кода. Ищет баги, не стилизует.",
        "system_prompt": (
            "Ты — строгий ревьюер Python-кода. Читай файлы через read_file и list_dir. "
            "Указывай конкретные строки, объясняй проблему, предлагай фикс. "
            "Не пиши общих похвал. Фокус на багах, не на стиле, если стиль не влияет на корректность."
        ),
    },
    {
        "name": "Explainer",
        "model": "deepseek-reasoner",
        "description": "Разбирает сложные темы пошагово, без воды.",
        "system_prompt": (
            "Ты — учитель. Объясняй пошагово, с примерами. Используй аналогии. "
            "В конце — короткое резюме в 3 пунктах. Избегай воды и повторов."
        ),
    },
    {
        "name": "Translator",
        "model": "deepseek-chat",
        "description": "Переводит тексты, сохраняя стиль. Без инструментов.",
        "system_prompt": (
            "Ты — переводчик. Переводи текст пользователя, сохраняя регистр, "
            "стиль, идиомы. Если язык не указан — переводи между русским и английским. "
            "Не добавляй пояснений, только перевод."
        ),
    },
]


def _write_default_presets():
    for p in DEFAULT_PRESETS:
        fname = p["name"].lower().replace(" ", "_") + ".json"
        fp = PRESET_DIR / fname
        if not fp.exists():
            fp.write_text(json.dumps(p, ensure_ascii=False, indent=2),
                          encoding="utf-8")


_write_default_presets()


def load_presets() -> list:
    _write_default_presets()
    out = []
    for p in sorted(PRESET_DIR.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            d.setdefault("model", "deepseek-v4-pro")
            d.setdefault("description", "")
            d.setdefault("system_prompt", "")
            out.append(Preset(
                name=d["name"], model=d["model"],
                system_prompt=d["system_prompt"],
                description=d["description"], path=p,
            ))
        except Exception:
            continue
    return out


def save_preset(name, model, system_prompt, description=""):
    fname = name.lower().replace(" ", "_") + ".json"
    fp = PRESET_DIR / fname
    fp.write_text(json.dumps({
        "name": name, "model": model,
        "system_prompt": system_prompt, "description": description,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return fp


def delete_preset(name):
    fname = name.lower().replace(" ", "_") + ".json"
    fp = PRESET_DIR / fname
    if fp.exists():
        fp.unlink()


def load_plugins(registry) -> list:
    """Сканирует PLUGIN_DIR, вызывает register(registry) в каждом .py."""
    infos = []
    for p in sorted(PLUGIN_DIR.glob("*.py")):
        if p.name.startswith("_"):
            continue
        info = PluginInfo(name=p.stem, path=p, loaded=False, tools=[])
        try:
            spec = importlib.util.spec_from_file_location(
                "neurocore_plugin_" + p.stem, p,
            )
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            if hasattr(mod, "register"):
                before = set(registry._tools.keys())
                mod.register(registry)
                after = set(registry._tools.keys())
                info.tools = sorted(after - before)
                info.loaded = True
            else:
                info.error = "нет функции register(registry)"
        except Exception as e:
            info.error = type(e).__name__ + ": " + str(e)
            info.error += "\n" + traceback.format_exc()[:400]
        infos.append(info)
    return infos


PLUGIN_TEMPLATE = """# Пример плагина NeuroCore.
# Сохрани этот файл в ~/.neurocore/plugins/my_plugin.py и перезапусти приложение.
from neurocore.tools.base import Tool


class EchoTool(Tool):
    name = "echo"
    description = "Возвращает переданный текст без изменений."
    parameters = {"text": "строка для эха"}

    def run(self, text: str) -> str:
        return "echo: " + text


def register(registry):
    registry.register(EchoTool())
"""


# ============================================================
# Официальные плагины (все встроенные)
# ============================================================
OFFICIAL_PLUGINS = [
    {
        "id": "agent_teams",
        "name": "Команды агентов",
        "icon": "users",
        "description": "Включить командную работу: инструменты команды, список участников и общую доску задач.",
        "experimental": True,
        "default": False,
    },
    {
        "id": "auto_auth_review",
        "name": "Автопроверка авторизации",
        "icon": "shield",
        "description": "Добавить режим автопроверки: модель оценивает авторизацию перед каждым вызовом инструмента.",
        "experimental": True,
        "default": False,
    },
    {
        "id": "automation_tasks",
        "name": "Автоматические задачи",
        "icon": "clock",
        "description": "Запускать задачи в сессиях по расписанию или в заданное время.",
        "experimental": True,
        "default": False,
    },
    {
        "id": "voice_input",
        "name": "Голосовой ввод",
        "icon": "mic",
        "description": "Локальная транскрипция записей через SenseVoice; при первом использовании нужны зависимости.",
        "experimental": True,
        "default": False,
    },
    {
        "id": "shell",
        "name": "Оболочка",
        "icon": "terminal",
        "description": "Ограничить время выполнения команды и размер её вывода.",
        "experimental": False,
        "default": True,
    },
    {
        "id": "agent_loop",
        "name": "Цикл агента",
        "icon": "loop",
        "description": "Управление тем, как агент вызывает инструменты.",
        "experimental": False,
        "default": True,
    },
    {
        "id": "subagent",
        "name": "Субагент",
        "icon": "layers",
        "description": "Настроить глубину рекурсии, количество и модели субагентов.",
        "experimental": False,
        "default": True,
    },
    {
        "id": "web_search",
        "name": "Веб-поиск",
        "icon": "search",
        "description": "Настроить поискового провайдера DeepSeek.",
        "experimental": False,
        "default": True,
    },
]


PLUGINS_STATE_FILE = PLUGIN_DIR.parent / "plugins_state.json"


def load_plugin_states() -> dict:
    """Возвращает {id: enabled_bool}."""
    defaults = {p["id"]: p["default"] for p in OFFICIAL_PLUGINS}
    if PLUGINS_STATE_FILE.exists():
        try:
            data = json.loads(PLUGINS_STATE_FILE.read_text(encoding="utf-8"))
            for k, v in data.items():
                if k in defaults:
                    defaults[k] = bool(v)
        except Exception:
            pass
    return defaults


def save_plugin_states(states: dict):
    PLUGINS_STATE_FILE.write_text(
        json.dumps(states, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
