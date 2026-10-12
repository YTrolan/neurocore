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


# ============================================================
# БРАУЗЕРЫ
# ============================================================
BROWSERS = {
    "chrome": {
        "display": "Google Chrome",
        "exe": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ],
        "user_data": r"%LOCALAPPDATA%\Google\Chrome\User Data",
        "profile_sub": "Default",
        "playwright_channel": "chrome",
    },
    "edge": {
        "display": "Microsoft Edge",
        "exe": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ],
        "user_data": r"%LOCALAPPDATA%\Microsoft\Edge\User Data",
        "profile_sub": "Default",
        "playwright_channel": "msedge",
    },
    "brave": {
        "display": "Brave",
        "exe": [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        ],
        "user_data": r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data",
        "profile_sub": "Default",
        "playwright_channel": None,
    },
    "vivaldi": {
        "display": "Vivaldi",
        "exe": [
            r"C:\Program Files\Vivaldi\Application\vivaldi.exe",
            r"%LOCALAPPDATA%\Vivaldi\Application\vivaldi.exe",
        ],
        "user_data": r"%LOCALAPPDATA%\Vivaldi\User Data",
        "profile_sub": "Default",
        "playwright_channel": None,
    },
    "opera": {
        "display": "Opera",
        "exe": [
            r"C:\Program Files\Opera\opera.exe",
            r"%LOCALAPPDATA%\Programs\Opera\opera.exe",
        ],
        "user_data": r"%APPDATA%\Opera Software\Opera Stable",
        "profile_sub": "",
        "playwright_channel": None,
    },
}


def _expand(path: str) -> str:
    return os.path.expandvars(path)


def get_available_browsers() -> dict:
    """Возвращает {kind: info} для установленных браузеров."""
    result = {}
    for kind, info in BROWSERS.items():
        exe = None
        for p in info["exe"]:
            p_expanded = _expand(p)
            if os.path.exists(p_expanded):
                exe = p_expanded
                break
        if not exe:
            continue
        ud = _expand(info["user_data"])
        if not os.path.isdir(ud):
            continue
        result[kind] = {
            "display": info["display"],
            "exe": exe,
            "user_data": ud,
            "profile_sub": info["profile_sub"],
            "channel": info["playwright_channel"],
        }
    return result


def _pick_browser(browser_kind: str, available: dict) -> str:
    """auto = chrome → edge → brave → vivaldi → opera."""
    if browser_kind and browser_kind != "auto":
        if browser_kind in available:
            return browser_kind
        print(f"[token] '{browser_kind}' не найден, авто-выбор", flush=True)
    for pref in ("chrome", "edge", "brave", "vivaldi", "opera"):
        if pref in available:
            return pref
    return list(available.keys())[0] if available else ""


def _copy_profile(src_user_data: str, profile_sub: str, dst_dir: Path):
    """Копирует профиль браузера во временную папку."""
    if dst_dir.exists():
        shutil.rmtree(dst_dir, ignore_errors=True)
    dst_dir.mkdir(parents=True, exist_ok=True)

    src_root = Path(src_user_data)
    dst_root = dst_dir

    # Local State в корне User Data
    src_ls = src_root / "Local State"
    if src_ls.exists():
        try:
            shutil.copy2(src_ls, dst_root / "Local State")
        except Exception as e:
            print(f"[token] skip Local State: {e}", flush=True)

    # Профиль
    if profile_sub:
        src_prof = src_root / profile_sub
        dst_prof = dst_root / profile_sub
    else:
        src_prof = src_root
        dst_prof = dst_root

    if not src_prof.exists():
        raise RuntimeError(f"нет папки профиля: {src_prof}")

    dst_prof.mkdir(parents=True, exist_ok=True)

    # Файлы
    for fname in ("Cookies", "Cookies-journal", "Preferences",
                  "Login Data", "Login Data-journal", "Web Data",
                  "Secure Preferences"):
        src_f = src_prof / fname
        if src_f.exists():
            try:
                shutil.copy2(src_f, dst_prof / fname)
            except Exception as e:
                print(f"[token] skip {fname}: {e}", flush=True)

    # Папки
    for dname in ("Local Storage", "Session Storage", "IndexedDB"):
        src_d = src_prof / dname
        dst_d = dst_prof / dname
        if src_d.exists():
            try:
                shutil.copytree(
                    src_d, dst_d, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(
                        "*.lock", "LOCK", "*.tmp"))
            except Exception as e:
                print(f"[token] skip dir {dname}: {e}", flush=True)


def _extract_token(raw):
    if not raw:
        return ""
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj.get("value", "") or obj.get("token", "")
        return str(obj)
    except Exception:
        return raw.strip('"').strip("'")


def fetch_token_via_browser(timeout: int = 60,
                             browser_kind: str = "") -> str:
    """
    Забрать userToken из основного браузера.
    
    browser_kind: "auto" | "chrome" | "edge" | "brave" | "vivaldi" | "opera"
    Если пусто — берём из config.json.
    """
    if not browser_kind:
        try:
            from . import config as cfgmod
            browser_kind = cfgmod.load().get("browser_kind", "auto") or "auto"
        except Exception:
            browser_kind = "auto"

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("нужен playwright: pip install playwright")

    available = get_available_browsers()
    if not available:
        raise RuntimeError(
            "не найден ни один браузер. Поддерживаются: "
            "Chrome, Edge, Brave, Vivaldi, Opera")

    print(f"[token] найдены браузеры: {list(available.keys())}", flush=True)

    kind = _pick_browser(browser_kind, available)
    if not kind:
        raise RuntimeError("не удалось выбрать браузер")

    info = available[kind]
    print(f"[token] использую: {info['display']}", flush=True)

    # Копируем профиль
    tmp_dir = TOKEN_DIR / f"browser_copy_{kind}"
    print(f"[token] копирую профиль...", flush=True)
    _copy_profile(info["user_data"], info["profile_sub"], tmp_dir)
    print(f"[token] профиль готов", flush=True)

    pw = sync_playwright().start()
    launch = {
        "user_data_dir": str(tmp_dir),
        "headless": False,
        "args": ["--no-first-run", "--no-default-browser-check"],
    }
    if info["channel"]:
        launch["channel"] = info["channel"]
    else:
        launch["executable_path"] = info["exe"]

    try:
        ctx = pw.chromium.launch_persistent_context(**launch)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        page.goto("https://chat.deepseek.com",
                  wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        token = ""
        try:
            raw = page.evaluate("() => localStorage.getItem('userToken')")
            token = _extract_token(raw)
        except Exception:
            pass

        # Если не сразу — ждём логина
        if not token:
            print("[token] залогинься в окне (до 3 мин)", flush=True)
            start = time.time()
            while time.time() - start < timeout * 3:
                try:
                    raw = page.evaluate(
                        "() => localStorage.getItem('userToken')")
                    token = _extract_token(raw)
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
            shutil.rmtree(tmp_dir, ignore_errors=True)
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
