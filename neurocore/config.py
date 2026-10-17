"""NeuroCore config: providers, models, settings."""
import json
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path

DIR = Path.home() / ".neurocore"
DIR.mkdir(parents=True, exist_ok=True)
FILE = DIR / "config.json"


@dataclass
class ProviderConfig:
    id: str
    name: str
    kind: str          # "opendeep" | "openai_compat"
    base_url: str = ""
    api_key: str = ""
    models: list = field(default_factory=list)


DEFAULTS = {
    "browser_kind": "auto",

    "chat_limit": 100,

    "output_dir": "",
    "providers": [
        {
            "id": "deepseek",
            "name": "DeepSeek",
            "kind": "opendeep",
            "base_url": "",
            "api_key": "",
            "models": ["deepseek-v4-pro", "deepseek-v4-flash",
                       "deepseek-chat", "deepseek-reasoner"],
        },
        {
            "id": "openai",
            "name": "OpenAI",
            "kind": "openai_compat",
            "base_url": "https://api.openai.com/v1",
            "api_key": "",
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        },
        {
            "id": "openrouter",
            "name": "OpenRouter",
            "kind": "openai_compat",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "",
            "models": ["anthropic/claude-3.5-sonnet",
                       "google/gemini-2.0-flash-exp",
                       "meta-llama/llama-3.3-70b-instruct"],
        },
        {
            "id": "custom",
            "name": "Custom endpoint",
            "kind": "openai_compat",
            "base_url": "",
            "api_key": "",
            "models": [],
        },
    ],
    "active_provider": "deepseek",
    "active_model": "deepseek-v4-pro",
    "theme": "dark",
    "workspaces": [
        {"name": "По умолчанию", "path": ""},
    ],
    "active_workspace": "По умолчанию",
}


def _deep_merge(base, patch):
    if isinstance(base, dict) and isinstance(patch, dict):
        out = deepcopy(base)
        for k, v in patch.items():
            out[k] = _deep_merge(base.get(k), v) if k in base else v
        return out
    return deepcopy(patch)


def load() -> dict:
    if FILE.exists():
        try:
            user = json.loads(FILE.read_text(encoding="utf-8"))
            if not isinstance(user, dict):
                return deepcopy(DEFAULTS)
            return _deep_merge(DEFAULTS, user)
        except (OSError, ValueError):
            return deepcopy(DEFAULTS)
    cfg = deepcopy(DEFAULTS)
    save(cfg)
    return cfg


def save(cfg: dict):
    FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False),
                    encoding="utf-8")


def get_provider(cfg: dict, pid: str) -> dict | None:
    for p in cfg.get("providers", []):
        if p["id"] == pid:
            return p
    return None


def active_provider(cfg: dict) -> dict:
    p = get_provider(cfg, cfg.get("active_provider", "deepseek"))
    if p:
        return p
    return cfg["providers"][0]


def add_provider(cfg, name, kind, base_url, api_key, models):
    pid = "p_" + uuid.uuid4().hex[:6]
    cfg["providers"].append({
        "id": pid, "name": name, "kind": kind,
        "base_url": base_url, "api_key": api_key,
        "models": [m.strip() for m in models if m.strip()],
    })
    save(cfg)
    return pid


def remove_provider(cfg, pid):
    cfg["providers"] = [p for p in cfg["providers"] if p["id"] != pid]
    if cfg.get("active_provider") == pid:
        cfg["active_provider"] = cfg["providers"][0]["id"] if cfg["providers"] else ""
    save(cfg)


def get_workspaces(cfg) -> list:
    return cfg.get("workspaces", [{"name": "По умолчанию", "path": ""}])


def add_workspace(cfg, name, path):
    ws = cfg.setdefault("workspaces", [])
    for w in ws:
        if w["name"] == name:
            w["path"] = path
            save(cfg)
            return
    ws.append({"name": name, "path": path})
    save(cfg)


def remove_workspace(cfg, name):
    ws = cfg.get("workspaces", [])
    cfg["workspaces"] = [w for w in ws if w["name"] != name]
    if not cfg["workspaces"]:
        cfg["workspaces"] = [{"name": "По умолчанию", "path": ""}]
    if cfg.get("active_workspace") == name:
        cfg["active_workspace"] = cfg["workspaces"][0]["name"]
    save(cfg)


def active_workspace(cfg) -> dict:
    name = cfg.get("active_workspace", "По умолчанию")
    for w in get_workspaces(cfg):
        if w["name"] == name:
            return w
    return {"name": "По умолчанию", "path": ""}


# ============================================================
# Папка для сохранения файлов по умолчанию
# ============================================================
def get_output_dir() -> str:
    """Возвращает папку, куда агент сохраняет файлы без пути."""
    cfg = load()
    d = cfg.get("output_dir", "").strip()
    if d and Path(d).exists():
        return d
    return str(Path.cwd())


def set_output_dir(path: str):
    """Сохранить папку."""
    cfg = load()
    cfg["output_dir"] = str(path).strip()
    save(cfg)
