"""Менеджер токена DeepSeek — хранит в ~/.neurocore/token.txt."""
import json
import os
import shutil
import time
from pathlib import Path

TOKEN_DIR = Path.home() / ".neurocore"
TOKEN_FILE = TOKEN_DIR / "token.txt"


def load_token() -> str:
    """Токен: 1) файл, 2) env DEEPSEEK_TOKEN, 3) пусто."""
    try:
        TOKEN_DIR.mkdir(parents=True, exist_ok=True)
        if TOKEN_FILE.exists():
            t = TOKEN_FILE.read_text(encoding="utf-8").strip()
            if t:
                return t
    except Exception:
        pass
    return os.getenv("DEEPSEEK_TOKEN", "") or ""


def save_token(token: str) -> bool:
    try:
        TOKEN_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(token.strip(), encoding="utf-8")
        return True
    except Exception as e:
        print(f"[token] save error: {e}", flush=True)
        return False


def clear_token():
    try:
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
    except Exception:
        pass


def fetch_token_via_browser(timeout: int = 60) -> str:
    """
    Забрать userToken из ОСНОВНОГО профиля Chrome.
    Копирует профиль в temp, основной Chrome не трогает.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("нужен playwright: pip install playwright")

    chrome_user_data = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
    if not chrome_user_data.exists():
        raise RuntimeError(f"нет папки Chrome: {chrome_user_data}")

    chrome_exe = Path(r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
    if not chrome_exe.exists():
        chrome_exe = Path(r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe")

    tmp_root = TOKEN_DIR / "chrome_copy"
    if tmp_root.exists():
        shutil.rmtree(tmp_root, ignore_errors=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    src_default = chrome_user_data / "Default"
    dst_default = tmp_root / "Default"

    if not src_default.exists():
        raise RuntimeError(f"нет профиля Default: {src_default}")

    print("[token] копирую профиль Chrome...", flush=True)
    dst_default.mkdir(exist_ok=True)

    for fname in ["Cookies", "Cookies-journal", "Preferences",
                  "Login Data", "Login Data-journal", "Web Data",
                  "Secure Preferences"]:
        src_f = src_default / fname
        if src_f.exists():
            try:
                shutil.copy2(src_f, dst_default / fname)
            except Exception as e:
                print(f"[token] skip {fname}: {e}", flush=True)

    for dname in ["Local Storage", "Session Storage", "IndexedDB", "Network"]:
        src_d = src_default / dname
        dst_d = dst_default / dname
        if src_d.exists():
            try:
                shutil.copytree(src_d, dst_d, dirs_exist_ok=True,
                                ignore=shutil.ignore_patterns(
                                    "*.lock", "LOCK", "*.tmp"))
            except Exception as e:
                print(f"[token] skip dir {dname}: {e}", flush=True)

    src_ls = chrome_user_data / "Local State"
    if src_ls.exists():
        try:
            shutil.copy2(src_ls, tmp_root / "Local State")
        except Exception:
            pass

    print(f"[token] профиль скопирован", flush=True)

    pw = sync_playwright().start()
    launch_kwargs = {
        "user_data_dir": str(tmp_root),
        "headless": False,
        "args": ["--no-first-run", "--no-default-browser-check"],
    }
    if chrome_exe.exists():
        launch_kwargs["executable_path"] = str(chrome_exe)

    try:
        ctx = pw.chromium.launch_persistent_context(**launch_kwargs)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        page.goto("https://chat.deepseek.com",
                  wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        token = ""
        try:
            raw = page.evaluate("() => localStorage.getItem('userToken')")
            if raw:
                try:
                    obj = json.loads(raw)
                    if isinstance(obj, dict):
                        token = obj.get("value", "") or obj.get("token", "")
                    else:
                        token = str(obj)
                except Exception:
                    token = raw.strip('"').strip("'")
        except Exception as e:
            print(f"[token] localStorage: {e}", flush=True)

        if not token:
            print("[token] не нашёл. Залогинься в окне. Жду 2 мин...",
                  flush=True)
            start = time.time()
            while time.time() - start < timeout:
                try:
                    raw = page.evaluate(
                        "() => localStorage.getItem('userToken')")
                    if raw:
                        try:
                            obj = json.loads(raw)
                            if isinstance(obj, dict):
                                token = obj.get("value", "") or obj.get("token", "")
                            else:
                                token = str(obj)
                        except Exception:
                            token = raw.strip('"').strip("'")
                        if token:
                            break
                except Exception:
                    pass
                time.sleep(1.5)

        try:
            ctx.close()
        except Exception:
            pass
        try:
            pw.stop()
        except Exception:
            pass
        try:
            shutil.rmtree(tmp_root, ignore_errors=True)
        except Exception:
            pass

        if token:
            save_token(token)
            print(f"[token] получен, длина {len(token)}", flush=True)
            return token
        return ""
    except Exception as e:
        try:
            pw.stop()
        except Exception:
            pass
        raise

