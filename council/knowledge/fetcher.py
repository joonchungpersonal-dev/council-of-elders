"""
Automated knowledge fetcher for public domain texts.

Fetches texts from Project Gutenberg and other free sources,
cleans them, and adds them to the elder knowledge bases.
"""

import re
import urllib.request
from pathlib import Path

from council.config import get_knowledge_dir
from council.knowledge.sources import PUBLIC_SOURCES, EMBEDDED_WISDOM


def clean_gutenberg_text(text: str) -> str:
    """Clean Project Gutenberg text by removing headers/footers."""
    # Find start of actual content
    start_markers = [
        "*** START OF THIS PROJECT GUTENBERG",
        "*** START OF THE PROJECT GUTENBERG",
        "*END*THE SMALL PRINT",
    ]
    end_markers = [
        "*** END OF THIS PROJECT GUTENBERG",
        "*** END OF THE PROJECT GUTENBERG",
        "End of the Project Gutenberg",
        "End of Project Gutenberg",
    ]

    start_idx = 0
    for marker in start_markers:
        idx = text.find(marker)
        if idx != -1:
            # Find the end of that line
            newline_idx = text.find("\n", idx)
            if newline_idx != -1:
                start_idx = newline_idx + 1
            break

    end_idx = len(text)
    for marker in end_markers:
        idx = text.find(marker)
        if idx != -1:
            end_idx = idx
            break

    text = text[start_idx:end_idx].strip()

    # Remove excessive blank lines
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    return text


def fetch_text(url: str, source_type: str = "gutenberg") -> str | None:
    """Fetch text from a URL."""
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'CouncilOfElders/1.0 (Educational Purpose)'}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            text = response.read().decode('utf-8', errors='ignore')

        if source_type == "gutenberg":
            text = clean_gutenberg_text(text)

        return text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def save_knowledge_file(elder_id: str, title: str, content: str) -> Path:
    """Save knowledge to a file."""
    knowledge_dir = get_knowledge_dir() / elder_id
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    # Create safe filename
    safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
    filepath = knowledge_dir / f"{safe_title}.txt"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n")
        f.write(content)

    return filepath


def fetch_all_public_sources(elder_id: str | None = None, verbose: bool = True) -> dict[str, list[Path]]:
    """
    Fetch all public domain sources for elders.

    Args:
        elder_id: Specific elder to fetch for, or None for all
        verbose: Print progress

    Returns:
        Dict mapping elder_id to list of saved file paths
    """
    results = {}

    sources_to_fetch = PUBLIC_SOURCES
    if elder_id:
        sources_to_fetch = {elder_id: PUBLIC_SOURCES.get(elder_id, [])}

    for eid, sources in sources_to_fetch.items():
        results[eid] = []

        for source in sources:
            if source["type"] == "berkshire_index":
                # Skip index pages - these need special handling
                if verbose:
                    print(f"  [skip] {source['title']} - requires manual download")
                continue

            if verbose:
                print(f"  Fetching: {source['title']}...")

            content = fetch_text(source["url"], source["type"])
            if content:
                filepath = save_knowledge_file(eid, source["title"], content)
                results[eid].append(filepath)
                if verbose:
                    print(f"    ✓ Saved to {filepath}")
            else:
                if verbose:
                    print(f"    ✗ Failed to fetch")

    return results


def save_embedded_wisdom(elder_id: str | None = None, verbose: bool = True) -> dict[str, Path]:
    """
    Save embedded wisdom (key quotes) to files.

    Args:
        elder_id: Specific elder, or None for all
        verbose: Print progress

    Returns:
        Dict mapping elder_id to saved file path
    """
    results = {}

    wisdom_to_save = EMBEDDED_WISDOM
    if elder_id:
        wisdom_to_save = {elder_id: EMBEDDED_WISDOM.get(elder_id, "")}

    for eid, wisdom in wisdom_to_save.items():
        if not wisdom:
            continue

        if verbose:
            print(f"  Saving key wisdom for {eid}...")

        filepath = save_knowledge_file(eid, "Key_Wisdom_and_Quotes", wisdom)
        results[eid] = filepath

        if verbose:
            print(f"    ✓ Saved to {filepath}")

    return results


def setup_all_knowledge(verbose: bool = True) -> dict:
    """
    Run complete knowledge setup for all elders.

    This is the main entry point for automated setup.

    Returns:
        Summary of what was set up
    """
    if verbose:
        print("\n" + "=" * 60)
        print("COUNCIL OF ELDERS - AUTOMATED KNOWLEDGE SETUP")
        print("=" * 60 + "\n")

    results = {
        "embedded_wisdom": {},
        "public_sources": {},
        "errors": [],
    }

    # Step 1: Save embedded wisdom (always available, no network needed)
    if verbose:
        print("Step 1: Saving embedded wisdom (key quotes)...\n")

    try:
        results["embedded_wisdom"] = save_embedded_wisdom(verbose=verbose)
    except Exception as e:
        results["errors"].append(f"Embedded wisdom: {e}")
        if verbose:
            print(f"  ✗ Error: {e}")

    # Step 2: Fetch public domain texts
    if verbose:
        print("\nStep 2: Fetching public domain texts...\n")

    try:
        results["public_sources"] = fetch_all_public_sources(verbose=verbose)
    except Exception as e:
        results["errors"].append(f"Public sources: {e}")
        if verbose:
            print(f"  ✗ Error: {e}")

    # Summary
    if verbose:
        print("\n" + "=" * 60)
        print("SETUP COMPLETE")
        print("=" * 60)

        total_files = sum(len(files) for files in results["public_sources"].values())
        total_wisdom = len(results["embedded_wisdom"])

        print(f"\n  Embedded wisdom files: {total_wisdom}")
        print(f"  Public domain texts:   {total_files}")

        if results["errors"]:
            print(f"  Errors: {len(results['errors'])}")
            for err in results["errors"]:
                print(f"    - {err}")

        print(f"\n  Knowledge stored in: ~/.council/knowledge/")
        print()

    return results
