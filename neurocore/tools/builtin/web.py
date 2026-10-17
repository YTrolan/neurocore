"""Инструменты интернета — параллельные запросы, быстро."""
import concurrent.futures
import re
import urllib.parse
from urllib.parse import quote_plus

import requests

from ..base import Tool

requests.packages.urllib3.disable_warnings()


UA_BROWSER = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)
UA_WIKI = "NeuroCoreBot/1.0 (personal; local)"

# короткий таймаут — быстро падаем и пробуем другой источник
TIMEOUT = 6


def _strip_html(html: str) -> str:
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.DOTALL | re.I)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.DOTALL | re.I)
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", html)
    for k, v in {"&nbsp;": " ", "&amp;": "&", "&lt;": "<",
                 ">": ">", "&quot;": '"', "&#39;": "'"}.items():
        text = text.replace(k, v)
    return re.sub(r"\s+", " ", text).strip()


# ============================================================
# Fetcher — читает страницу
# ============================================================
class WebFetchTool(Tool):
    name = "web_fetch"
    description = ("Скачать URL и вернуть текст страницы. "
                   "Используй для чтения статей.")
    parameters = {"url": "полный URL"}

    def __init__(self, timeout: int = 12, max_chars: int = 8000):
        self.timeout = timeout
        self.max_chars = max_chars

    def run(self, url: str) -> str:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        headers = {
            "User-Agent": UA_WIKI if "wikipedia.org" in url else UA_BROWSER,
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        }
        last = f"[error] не загрузить {url}"
        for verify in (True, False):
            try:
                r = requests.get(url, headers=headers, timeout=self.timeout,
                                 allow_redirects=True, verify=verify)
                ctype = r.headers.get("content-type", "").lower()
                is_html = "html" in ctype or url.endswith((".html", "/"))
                text = _strip_html(r.text) if is_html else r.text
                if len(text) > self.max_chars:
                    text = text[:self.max_chars] + "...[обрезано]"
                note = "" if verify else " [SSL off]"
                return f"[{r.status_code}] {url}{note}\n{text or '(пусто)'}"
            except requests.exceptions.SSLError:
                continue
            except requests.exceptions.Timeout:
                return f"[timeout {self.timeout}s] {url}"
            except Exception as e:
                last = f"[error] {type(e).__name__}: {e}"
                continue
        return last


# ============================================================
# Search — параллельно Bing + Wikipedia
# ============================================================
class WebSearchTool(Tool):
    name = "web_search"
    description = ("Найти информацию в интернете. Возвращает результаты "
                   "с URL. Работает через Bing + Wikipedia параллельно.")
    parameters = {"query": "поисковый запрос"}

    def __init__(self, timeout: int = TIMEOUT, max_results: int = 6):
        self.timeout = timeout
        self.max_results = max_results

    def run(self, query: str) -> str:
        ex = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        try:
            futures = [
                ex.submit(self._bing, query),
                ex.submit(self._wikipedia, query),
            ]
            try:
                for f in concurrent.futures.as_completed(
                        futures, timeout=self.timeout + 1):
                    try:
                        r = f.result()
                        if r and len(r) > 30:
                            return r
                    except Exception:
                        continue
            except concurrent.futures.TimeoutError:
                pass
        finally:
            ex.shutdown(wait=False)

        q = quote_plus(query)
        return (
            "(не удалось получить результаты автоматически)\n"
            f"Google: https://www.google.com/search?q={q}\n"
            f"Яндекс: https://yandex.ru/search/?text={q}"
        )

    # ---------- Bing (основной, 1 запрос) ----------
    def _bing(self, query: str) -> str:
        q = quote_plus(query)
        r = requests.get(
            f"https://www.bing.com/search?q={q}&setlang=ru&cc=RU",
            headers={
                "User-Agent": UA_BROWSER,
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            },
            timeout=self.timeout,
            verify=False,
        )
        if r.status_code != 200:
            return ""
        html = r.text
        blocks = re.findall(
            r'<li class="b_algo".*?<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>'
            r'.*?(?:<p[^>]*>(.*?)</p>|<div class="b_caption"[^>]*>(.*?)</div>)',
            html, flags=re.DOTALL | re.I,
        )
        out = ["Bing:"]
        for url, title, s1, s2 in blocks[: self.max_results]:
            title = _strip_html(title)
            snip = _strip_html(s1 or s2 or "")
            if not title or len(title) < 3:
                continue
            out.append(f"• {title}\n  {url}\n  {snip[:200]}")
        return "\n\n".join(out) if len(out) > 1 else ""

    # ---------- Wikipedia (fallback, 1 запрос REST) ----------
    def _wikipedia(self, query: str) -> str:
        lang = "ru" if re.search(r"[а-яА-Я]", query) else "en"
        t = urllib.parse.quote(query.replace(" ", "_"))
        try:
            r = requests.get(
                f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{t}",
                headers={"User-Agent": UA_WIKI},
                timeout=self.timeout,
                verify=False,
            )
            if r.status_code == 200:
                d = r.json()
                extract = d.get("extract", "")
                if extract and len(extract) > 40:
                    url = d.get("content_urls", {}).get(
                        "desktop", {}).get("page", "")
                    return (f"Wikipedia:\n• {d.get('title', query)}\n"
                            f"  {url}\n  {extract[:400]}")
        except Exception:
            pass

        try:
            r = requests.get(
                f"https://{lang}.wikipedia.org/w/api.php",
                params={"action": "opensearch", "search": query,
                        "limit": self.max_results, "namespace": 0,
                        "format": "json"},
                headers={"User-Agent": UA_WIKI},
                timeout=self.timeout,
                verify=False,
            )
            if r.status_code == 200:
                d = r.json()
                if isinstance(d, list) and len(d) >= 4 and d[1]:
                    out = [f"Wikipedia ({lang}):"]
                    for i, title in enumerate(d[1][: self.max_results]):
                        url = d[3][i] if i < len(d[3]) else ""
                        out.append(f"• {title}\n  {url}")
                    return "\n\n".join(out)
        except Exception:
            pass
        return ""


# ============================================================
# WebText
# ============================================================
class WebTextTool(Tool):
    name = "web_text"
    description = "Скачать страницу и вернуть ТОЛЬКО читаемый текст."
    parameters = {"url": "URL"}

    def __init__(self, timeout: int = 15, max_chars: int = 6000):
        self.timeout = timeout
        self.max_chars = max_chars

    def run(self, url: str) -> str:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            headers = {
                "User-Agent": UA_WIKI if "wikipedia.org" in url else UA_BROWSER,
                "Accept-Language": "ru-RU,ru;q=0.9",
            }
            r = requests.get(url, headers=headers, timeout=self.timeout,
                             verify=False, allow_redirects=True)
            text = _strip_html(r.text)
            if len(text) > self.max_chars:
                text = text[:self.max_chars] + "..."
            return text or "(пусто)"
        except Exception as e:
            return f"[error] {type(e).__name__}: {e}"


__all__ = ["WebFetchTool", "WebSearchTool", "WebTextTool"]
