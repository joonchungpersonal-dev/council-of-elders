"""Documentary and video content discovery with Amazon Prime Video affiliate links.

Uses LLM to discover real documentaries, lectures, and interviews
about council elders, with Amazon Prime Video affiliate links.
"""

import logging
import urllib.parse

from council.config import get_config_value
from council.llm import chat

logger = logging.getLogger(__name__)


def _make_prime_video_url(title: str, tag: str) -> str:
    """Generate an Amazon Prime Video search URL with affiliate tag."""
    params = {"k": title, "i": "instant-video"}
    if tag:
        params["tag"] = tag
    return "https://www.amazon.com/s?" + urllib.parse.urlencode(params)


def discover_documentaries(name: str, expertise: str = "") -> list[dict]:
    """Use LLM to discover real documentaries/lectures/interviews about a person.

    Returns a list of dicts with title, description, type, and amazon_url.
    """
    tag = get_config_value("amazon_affiliate_tag", "")

    prompt = (
        f"List real, published documentaries, lecture recordings, and notable interviews "
        f"featuring or about {name} that may be available on Amazon Prime Video or for "
        f"purchase on Amazon.\n\n"
        f"Their expertise: {expertise}\n\n"
        f"Format each item as exactly one line:\n"
        f"TYPE: Title | Brief Description\n\n"
        f"Where TYPE is one of: documentary, lecture, interview, series\n\n"
        f"List up to 5 items. Only include REAL, actually produced content. "
        f"Do not invent fictional titles."
    )
    messages = [{"role": "user", "content": prompt}]
    response = "".join(chat(messages, stream=True))

    items = []
    valid_types = {"documentary", "lecture", "interview", "series"}

    for line in response.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        colon_idx = line.find(":")
        if colon_idx < 0:
            continue

        content_type = line[:colon_idx].strip().lower().strip("*").strip("-").strip()
        rest = line[colon_idx + 1:].strip()

        if content_type not in valid_types:
            continue

        parts = rest.split("|")
        if len(parts) < 2:
            # Fallback: try " - " as separator
            parts = rest.split(" - ", 1)
        if len(parts) < 2:
            logger.debug("Could not parse documentary line: %s", line)
            continue

        title = parts[0].strip().strip('"').strip("*")
        description = parts[1].strip().strip('"').strip("*")

        if not title:
            continue

        items.append({
            "title": title,
            "description": description,
            "type": content_type,
            "amazon_url": _make_prime_video_url(title, tag),
        })

    return items
