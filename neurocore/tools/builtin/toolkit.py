"""Дополнительные инструменты NeuroCore — большой пакет."""
import base64 as _b64
import hashlib
import json as _json
import os
import platform
import random
import shutil as _sh
import time
import urllib.request
import uuid as _uuid
import webbrowser
import zipfile
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QApplication

from ..base import Tool

try:
    import psutil
except ImportError:  # psutil необязателен
    psutil = None

try:
    from win10toast import ToastNotifier
except ImportError:  # win10toast необязателен
    ToastNotifier = None


# ============================================================
# ФАЙЛЫ
# ============================================================
class GrepTool(Tool):
    name = "grep"
    description = "Найти строки в файлах по подстроке (рекурсивно)."
    parameters = {"pattern": "что искать",
                  "path": "где искать (по умолчанию '.')",
                  "ext": "расширение, например .py (опционально)"}

    def run(self, pattern: str, path: str = ".", ext: str = "") -> str:
        try:
            root = Path(path)
            hits = []
            for f in root.rglob("*" + ext if ext else "*"):
                if not f.is_file():
                    continue
                try:
                    for i, line in enumerate(
                        f.read_text(encoding="utf-8", errors="ignore").split("\n"), 1
                    ):
                        if pattern in line:
                            hits.append(f"{f}:{i}: {line.rstrip()[:120]}")
                            if len(hits) > 300:
                                break
                except Exception:
                    continue
                if len(hits) > 300:
                    break
            return "\n".join(hits) or "(совпадений нет)"
        except Exception as e:
            return f"[error] {e}"


class FindTool(Tool):
    name = "find"
    description = "Найти файлы по маске (например *.py)."
    parameters = {"mask": "маска, например *.py",
                  "path": "директория (по умолчанию '.')"}

    def run(self, mask: str = "*", path: str = ".") -> str:
        try:
            files = list(Path(path).rglob(mask))
            return "\n".join(str(f) for f in files[:500]) or "(нет)"
        except Exception as e:
            return f"[error] {e}"


class MkdirTool(Tool):
    name = "mkdir"
    description = "Создать директорию (с родителями)."
    parameters = {"path": "путь к папке"}

    def run(self, path: str) -> str:
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return f"[ok] создано: {path}"
        except Exception as e:
            return f"[error] {e}"


class RemoveTool(Tool):
    name = "rm"
    description = "Удалить файл или папку."
    parameters = {"path": "путь", "recursive": "true — для папки"}

    def run(self, path: str, recursive: str = "false") -> str:
        try:
            p = Path(path)
            if recursive.lower() == "true":
                _sh.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
            return f"[ok] удалено: {path}"
        except Exception as e:
            return f"[error] {e}"


class MoveTool(Tool):
    name = "mv"
    description = "Переместить/переименовать файл или папку."
    parameters = {"src": "откуда", "dst": "куда"}

    def run(self, src: str, dst: str) -> str:
        try:
            _sh.move(src, dst)
            return f"[ok] {src} → {dst}"
        except Exception as e:
            return f"[error] {e}"


class CopyTool(Tool):
    name = "cp"
    description = "Скопировать файл или папку."
    parameters = {"src": "откуда", "dst": "куда"}

    def run(self, src: str, dst: str) -> str:
        try:
            s = Path(src)
            if s.is_dir():
                _sh.copytree(src, dst, dirs_exist_ok=True)
            else:
                _sh.copy2(src, dst)
            return f"[ok] {src} → {dst}"
        except Exception as e:
            return f"[error] {e}"


class HeadTool(Tool):
    name = "head"
    description = "Первые N строк файла (по умолчанию 20)."
    parameters = {"path": "файл", "n": "сколько строк"}

    def run(self, path: str, n: str = "20") -> str:
        try:
            k = int(n)
            lines = Path(path).read_text(encoding="utf-8", errors="ignore").split("\n")
            return "\n".join(lines[:k])
        except Exception as e:
            return f"[error] {e}"


class TailTool(Tool):
    name = "tail"
    description = "Последние N строк файла (по умолчанию 20)."
    parameters = {"path": "файл", "n": "сколько строк"}

    def run(self, path: str, n: str = "20") -> str:
        try:
            k = int(n)
            lines = Path(path).read_text(encoding="utf-8", errors="ignore").split("\n")
            return "\n".join(lines[-k:])
        except Exception as e:
            return f"[error] {e}"


class WcTool(Tool):
    name = "wc"
    description = "Подсчитать строки/слова/символы файла."
    parameters = {"path": "файл"}

    def run(self, path: str) -> str:
        try:
            t = Path(path).read_text(encoding="utf-8", errors="ignore")
            return (f"строк: {t.count(chr(10))+1}  "
                    f"слов: {len(t.split())}  "
                    f"символов: {len(t)}")
        except Exception as e:
            return f"[error] {e}"


# ============================================================
# СИСТЕМА
# ============================================================
class SystemInfoTool(Tool):
    name = "system_info"
    description = "Информация о системе: ОС, CPU, Python, память."
    parameters = {}

    def run(self) -> str:
        try:
            lines = [
                f"OS:       {platform.system()} {platform.release()}",
                f"Machine:  {platform.machine()}",
                f"Processor:{platform.processor()}",
                f"Python:   {platform.python_version()}",
                f"CWD:      {os.getcwd()}",
            ]
            if psutil is not None:
                lines.append(f"CPU:      {psutil.cpu_percent(interval=0.1)}%")
                vm = psutil.virtual_memory()
                lines.append(f"RAM:      {vm.used // 1024 // 1024} / "
                             f"{vm.total // 1024 // 1024} MB")
            return "\n".join(lines)
        except Exception as e:
            return f"[error] {e}"


class ProcessListTool(Tool):
    name = "process_list"
    description = "Список запущенных процессов."
    parameters = {"filter": "фильтр по имени (опционально)"}

    def run(self, filter: str = "") -> str:
        if psutil is None:
            return "[error] нужен psutil: pip install psutil"
        try:
            rows = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent"]):
                try:
                    n = p.info["name"] or ""
                    if filter and filter.lower() not in n.lower():
                        continue
                    rows.append(f"{p.info['pid']:>6}  {n}")
                except Exception:
                    continue
            return "\n".join(rows[:200]) or "(нет)"
        except Exception as e:
            return f"[error] {e}"


class EnvGetTool(Tool):
    name = "env_get"
    description = "Получить значение переменной окружения."
    parameters = {"name": "имя переменной"}

    def run(self, name: str) -> str:
        v = os.environ.get(name)
        return f"{name}={v}" if v is not None else f"(нет переменной {name})"


class EnvSetTool(Tool):
    name = "env_set"
    description = "Установить переменную окружения в текущем процессе."
    parameters = {"name": "имя", "value": "значение"}

    def run(self, name: str, value: str) -> str:
        os.environ[name] = value
        return f"[ok] {name} установлена"


class DiskUsageTool(Tool):
    name = "disk_usage"
    description = "Свободное место на дисках."
    parameters = {}

    def run(self) -> str:
        if psutil is not None:
            try:
                out = []
                for part in psutil.disk_partitions():
                    try:
                        u = psutil.disk_usage(part.mountpoint)
                        out.append(
                            f"{part.device:15} {u.free // 1024**3} GB свободно "
                            f"из {u.total // 1024**3} GB")
                    except Exception:
                        continue
                return "\n".join(out)
            except Exception as e:
                return f"[error] {e}"
        t, u, f = _sh.disk_usage(".")
        return f"свободно: {f // 1024**3} GB из {t // 1024**3} GB"


# ============================================================
# ДАННЫЕ
# ============================================================
class Base64Tool(Tool):
    name = "base64"
    description = "Кодировать/декодировать строку в base64."
    parameters = {"mode": "encode или decode", "text": "строка"}

    def run(self, mode: str, text: str) -> str:
        try:
            if mode == "encode":
                return _b64.b64encode(text.encode()).decode()
            return _b64.b64decode(text.encode()).decode()
        except Exception as e:
            return f"[error] {e}"


class HashTool(Tool):
    name = "hash"
    description = "MD5/SHA256 хеш строки или файла."
    parameters = {"target": "строка или путь к файлу",
                  "algo": "md5 или sha256 (по умолчанию sha256)"}

    def run(self, target: str, algo: str = "sha256") -> str:
        try:
            h = hashlib.new(algo)
            p = Path(target)
            if p.is_file():
                with open(p, "rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):
                        h.update(chunk)
            else:
                h.update(target.encode())
            return h.hexdigest()
        except Exception as e:
            return f"[error] {e}"


class JsonPrettyTool(Tool):
    name = "json_pretty"
    description = "Форматировать JSON строку."
    parameters = {"text": "JSON строка"}

    def run(self, text: str) -> str:
        try:
            return _json.dumps(_json.loads(text), indent=2, ensure_ascii=False)
        except Exception as e:
            return f"[error] {e}"


class UuidTool(Tool):
    name = "uuid"
    description = "Сгенерировать UUID4."
    parameters = {}

    def run(self) -> str:
        return str(_uuid.uuid4())


class RandTool(Tool):
    name = "rand"
    description = "Случайное число или строка."
    parameters = {"min": "мин (по умолчанию 0)",
                  "max": "макс (по умолчанию 100)"}

    def run(self, min: str = "0", max: str = "100") -> str:
        try:
            return str(random.randint(int(min), int(max)))
        except Exception as e:
            return f"[error] {e}"


# ============================================================
# WEB
# ============================================================
class HttpGetTool(Tool):
    name = "http_get"
    description = "Сделать GET-запрос к URL, вернуть текст ответа."
    parameters = {"url": "адрес",
                  "timeout": "секунд (по умолчанию 15)"}

    def run(self, url: str, timeout: str = "15") -> str:
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 NeuroCore/0.1"})
            with urllib.request.urlopen(req, timeout=float(timeout)) as r:
                data = r.read().decode("utf-8", errors="ignore")
            return data[:5000] + ("\n..." if len(data) > 5000 else "")
        except Exception as e:
            return f"[error] {e}"


class DownloadFileTool(Tool):
    name = "download_file"
    description = "Скачать файл по URL и сохранить на диск."
    parameters = {"url": "адрес", "path": "куда сохранить"}

    def run(self, url: str, path: str) -> str:
        try:
            urllib.request.urlretrieve(url, path)
            size = Path(path).stat().st_size
            return f"[ok] скачано {size} байт в {path}"
        except Exception as e:
            return f"[error] {e}"


class OpenUrlTool(Tool):
    name = "open_url"
    description = "Открыть URL в браузере по умолчанию."
    parameters = {"url": "адрес"}

    def run(self, url: str) -> str:
        try:
            webbrowser.open(url)
            return f"[ok] открываю {url}"
        except Exception as e:
            return f"[error] {e}"


# ============================================================
# УТИЛИТЫ
# ============================================================
class CalcTool(Tool):
    name = "calc"
    description = "Вычислить математическое выражение (безопасно)."
    parameters = {"expr": "выражение, например 2+2*10"}

    def run(self, expr: str) -> str:
        try:
            allowed = set("0123456789+-*/().%^ ")
            if not set(expr) <= allowed:
                return "[error] недопустимые символы"
            safe = expr.replace("^", "**")
            return str(eval(safe, {"__builtins__": {}}, {}))
        except Exception as e:
            return f"[error] {e}"


class SleepTool(Tool):
    name = "sleep"
    description = "Подождать N секунд."
    parameters = {"seconds": "сколько (можно дробное)"}

    def run(self, seconds: str = "1") -> str:
        try:
            time.sleep(float(seconds))
            return f"[ok] подождал {seconds}s"
        except Exception as e:
            return f"[error] {e}"


class TimeNowTool(Tool):
    name = "time_now"
    description = "Текущее время и дата."
    parameters = {}

    def run(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class NotifyTool(Tool):
    name = "notify"
    description = "Показать системное уведомление Windows."
    parameters = {"title": "заголовок", "text": "текст"}

    def run(self, title: str, text: str) -> str:
        if ToastNotifier is None:
            return "[error] нужен win10toast: pip install win10toast"
        try:
            ToastNotifier().show_toast(title, text, duration=5)
            return "[ok] уведомление показано"
        except Exception as e:
            return f"[error] {e}"


class ClipboardGetTool(Tool):
    name = "clipboard_get"
    description = "Получить текст из буфера обмена."
    parameters = {}

    def run(self) -> str:
        try:
            return QApplication.clipboard().text() or "(пусто)"
        except Exception as e:
            return f"[error] {e}"


class ClipboardSetTool(Tool):
    name = "clipboard_set"
    description = "Положить текст в буфер обмена."
    parameters = {"text": "что положить"}

    def run(self, text: str) -> str:
        try:
            QApplication.clipboard().setText(text)
            return f"[ok] скопировано {len(text)} символов"
        except Exception as e:
            return f"[error] {e}"


# ============================================================
# АРХИВЫ
# ============================================================
class ZipCreateTool(Tool):
    name = "zip_create"
    description = "Заархивировать папку или файл в ZIP."
    parameters = {"src": "что архивировать", "dst": "имя .zip"}

    def run(self, src: str, dst: str) -> str:
        try:
            s = Path(src)
            with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
                if s.is_file():
                    z.write(s, s.name)
                else:
                    for f in s.rglob("*"):
                        if f.is_file():
                            z.write(f, f.relative_to(s.parent))
            return f"[ok] архив: {dst}"
        except Exception as e:
            return f"[error] {e}"


class ZipExtractTool(Tool):
    name = "zip_extract"
    description = "Распаковать ZIP."
    parameters = {"path": "архив", "dst": "куда (по умолчанию '.')"}

    def run(self, path: str, dst: str = ".") -> str:
        try:
            with zipfile.ZipFile(path, "r") as z:
                z.extractall(dst)
            return f"[ok] распаковано в {dst}"
        except Exception as e:
            return f"[error] {e}"


# ============================================================
# СПИСОК ВСЕХ ТУЛОВ (для регистрации)
# ============================================================
ALL_TOOLS = [
    GrepTool, FindTool, MkdirTool, RemoveTool, MoveTool, CopyTool,
    HeadTool, TailTool, WcTool,
    SystemInfoTool, ProcessListTool, EnvGetTool, EnvSetTool, DiskUsageTool,
    Base64Tool, HashTool, JsonPrettyTool, UuidTool, RandTool,
    HttpGetTool, DownloadFileTool, OpenUrlTool,
    CalcTool, SleepTool, TimeNowTool, NotifyTool,
    ClipboardGetTool, ClipboardSetTool,
    ZipCreateTool, ZipExtractTool,
]
