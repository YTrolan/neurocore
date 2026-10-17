"""Desktop control через pyautogui."""
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

from ..base import Tool

DISABLED = os.getenv("NEUROCORE_DISABLE_GUI_CONTROL", "") == "1"
LOG_FILE = Path.cwd() / "gui_control.log"


def _log(msg):
    try:
        ts = datetime.now().strftime("%H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


def _check():
    if DISABLED:
        raise RuntimeError("GUI control отключён")


def _pg():
    import pyautogui

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.3
    return pyautogui


class DesktopScreenshotTool(Tool):
    name = "desktop_screenshot"
    description = "Сделать снимок экрана и сохранить в PNG."
    parameters = {"path": "куда сохранить"}

    def run(self, path="screen.png"):
        _check()
        try:
            pg = _pg()
            img = pg.screenshot()
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(p))
            _log(f"screenshot → {p}")
            return f"[ok] снимок: {p} ({img.size[0]}x{img.size[1]})"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopSeeTool(Tool):
    name = "desktop_see"
    description = ("Снимок экрана + ОПИСАНИЕ от vision-модели. "
                   "Используй чтобы 'увидеть' что на экране.")
    parameters = {"prompt": "что именно описать"}

    def run(self, prompt="Опиши что на экране."):
        """Vision через opendeep не работает — отключено."""
        _check()
        try:
            pg = _pg()
            tmp = Path.cwd() / "_see_tmp.png"
            pg.screenshot(str(tmp))
            # удаляем временный файл сразу
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass
            return ("[disabled] vision не работает. Скриншот НЕ нужен — "
                    "для сайтов используй `browser_open(url)`, "
                    "для поиска — `deepseek_search`.")
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopClickTool(Tool):
    name = "desktop_click"
    description = "Клик мышью в (x, y)."
    parameters = {"x": "X", "y": "Y",
                  "button": "left/right/middle", "clicks": "1 или 2"}

    def run(self, x, y, button="left", clicks=1):
        _check()
        try:
            _pg().click(int(x), int(y), clicks=int(clicks), button=button)
            _log(f"click ({x},{y})")
            time.sleep(0.15)
            return f"[ok] клик ({x},{y})"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopDoubleClickTool(Tool):
    name = "desktop_double_click"
    description = "Двойной клик."
    parameters = {"x": "X", "y": "Y"}

    def run(self, x, y):
        _check()
        try:
            _pg().doubleClick(int(x), int(y))
            time.sleep(0.15)
            return f"[ok] двойной клик ({x},{y})"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopRightClickTool(Tool):
    name = "desktop_right_click"
    description = "ПКМ в (x, y)."
    parameters = {"x": "X", "y": "Y"}

    def run(self, x, y):
        _check()
        try:
            _pg().rightClick(int(x), int(y))
            time.sleep(0.15)
            return f"[ok] ПКМ ({x},{y})"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopMoveTool(Tool):
    name = "desktop_move"
    description = "Переместить курсор."
    parameters = {"x": "X", "y": "Y"}

    def run(self, x, y):
        _check()
        try:
            _pg().moveTo(int(x), int(y), duration=0.3)
            return f"[ok] курсор ({x},{y})"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopDragTool(Tool):
    name = "desktop_drag"
    description = "Перетащить от (x1,y1) до (x2,y2)."
    parameters = {"x1": "старт X", "y1": "старт Y",
                  "x2": "финиш X", "y2": "финиш Y"}

    def run(self, x1, y1, x2, y2):
        _check()
        try:
            pg = _pg()
            pg.moveTo(int(x1), int(y1))
            pg.dragTo(int(x2), int(y2), duration=0.5)
            _log(f"drag ({x1},{y1})→({x2},{y2})")
            return "[ok] перетащено"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopScrollTool(Tool):
    name = "desktop_scroll"
    description = "Прокрутка колесом (+вверх, -вниз)."
    parameters = {"amount": "число",
                  "x": "опц. X", "y": "опц. Y"}

    def run(self, amount, x=None, y=None):
        _check()
        try:
            pg = _pg()
            if x is not None and y is not None:
                pg.moveTo(int(x), int(y))
            pg.scroll(int(amount))
            return f"[ok] прокрутка {amount}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopTypeTool(Tool):
    name = "desktop_type"
    description = "Напечатать текст."
    parameters = {"text": "текст"}

    def run(self, text):
        _check()
        try:
            _pg().typewrite(text, interval=0.02)
            _log(f"type: {len(text)} симв.")
            return f"[ok] {len(text)} символов"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopHotkeyTool(Tool):
    name = "desktop_hotkey"
    description = "Комбинация клавиш, например 'ctrl+c'."
    parameters = {"keys": "через +"}

    def run(self, keys):
        _check()
        try:
            parts = [k.strip().lower() for k in keys.split("+") if k.strip()]
            _pg().hotkey(*parts)
            _log(f"hotkey: {keys}")
            return f"[ok] нажато {keys}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopPressTool(Tool):
    name = "desktop_press"
    description = "Одна клавиша (enter, esc, tab)."
    parameters = {"key": "имя", "times": "сколько раз"}

    def run(self, key, times=1):
        _check()
        try:
            pg = _pg()
            for _ in range(int(times)):
                pg.press(key)
            return f"[ok] {key} x{times}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopWindowsTool(Tool):
    name = "desktop_windows"
    description = "Список открытых окон."
    parameters = {}

    def run(self):
        _check()
        try:
            wins = []
            import pygetwindow as gw

            for w in gw.getAllWindows():
                if w.title and w.width > 50 and w.height > 50:
                    wins.append(f"• {w.title[:70]!r}  "
                                f"({w.left},{w.top}) {w.width}x{w.height}")
            return "Окна:\n" + "\n".join(wins) if wins else "(нет окон)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopFocusWindowTool(Tool):
    name = "desktop_focus_window"
    description = "Активировать окно по части заголовка."
    parameters = {"title": "часть заголовка"}

    def run(self, title):
        _check()
        try:
            import pygetwindow as gw

            for w in gw.getAllWindows():
                if title.lower() in (w.title or "").lower():
                    if w.isMinimized:
                        w.restore()
                    w.activate()
                    return f"[ok] активировано: {w.title}"
            return f"[error] окно не найдено: {title!r}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopActiveWindowTool(Tool):
    name = "desktop_active_window"
    description = "Заголовок активного окна."
    parameters = {}

    def run(self):
        _check()
        try:
            import pygetwindow as gw

            w = gw.getActiveWindow()
            return f"{w.title!r} ({w.left},{w.top})" if w else "(нет)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopScreenSizeTool(Tool):
    name = "desktop_screen_size"
    description = "Размер экрана."
    parameters = {}

    def run(self):
        _check()
        try:
            w, h = _pg().size()
            return f"Экран: {w} x {h}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopCursorPosTool(Tool):
    name = "desktop_cursor_pos"
    description = "Позиция курсора."
    parameters = {}

    def run(self):
        _check()
        try:
            x, y = _pg().position()
            return f"Курсор: ({x}, {y})"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopWaitTool(Tool):
    name = "desktop_wait"
    description = "Подождать N секунд."
    parameters = {"seconds": "число"}

    def run(self, seconds=1.0):
        try:
            s = min(float(seconds), 2.0)
            time.sleep(s)
            return f"[ok] подождал {s}s"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"




class DesktopOpenUrlTool(Tool):
    name = "desktop_open_url"
    description = ("Открыть URL в браузере ОДНИМ вызовом. "
                   "Используй это вместо shell/start-process.")
    parameters = {"url": "полный URL"}

    def run(self, url):
        _check()
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            subprocess.Popen(
                ["cmd", "/c", "start", "", url],
                shell=False,
                creationflags=0x08000000,  # CREATE_NO_WINDOW
            )
            _log(f"open_url: {url}")
            return f"[ok] открываю {url}"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopReadClipboardTool(Tool):
    name = "desktop_read_clipboard"
    description = "Прочитать текст из буфера обмена."
    parameters = {}

    def run(self):
        _check()
        try:
            import pyperclip

            txt = pyperclip.paste() or ""
            _log(f"read_clipboard: {len(txt)} симв.")
            return txt[:3000] or "(буфер пуст)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopCopyAllTool(Tool):
    name = "desktop_copy_all"
    description = ("Скопировать весь текст текущего окна "
                   "(Ctrl+A, Ctrl+C) и вернуть его из буфера.")
    parameters = {}

    def run(self):
        _check()
        try:
            pg = _pg()
            import pyperclip

            pyperclip.copy("")  # очистка
            time.sleep(0.1)
            pg.hotkey("ctrl", "a")
            time.sleep(0.15)
            pg.hotkey("ctrl", "c")
            time.sleep(0.3)
            txt = pyperclip.paste() or ""
            return txt[:4000] or "(скопировалось пусто)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


class DesktopFindInPageTool(Tool):
    name = "desktop_find_in_page"
    description = ("Найти текст на странице (Ctrl+F, ввод, Enter). "
                   "Возвращает позицию совпадения если удастся.")
    parameters = {"text": "что искать"}

    def run(self, text):
        _check()
        try:
            pg = _pg()
            pg.hotkey("ctrl", "f")
            time.sleep(0.2)
            pg.typewrite(text, interval=0.01)
            time.sleep(0.3)
            pg.press("enter")
            time.sleep(0.2)
            return f"[ok] ищу {text!r} на странице"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"





class DesktopCleanupTool(Tool):
    name = "desktop_cleanup_screenshots"
    description = ("Удалить ВСЕ временные PNG-скриншоты из рабочей папки. "
                   "Вызывай ПОСЛЕ того как закончил смотреть скриншоты.")
    parameters = {"keep": "имя файла для сохранения (опционально)"}

    def run(self, keep=""):
        _check()
        try:
            cwd = Path.cwd()
            patterns = [
                "screen.png", "_see_tmp.png", "browser.png",
                "wb_*.png", "*_screen.png", "*_screenshot.png",
            ]
            deleted = []
            keep_path = (cwd / keep).resolve() if keep else None

            for pat in patterns:
                for f in cwd.glob(pat):
                    try:
                        if keep_path and f.resolve() == keep_path:
                            continue
                        f.unlink()
                        deleted.append(f.name)
                    except Exception:
                        pass

            if not deleted:
                return "[ok] нечего удалять"
            _log(f"cleanup: удалено {len(deleted)} файлов")
            return f"[ok] удалено {len(deleted)}: " + ", ".join(deleted[:10])
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"



ALL_DESKTOP_TOOLS = [
    DesktopCleanupTool,
    DesktopOpenUrlTool,
    DesktopReadClipboardTool,
    DesktopCopyAllTool,
    DesktopFindInPageTool,
    DesktopScreenshotTool, DesktopSeeTool, DesktopClickTool,
    DesktopDoubleClickTool, DesktopRightClickTool, DesktopMoveTool,
    DesktopDragTool, DesktopScrollTool, DesktopTypeTool,
    DesktopHotkeyTool, DesktopPressTool, DesktopWindowsTool,
    DesktopFocusWindowTool, DesktopActiveWindowTool,
    DesktopScreenSizeTool, DesktopCursorPosTool, DesktopWaitTool,
]
