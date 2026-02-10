"""Biography fetcher -- Wikipedia REST API with LLM fallback."""

import urllib.parse
import urllib.request
import json

from council.llm import chat


def fetch_wikipedia_summary(name: str) -> dict | None:
    """Fetch a summary from the Wikipedia REST API.

    Fast (~500ms), free, no API key needed.
    Returns dict with 'summary', 'url', 'thumbnail' or None.
    """
    title = urllib.parse.quote(name.replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CouncilOfElders/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        if data.get("type") == "disambiguation":
            return None

        extract = data.get("extract", "")
        if not extract or len(extract) < 50:
            return None

        result = {
            "summary": extract,
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "source": "wikipedia",
        }

        thumbnail = data.get("thumbnail", {}).get("source")
        if thumbnail:
            result["thumbnail"] = thumbnail

        return result

    except Exception:
        return None


def generate_llm_biography(name: str, expertise: str) -> str:
    """Generate a short biography using the LLM as fallback."""
    prompt = (
        f"Write a concise 2-3 sentence biography of {name}, "
        f"focusing on their expertise in {expertise}. "
        f"Include their most notable contributions and era. "
        f"Be factual and direct. Do not use any introductory phrases."
    )
    messages = [{"role": "user", "content": prompt}]
    return "".join(chat(messages, stream=True))


def get_biography(name: str, expertise: str = "") -> dict:
    """Get a biography for a person -- Wikipedia first, then LLM fallback."""
    wiki = fetch_wikipedia_summary(name)
    if wiki:
        return wiki

    summary = generate_llm_biography(name, expertise)
    return {
        "summary": summary,
        "source": "llm",
    }
