"""Amazon memorabilia discovery and affiliate link generation.

Uses LLM to discover collectible items (sculptures, busts, prints, figurines,
coins, posters) related to council elders, with Amazon affiliate links.
"""

import logging
import re
import urllib.parse

from council.config import get_config_value
from council.llm import chat

logger = logging.getLogger(__name__)


def _make_memorabilia_url(search_term: str, tag: str) -> str:
    """Generate an Amazon search URL for memorabilia with affiliate tag."""
    params = {"k": search_term}
    if tag:
        params["tag"] = tag
    return "https://www.amazon.com/s?" + urllib.parse.urlencode(params)


def discover_memorabilia(name: str, expertise: str = "") -> list[dict]:
    """Use LLM to discover Amazon-purchasable collectibles for a person.

    Returns a list of dicts with title, description, category, and affiliate_url.
    """
    tag = get_config_value("amazon_affiliate_tag", "")

    prompt = (
        f"List collectible memorabilia items related to {name} that can be purchased "
        f"on Amazon. Focus on: sculptures, busts, figurines, art prints, posters, "
        f"commemorative coins, historical replicas, or decorative items.\n\n"
        f"Their expertise: {expertise}\n\n"
        f"Format each item as exactly one line:\n"
        f"CATEGORY: Search Term | Brief Description\n\n"
        f"Where CATEGORY is one of: sculpture, bust, print, poster, figurine, coin, replica, decor\n\n"
        f"List up to 6 items. Only include items that would realistically be found on Amazon. "
        f"Be specific with search terms so they find actual products."
    )
    messages = [{"role": "user", "content": prompt}]
    response = "".join(chat(messages, stream=True))

    items = []
    valid_categories = {
        "sculpture", "bust", "print", "poster",
        "figurine", "coin", "replica", "decor",
    }

    for line in response.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        # Parse CATEGORY: Search Term | Description
        colon_idx = line.find(":")
        if colon_idx < 0:
            continue

        category = line[:colon_idx].strip().lower().strip("*").strip("-").strip()
        rest = line[colon_idx + 1:].strip()

        if category not in valid_categories:
            continue

        parts = rest.split("|")
        if len(parts) < 2:
            # Fallback: try " - " as separator
            parts = rest.split(" - ", 1)
        if len(parts) < 2:
            logger.debug("Could not parse memorabilia line: %s", line)
            continue

        search_term = parts[0].strip().strip('"').strip("*")
        description = parts[1].strip().strip('"').strip("*")

        if not search_term:
            continue

        items.append({
            "title": search_term,
            "description": description,
            "category": category,
            "affiliate_url": _make_memorabilia_url(search_term, tag),
        })

    return items


def get_memorabilia_for_elder(
    elder_id: str, name: str, expertise: str = ""
) -> list[dict]:
    """Get memorabilia for any elder (built-in or custom).

    Checks custom elder cache first, falls back to LLM discovery.
    """
    # Check if this is a custom elder with saved memorabilia
    try:
        from council.elders.custom import get_custom_elder_data

        data = get_custom_elder_data(elder_id)
        if data and data.get("memorabilia"):
            return data["memorabilia"]
    except Exception:
        pass

    return discover_memorabilia(name, expertise)
