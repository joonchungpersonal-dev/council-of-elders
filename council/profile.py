"""Adaptive user profile: implicit learning from session behavior."""

import json
from datetime import datetime, timezone
from pathlib import Path

from council.config import get_profile_path

# Keyword-based question classifier
CATEGORY_KEYWORDS = {
    "career": ["job", "career", "quit", "promotion", "salary", "boss", "startup", "hire", "work", "resume", "interview", "fired", "coworker"],
    "investing": ["invest", "portfolio", "stock", "market", "money", "wealth", "fund", "asset", "crypto", "retire", "compound", "dividend"],
    "relationships": ["relationship", "partner", "friend", "family", "love", "marriage", "conflict", "divorce", "dating", "parent", "sibling"],
    "philosophy": ["meaning", "purpose", "truth", "existence", "virtue", "ethics", "moral", "death", "consciousness", "free will", "stoic", "wisdom"],
    "emotional": ["anxious", "depressed", "stress", "fear", "overwhelm", "lonely", "empty", "angry", "grief", "burnout", "hopeless", "worried"],
    "creative": ["write", "create", "art", "music", "design", "brainstorm", "innovate", "imagine", "novel", "paint", "compose", "creative"],
    "strategy": ["compete", "negotiate", "plan", "decision", "risk", "advantage", "opponent", "strategy", "tactics", "leverage", "win", "game theory"],
    "health": ["health", "exercise", "diet", "sleep", "meditat", "habit", "routine", "discipline", "fitness", "weight", "energy", "wellness"],
}

MIN_SESSIONS_FOR_CONTEXT = 3
MAX_RECENT_TOPICS = 20


def _default_profile() -> dict:
    """Return a fresh default profile."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "version": 1,
        "created": now,
        "updated": now,
        "session_count": 0,
        "topic_counts": {},
        "elder_stats": {},
        "mode_stats": {},
        "settings_tendency": {
            "dialectic_tension_values": [],
            "response_length_counts": {},
            "discussion_length_counts": {},
        },
        "override_count": 0,
        "recent_topics": [],
    }


def load_profile() -> dict:
    """Load profile from disk, creating a default if missing."""
    path = get_profile_path()
    if path.exists():
        try:
            with open(path) as f:
                profile = json.load(f)
            # Ensure all expected keys exist (forward-compat)
            default = _default_profile()
            for key in default:
                if key not in profile:
                    profile[key] = default[key]
            if "settings_tendency" in profile:
                st_default = default["settings_tendency"]
                for key in st_default:
                    if key not in profile["settings_tendency"]:
                        profile["settings_tendency"][key] = st_default[key]
            return profile
        except (json.JSONDecodeError, KeyError):
            return _default_profile()
    return _default_profile()


def save_profile(profile: dict) -> None:
    """Write profile to disk."""
    path = get_profile_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    profile["updated"] = datetime.now(timezone.utc).isoformat()
    with open(path, "w") as f:
        json.dump(profile, f, indent=2)


def classify_question(text: str) -> str:
    """Rule-based keyword classifier. Returns the best-matching category."""
    text_lower = text.lower()
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score
    if not scores:
        return "general"
    return max(scores, key=scores.get)


def record_session(session_data: dict) -> None:
    """Update profile with signals from a completed session.

    Expected session_data keys:
        question, category, mode, elder_ids, was_auto_selected,
        was_mode_auto_selected, follow_up_count, podcast_generated,
        journal_saved, duration_sec, settings, override_count
    """
    profile = load_profile()
    profile["session_count"] += 1

    # Topic counts
    category = session_data.get("category", "general")
    profile["topic_counts"][category] = profile["topic_counts"].get(category, 0) + 1

    # Elder stats
    elder_ids = session_data.get("elder_ids", [])
    follow_ups = session_data.get("follow_up_count", 0)
    podcast = session_data.get("podcast_generated", False)
    journal = session_data.get("journal_saved", False)
    manual_pick = not session_data.get("was_auto_selected", True)

    for eid in elder_ids:
        if eid not in profile["elder_stats"]:
            profile["elder_stats"][eid] = {
                "sessions": 0, "follow_ups": 0,
                "podcasts": 0, "journals": 0, "manual_picks": 0,
            }
        stats = profile["elder_stats"][eid]
        stats["sessions"] += 1
        stats["follow_ups"] += follow_ups
        if podcast:
            stats["podcasts"] += 1
        if journal:
            stats["journals"] += 1
        if manual_pick:
            stats["manual_picks"] += 1

    # Mode stats
    mode = session_data.get("mode", "")
    if mode:
        if mode not in profile["mode_stats"]:
            profile["mode_stats"][mode] = {"sessions": 0, "follow_ups": 0, "podcasts": 0}
        ms = profile["mode_stats"][mode]
        ms["sessions"] += 1
        ms["follow_ups"] += follow_ups
        if podcast:
            ms["podcasts"] += 1

    # Settings tendency
    settings = session_data.get("settings", {})
    st = profile["settings_tendency"]
    if "dialectic_tension" in settings:
        st["dialectic_tension_values"].append(settings["dialectic_tension"])
        # Keep only last 50 values
        st["dialectic_tension_values"] = st["dialectic_tension_values"][-50:]
    if "response_length" in settings:
        rl = settings["response_length"]
        st["response_length_counts"][rl] = st["response_length_counts"].get(rl, 0) + 1
    if "discussion_length" in settings:
        dl = settings["discussion_length"]
        st["discussion_length_counts"][dl] = st["discussion_length_counts"].get(dl, 0) + 1

    # Override count
    profile["override_count"] += session_data.get("override_count", 0)

    # Recent topics
    question = session_data.get("question", "")
    if question:
        profile["recent_topics"].append({
            "question": question,
            "category": category,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        profile["recent_topics"] = profile["recent_topics"][-MAX_RECENT_TOPICS:]

    save_profile(profile)


def get_profile_context() -> str:
    """Generate a text summary of user preferences for LLM injection.

    Returns empty string if fewer than MIN_SESSIONS_FOR_CONTEXT sessions.
    """
    profile = load_profile()
    if profile["session_count"] < MIN_SESSIONS_FOR_CONTEXT:
        return ""

    lines = [f"User profile ({profile['session_count']} sessions):"]

    # Top topics
    tc = profile.get("topic_counts", {})
    if tc:
        top_topics = sorted(tc, key=tc.get, reverse=True)[:3]
        lines.append(f"- Most common topics: {', '.join(top_topics)}")

    # Top elders by engagement (sessions + follow_ups as weight)
    es = profile.get("elder_stats", {})
    if es:
        def _engagement(eid):
            s = es[eid]
            return s["sessions"] + s["follow_ups"] * 0.5
        top_elders = sorted(es, key=_engagement, reverse=True)[:3]
        parts = []
        for eid in top_elders:
            s = es[eid]
            parts.append(f"{eid} ({s['sessions']} sessions, {s['follow_ups']} follow-ups)")
        lines.append(f"- Most engaged elders: {', '.join(parts)}")

    # Preferred mode
    ms = profile.get("mode_stats", {})
    if ms:
        top_mode = max(ms, key=lambda m: ms[m]["sessions"])
        lines.append(f"- Preferred mode: {top_mode} ({ms[top_mode]['sessions']} sessions)")

    # Settings tendencies
    st = profile.get("settings_tendency", {})
    tension_vals = st.get("dialectic_tension_values", [])
    if tension_vals:
        avg_tension = round(sum(tension_vals) / len(tension_vals))
        lines.append(f"- Typical settings: ~{avg_tension} dialectic tension")

    rl_counts = st.get("response_length_counts", {})
    if rl_counts:
        top_rl = max(rl_counts, key=rl_counts.get)
        lines.append(f"- Preferred response length: {top_rl}")

    # Override tendency
    if profile["session_count"] >= 5:
        override_rate = profile.get("override_count", 0) / profile["session_count"]
        if override_rate < 0.2:
            lines.append("- Rarely overrides auto-selections")
        elif override_rate > 0.5:
            lines.append("- Frequently overrides auto-selections")

    return "\n".join(lines)
