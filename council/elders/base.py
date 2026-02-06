"""Base Elder class and registry."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class Elder(ABC):
    """Base class for all elders in the council."""

    id: str
    name: str
    title: str
    era: str
    color: str  # Rich color for terminal display
    mental_models: list[str] = field(default_factory=list)
    key_works: list[str] = field(default_factory=list)

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt that defines this elder's personality."""
        pass

    @property
    def short_description(self) -> str:
        """Short one-line description of this elder."""
        return f"{self.name} - {self.title}"

    def get_greeting(self) -> str:
        """Return a characteristic greeting from this elder."""
        return f"I am {self.name}. How may I help you think through your question?"


class ElderRegistry:
    """Registry of all available elders."""

    _elders: ClassVar[dict[str, Elder]] = {}

    @classmethod
    def register(cls, elder: Elder) -> None:
        """Register an elder."""
        cls._elders[elder.id] = elder

    @classmethod
    def get(cls, elder_id: str) -> Elder | None:
        """Get an elder by ID."""
        return cls._elders.get(elder_id)

    @classmethod
    def get_all(cls) -> list[Elder]:
        """Get all registered elders."""
        return list(cls._elders.values())

    @classmethod
    def get_ids(cls) -> list[str]:
        """Get all elder IDs."""
        return list(cls._elders.keys())

    @classmethod
    def exists(cls, elder_id: str) -> bool:
        """Check if an elder exists."""
        return elder_id in cls._elders
