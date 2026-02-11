"""Amazon book discovery and affiliate link generation.

MVP uses search-link generation (no API key needed).
Future upgrade path: swap _make_affiliate_url for PA-API 5.0 calls.
"""

import json as _json
import logging
import re
import urllib.parse
import urllib.request

from council.config import get_config_value
from council.llm import chat

logger = logging.getLogger(__name__)


def verify_book_exists(title: str, author: str) -> dict:
    """Verify a book exists via the Open Library Search API.

    Returns {"verified": bool, "open_library_key": str|None, "first_publish_year": int|None}.
    Gracefully returns verified=False on any network or parse error.
    """
    try:
        params = urllib.parse.urlencode({
            "title": title,
            "author": author,
            "limit": "3",
        })
        url = f"https://openlibrary.org/search.json?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "CouncilOfElders/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = _json.loads(resp.read().decode())

        title_lower = title.lower()
        author_lower = author.lower()

        for doc in data.get("docs", []):
            doc_title = (doc.get("title") or "").lower()
            doc_authors = [a.lower() for a in (doc.get("author_name") or [])]

            # Fuzzy title match: check containment in either direction
            title_match = (
                title_lower in doc_title
                or doc_title in title_lower
                or _word_overlap(title_lower, doc_title) >= 0.6
            )
            # Author match: any listed author's last name matches
            author_match = any(
                author_lower.split()[-1] in a or a.split()[-1] in author_lower
                for a in doc_authors
            ) if doc_authors else False

            if title_match and author_match:
                return {
                    "verified": True,
                    "open_library_key": doc.get("key"),
                    "first_publish_year": doc.get("first_publish_year"),
                }

        return {"verified": False, "open_library_key": None, "first_publish_year": None}
    except Exception:
        logger.debug("Open Library verification failed for '%s' by '%s'", title, author)
        return {"verified": False, "open_library_key": None, "first_publish_year": None}


def _word_overlap(a: str, b: str) -> float:
    """Return the fraction of words in common between two strings."""
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    return len(intersection) / min(len(words_a), len(words_b))


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

    # Verify each book against Open Library
    for book in books:
        verification = verify_book_exists(book["title"], book["author"])
        book["verified"] = verification["verified"]
        book["open_library_key"] = verification["open_library_key"]
        book["first_publish_year"] = verification["first_publish_year"]

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
