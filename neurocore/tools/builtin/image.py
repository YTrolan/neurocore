import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from ..base import Tool

ENDPOINTS = [
    "https://image.pollinations.ai/prompt/{p}?width={w}&height={h}&nologo=true",
    "https://image.pollinations.ai/prompt/{p}?width={w}&height={h}&nologo=true&model=flux",
    "https://pollinations.ai/p/{p}?width={w}&height={h}&nologo=true",
]


class GenerateImageTool(Tool):
    """Генерация изображений через бесплатный Pollinations API."""

    name = "generate_image"
    description = (
        "Сгенерировать изображение по текстовому описанию и сохранить в файл. "
        "Используй ВСЕГДА, когда пользователь просит нарисовать/сгенерировать картинку."
    )
    parameters = {
        "prompt": "детальное описание картинки на английском",
        "path": "куда сохранить, например 'cat.png'",
    }

    def __init__(self, width: int = 1024, height: int = 1024, timeout: int = 25):
        self.width = width
        self.height = height
        self.timeout = timeout

    def _try_url(self, url: str) -> bytes | None:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; NeuroCore/0.1)",
                "Accept": "image/*",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                ctype = r.headers.get("Content-Type", "")
                if not ctype.startswith("image/"):
                    print(
                        f"  [!] получен не image ({ctype}), пробую другой источник",
                        file=sys.stderr,
                    )
                    return None
                return r.read()
        except Exception as e:
            print(f"  [!] {type(e).__name__}: {e}", file=sys.stderr)
            return None

    def run(self, prompt: str, path: str = "generated.png") -> str:
        p = urllib.parse.quote(prompt)
        last_err = "неизвестная ошибка"

        for i, tpl in enumerate(ENDPOINTS, 1):
            url = tpl.format(p=p, w=self.width, h=self.height)
            host = url.split("/")[2]
            print(f"  · источник {i}/{len(ENDPOINTS)}: {host} (до {self.timeout}s)",
                  file=sys.stderr)
            t0 = time.time()
            data = self._try_url(url)
            if data:
                out = Path(path)
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(data)
                dt = time.time() - t0
                return f"[ok] изображение сохранено: {out} ({len(data)} байт, {dt:.1f}s)"
            last_err = f"источник {i} не ответил"

        return f"[error] все источники исчерпаны. Последнее: {last_err}"


__all__ = ["GenerateImageTool"]
