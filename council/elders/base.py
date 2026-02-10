"""Base Elder class and registry."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

# External personalities directory (proprietary, not in repo)
PERSONALITIES_DIR = Path.home() / ".council" / "personalities"


def load_external_prompt(elder_id: str) -> str | None:
    """Load a personality prompt from the external proprietary directory."""
    prompt_file = PERSONALITIES_DIR / f"{elder_id}.txt"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    return None


def save_external_prompt(elder_id: str, prompt: str) -> Path:
    """Save a personality prompt to the external proprietary directory."""
    PERSONALITIES_DIR.mkdir(parents=True, exist_ok=True)
    prompt_file = PERSONALITIES_DIR / f"{elder_id}.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    return prompt_file


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
    is_custom: bool = False

    @property
    def system_prompt(self) -> str:
        """Return the system prompt that defines this elder's personality.

        First checks for external proprietary prompt in ~/.council/personalities/
        Falls back to built-in prompt if no external file exists.
        """
        external = load_external_prompt(self.id)
        if external:
            return external
        return self._builtin_prompt

    @property
    @abstractmethod
    def _builtin_prompt(self) -> str:
        """Built-in fallback prompt (open source version)."""
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

    @classmethod
    def unregister(cls, elder_id: str) -> bool:
        """Remove an elder from the registry."""
        if elder_id in cls._elders:
            del cls._elders[elder_id]
            return True
        return False


@dataclass
class NominatedElder(Elder):
    """A dynamically-created elder nominated during a discussion.

    Never registered in ElderRegistry -- exists only for the session.
    """

    _prompt: str = ""
    _nominated_by: str = ""
    _expertise: str = ""

    @property
    def _builtin_prompt(self) -> str:
        return self._prompt
