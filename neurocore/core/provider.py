from abc import ABC, abstractmethod

from .message import Message


class Provider(ABC):
    @abstractmethod
    def chat(self, messages: list[Message]) -> Message: ...

    @abstractmethod
    def reset(self) -> None: ...
