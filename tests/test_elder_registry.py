"""Tests for elder registry."""

from council.elders.base import Elder, ElderRegistry, NominatedElder


def test_all_registered_elders_have_required_fields():
    """Every registered elder must have non-empty id, name, title, color.
    Era can be empty for custom/nominated elders."""
    elders = ElderRegistry.get_all()
    assert len(elders) > 0, "No elders registered"

    for elder in elders:
        assert elder.id, f"Elder missing id: {elder}"
        assert elder.name, f"Elder {elder.id} missing name"
        assert elder.title, f"Elder {elder.id} missing title"
        assert elder.color, f"Elder {elder.id} missing color"
        # Built-in elders must have era; custom elders may not
        if not elder.is_custom:
            assert elder.era, f"Built-in elder {elder.id} missing era"


def test_get_by_id():
    elder = ElderRegistry.get("aurelius")
    assert elder is not None
    assert elder.name == "Marcus Aurelius"


def test_get_nonexistent_returns_none():
    assert ElderRegistry.get("nonexistent_elder_xyz") is None


def test_exists():
    assert ElderRegistry.exists("aurelius")
    assert not ElderRegistry.exists("nonexistent_elder_xyz")


def test_get_ids_returns_strings():
    ids = ElderRegistry.get_ids()
    assert len(ids) > 0
    for eid in ids:
        assert isinstance(eid, str)


def test_nominated_elder_not_in_registry():
    """NominatedElder instances should NOT be auto-registered."""
    nom = NominatedElder(
        id="test_nominated",
        name="Test Person",
        title="Test Title",
        era="Modern",
        color="blue",
        _prompt="You are a test elder.",
    )
    assert not ElderRegistry.exists("test_nominated")
