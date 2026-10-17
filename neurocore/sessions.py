"""Session storage: load, save, export, import, duplicate."""
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

DIR = Path.home() / ".neurocore" / "sessions"
DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Session:
    id: str
    title: str
    created: float
    updated: float
    messages: list = field(default_factory=list)  # [{role, content, ts?}]
    model: str = "deepseek-v4-pro"
    preset: str = ""
    workspace: str = ""

    @classmethod
    def new(cls, model: str = "deepseek-v4-pro", preset: str = "",
            workspace: str = "") -> "Session":
        now = time.time()
        return cls(id=uuid.uuid4().hex[:12], title="Новая сессия",
                   created=now, updated=now, model=model, preset=preset,
                   workspace=workspace)

    def save(self):
        p = DIR / (self.id + ".json")
        p.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2),
                     encoding="utf-8")

    @classmethod
    def load(cls, sid: str) -> "Session":
        p = DIR / (sid + ".json")
        if not p.exists():
            raise FileNotFoundError("session not found: " + sid)
        d = json.loads(p.read_text(encoding="utf-8"))
        d.setdefault("model", "deepseek-v4-pro")
        d.setdefault("preset", "")
        d.setdefault("workspace", "")
        return cls(**d)

    @classmethod
    def all(cls) -> list:
        out = []
        for p in DIR.glob("*.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                d.setdefault("model", "deepseek-v4-pro")
                d.setdefault("preset", "")
                d.setdefault("workspace", "")
                out.append(cls(**d))
            except Exception:
                pass
        out.sort(key=lambda s: s.updated, reverse=True)
        return out

    @classmethod
    def delete(cls, sid: str):
        p = DIR / (sid + ".json")
        if p.exists():
            p.unlink()

    def duplicate(self) -> "Session":
        now = time.time()
        copy = Session(
            id=uuid.uuid4().hex[:12],
            title=self.title + " (copy)",
            created=now, updated=now,
            messages=[dict(m) for m in self.messages],
            model=self.model, preset=self.preset, workspace=self.workspace,
        )
        copy.save()
        return copy

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content,
                              "ts": time.time()})
        self.updated = time.time()
        if role == "user" and self.title in ("New session", "Untitled", "Новая сессия"):
            first = content.strip().split("\n")[0][:48]
            if first:
                self.title = first
        self.save()

    def rename(self, new_title: str):
        self.title = (new_title.strip()[:60] or "New session")
        self.updated = time.time()
        self.save()

    def export_markdown(self) -> str:
        lines = ["# " + self.title, "",
                 "*Модель: " + self.model + "*", ""]
        for m in self.messages:
            role = m["role"]
            if role == "user":
                lines.append("## 👤 User")
            elif role == "assistant":
                lines.append("## 🐋 NeuroCore")
            else:
                lines.append("## " + role)
            lines.append("")
            lines.append(m["content"])
            lines.append("")
        return "\n".join(lines)

    def export_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def import_json(cls, text: str) -> "Session":
        d = json.loads(text)
        d["id"] = uuid.uuid4().hex[:12]
        d["updated"] = time.time()
        d.setdefault("model", "deepseek-v4-pro")
        d.setdefault("preset", "")
        s = cls(**d)
        s.save()
        return s
