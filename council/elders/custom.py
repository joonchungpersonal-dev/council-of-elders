"""Custom elder persistence -- save/load enriched elders as JSON."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from council.config import get_config_dir
from council.elders.base import ElderRegistry, NominatedElder


CUSTOM_ELDERS_DIR = get_config_dir() / "elders" / "custom"


@dataclass
class CustomElder(NominatedElder):
    """A persisted elder with enrichment data, biography, and books."""

    is_custom: bool = True
    biography: dict = field(default_factory=dict)
    books: list[dict] = field(default_factory=list)
    enrichment: dict = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "era": self.era,
            "color": self.color,
            "prompt": self._prompt,
            "nominated_by": self._nominated_by,
            "expertise": self._expertise,
            "is_custom": True,
            "biography": self.biography,
            "books": self.books,
            "enrichment": self.enrichment,
            "created_at": self.created_at or datetime.now().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CustomElder":
        return cls(
            id=data["id"],
            name=data["name"],
            title=data.get("title", ""),
            era=data.get("era", ""),
            color=data.get("color", "bright_magenta"),
            _prompt=data.get("prompt", ""),
            _nominated_by=data.get("nominated_by", ""),
            _expertise=data.get("expertise", ""),
            biography=data.get("biography", {}),
            books=data.get("books", []),
            enrichment=data.get("enrichment", {}),
            created_at=data.get("created_at", ""),
        )

    @classmethod
    def from_nominated(cls, nominated: NominatedElder) -> "CustomElder":
        """Promote a NominatedElder to a CustomElder."""
        elder_id = nominated.id.replace("nominated_", "custom_")
        return cls(
            id=elder_id,
            name=nominated.name,
            title=nominated.title,
            era=nominated.era,
            color=nominated.color,
            _prompt=nominated._prompt,
            _nominated_by=nominated._nominated_by,
            _expertise=nominated._expertise,
            created_at=datetime.now().isoformat(),
        )


def _get_custom_dir() -> Path:
    CUSTOM_ELDERS_DIR.mkdir(parents=True, exist_ok=True)
    return CUSTOM_ELDERS_DIR


def save_custom_elder(elder_data: dict | CustomElder) -> Path:
    """Save a custom elder to disk as JSON."""
    if isinstance(elder_data, CustomElder):
        data = elder_data.to_dict()
    else:
        data = elder_data

    elder_id = data["id"]
    if not elder_id.startswith("custom_"):
        elder_id = f"custom_{elder_id}"
        data["id"] = elder_id

    filepath = _get_custom_dir() / f"{elder_id}.json"
    filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Register in the registry so the elder is available immediately
    elder = CustomElder.from_dict(data)
    ElderRegistry.register(elder)

    return filepath


def load_custom_elders() -> list[CustomElder]:
    """Load all saved custom elders from disk and register them."""
    custom_dir = _get_custom_dir()
    elders = []

    for path in sorted(custom_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            elder = CustomElder.from_dict(data)
            ElderRegistry.register(elder)
            elders.append(elder)
        except Exception as e:
            print(f"Warning: could not load custom elder {path.name}: {e}")

    return elders


def delete_custom_elder(elder_id: str) -> bool:
    """Delete a custom elder from disk and unregister it."""
    filepath = _get_custom_dir() / f"{elder_id}.json"
    if filepath.exists():
        filepath.unlink()
        ElderRegistry.unregister(elder_id)
        return True
    return False


def update_custom_elder(elder_id: str, updates: dict) -> bool:
    """Update fields of a saved custom elder."""
    filepath = _get_custom_dir() / f"{elder_id}.json"
    if not filepath.exists():
        return False

    data = json.loads(filepath.read_text(encoding="utf-8"))
    data.update(updates)
    filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Re-register with updated data
    elder = CustomElder.from_dict(data)
    ElderRegistry.register(elder)
    return True


def get_custom_elder_data(elder_id: str) -> dict | None:
    """Read the raw JSON data for a custom elder."""
    filepath = _get_custom_dir() / f"{elder_id}.json"
    if not filepath.exists():
        return None
    return json.loads(filepath.read_text(encoding="utf-8"))
