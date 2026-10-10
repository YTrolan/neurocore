from pathlib import Path

from ..base import Tool


def _resolve(path: str) -> Path:
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    return p


class ReadFileTool(Tool):
    name = "read_file"
    description = "Прочитать содержимое файла. Путь может быть относительным или абсолютным."
    parameters = {"path": "путь к файлу"}

    def run(self, path: str) -> str:
        try:
            p = _resolve(path)
            if not p.exists():
                return "[error] файл не найден: " + str(p)
            if p.is_dir():
                return "[error] это директория, а не файл: " + str(p)
            return p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return "[error] " + type(e).__name__ + ": " + str(e)


class WriteFileTool(Tool):
    name = "write_file"
    description = ("Записать содержимое в файл (перезаписывает). "
                   "Если путь относительный — сохраняется в папку из "
                   "настроек (или текущую). Абсолютный путь — как есть.")
    parameters = {"path": "путь (можно только имя файла)",
                  "content": "новое содержимое"}

    def __init__(self, base_dir: str = ""):
        self.base_dir = base_dir

    def _target(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        # относительный — от base_dir или cwd
        if self.base_dir and Path(self.base_dir).exists():
            return Path(self.base_dir) / p
        return Path.cwd() / p

    def run(self, path: str, content: str) -> str:
        try:
            p = self._target(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return "[ok] записано " + str(len(content)) + " символов в " + str(p)
        except Exception as e:
            return "[error] " + type(e).__name__ + ": " + str(e)

class ListDirTool(Tool):
    name = "list_dir"
    description = "Показать содержимое директории. Без аргумента — текущая рабочая директория."
    parameters = {"path": "путь (по умолчанию текущая папка)"}

    def run(self, path: str = ".") -> str:
        try:
            p = _resolve(path)
            if not p.exists():
                return "[error] путь не найден: " + str(p)
            if not p.is_dir():
                return "[error] это не директория: " + str(p)
            entries = sorted(p.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
            lines = []
            for e in entries:
                lines.append(("d" if e.is_dir() else "f") + " " + e.name)
            return "[" + str(p) + "]\n" + ("\n".join(lines) if lines else "(пусто)")
        except Exception as e:
            return "[error] " + type(e).__name__ + ": " + str(e)
