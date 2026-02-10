"""Wisdom Journal — persistent per-topic document that accumulates insights."""

import json
import re
from datetime import datetime
from pathlib import Path

JOURNALS_DIR = Path(__file__).parent.parent / "data" / "journals"
INDEX_FILE = JOURNALS_DIR / "_index.json"


def _ensure_dir():
    """Ensure the journals directory exists."""
    JOURNALS_DIR.mkdir(parents=True, exist_ok=True)


def _slugify(title: str) -> str:
    """Convert a title to a URL-safe slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def _load_index() -> dict:
    """Load the journal index."""
    if INDEX_FILE.exists():
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    return {"journals": []}


def _save_index(index: dict):
    """Save the journal index."""
    _ensure_dir()
    INDEX_FILE.write_text(json.dumps(index, indent=2), encoding="utf-8")


def list_journals() -> list[dict]:
    """Return metadata for all journals."""
    index = _load_index()
    return index.get("journals", [])


def get_journal(slug: str) -> dict | None:
    """Get a journal's content and metadata by slug."""
    index = _load_index()
    meta = next((j for j in index.get("journals", []) if j["slug"] == slug), None)
    if not meta:
        return None

    journal_file = JOURNALS_DIR / f"{slug}.md"
    content = journal_file.read_text(encoding="utf-8") if journal_file.exists() else ""

    return {**meta, "content": content}


def create_journal(title: str) -> dict:
    """Create a new journal. Returns the journal metadata."""
    _ensure_dir()
    slug = _slugify(title)
    index = _load_index()

    # Check for duplicate slug
    existing = [j for j in index.get("journals", []) if j["slug"] == slug]
    if existing:
        return existing[0]

    now = datetime.now().strftime("%Y-%m-%d")
    meta = {
        "slug": slug,
        "title": title,
        "created": now,
        "updated": now,
    }

    # Create the markdown file
    journal_file = JOURNALS_DIR / f"{slug}.md"
    initial_content = f"# {title} — Wisdom Journal\n\n> Last updated: {now}\n\n## Core Values\n\n## Key Insights\n"
    journal_file.write_text(initial_content, encoding="utf-8")

    # Update index
    index.setdefault("journals", []).append(meta)
    _save_index(index)

    return meta


def append_to_journal(slug: str, entry: dict) -> bool:
    """Append insights from a discussion to a journal.

    entry should contain:
        - insights: list of {elder: str, text: str}
        - takeaway: str
        - topic: str (the question discussed)
        - core_values: list[str] (optional, to merge into Core Values section)
    """
    journal_file = JOURNALS_DIR / f"{slug}.md"
    if not journal_file.exists():
        return False

    content = journal_file.read_text(encoding="utf-8")
    now = datetime.now().strftime("%Y-%m-%d")
    date_display = datetime.now().strftime("%b %d, %Y")

    # Build the new entry
    entry_lines = [f"\n### {date_display} — \"{entry.get('topic', 'Discussion')}\"\n"]
    for insight in entry.get("insights", []):
        entry_lines.append(f"- **{insight.get('elder', 'Elder')}**: {insight.get('text', '')}")
    if entry.get("takeaway"):
        entry_lines.append(f"\n**Takeaway:** {entry['takeaway']}\n")

    new_entry = "\n".join(entry_lines)

    # Append to Key Insights section
    if "## Key Insights" in content:
        content = content.replace("## Key Insights\n", f"## Key Insights\n{new_entry}\n", 1)
    else:
        content += f"\n## Key Insights\n{new_entry}\n"

    # Merge core values if provided
    core_values = entry.get("core_values", [])
    if core_values and "## Core Values" in content:
        values_text = "\n".join(f"- {v}" for v in core_values)
        # Find existing core values and append new ones
        cv_match = re.search(r"(## Core Values\n)(.*?)(\n## )", content, re.DOTALL)
        if cv_match:
            existing = cv_match.group(2).strip()
            if existing:
                new_cv = f"{existing}\n{values_text}\n"
            else:
                new_cv = f"{values_text}\n"
            content = content[:cv_match.start(2)] + new_cv + content[cv_match.start(3):]
        else:
            # Core Values is the last section
            cv_pos = content.find("## Core Values\n")
            if cv_pos >= 0:
                rest_start = cv_pos + len("## Core Values\n")
                rest = content[rest_start:].strip()
                if rest:
                    content = content[:rest_start] + rest + "\n" + values_text + "\n"
                else:
                    content = content[:rest_start] + values_text + "\n"

    # Update the "Last updated" line
    content = re.sub(
        r"> Last updated: .*",
        f"> Last updated: {now}",
        content,
    )

    journal_file.write_text(content, encoding="utf-8")

    # Update index timestamp
    index = _load_index()
    for j in index.get("journals", []):
        if j["slug"] == slug:
            j["updated"] = now
            break
    _save_index(index)

    return True


def delete_journal(slug: str) -> bool:
    """Delete a journal and its index entry."""
    journal_file = JOURNALS_DIR / f"{slug}.md"
    if journal_file.exists():
        journal_file.unlink()

    index = _load_index()
    journals = index.get("journals", [])
    index["journals"] = [j for j in journals if j["slug"] != slug]
    _save_index(index)

    return True
