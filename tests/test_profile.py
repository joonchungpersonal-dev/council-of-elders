"""Tests for the adaptive user profile module."""

import json
import pytest
from unittest.mock import patch
from pathlib import Path

from council.profile import (
    classify_question,
    load_profile,
    save_profile,
    record_session,
    get_profile_context,
    _default_profile,
)


@pytest.fixture
def tmp_profile(tmp_path, monkeypatch):
    """Redirect profile storage to a temp directory."""
    profile_path = tmp_path / "profile.json"
    monkeypatch.setattr("council.profile.get_profile_path", lambda: profile_path)
    return profile_path


# ── classify_question ──


class TestClassifyQuestion:
    def test_career_keywords(self):
        assert classify_question("Should I quit my job?") == "career"
        assert classify_question("How do I negotiate a promotion?") == "career"

    def test_investing_keywords(self):
        assert classify_question("How should I invest my portfolio?") == "investing"
        assert classify_question("Is the stock market overvalued?") == "investing"

    def test_relationships(self):
        assert classify_question("My partner and I have a conflict") == "relationships"

    def test_philosophy(self):
        assert classify_question("What is the meaning of existence?") == "philosophy"
        assert classify_question("How should I think about virtue and ethics?") == "philosophy"

    def test_emotional(self):
        assert classify_question("I feel anxious and overwhelmed") == "emotional"
        assert classify_question("I'm stressed and lonely") == "emotional"

    def test_creative(self):
        assert classify_question("Help me brainstorm a creative design") == "creative"

    def test_strategy(self):
        assert classify_question("How do I negotiate and gain advantage?") == "strategy"

    def test_health(self):
        assert classify_question("How do I build a meditation habit?") == "health"

    def test_general_fallback(self):
        assert classify_question("What color is the sky?") == "general"
        assert classify_question("Hello") == "general"

    def test_case_insensitive(self):
        assert classify_question("SHOULD I QUIT MY JOB?") == "career"

    def test_multiple_categories_picks_highest(self):
        # "invest money" hits investing twice, career "work" once
        result = classify_question("Should I invest money from work?")
        assert result in ("investing", "career")


# ── load_profile / save_profile ──


class TestProfileIO:
    def test_load_creates_default(self, tmp_profile):
        assert not tmp_profile.exists()
        profile = load_profile()
        assert profile["version"] == 1
        assert profile["session_count"] == 0
        assert profile["topic_counts"] == {}

    def test_save_and_reload(self, tmp_profile):
        profile = load_profile()
        profile["session_count"] = 5
        profile["topic_counts"]["career"] = 3
        save_profile(profile)

        assert tmp_profile.exists()
        reloaded = load_profile()
        assert reloaded["session_count"] == 5
        assert reloaded["topic_counts"]["career"] == 3

    def test_load_handles_corrupt_json(self, tmp_profile):
        tmp_profile.write_text("not valid json{{{")
        profile = load_profile()
        assert profile["version"] == 1
        assert profile["session_count"] == 0

    def test_load_backfills_missing_keys(self, tmp_profile):
        # Write a profile missing some keys
        partial = {"version": 1, "session_count": 10}
        tmp_profile.write_text(json.dumps(partial))
        profile = load_profile()
        assert profile["session_count"] == 10
        assert profile["topic_counts"] == {}
        assert profile["elder_stats"] == {}
        assert "dialectic_tension_values" in profile["settings_tendency"]

    def test_save_updates_timestamp(self, tmp_profile):
        profile = load_profile()
        old_updated = profile.get("updated", "")
        save_profile(profile)
        reloaded = load_profile()
        # Updated timestamp should be set
        assert reloaded["updated"]


# ── record_session ──


class TestRecordSession:
    def test_increments_session_count(self, tmp_profile):
        record_session({
            "question": "test",
            "category": "career",
            "mode": "panel",
            "elder_ids": ["munger"],
            "was_auto_selected": True,
        })
        profile = load_profile()
        assert profile["session_count"] == 1

    def test_increments_topic_counts(self, tmp_profile):
        record_session({"question": "q", "category": "career", "elder_ids": []})
        record_session({"question": "q", "category": "career", "elder_ids": []})
        record_session({"question": "q", "category": "philosophy", "elder_ids": []})
        profile = load_profile()
        assert profile["topic_counts"]["career"] == 2
        assert profile["topic_counts"]["philosophy"] == 1

    def test_tracks_elder_stats(self, tmp_profile):
        record_session({
            "question": "q",
            "category": "general",
            "mode": "panel",
            "elder_ids": ["munger", "aurelius"],
            "was_auto_selected": True,
            "follow_up_count": 2,
            "podcast_generated": True,
            "journal_saved": False,
        })
        profile = load_profile()
        assert profile["elder_stats"]["munger"]["sessions"] == 1
        assert profile["elder_stats"]["munger"]["follow_ups"] == 2
        assert profile["elder_stats"]["munger"]["podcasts"] == 1
        assert profile["elder_stats"]["munger"]["journals"] == 0
        assert profile["elder_stats"]["munger"]["manual_picks"] == 0

    def test_tracks_manual_picks(self, tmp_profile):
        record_session({
            "question": "q",
            "elder_ids": ["franklin"],
            "was_auto_selected": False,
        })
        profile = load_profile()
        assert profile["elder_stats"]["franklin"]["manual_picks"] == 1

    def test_tracks_mode_stats(self, tmp_profile):
        record_session({"question": "q", "mode": "salon", "elder_ids": [], "follow_up_count": 1, "podcast_generated": True})
        record_session({"question": "q", "mode": "salon", "elder_ids": [], "follow_up_count": 0, "podcast_generated": False})
        profile = load_profile()
        assert profile["mode_stats"]["salon"]["sessions"] == 2
        assert profile["mode_stats"]["salon"]["follow_ups"] == 1
        assert profile["mode_stats"]["salon"]["podcasts"] == 1

    def test_tracks_settings_tendency(self, tmp_profile):
        record_session({
            "question": "q",
            "elder_ids": [],
            "settings": {
                "dialectic_tension": 60,
                "response_length": "detailed",
                "discussion_length": "quick",
            },
        })
        profile = load_profile()
        assert profile["settings_tendency"]["dialectic_tension_values"] == [60]
        assert profile["settings_tendency"]["response_length_counts"]["detailed"] == 1
        assert profile["settings_tendency"]["discussion_length_counts"]["quick"] == 1

    def test_tracks_override_count(self, tmp_profile):
        record_session({"question": "q", "elder_ids": [], "override_count": 2})
        profile = load_profile()
        assert profile["override_count"] == 2

    def test_recent_topics_capped(self, tmp_profile):
        for i in range(25):
            record_session({"question": f"q{i}", "category": "general", "elder_ids": []})
        profile = load_profile()
        assert len(profile["recent_topics"]) == 20
        # Most recent should be last
        assert profile["recent_topics"][-1]["question"] == "q24"


# ── get_profile_context ──


class TestGetProfileContext:
    def test_empty_for_cold_start(self, tmp_profile):
        assert get_profile_context() == ""

    def test_empty_for_less_than_3_sessions(self, tmp_profile):
        record_session({"question": "q", "elder_ids": []})
        record_session({"question": "q", "elder_ids": []})
        assert get_profile_context() == ""

    def test_returns_context_after_3_sessions(self, tmp_profile):
        for _ in range(3):
            record_session({
                "question": "career question",
                "category": "career",
                "mode": "panel",
                "elder_ids": ["munger"],
                "was_auto_selected": True,
                "follow_up_count": 1,
                "settings": {"dialectic_tension": 50, "response_length": "moderate"},
            })
        context = get_profile_context()
        assert "3 sessions" in context
        assert "career" in context
        assert "munger" in context
        assert "panel" in context

    def test_context_shows_override_tendency(self, tmp_profile):
        for _ in range(5):
            record_session({
                "question": "q",
                "category": "general",
                "mode": "panel",
                "elder_ids": ["munger"],
                "was_auto_selected": True,
                "settings": {},
            })
        context = get_profile_context()
        assert "Rarely overrides" in context

    def test_context_shows_frequent_overrides(self, tmp_profile):
        for _ in range(5):
            record_session({
                "question": "q",
                "category": "general",
                "mode": "panel",
                "elder_ids": ["munger"],
                "override_count": 1,
                "settings": {},
            })
        context = get_profile_context()
        assert "Frequently overrides" in context

    def test_context_includes_tension_average(self, tmp_profile):
        for _ in range(3):
            record_session({
                "question": "q",
                "mode": "panel",
                "elder_ids": ["munger"],
                "settings": {"dialectic_tension": 60},
            })
        context = get_profile_context()
        assert "~60 dialectic tension" in context
