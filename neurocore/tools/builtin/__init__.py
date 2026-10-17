"""Встроенные инструменты NeuroCore.

Инструменты сгруппированы по файлам:
    files.py            — базовые файловые операции
    shell.py            — shell
    web.py              — web
    deepseek_search.py  — поиск
    image.py            — генерация изображений
    browser_control.py  — управление браузером
    gui_control.py      — управление рабочим столом
    roblox_auto.py      — автоматизация Roblox
    token_tools.py      — токены
    toolkit.py          — набор 1
    toolkit_v2.py       — набор 2 (файлы/система/данные)
    toolkit_v3.py       — набор 3 (windows/dev/web/text/math/time)
"""
from importlib import import_module

__all__ = [
    "DeepSeekSearchTool",
    "ShellTool",
    "ReadFileTool",
    "WriteFileTool",
    "ListDirTool",
    "GenerateImageTool",
    "ALL_TOOLS",
    "ALL_V2_TOOLS",
    "ALL_V3_TOOLS",
    "ALL_DESKTOP_TOOLS",
    "ALL_BROWSER_TOOLS",
]

# Keep the public imports without loading every optional integration at startup.
_EXPORTS = {
    "DeepSeekSearchTool": ".deepseek_search",
    "ShellTool": ".shell",
    "ReadFileTool": ".files",
    "WriteFileTool": ".files",
    "ListDirTool": ".files",
    "GenerateImageTool": ".image",
    "ALL_TOOLS": ".toolkit",
    "ALL_V2_TOOLS": ".toolkit_v2",
    "ALL_V3_TOOLS": ".toolkit_v3",
    "ALL_DESKTOP_TOOLS": ".gui_control",
    "ALL_BROWSER_TOOLS": ".browser_control",
}


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(_EXPORTS[name], __name__), name)
    globals()[name] = value
    return value
