"""Загрузка файлов + POW для chat.deepseek.com."""
import uuid
from pathlib import Path

import requests

API_BASE = "https://chat.deepseek.com/api/v0"


def _client_headers(token: str) -> dict:
    return {
        "accept": "*/*",
        "accept-language": "ru-RU,ru;q=0.9,en;q=0.8",
        "authorization": "Bearer " + token,
        "origin": "https://chat.deepseek.com",
        "referer": "https://chat.deepseek.com/",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0 Safari/537.36"
        ),
        "x-client-bundle-id": "com.deepseek.chat",
        "x-client-locale": "ru",
        "x-client-platform": "web",
        "x-client-timezone-offset": "10800",
        "x-client-version": "2.5.0",
        "x-device-id": str(uuid.uuid4()),
        "x-device-model": "",
        "x-model-type": "default",
        "x-thinking-enabled": "1",
    }


def _solve_pow(token: str, target_path: str, timeout: int = 30):
    """Решает POW. Возвращает base64-ответ или None."""
    try:
        from opendeep.pow import DeepSeekPOW
    except ImportError as e:
        print("[upload] POW недоступен:", e)
        return None

    headers = _client_headers(token)
    headers["content-type"] = "application/json"

    try:
        r = requests.post(
            API_BASE + "/chat/create_pow_challenge",
            headers=headers,
            json={"target_path": target_path},
            timeout=timeout,
        )
        if not r.ok:
            print("[upload] create_pow_challenge HTTP", r.status_code,
                  r.text[:300])
            return None
        data = r.json()
        challenge = (data.get("data", {})
                        .get("biz_data", {})
                        .get("challenge"))
        if not challenge:
            print("[upload] нет challenge в ответе")
            return None

        solver = DeepSeekPOW()
        return solver.solve_challenge(challenge)
    except Exception as e:
        print("[upload] ошибка POW:", type(e).__name__, e)
        return None


def upload_file(path: str, token: str, timeout: int = 60) -> dict:
    """Загружает файл. Возвращает {status, ok, response}."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    ext = p.suffix.lower()
    mime = {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
        ".svg": "image/svg+xml", ".pdf": "application/pdf",
        ".txt": "text/plain",
    }.get(ext, "application/octet-stream")

    data = p.read_bytes()
    target_path = "/api/v0/file/upload_file"

    headers = _client_headers(token)
    headers["x-file-size"] = str(len(data))
    headers["priority"] = "u=1, i"

    pow_resp = _solve_pow(token, target_path, timeout)
    if pow_resp:
        headers["x-ds-pow-response"] = pow_resp
        print("[upload] POW получен")
    else:
        print("[upload] POW не решён — пробую без него")

    files = {"file": (p.name, data, mime)}

    r = requests.post(
        API_BASE + "/file/upload_file",
        headers=headers, files=files, timeout=timeout,
    )

    try:
        payload = r.json()
    except Exception:
        payload = {"raw": r.text[:500]}

    return {"status": r.status_code, "ok": r.status_code == 200,
            "response": payload}


def fetch_files(file_ids, token: str, timeout: int = 20) -> dict:
    if not file_ids:
        return {"ok": False}
    if isinstance(file_ids, (list, tuple)):
        ids = ",".join(file_ids)
    else:
        ids = str(file_ids)
    r = requests.get(
        API_BASE + "/file/fetch_files",
        params={"file_ids": ids},
        headers=_client_headers(token),
        timeout=timeout,
    )
    try:
        payload = r.json()
    except Exception:
        payload = {"raw": r.text[:500]}
    return {"status": r.status_code, "ok": r.status_code == 200,
            "response": payload}
