from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    role: Role
    content: str
    name: str | None = None

    def to_dict(self) -> dict:
        d = {"role": self.role.value, "content": self.content}
        if self.name:
            d["name"] = self.name
        return d
