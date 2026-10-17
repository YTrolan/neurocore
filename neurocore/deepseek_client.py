"""DeepSeek chat с поддержкой файлов (vision)."""
import json
import time

import requests

from .deepseek_upload import API_BASE as BASE
from .deepseek_upload import _client_headers, _solve_pow, upload_file


class DeepSeekClient:
    """Statefull чат-сессия DeepSeek с поддержкой ref_file_ids."""

    def __init__(self, token: str, model: str = "deepseek-v4-pro",
                 thinking: bool = False):
        self.token = token
        self.model = model
        self.thinking = thinking
        self.session_id = None
        self.parent_id = None

    def reset(self):
        self.session_id = None
        self.parent_id = None

    def _headers(self):
        return _client_headers(self.token)

    def _create_session(self):
        h = self._headers()
        h["content-type"] = "application/json"
        r = requests.post(
            BASE + "/chat_session/create",
            headers=h,
            json={"character_id": None},
            timeout=30,
        )
        r.raise_for_status()
        biz = r.json().get("data", {}).get("biz_data", {})
        self.session_id = (biz.get("id") or
                            biz.get("chat_session", {}).get("id"))
        if not self.session_id:
            raise RuntimeError("Не получил session_id: " + r.text[:300])

    # ---------- загрузка картинок ----------
    def upload_image(self, path: str) -> str:
        r = upload_file(path, self.token)
        if not r.get("ok"):
            raise RuntimeError("Загрузка не удалась: " +
                                str(r.get("response"))[:300])
        fid = (r["response"].get("data", {})
                          .get("biz_data", {})
                          .get("id"))
        if not fid:
            raise RuntimeError("Нет file_id: " + str(r["response"])[:300])
        return fid

    def wait_ready(self, file_id: str, timeout: float = 30.0) -> bool:
        t0 = time.time()
        while time.time() - t0 < timeout:
            r = requests.get(
                BASE + "/file/fetch_files",
                params={"file_ids": file_id},
                headers=self._headers(),
                timeout=15,
            )
            if r.ok:
                files = (r.json().get("data", {})
                                 .get("biz_data", {})
                                 .get("files", []))
                if files:
                    st = files[0].get("status")
                    if st == "SUCCESS":
                        return True
                    if st == "ERROR":
                        return False
            time.sleep(0.5)
        return False

    # ---------- отправка сообщения ----------
    def send(self, prompt: str, file_ids: list = None,
             on_chunk=None) -> str:
        if self.session_id is None:
            self._create_session()

        target_path = "/api/v0/chat/completion"
        headers = self._headers()
        headers["content-type"] = "application/json"

        pow_resp = _solve_pow(self.token, target_path)
        if pow_resp:
            headers["x-ds-pow-response"] = pow_resp

        payload = {
            "chat_session_id": self.session_id,
            "parent_message_id": self.parent_id,
            "prompt": prompt,
            "ref_file_ids": list(file_ids or []),
            "thinking_enabled": bool(self.thinking),
            "search_enabled": False,
            "action": None,
            "preempt": False,
            "model_type": "default",
        }

        r = requests.post(BASE + "/chat/completion",
                           headers=headers, json=payload,
                           stream=True, timeout=180)
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")

        full = ""
        for line in r.iter_lines():
            if not line:
                continue
            text = line.decode("utf-8", errors="replace")
            if not text.startswith("data: ") or text == "data: [DONE]":
                continue
            try:
                data = json.loads(text[6:])
            except Exception:
                continue

            if "response_message_id" in data:
                self.parent_id = data["response_message_id"]

            content = ""
            if "choices" in data:
                choices = data.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
            elif "v" in data:
                val = data["v"]
                if isinstance(val, dict) and "response" in val:
                    mid = val["response"].get("message_id")
                    if mid:
                        self.parent_id = mid
                    for frag in val["response"].get("fragments", []):
                        if frag.get("type") != "THINK":
                            c = frag.get("content", "")
                            if c:
                                content = c
                elif isinstance(val, str):
                    if data.get("p") != "response/status":
                        content = val

            if content:
                full += content
                if on_chunk:
                    on_chunk(content)

        return full


    def upload_and_wait(self, path: str) -> str | None:
        """Загружает картинку и ждёт SUCCESS. Возвращает file_id или None."""
        try:
            fid = self.upload_image(path)
        except Exception as e:
            print("[vision] ошибка загрузки:", e)
            return None
        if not self.wait_ready(fid):
            print("[vision] файл не обработался:", fid)
            return None
        return fid
