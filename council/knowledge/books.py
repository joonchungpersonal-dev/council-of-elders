"""Amazon book discovery and affiliate link generation.

MVP uses search-link generation (no API key needed).
Future upgrade path: swap _make_affiliate_url for PA-API 5.0 calls.
"""

import logging
import re
import urllib.parse

from council.config import get_config_value
from council.llm import chat

logger = logging.getLogger(__name__)


def _make_affiliate_url(title: str, author: str, tag: str) -> str:
    """Generate an Amazon search URL with affiliate tag."""
    query = f"{title} {author}".strip()
    params = {"k": query}
    if tag:
        params["tag"] = tag
    return "https://www.amazon.com/s?" + urllib.parse.urlencode(params)


def _make_kindle_url(title: str, author: str, tag: str) -> str:
    """Generate a Kindle-specific Amazon search URL."""
    query = f"{title} {author} Kindle".strip()
    params = {"k": query, "i": "digital-text"}
    if tag:
        params["tag"] = tag
    return "https://www.amazon.com/s?" + urllib.parse.urlencode(params)


def discover_books(name: str, expertise: str = "") -> list[dict]:
    """Use LLM to discover books BY and ABOUT a person.

    Returns a list of dicts with title, author, type ('by'/'about'),
    and affiliate URLs.
    """
    tag = get_config_value("amazon_affiliate_tag", "")

    prompt = (
        f"List the most important books written BY {name} and notable books "
        f"written ABOUT {name} (biographies, analyses, etc.).\n\n"
        f"Their expertise: {expertise}\n\n"
        f"Format each book as exactly one line:\n"
        f"BY: Title | Author\n"
        f"ABOUT: Title | Author\n\n"
        f"List up to 5 books BY and up to 3 books ABOUT. "
        f"Only include real, published books. If {name} has no published books, "
        f"skip the BY section."
    )
    messages = [{"role": "user", "content": prompt}]
    response = "".join(chat(messages, stream=True))

    books = []
    for line in response.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        book_type = None
        if line.upper().startswith("BY:"):
            book_type = "by"
            line = line[3:].strip()
        elif line.upper().startswith("ABOUT:"):
            book_type = "about"
            line = line[6:].strip()
        else:
            # Fallback: try regex for numbered or bullet lines like "1. Title by Author"
            m = re.match(r'^[\d\-\*\.]+\s*(BY|ABOUT)[:\s]+(.+)', line, re.IGNORECASE)
            if m:
                book_type = m.group(1).lower()
                line = m.group(2).strip()
            else:
                continue

        parts = line.split("|")
        if len(parts) < 2:
            # Try " by " as separator
            parts = line.split(" by ", 1)
        if len(parts) < 2:
            # Fallback: try " - " as separator
            parts = line.split(" - ", 1)
        if len(parts) < 2:
            logger.debug("Could not parse book line: %s", line)
            continue

        title = parts[0].strip().strip('"').strip("*")
        author = parts[1].strip().strip('"').strip("*")

        if not title or not author:
            continue

        books.append({
            "title": title,
            "author": author,
            "type": book_type,
            "affiliate_url": _make_affiliate_url(title, author, tag),
            "kindle_url": _make_kindle_url(title, author, tag),
        })

    return books


def get_books_for_elder(elder_id: str, name: str, expertise: str = "") -> list[dict]:
    """Get book recommendations for any elder (built-in or custom).

    Checks custom elder data first, falls back to LLM discovery.
    """
    # Check if this is a custom elder with saved books
    try:
        from council.elders.custom import get_custom_elder_data

        data = get_custom_elder_data(elder_id)
        if data and data.get("books"):
            return data["books"]
    except Exception:
        pass

    # Check if the built-in elder has key_works we can use as seeds
    from council.elders.base import ElderRegistry

    elder = ElderRegistry.get(elder_id)
    tag = get_config_value("amazon_affiliate_tag", "")

    if elder and hasattr(elder, "key_works") and elder.key_works:
        books = []
        for work in elder.key_works:
            books.append({
                "title": work,
                "author": name or elder.name,
                "type": "by",
                "affiliate_url": _make_affiliate_url(work, elder.name, tag),
                "kindle_url": _make_kindle_url(work, elder.name, tag),
            })
        return books

    # Fall back to LLM discovery
    return discover_books(name or (elder.name if elder else ""), expertise)
