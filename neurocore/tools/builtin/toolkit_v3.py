"""toolkit_v3 — 100 инструментов для NeuroCore."""
import base64
import configparser
import csv
import hashlib
import hmac
import html
import http.client
import io
import ipaddress
import json
import math
import os
import pickle
import platform
import plistlib
import random
import re
import secrets
import shutil
import socket
import sqlite3
import ssl
import string
import subprocess
import sys
import tempfile
import textwrap
import time
import urllib.parse
import urllib.request
import uuid as _uuid
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

from ..base import Tool


def _resolve_path(path):
    """Ищет файл: сначала абсолютный, потом cwd, потом Downloads, потом output_dir."""
    p = Path(path)
    if p.is_absolute() and p.exists():
        return p
    # cwd
    if (Path.cwd() / p).exists():
        return Path.cwd() / p
    # Downloads
    dl = Path.home() / "Downloads" / p
    if dl.exists():
        return dl
    # из настроек output_dir
    try:
        from ... import config as _cfg
        d = _cfg.load().get("output_dir", "")
        if d and (Path(d) / p).exists():
            return Path(d) / p
    except Exception:
        pass
    # дефолт — cwd (даже если нет)
    return Path.cwd() / p




def _size_h(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


# ============================================================
# 1-10. WINDOWS SYSTEM
# ============================================================
class RegReadTool(Tool):
    name = "win_reg_read"
    description = "Прочитать значение из реестра Windows."
    parameters = {"key": "путь ключа", "name": "имя значения"}

    def run(self, key, name=""):
        try:
            import winreg
        except ImportError:
            return "[error] только Windows"
        try:
            # HKEY_LOCAL_MACHINE\... парсим
            parts = key.split("\\", 1)
            hive_map = {"HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
                        "HKLM": winreg.HKEY_LOCAL_MACHINE,
                        "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
                        "HKCU": winreg.HKEY_CURRENT_USER}
            hive = hive_map.get(parts[0].upper())
            if not hive:
                return "[error] неверный hive"
            sub = parts[1] if len(parts) > 1 else ""
            with winreg.OpenKey(hive, sub) as k:
                if name:
                    v, t = winreg.QueryValueEx(k, name)
                    return f"{name} = {v!r}"
                # перечислим все
                out, i = [], 0
                while True:
                    try:
                        n, v, t = winreg.EnumValue(k, i)
                        out.append(f"{n} = {v!r}")
                        i += 1
                    except OSError:
                        break
                return "\n".join(out) or "(пусто)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class RegWriteTool(Tool):
    name = "win_reg_write"
    description = "Записать значение в реестр."
    parameters = {"key": "путь", "name": "имя", "value": "значение",
                  "type": "REG_SZ|REG_DWORD"}

    def run(self, key, name, value, type="REG_SZ"):
        try:
            import winreg
        except ImportError:
            return "[error] только Windows"
        try:
            parts = key.split("\\", 1)
            hive_map = {"HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
                        "HKLM": winreg.HKEY_LOCAL_MACHINE,
                        "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
                        "HKCU": winreg.HKEY_CURRENT_USER}
            hive = hive_map.get(parts[0].upper())
            sub = parts[1] if len(parts) > 1 else ""
            t = winreg.REG_DWORD if "DWORD" in type.upper() else winreg.REG_SZ
            v = int(value) if t == winreg.REG_DWORD else str(value)
            with winreg.CreateKey(hive, sub) as k:
                winreg.SetValueEx(k, name, 0, t, v)
            return f"[ok] {key}\\{name} = {value}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class ServiceStatusTool(Tool):
    name = "win_service_status"
    description = "Статус службы Windows."
    parameters = {"name": "имя службы"}

    def run(self, name):
        try:
            r = subprocess.run(["sc", "query", name],
                                capture_output=True, text=True, timeout=10,
                                encoding="cp866", errors="replace")
            return (r.stdout or r.stderr)[:1500] or "(пусто)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class ServiceListTool(Tool):
    name = "win_service_list"
    description = "Список запущенных служб."
    parameters = {"filter": "подстрока в имени"}

    def run(self, filter=""):
        try:
            r = subprocess.run(["sc", "query", "type=", "service", "state=", "all"],
                                capture_output=True, text=True, timeout=20,
                                encoding="cp866", errors="replace")
            lines = (r.stdout or "").split("\n")
            out = []
            name = None
            for l in lines:
                l = l.strip()
                if l.startswith("SERVICE_NAME:"):
                    name = l.split(":", 1)[1].strip()
                elif l.startswith("STATE"):
                    state = l.split(":", 1)[1].strip() if ":" in l else l
                    if name and (not filter or filter.lower() in name.lower()):
                        out.append(f"{name}: {state}")
                    name = None
            return "\n".join(out[:200]) or "(нет)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class TaskListTool(Tool):
    name = "win_task_list"
    description = "Список задач Windows Scheduler."
    parameters = {}

    def run(self):
        try:
            r = subprocess.run(["schtasks", "/query", "/fo", "TABLE"],
                                capture_output=True, text=True, timeout=20,
                                encoding="cp866", errors="replace")
            return (r.stdout or r.stderr)[:3000] or "(пусто)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class FirewallStatusTool(Tool):
    name = "win_firewall_status"
    description = "Статус брандмауэра."
    parameters = {}

    def run(self):
        try:
            r = subprocess.run(["netsh", "advfirewall", "show", "allprofiles"],
                                capture_output=True, text=True, timeout=10,
                                encoding="cp866", errors="replace")
            return (r.stdout or r.stderr)[:2000] or "(пусто)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class WinVersionTool(Tool):
    name = "win_version"
    description = "Версия Windows."
    parameters = {}

    def run(self):
        try:
            return (f"система: {platform.system()} {platform.release()}\n"
                    f"версия: {platform.version()}\n"
                    f"архитектура: {platform.machine()}\n"
                    f"процессор: {platform.processor()}\n"
                    f"hostname: {socket.gethostname()}")
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class UserListTool(Tool):
    name = "win_user_list"
    description = "Список пользователей системы."
    parameters = {}

    def run(self):
        try:
            r = subprocess.run(["net", "user"],
                                capture_output=True, text=True, timeout=10,
                                encoding="cp866", errors="replace")
            return (r.stdout or r.stderr)[:1500] or "(пусто)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class AdminCheckTool(Tool):
    name = "win_admin_check"
    description = "Запущено ли с правами администратора."
    parameters = {}

    def run(self):
        try:
            import ctypes
            return "администратор" if ctypes.windll.shell32.IsUserAnAdmin() else "обычный пользователь"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class StartupListTool(Tool):
    name = "win_startup_list"
    description = "Программы в автозагрузке."
    parameters = {}

    def run(self):
        try:
            r = subprocess.run(
                ["wmic", "startup", "get", "Caption,Command,Location"],
                capture_output=True, text=True, timeout=15,
                encoding="cp866", errors="replace")
            return (r.stdout or r.stderr)[:2000] or "(пусто)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


# ============================================================
# 11-25. DEV TOOLS
# ============================================================
class GitStatusTool(Tool):
    name = "git_status"
    description = "Статус git в папке."
    parameters = {"path": "папка"}

    def run(self, path="."):
        try:
            r = subprocess.run(["git", "-C", path, "status", "--short"],
                                capture_output=True, text=True, timeout=15)
            return (r.stdout or r.stderr)[:2000] or "чисто"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class GitLogTool(Tool):
    name = "git_log"
    description = "История git коммитов."
    parameters = {"path": "папка", "n": "сколько (10)"}

    def run(self, path=".", n=10):
        try:
            r = subprocess.run(["git", "-C", path, "log", "--oneline", f"-{int(n)}"],
                                capture_output=True, text=True, timeout=15)
            return (r.stdout or r.stderr)[:2000] or "(нет коммитов)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class GitDiffTool(Tool):
    name = "git_diff"
    description = "Изменения в git."
    parameters = {"path": "папка", "file": "файл (опц.)"}

    def run(self, path=".", file=""):
        try:
            cmd = ["git", "-C", path, "diff"]
            if file:
                cmd.append(file)
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            return (r.stdout or r.stderr)[:3000] or "(нет изменений)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class PipListTool(Tool):
    name = "pip_list"
    description = "Установленные pip-пакеты."
    parameters = {"filter": "фильтр по имени"}

    def run(self, filter=""):
        try:
            r = subprocess.run([sys.executable, "-m", "pip", "list"],
                                capture_output=True, text=True, timeout=20)
            lines = (r.stdout or "").split("\n")
            if filter:
                lines = [l for l in lines if filter.lower() in l.lower() or
                         l.startswith(("---", "Package"))]
            return "\n".join(lines[:200])
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class PipInstallTool(Tool):
    name = "pip_install"
    description = "Установить pip-пакет."
    parameters = {"package": "имя пакета"}

    def run(self, package):
        try:
            r = subprocess.run([sys.executable, "-m", "pip", "install", package],
                                capture_output=True, text=True, timeout=180)
            tail = (r.stdout or "")[-1500:] + (r.stderr or "")[-500:]
            return f"[exit {r.returncode}]\n{tail}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class NodeNpmListTool(Tool):
    name = "npm_list"
    description = "Установленные npm пакеты."
    parameters = {"path": "папка проекта"}

    def run(self, path="."):
        try:
            r = subprocess.run(["npm", "list", "--depth=0"],
                                cwd=path, capture_output=True, text=True,
                                timeout=30, shell=True)
            return (r.stdout or r.stderr)[:2000]
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DockerPsTool(Tool):
    name = "docker_ps"
    description = "Запущенные docker контейнеры."
    parameters = {}

    def run(self):
        try:
            r = subprocess.run(["docker", "ps", "-a"],
                                capture_output=True, text=True, timeout=15)
            return (r.stdout or r.stderr)[:2000] or "(нет docker)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class PyCompileTool(Tool):
    name = "py_compile_file"
    description = "Проверить синтаксис .py файла."
    parameters = {"path": "файл или папка"}

    def run(self, path):
        try:
            p = Path(path)
            files = [p] if p.is_file() else list(p.rglob("*.py"))
            ok, bad = 0, []
            for f in files[:500]:
                try:
                    compile(f.read_text(encoding="utf-8", errors="ignore"),
                            str(f), "exec")
                    ok += 1
                except SyntaxError as e:
                    bad.append(f"{f}:{e.lineno}: {e.msg}")
            return f"[ok] {ok} файлов\n" + ("\n".join(bad) if bad else "ошибок нет")
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class PyDocTool(Tool):
    name = "py_doc_strings"
    description = "Извлечь docstrings из модуля."
    parameters = {"path": "файл .py"}

    def run(self, path):
        try:
            import ast
            tree = ast.parse(Path(path).read_text(encoding="utf-8"))
            out = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                    d = ast.get_docstring(node)
                    if d:
                        name = getattr(node, "name", "module")
                        out.append(f"--- {name} ---\n{d}")
            return "\n\n".join(out[:50]) or "(нет docstring)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class PyTreeTool(Tool):
    name = "py_ast_tree"
    description = "AST-дерево Python-файла."
    parameters = {"path": "файл .py"}

    def run(self, path):
        try:
            import ast
            tree = ast.parse(Path(path).read_text(encoding="utf-8"))
            return ast.dump(tree, indent=2)[:4000]
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class VenvInfoTool(Tool):
    name = "venv_info"
    description = "Информация о venv."
    parameters = {"path": "папка с venv"}

    def run(self, path):
        try:
            p = Path(path)
            cfg = p / "pyvenv.cfg"
            if not cfg.exists():
                return "[error] не venv"
            return cfg.read_text(encoding="utf-8")
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class RequirementsGenTool(Tool):
    name = "requirements_gen"
    description = "Собрать requirements.txt из импортов."
    parameters = {"path": "папка с .py", "dst": "куда"}

    def run(self, path=".", dst="requirements.txt"):
        try:
            imports = set()
            for f in Path(path).rglob("*.py"):
                if "__pycache__" in str(f):
                    continue
                src = f.read_text(encoding="utf-8", errors="ignore")
                for m in re.finditer(r"^\s*(?:import|from)\s+(\w+)", src, re.M):
                    imports.add(m.group(1))
            std = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else set()
            third = sorted(imports - std)
            Path(dst).write_text("\n".join(third), encoding="utf-8")
            return f"[ok] {len(third)} пакетов → {dst}\n" + "\n".join(third[:50])
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class PyTestRunTool(Tool):
    name = "pytest_run"
    description = "Запустить pytest в папке."
    parameters = {"path": "папка", "args": "доп. аргументы"}

    def run(self, path=".", args=""):
        try:
            cmd = [sys.executable, "-m", "pytest", "-q", "-x"]
            if args:
                cmd += args.split()
            r = subprocess.run(cmd, cwd=path, capture_output=True, text=True,
                                timeout=120)
            return f"[exit {r.returncode}]\n" + ((r.stdout or "") + (r.stderr or ""))[-2500:]
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class RegexTestTool(Tool):
    name = "regex_test"
    description = "Проверить regex на тексте."
    parameters = {"pattern": "regex", "text": "текст"}

    def run(self, pattern, text):
        try:
            m = list(re.finditer(pattern, text))
            if not m:
                return "(нет совпадений)"
            out = []
            for x in m[:50]:
                out.append(f"[{x.start()}:{x.end()}] {x.group()!r}"
                            + (f"  groups={x.groups()}" if x.groups() else ""))
            return "\n".join(out)
        except re.error as e:
            return f"[error] regex: {e}"


class Flake8Tool(Tool):
    name = "flake8_check"
    description = "Проверить стиль (flake8, если установлен)."
    parameters = {"path": "файл или папка"}

    def run(self, path):
        try:
            r = subprocess.run([sys.executable, "-m", "flake8", path, "--max-line-length=120"],
                                capture_output=True, text=True, timeout=60)
            return f"[exit {r.returncode}]\n" + (r.stdout or r.stderr)[:3000]
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


# ============================================================
# 26-40. DATA / FORMAT
# ============================================================
class TomlReadTool(Tool):
    name = "toml_read"
    description = "Прочитать TOML."
    parameters = {"path": "файл"}

    def run(self, path):
        try:
            try:
                import tomllib as _t
            except ImportError:
                import tomli as _t
            with open(path, "rb") as f:
                data = _t.load(f)
            return json.dumps(data, ensure_ascii=False, indent=2)[:5000]
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class TomlWriteTool(Tool):
    name = "toml_write"
    description = "Записать TOML из JSON."
    parameters = {"path": "файл", "json": "JSON-строка"}

    def run(self, path, json):
        try:
            import tomli_w
        except ImportError:
            return "[error] pip install tomli-w"
        try:
            d = __import__("json").loads(json)
            with open(path, "wb") as f:
                tomli_w.dump(d, f)
            return f"[ok] {path}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class IniReadTool(Tool):
    name = "ini_read"
    description = "Прочитать .ini."
    parameters = {"path": "файл"}

    def run(self, path):
        try:
            c = configparser.ConfigParser()
            c.read(path, encoding="utf-8")
            out = []
            for s in c.sections():
                out.append(f"[{s}]")
                for k, v in c[s].items():
                    out.append(f"{k} = {v}")
            return "\n".join(out) or "(пусто)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class IniWriteTool(Tool):
    name = "ini_write"
    description = "Записать .ini из JSON."
    parameters = {"path": "файл", "json": "JSON"}

    def run(self, path, json):
        try:
            d = __import__("json").loads(json)
            c = configparser.ConfigParser()
            c.read_dict(d)
            with open(path, "w", encoding="utf-8") as f:
                c.write(f)
            return f"[ok] {path}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class XmlReadTool(Tool):
    name = "xml_read"
    description = "Прочитать XML (сжатое дерево)."
    parameters = {"path": "файл"}

    def run(self, path):
        try:
            tree = ET.parse(path)
            root = tree.getroot()

            def dump(el, depth=0):
                out = ["  " * depth + f"<{el.tag}>" + (f" {el.attrib}" if el.attrib else "")]
                if el.text and el.text.strip():
                    out[-1] += f" = {el.text.strip()!r}"
                for c in el:
                    out.extend(dump(c, depth + 1))
                return out
            return "\n".join(dump(root))[:5000]
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class XmlToJsonTool(Tool):
    name = "xml_to_json"
    description = "XML → JSON."
    parameters = {"path": "XML", "dst": "куда"}

    def run(self, path, dst):
        try:
            import xmltodict
        except ImportError:
            return "[error] pip install xmltodict"
        try:
            d = xmltodict.parse(Path(path).read_text(encoding="utf-8"))
            Path(dst).write_text(json.dumps(d, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
            return f"[ok] {dst}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class SqliteQueryTool(Tool):
    name = "sqlite_query"
    description = "Выполнить SQL в SQLite."
    parameters = {"path": "БД", "sql": "запрос"}

    def run(self, path, sql):
        path = str(_resolve_path(path))
        try:
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute(sql)
            if sql.strip().lower().startswith(("select", "pragma", "with")):
                rows = cur.fetchall()
                if not rows:
                    return "(пусто)"
                cols = rows[0].keys()
                out = [" | ".join(cols)]
                for r in rows[:200]:
                    out.append(" | ".join(str(r[c]) for c in cols))
                return "\n".join(out)
            con.commit()
            n = cur.rowcount
            con.close()
            return f"[ok] затронуто строк: {n}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class SqliteTablesTool(Tool):
    name = "sqlite_tables"
    description = "Список таблиц в SQLite."
    parameters = {"path": "БД"}

    def run(self, path):
        path = str(_resolve_path(path))
        try:
            con = sqlite3.connect(path)
            cur = con.cursor()
            cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
            out = []
            for name, sql in cur.fetchall():
                out.append(f"--- {name} ---\n{sql}")
            con.close()
            return "\n\n".join(out[:30]) or "(нет таблиц)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class CsvToSqliteTool(Tool):
    name = "csv_to_sqlite"
    description = "Импортировать CSV в SQLite."
    parameters = {"csv": "CSV", "db": "БД", "table": "имя таблицы"}

    def run(self, csv_path, db, table):
        csv_path = str(_resolve_path(csv_path))
        db = str(_resolve_path(db))
        try:
            import csv as _csv_mod
            import sqlite3 as sq
            with open(csv_path, "r", encoding="utf-8", newline="") as f:
                reader = _csv_mod.reader(f)
                headers = next(reader)
                rows = list(reader)
            con = sq.connect(db)
            cur = con.cursor()
            cols = ", ".join(f'"{h}" TEXT' for h in headers)
            cur.execute(f'DROP TABLE IF EXISTS "{table}"')
            cur.execute(f'CREATE TABLE "{table}" ({cols})')
            q = f'INSERT INTO "{table}" VALUES ({",".join(["?"]*len(headers))})'
            cur.executemany(q, rows)
            con.commit()
            con.close()
            return f"[ok] {len(rows)} строк → {db}.{table}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class HtmlStripTool(Tool):
    name = "html_strip"
    description = "Убрать HTML-теги из файла."
    parameters = {"path": "файл", "dst": "куда (или - для вывода)"}

    def run(self, path, dst="-"):
        try:
            t = _resolve_path(path).read_text(encoding="utf-8", errors="ignore")
            t = re.sub(r"<script[\s\S]*?</script>", "", t, flags=re.I)
            t = re.sub(r"<style[\s\S]*?</style>", "", t, flags=re.I)
            t = re.sub(r"<[^>]+>", "", t)
            t = html.unescape(t)
            t = re.sub(r"\s+", " ", t).strip()
            if dst == "-":
                return t[:4000]
            Path(dst).write_text(t, encoding="utf-8")
            return f"[ok] → {dst}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class MarkdownToHtmlTool(Tool):
    name = "md_to_html"
    description = "Markdown → HTML."
    parameters = {"path": "MD", "dst": "HTML"}

    def run(self, path, dst):
        try:
            import markdown
            src_path = _resolve_path(path)
            t = markdown.markdown(src_path.read_text(encoding="utf-8"),
                                   extensions=["extra", "codehilite"])
            out_path = _resolve_path(dst)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(t, encoding="utf-8")
            return f"[ok] {out_path}"
        except ImportError:
            return "[error] pip install markdown"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class PickleReadTool(Tool):
    name = "pickle_read"
    description = "Прочитать pickle-файл (осторожно! только свои файлы)."
    parameters = {"path": "файл"}

    def run(self, path):
        try:
            with open(path, "rb") as f:
                return repr(pickle.load(f))[:3000]
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class SqliteSchemaTool(Tool):
    name = "sqlite_schema"
    description = "Схема SQLite (индексы, триггеры, views)."
    parameters = {"path": "БД"}

    def run(self, path):
        try:
            con = sqlite3.connect(path)
            cur = con.cursor()
            cur.execute("SELECT type, name, sql FROM sqlite_master ORDER BY type, name")
            out = []
            for t, n, s in cur.fetchall():
                out.append(f"--- {t}: {n} ---\n{s}")
            con.close()
            return "\n\n".join(out[:100])
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


# ============================================================
# 41-55. WEB / API
# ============================================================
class HttpPostTool(Tool):
    name = "http_post"
    description = "POST-запрос с JSON."
    parameters = {"url": "адрес", "json": "тело JSON",
                  "headers": "JSON с headers (опц.)"}

    def run(self, url, json, headers="{}"):
        try:
            import urllib.request as ur
            h = {"Content-Type": "application/json"}
            try:
                h.update(__import__("json").loads(headers))
            except Exception:
                pass
            req = ur.Request(url, data=json.encode("utf-8"),
                              headers=h, method="POST")
            with ur.urlopen(req, timeout=20) as r:
                return f"[{r.status}]\n{r.read().decode('utf-8', errors='ignore')[:4000]}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class HttpHeadTool(Tool):
    name = "http_head"
    description = "HEAD-запрос (только заголовки)."
    parameters = {"url": "адрес"}

    def run(self, url):
        try:
            import urllib.request as ur
            req = ur.Request(url, method="HEAD",
                              headers={"User-Agent": "Mozilla/5.0"})
            with ur.urlopen(req, timeout=15) as r:
                return f"[{r.status}]\n" + "\n".join(f"{k}: {v}" for k, v in r.headers.items())
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DnsLookupTool(Tool):
    name = "dns_lookup"
    description = "Разрешить домен в IP."
    parameters = {"host": "домен"}

    def run(self, host):
        try:
            import socket as s
            infos = s.getaddrinfo(host, None)
            seen = set()
            out = []
            for f, _, _, _, addr in infos:
                k = (f.name, addr[0])
                if k not in seen:
                    seen.add(k)
                    out.append(f"{f.name}: {addr[0]}")
            return "\n".join(out[:30]) or "(нет)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class SslCheckTool(Tool):
    name = "ssl_check"
    description = "Проверить SSL-сертификат сайта."
    parameters = {"host": "домен", "port": "порт (443)"}

    def run(self, host, port=443):
        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
                s.settimeout(10)
                s.connect((host, int(port)))
                cert = s.getpeercert()
                return (f"subject: {cert.get('subject')}\n"
                        f"issuer: {cert.get('issuer')}\n"
                        f"notAfter: {cert.get('notAfter')}\n"
                        f"serial: {cert.get('serialNumber')}")
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class UrlParseTool(Tool):
    name = "url_parse"
    description = "Разобрать URL на части."
    parameters = {"url": "URL"}

    def run(self, url):
        try:
            p = urlparse(url)
            qs = urllib.parse.parse_qs(p.query)
            return (f"scheme: {p.scheme}\nhost: {p.netloc}\n"
                    f"path: {p.path}\nfragment: {p.fragment}\n"
                    f"query: {json.dumps(qs, ensure_ascii=False, indent=2)}")
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class JwtDecodeTool(Tool):
    name = "jwt_decode"
    description = "Декодировать JWT (без проверки подписи)."
    parameters = {"token": "JWT"}

    def run(self, token):
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return "[error] не JWT"
            def dec(s):
                s += "=" * (-len(s) % 4)
                return base64.urlsafe_b64decode(s).decode("utf-8", errors="ignore")
            return (f"HEADER:\n{json.dumps(json.loads(dec(parts[0])), indent=2, ensure_ascii=False)}\n\n"
                    f"PAYLOAD:\n{json.dumps(json.loads(dec(parts[1])), indent=2, ensure_ascii=False)}")
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class UrlEncodeTool(Tool):
    name = "url_encode"
    description = "Кодировать строку для URL."
    parameters = {"text": "строка"}

    def run(self, text):
        return urllib.parse.quote(text, safe="")


class UrlDecodeTool(Tool):
    name = "url_decode"
    description = "Декодировать URL."
    parameters = {"text": "строка"}

    def run(self, text):
        return urllib.parse.unquote(text)


class HtmlEscapeTool(Tool):
    name = "html_escape"
    description = "Экранировать HTML-спецсимволы."
    parameters = {"text": "строка"}

    def run(self, text):
        return html.escape(text)


class HtmlUnescapeTool(Tool):
    name = "html_unescape"
    description = "Разэкранировать HTML."
    parameters = {"text": "строка"}

    def run(self, text):
        return html.unescape(text)


class HttpDownloadMultiTool(Tool):
    name = "download_multi"
    description = "Скачать несколько URL в папку."
    parameters = {"urls": "URL через пробел", "dst_dir": "папка"}

    def run(self, urls, dst_dir="."):
        try:
            d = Path(dst_dir)
            d.mkdir(parents=True, exist_ok=True)
            out = []
            for url in urls.split():
                try:
                    name = Path(urlparse(url).path).name or "file"
                    fp = d / name
                    urllib.request.urlretrieve(url, fp)
                    out.append(f"[ok] {name} ({_size_h(fp.stat().st_size)})")
                except Exception as e:
                    out.append(f"[!] {url}: {e}")
            return "\n".join(out)
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class WebHeadersGetTool(Tool):
    name = "web_headers_get"
    description = "Заголовки ответа сайта."
    parameters = {"url": "адрес"}

    def run(self, url):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return (f"[{r.status}]\n" +
                        "\n".join(f"{k}: {v}" for k, v in r.headers.items()))
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


# ============================================================
# 56-70. TEXT ADVANCED
# ============================================================
class SlugifyTool(Tool):
    name = "slugify"
    description = "Сделать slug из строки."
    parameters = {"text": "строка"}

    def run(self, text):
        try:
            import unicodedata
            t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
            t = re.sub(r"[^\w\s-]", "", t).strip().lower()
            return re.sub(r"[-\s]+", "-", t)
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class TransliterateTool(Tool):
    name = "transliterate"
    description = "Транслитерация рус → лат."
    parameters = {"text": "текст"}

    def run(self, text):
        m = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e",
             "ё": "e", "ж": "zh", "з": "z", "и": "i", "й": "j", "к": "k",
             "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
             "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "c",
             "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "",
             "э": "e", "ю": "yu", "я": "ya", " ": "-"}
        out = []
        for c in text.lower():
            out.append(m.get(c, c))
        return "".join(out)


class ExtractEmailsTool(Tool):
    name = "extract_emails"
    description = "Найти email в тексте."
    parameters = {"path": "файл"}

    def run(self, path):
        try:
            t = Path(path).read_text(encoding="utf-8", errors="ignore")
            m = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", t))
            return "\n".join(sorted(m)) or "(нет)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class ExtractUrlsTool(Tool):
    name = "extract_urls"
    description = "Найти URL в тексте."
    parameters = {"path": "файл"}

    def run(self, path):
        try:
            t = Path(path).read_text(encoding="utf-8", errors="ignore")
            m = set(re.findall(r"https?://[^\s<>\"']+", t))
            return "\n".join(sorted(m)) or "(нет)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class ExtractIpsTool(Tool):
    name = "extract_ips"
    description = "Найти IP-адреса в тексте."
    parameters = {"path": "файл"}

    def run(self, path):
        try:
            t = Path(path).read_text(encoding="utf-8", errors="ignore")
            ips = set()
            for m in re.finditer(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", t):
                try:
                    ipaddress.ip_address(m.group())
                    ips.add(m.group())
                except ValueError:
                    pass
            return "\n".join(sorted(ips)) or "(нет)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class ExtractPhonesTool(Tool):
    name = "extract_phones"
    description = "Найти телефоны в тексте."
    parameters = {"path": "файл"}

    def run(self, path):
        try:
            t = Path(path).read_text(encoding="utf-8", errors="ignore")
            m = set(re.findall(r"\+?\d[\d\s\-\(\)]{7,}\d", t))
            return "\n".join(sorted(m)) or "(нет)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class ExtractDatesTool(Tool):
    name = "extract_dates"
    description = "Найти даты в тексте."
    parameters = {"path": "файл"}

    def run(self, path):
        try:
            t = Path(path).read_text(encoding="utf-8", errors="ignore")
            pat = r"\b(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}-\d{2}-\d{2})\b"
            m = set(re.findall(pat, t))
            return "\n".join(sorted(m)) or "(нет)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class TextTruncateTool(Tool):
    name = "text_truncate"
    description = "Обрезать текст по словам."
    parameters = {"path": "файл", "limit": "символов"}

    def run(self, path, limit=500):
        try:
            t = Path(path).read_text(encoding="utf-8", errors="ignore")
            n = int(limit)
            if len(t) <= n:
                return t
            return t[:n].rsplit(" ", 1)[0] + "..."
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class TextSplitSentencesTool(Tool):
    name = "text_split_sentences"
    description = "Разбить текст на предложения."
    parameters = {"path": "файл"}

    def run(self, path):
        try:
            t = Path(path).read_text(encoding="utf-8", errors="ignore")
            s = re.split(r"(?<=[.!?])\s+", t)
            return "\n".join(f"{i+1}. {x.strip()}" for i, x in enumerate(s[:100]) if x.strip())
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class TextWordFreqTool(Tool):
    name = "text_word_freq"
    description = "Частота слов в тексте."
    parameters = {"path": "файл", "top": "сколько (30)"}

    def run(self, path, top=30):
        try:
            t = Path(path).read_text(encoding="utf-8", errors="ignore").lower()
            words = re.findall(r"\w{3,}", t)
            c = Counter(words)
            return "\n".join(f"{n:>5}  {w}" for w, n in c.most_common(int(top)))
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class TextNormalizeTool(Tool):
    name = "text_normalize"
    description = "Нормализовать пробелы и переносы."
    parameters = {"path": "файл"}

    def run(self, path):
        try:
            p = Path(path)
            t = p.read_text(encoding="utf-8")
            t = re.sub(r"[ \t]+", " ", t)
            t = re.sub(r"\n{3,}", "\n\n", t).strip()
            p.write_text(t, encoding="utf-8")
            return f"[ok] {path}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class TextRemoveLinesTool(Tool):
    name = "text_remove_lines"
    description = "Удалить строки по regex."
    parameters = {"path": "файл", "pattern": "regex",
                  "invert": "true — оставить только совпадения"}

    def run(self, path, pattern, invert="false"):
        try:
            p = Path(path)
            lines = p.read_text(encoding="utf-8").splitlines()
            inv = invert.lower() == "true"
            out = [l for l in lines if (bool(re.search(pattern, l)) == inv)]
            p.write_text("\n".join(out), encoding="utf-8")
            return f"[ok] осталось {len(out)}/{len(lines)}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class TextIndentTool(Tool):
    name = "text_indent"
    description = "Добавить отступ всем строкам."
    parameters = {"path": "файл", "n": "пробелов"}

    def run(self, path, n=4):
        try:
            p = Path(path)
            pad = " " * int(n)
            p.write_text("\n".join(pad + l if l else l
                                    for l in p.read_text(encoding="utf-8").splitlines()),
                          encoding="utf-8")
            return f"[ok] {path}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class TextRemoveEmptyLinesTool(Tool):
    name = "text_remove_empty_lines"
    description = "Убрать пустые строки."
    parameters = {"path": "файл"}

    def run(self, path):
        try:
            p = Path(path)
            lines = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
            p.write_text("\n".join(lines), encoding="utf-8")
            return f"[ok] {len(lines)} строк"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


# ============================================================
# 71-80. ENCODING / CRYPTO
# ============================================================
class HexDumpTool(Tool):
    name = "hex_dump"
    description = "Hex-дамп файла."
    parameters = {"path": "файл", "limit": "байт (256)"}

    def run(self, path, limit=256):
        try:
            with open(path, "rb") as f:
                data = f.read(int(limit))
            out = []
            for i in range(0, len(data), 16):
                chunk = data[i:i+16]
                hx = " ".join(f"{b:02x}" for b in chunk)
                asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
                out.append(f"{i:08x}  {hx:<48}  {asc}")
            return "\n".join(out)
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class BinaryViewTool(Tool):
    name = "binary_view"
    description = "Битовое представление первых байт."
    parameters = {"path": "файл", "limit": "байт (16)"}

    def run(self, path, limit=16):
        try:
            with open(path, "rb") as f:
                data = f.read(int(limit))
            return "\n".join(f"{b:08b}" for b in data)
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class Rot13Tool(Tool):
    name = "rot13"
    description = "ROT13-шифр."
    parameters = {"text": "текст"}

    def run(self, text):
        return text.translate(str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"))


class HashHmacTool(Tool):
    name = "hmac_sha256"
    description = "HMAC-SHA256."
    parameters = {"key": "ключ", "text": "текст"}

    def run(self, key, text):
        return hmac.new(key.encode(), text.encode(), hashlib.sha256).hexdigest()


class PasswordGenTool(Tool):
    name = "password_gen"
    description = "Сгенерировать пароль."
    parameters = {"length": "длина (16)",
                  "symbols": "true — со спецсимволами"}

    def run(self, length=16, symbols="true"):
        try:
            n = int(length)
            chars = string.ascii_letters + string.digits
            if symbols.lower() == "true":
                chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
            return "".join(secrets.choice(chars) for _ in range(n))
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class UuidGenTool(Tool):
    name = "uuid_gen"
    description = "Сгенерировать UUID4."
    parameters = {}

    def run(self):
        return str(_uuid.uuid4())


class UuidValidateTool(Tool):
    name = "uuid_validate"
    description = "Проверить валидность UUID."
    parameters = {"text": "строка"}

    def run(self, text):
        try:
            u = _uuid.UUID(text)
            return f"[ok] версия {u.version}"
        except ValueError:
            return "[error] не UUID"


class Base32Tool(Tool):
    name = "base32"
    description = "Кодировать/декодировать base32."
    parameters = {"mode": "encode|decode", "text": "текст"}

    def run(self, mode, text):
        try:
            if mode == "encode":
                return base64.b32encode(text.encode()).decode()
            return base64.b32decode(text.encode()).decode()
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class Base85Tool(Tool):
    name = "base85"
    description = "Кодировать/декодировать base85."
    parameters = {"mode": "encode|decode", "text": "текст"}

    def run(self, mode, text):
        try:
            if mode == "encode":
                return base64.b85encode(text.encode()).decode()
            return base64.b85decode(text.encode()).decode()
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


# ============================================================
# 81-90. MATH / RANDOM
# ============================================================
class MathEvalTool(Tool):
    name = "math_eval"
    description = "Вычислить выражение с математикой."
    parameters = {"expr": "выражение"}

    def run(self, expr):
        try:
            safe_ns = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
            safe_ns.update({"abs": abs, "min": min, "max": max, "round": round,
                            "sum": sum, "pow": pow})
            expr = expr.replace("^", "**")
            if not re.match(r"^[\d\s+\-*/().,%^a-zA-Z_]+$", expr):
                return "[error] недопустимые символы"
            return str(eval(expr, {"__builtins__": {}}, safe_ns))
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class MathStatsTool(Tool):
    name = "math_stats"
    description = "Статистика набора чисел."
    parameters = {"numbers": "числа через пробел или запятую"}

    def run(self, numbers):
        try:
            nums = [float(x) for x in re.split(r"[\s,]+", numbers) if x]
            if not nums:
                return "[error] нет чисел"
            import statistics
            return (f"count: {len(nums)}\n"
                    f"sum: {sum(nums)}\n"
                    f"min: {min(nums)}\n"
                    f"max: {max(nums)}\n"
                    f"mean: {statistics.mean(nums)}\n"
                    f"median: {statistics.median(nums)}\n"
                    f"stdev: {statistics.stdev(nums) if len(nums) > 1 else 0}")
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class PrimeCheckTool(Tool):
    name = "prime_check"
    description = "Проверить число на простоту."
    parameters = {"n": "число"}

    def run(self, n):
        try:
            x = int(n)
            if x < 2:
                return f"{x} — не простое"
            for i in range(2, int(x**0.5) + 1):
                if x % i == 0:
                    return f"{x} — составное (делится на {i})"
            return f"{x} — простое"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class FibonacciTool(Tool):
    name = "fibonacci"
    description = "Первые N чисел Фибоначчи."
    parameters = {"n": "сколько (20)"}

    def run(self, n=20):
        try:
            k = int(n)
            a, b, out = 0, 1, []
            for _ in range(k):
                out.append(a)
                a, b = b, a + b
            return " ".join(map(str, out))
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class FactorialTool(Tool):
    name = "factorial"
    description = "Факториал n!"
    parameters = {"n": "число"}

    def run(self, n):
        try:
            k = int(n)
            if k < 0 or k > 1000:
                return "[error] 0..1000"
            return str(math.factorial(k))
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class GcdTool(Tool):
    name = "gcd_lcm"
    description = "НОД и НОК двух чисел."
    parameters = {"a": "число", "b": "число"}

    def run(self, a, b):
        try:
            x, y = int(a), int(b)
            g = math.gcd(x, y)
            l = x * y // g if g else 0
            return f"НОД: {g}\nНОК: {l}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DiceRollTool(Tool):
    name = "dice_roll"
    description = "Бросить кубики."
    parameters = {"dice": "NdM (2d6)", "count": "раз повторить"}

    def run(self, dice="1d6", count=1):
        try:
            m = re.match(r"(\d+)d(\d+)", dice.lower())
            if not m:
                return "[error] формат NdM"
            n, sides = int(m.group(1)), int(m.group(2))
            out = []
            for _ in range(int(count)):
                rolls = [random.randint(1, sides) for _ in range(n)]
                out.append(f"{rolls} = {sum(rolls)}")
            return "\n".join(out)
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class CoinFlipTool(Tool):
    name = "coin_flip"
    description = "Подбросить монету."
    parameters = {"count": "раз (1)"}

    def run(self, count=1):
        try:
            return " ".join(random.choice(["орел", "решка"])
                             for _ in range(int(count)))
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class RandStringTool(Tool):
    name = "rand_string"
    description = "Случайная строка."
    parameters = {"length": "длина (16)"}

    def run(self, length=16):
        try:
            return "".join(random.choice(string.ascii_letters + string.digits)
                           for _ in range(int(length)))
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class RandomPickTool(Tool):
    name = "random_pick"
    description = "Случайно выбрать из списка."
    parameters = {"items": "элементы через |", "count": "сколько (1)"}

    def run(self, items, count=1):
        try:
            xs = [x.strip() for x in items.split("|") if x.strip()]
            if not xs:
                return "[error] пусто"
            k = min(int(count), len(xs))
            return "\n".join(random.sample(xs, k))
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


# ============================================================
# 91-100. TIME / DATE
# ============================================================
class TimestampNowTool(Tool):
    name = "timestamp_now"
    description = "Текущий Unix timestamp."
    parameters = {}

    def run(self):
        return f"{int(time.time())} ({datetime.now():%Y-%m-%d %H:%M:%S})"


class TimestampConvertTool(Tool):
    name = "timestamp_convert"
    description = "Unix timestamp → дата (и обратно)."
    parameters = {"value": "число или дата"}

    def run(self, value):
        try:
            if value.isdigit():
                dt = datetime.fromtimestamp(int(value))
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return str(int(dt.timestamp()))
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DateDiffTool(Tool):
    name = "date_diff"
    description = "Разница между датами."
    parameters = {"a": "YYYY-MM-DD", "b": "YYYY-MM-DD"}

    def run(self, a, b):
        try:
            da = datetime.strptime(a, "%Y-%m-%d")
            db = datetime.strptime(b, "%Y-%m-%d")
            d = db - da
            return (f"дней: {d.days}\n"
                    f"всего часов: {d.days * 24 + d.seconds // 3600}")
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DateAddTool(Tool):
    name = "date_add"
    description = "Прибавить дни к дате."
    parameters = {"date": "YYYY-MM-DD", "days": "число (может быть -)"}

    def run(self, date, days):
        try:
            d = datetime.strptime(date, "%Y-%m-%d") + timedelta(days=int(days))
            return d.strftime("%Y-%m-%d (%A)")
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class WeekNumberTool(Tool):
    name = "week_number"
    description = "Номер недели и день года."
    parameters = {"date": "YYYY-MM-DD (опц., иначе сегодня)"}

    def run(self, date=""):
        try:
            d = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()
            return f"ISO неделя: {d.isocalendar().week}\nдень года: {d.timetuple().tm_yday}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class CronNextTool(Tool):
    name = "cron_next"
    description = "Следующее время для cron-выражения."
    parameters = {"expr": "5-польное cron", "n": "сколько раз (5)"}

    def run(self, expr, n=5):
        try:
            from croniter import croniter
        except ImportError:
            return "[error] pip install croniter"
        try:
            it = croniter(expr, datetime.now())
            return "\n".join(str(it.get_next(datetime)) for _ in range(int(n)))
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class TimezoneInfoTool(Tool):
    name = "timezone_info"
    description = "Информация о часовом поясе."
    parameters = {"zone": "Europe/Moscow (опц.)"}

    def run(self, zone=""):
        try:
            import zoneinfo
            z = zoneinfo.ZoneInfo(zone or "UTC")
            now = datetime.now(z)
            return (f"зона: {z}\n"
                    f"время: {now:%Y-%m-%d %H:%M:%S %Z}\n"
                    f"UTC-offset: {now.utcoffset()}")
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class FormatDurationTool(Tool):
    name = "format_duration"
    description = "Секунды в человеческое время."
    parameters = {"seconds": "секунды"}

    def run(self, seconds):
        try:
            s = int(seconds)
            parts = []
            for label, n in (("д", 86400), ("ч", 3600), ("мин", 60), ("с", 1)):
                if s >= n:
                    v, s = divmod(s, n)
                    parts.append(f"{v}{label}")
            return " ".join(parts) or "0с"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class TimeCompareTool(Tool):
    name = "time_compare"
    description = "Сравнить время (со сколькими-то единицами)."
    parameters = {"a": "секунды", "b": "секунды"}

    def run(self, a, b):
        try:
            x, y = float(a), float(b)
            r = x / y if y else 0
            return f"{x} / {y} = {r:.4f}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class CalendarMonthTool(Tool):
    name = "calendar_month"
    description = "Показать календарь месяца."
    parameters = {"year": "год", "month": "месяц"}

    def run(self, year, month):
        try:
            import calendar
            return calendar.month(int(year), int(month))
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


# ============================================================
# ЭКСПОРТ
# ============================================================
ALL_V3_TOOLS = [
    # Windows
    RegReadTool, RegWriteTool, ServiceStatusTool, ServiceListTool,
    TaskListTool, FirewallStatusTool, WinVersionTool, UserListTool,
    AdminCheckTool, StartupListTool,
    # Dev
    GitStatusTool, GitLogTool, GitDiffTool, PipListTool, PipInstallTool,
    NodeNpmListTool, DockerPsTool, PyCompileTool, PyDocTool, PyTreeTool,
    VenvInfoTool, RequirementsGenTool, PyTestRunTool, RegexTestTool,
    Flake8Tool,
    # Data
    TomlReadTool, TomlWriteTool, IniReadTool, IniWriteTool, XmlReadTool,
    XmlToJsonTool, SqliteQueryTool, SqliteTablesTool, CsvToSqliteTool,
    HtmlStripTool, MarkdownToHtmlTool, PickleReadTool, SqliteSchemaTool,
    # Web
    HttpPostTool, HttpHeadTool, DnsLookupTool, SslCheckTool, UrlParseTool,
    JwtDecodeTool, UrlEncodeTool, UrlDecodeTool, HtmlEscapeTool,
    HtmlUnescapeTool, HttpDownloadMultiTool, WebHeadersGetTool,
    # Text
    SlugifyTool, TransliterateTool, ExtractEmailsTool, ExtractUrlsTool,
    ExtractIpsTool, ExtractPhonesTool, ExtractDatesTool, TextTruncateTool,
    TextSplitSentencesTool, TextWordFreqTool, TextNormalizeTool,
    TextRemoveLinesTool, TextIndentTool, TextRemoveEmptyLinesTool,
    # Encoding
    HexDumpTool, BinaryViewTool, Rot13Tool, HashHmacTool, PasswordGenTool,
    UuidGenTool, UuidValidateTool, Base32Tool, Base85Tool,
    # Math
    MathEvalTool, MathStatsTool, PrimeCheckTool, FibonacciTool,
    FactorialTool, GcdTool, DiceRollTool, CoinFlipTool, RandStringTool,
    RandomPickTool,
    # Time
    TimestampNowTool, TimestampConvertTool, DateDiffTool, DateAddTool,
    WeekNumberTool, CronNextTool, TimezoneInfoTool, FormatDurationTool,
    TimeCompareTool, CalendarMonthTool,
]