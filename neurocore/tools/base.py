from abc import ABC, abstractmethod


class Tool(ABC):
    name: str
    description: str
    parameters: dict

    @abstractmethod
    def run(self, **kwargs) -> str: ...

    def spec(self) -> str:
        args = ", ".join(f"{k}: {v}" for k, v in self.parameters.items()) or "нет"
        return "- **" + self.name + "** — " + self.description + "\n  Аргументы: " + args
