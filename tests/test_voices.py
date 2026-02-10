"""Tests for TTS voice ID resolution."""

from council.tts.voices import (
    get_elevenlabs_voice_id,
    DEFAULT_VOICE_ID,
    ELEVENLABS_VOICE_MAP,
    ELEVENLABS_RAP_VOICE_MAP,
    ELEVENLABS_POETRY_VOICE_MAP,
    RAP_HOST_VOICE_ID,
    POETRY_MC_VOICE_ID,
    NARRATOR_VOICE_ID,
)


def test_known_elder_returns_mapped_voice():
    voice_id = get_elevenlabs_voice_id("aurelius")
    assert voice_id == ELEVENLABS_VOICE_MAP["aurelius"]


def test_unknown_elder_returns_default():
    voice_id = get_elevenlabs_voice_id("nonexistent_elder_xyz")
    assert voice_id == DEFAULT_VOICE_ID


def test_rap_mode_returns_rap_voice():
    voice_id = get_elevenlabs_voice_id("aurelius", mode="rap")
    assert voice_id == ELEVENLABS_RAP_VOICE_MAP["aurelius"]


def test_rap_mode_moderator_returns_host():
    voice_id = get_elevenlabs_voice_id("__moderator__", mode="rap")
    assert voice_id == RAP_HOST_VOICE_ID


def test_poetry_mode_returns_poetry_voice():
    voice_id = get_elevenlabs_voice_id("aurelius", mode="poetry")
    assert voice_id == ELEVENLABS_POETRY_VOICE_MAP["aurelius"]


def test_poetry_mode_moderator_returns_mc():
    voice_id = get_elevenlabs_voice_id("__moderator__", mode="poetry")
    assert voice_id == POETRY_MC_VOICE_ID


def test_rap_mode_unknown_elder_falls_back_to_standard():
    # An elder in standard map but not rap map should fall back to standard
    elder_id = "franklin"  # in standard map, not in rap map
    voice_id = get_elevenlabs_voice_id(elder_id, mode="rap")
    assert voice_id == ELEVENLABS_VOICE_MAP[elder_id]


def test_poetry_mode_unknown_elder_falls_back_to_standard():
    elder_id = "franklin"  # in standard map, not in poetry map
    voice_id = get_elevenlabs_voice_id(elder_id, mode="poetry")
    assert voice_id == ELEVENLABS_VOICE_MAP[elder_id]


def test_standard_mode_explicit_empty_string():
    voice_id = get_elevenlabs_voice_id("aurelius", mode="")
    assert voice_id == ELEVENLABS_VOICE_MAP["aurelius"]


def test_all_voice_ids_are_non_empty_strings():
    for elder_id, voice_id in ELEVENLABS_VOICE_MAP.items():
        assert isinstance(voice_id, str) and len(voice_id) > 0, f"Bad voice ID for {elder_id}"
    for elder_id, voice_id in ELEVENLABS_RAP_VOICE_MAP.items():
        assert isinstance(voice_id, str) and len(voice_id) > 0, f"Bad rap voice ID for {elder_id}"
    for elder_id, voice_id in ELEVENLABS_POETRY_VOICE_MAP.items():
        assert isinstance(voice_id, str) and len(voice_id) > 0, f"Bad poetry voice ID for {elder_id}"
