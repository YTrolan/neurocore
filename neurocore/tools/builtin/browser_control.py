"""Playwright + Chrome — чтение сайтов без скриншотов."""
import os
import time
from datetime import datetime
from pathlib import Path

from ..base import Tool

DISABLED = os.getenv("NEUROCORE_DISABLE_GUI_CONTROL", "") == "1"
LOG_FILE = Path.cwd() / "gui_control.log"

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

_state = {"pw": None, "browser": None, "page": None}


def _log(m):
    try:
        ts = datetime.now().strftime("%H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {m}\n")
    except Exception:
        pass


def _ensure():
    if _state["page"]:
        return _state["page"]
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    kwargs = {"headless": False}
    if Path(CHROME).exists():
        kwargs["executable_path"] = CHROME
        _log(f"browser: {CHROME}")
    else:
        kwargs["channel"] = "chrome"
    b = pw.chromium.launch(**kwargs)
    p = b.new_page(viewport={"width": 1280, "height": 900})
    _state["pw"] = pw
    _state["browser"] = b
    _state["page"] = p
    print("[browser] Chrome запущен", flush=True)
    return p


class BrowserOpenTool(Tool):
    name = "browser_open"
    description = ("ОТКРЫТЬ САЙТ. Возвращает title + весь видимый ТЕКСТ страницы. "
                   "Используй ЭТО для чтения сайтов, а не desktop_*.")
    parameters = {"url": "URL", "wait": "сек ожидания (по умолчанию 1.5)"}

    def run(self, url="", wait=1.5):
        if DISABLED:
            return "[error] browser control отключён"
        if not url:
            return "[error] нужен url"
        try:
            page = _ensure()
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(float(wait))
            title = page.title()
            text = page.inner_text("body")
            if len(text) > 6000:
                text = text[:6000] + "...[обрезано]"
            _log(f"open: {url}")
            return f"[{title}]\n{url}\n\n{text}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class BrowserClickTool(Tool):
    name = "browser_click"
    description = "Клик по тексту ссылки/кнопки на открытой странице."
    parameters = {"text": "текст элемента"}

    def run(self, text=""):
        if DISABLED:
            return "[error] отключено"
        try:
            page = _ensure()
            page.get_by_text(text, exact=False).first.click(timeout=6000)
            time.sleep(1.0)
            new = page.inner_text("body")[:4000]
            _log(f"click: {text!r}")
            return f"[ok] клик {text!r}. Новая страница:\n{new}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class BrowserTypeTool(Tool):
    name = "browser_type"
    description = "Ввести текст в поле поиска (по CSS-селектору) и Enter."
    parameters = {"selector": "CSS (например 'input[type=search]' или 'input[name=q]')",
                  "text": "что ввести"}

    def run(self, selector="", text=""):
        if DISABLED:
            return "[error] отключено"
        try:
            page = _ensure()
            page.fill(selector, text, timeout=6000)
            page.press(selector, "Enter")
            time.sleep(2.0)
            return f"[ok] ввёл {text!r} в {selector}. Сейчас: {page.url}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class BrowserGetTextTool(Tool):
    name = "browser_get_text"
    description = "Текст текущей страницы (после кликов/поиска)."
    parameters = {"max": "макс символов (по умолчанию 5000)"}

    def run(self, max=5000):
        if DISABLED:
            return "[error] отключено"
        try:
            page = _ensure()
            t = page.inner_text("body")
            return (t[:int(max)] + "...[обрезано]") if len(t) > int(max) else t
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class BrowserCloseTool(Tool):
    name = "browser_close"
    description = "Закрыть браузер."
    parameters = {}

    def run(self):
        try:
            if _state["browser"]:
                _state["browser"].close()
            if _state["pw"]:
                _state["pw"].stop()
            _state["pw"] = _state["browser"] = _state["page"] = None
            return "[ok] закрыт"
        except Exception as e:
            return f"[error] {e}"


ALL_BROWSER_TOOLS = [
    BrowserOpenTool,
    BrowserClickTool,
    BrowserTypeTool,
    BrowserGetTextTool,
    BrowserCloseTool,
]
