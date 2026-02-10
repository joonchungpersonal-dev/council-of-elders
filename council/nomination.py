"""Elder nomination system for dynamically introducing guest experts.

Three responsibilities:
1. NOMINATION_INSTRUCTION -- appended to elder system prompts during roundtable/debate
2. Parsing -- regex extraction of [NOMINATE: Name | Expertise] tags
3. Dynamic elder factory -- creates NominatedElder instances via LLM-generated persona
"""

import re

from council.elders.base import NominatedElder
from council.llm import chat


# Appended to elder system prompts when nominations are enabled
NOMINATION_INSTRUCTION = """

If this discussion would genuinely benefit from a specific person's expertise -- \
someone NOT currently in this council -- you may nominate them by placing this tag \
at the very end of your response:
[NOMINATE: Full Name | their specific expertise relevant to this topic]
Only nominate when there is a clear gap. Most responses should NOT include a nomination."""

_NOMINATION_RE = re.compile(r"\[NOMINATE:\s*(.+?)\s*\|\s*(.+?)\s*\]")


def parse_nomination(text: str) -> tuple[str, str] | None:
    """Extract a nomination tag from an elder's response.

    Returns (name, expertise) or None if no nomination found.
    """
    match = _NOMINATION_RE.search(text)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None


def strip_nomination_tag(text: str) -> str:
    """Remove the nomination tag from text for clean display."""
    return _NOMINATION_RE.sub("", text).rstrip()


def _make_slug(name: str) -> str:
    """Convert a name to a URL-safe slug."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def find_existing_elder(name: str):
    """Check if a nominated person is already a registered elder.

    Returns the Elder if found, None otherwise.
    """
    from council.elders import ElderRegistry

    name_lower = name.lower().strip()
    for elder in ElderRegistry.get_all():
        # Exact match
        if elder.name.lower() == name_lower:
            return elder
        # Substring match (e.g. "Kahneman" matches "Daniel Kahneman")
        if name_lower in elder.name.lower() or elder.name.lower() in name_lower:
            return elder
        # Last name match
        if name_lower.split()[-1] == elder.name.lower().split()[-1]:
            return elder
    return None


def create_nominated_elder(
    name: str,
    expertise: str,
    topic: str,
    nominated_by: str,
) -> NominatedElder:
    """Create a NominatedElder with an LLM-generated persona prompt.

    Args:
        name: Full name of the person to embody (e.g. "Benjamin Graham")
        expertise: Their relevant expertise (e.g. "value investing")
        topic: The current discussion topic
        nominated_by: Name of the elder who made the nomination
    """
    persona_request = (
        f"Write a concise system prompt (200-400 words) for an AI to embody {name} "
        f"in a council discussion about: \"{topic}\"\n\n"
        f"They were nominated for their expertise in: {expertise}\n\n"
        f"The prompt should capture their:\n"
        f"- Communication style and personality\n"
        f"- Core philosophy and mental models\n"
        f"- How they would approach this specific topic\n"
        f"- Characteristic phrases or mannerisms\n\n"
        f"Start the prompt with 'You are embodying {name}' and write it in second person. "
        f"Include a note that they are a guest expert invited by {nominated_by} to contribute "
        f"their unique perspective. They should be direct and substantive, building on "
        f"what the other council members have already discussed."
    )

    messages = [{"role": "user", "content": persona_request}]
    prompt_text = "".join(chat(messages, stream=True))

    slug = _make_slug(name)

    return NominatedElder(
        id=f"nominated_{slug}",
        name=name,
        title=f"Guest Expert — {expertise}",
        era="",
        color="bright_magenta",
        _prompt=prompt_text,
        _nominated_by=nominated_by,
        _expertise=expertise,
    )
