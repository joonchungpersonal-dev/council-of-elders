"""
Kindle Book Ingestion Pipeline

Processes ePub files extracted from Kindle books via Calibre + DeDRM plugin.
Maps books to elders and ingests them into the knowledge base.
"""

import re
import sys
from pathlib import Path
from typing import Optional

from council.knowledge.store import get_knowledge_store


# Book-to-Elder mapping based on ASIN and title keywords
BOOK_ELDER_MAP = {
    # Robert Greene
    "B0041KLCH0": ("greene", "The 48 Laws of Power"),
    "B000W94FE6": ("greene", "The Art of Seduction"),
    "B000W9149K": ("greene", "The 33 Strategies of War"),
    "B005MJFA2W": ("greene", "Mastery"),
    "B00555X8OA": ("greene", "The 50th Law"),
    "B01065DOJQ": ("greene", "The Laws of Human Nature"),

    # Jordan Peterson (12 Rules)
    "B07D23CFGR": ("peterson", "12 Rules for Life"),
    "B08GKNXM91": ("peterson", "Beyond Order"),

    # Naval Ravikant
    "B08FF8MTM6": ("naval", "The Almanack of Naval Ravikant"),

    # Rick Rubin
    "B09R99TQFP": ("rubin", "The Creative Act"),

    # Oprah
    "B00GSYOSIY": ("oprah", "What I Know For Sure"),

    # Carl Jung
    "B00E63J340": ("jung", "Man and His Symbols"),
    "B01KBLRZ50": ("jung", "The Red Book"),

    # Charlie Munger
    "B0BQMFDBJD": ("munger", "Poor Charlie's Almanack"),

    # Marcus Aurelius
    "B000FC1JAI": ("aurelius", "Meditations"),

    # Seneca
    "B00K6RU2DE": ("seneca", "Letters from a Stoic"),

    # Nassim Taleb
    "B002RI99E4": ("taleb", "The Black Swan"),
    "B0083DJWGO": ("taleb", "Antifragile"),
    "B00C5BQWHK": ("taleb", "Fooled by Randomness"),

    # Nathaniel Branden
    "B0031TZBG6": ("branden", "The Six Pillars of Self-Esteem"),

    # Thich Nhat Hanh
    "B00F52PBX6": ("thich", "The Miracle of Mindfulness"),
    "B00FUVKNTA": ("thich", "Peace Is Every Step"),
    "B00CCNLU5U": ("thich", "Being Peace"),

    # Jon Kabat-Zinn
    "B00C4BA3UK": ("kabatzinn", "Full Catastrophe Living"),
    "B000SEGMPM": ("kabatzinn", "Wherever You Go There You Are"),
    "B00K6ZUAMW": ("kabatzinn", "Mindfulness for Beginners"),

    # Daniel Kahneman
    "B00555X8OA": ("kahneman", "Thinking Fast and Slow"),
    "B093Y5CWVL": ("kahneman", "Noise"),

    # Philip Tetlock
    "B00RKO6MS8": ("tetlock", "Superforecasting"),
    "B000SEGJ8M": ("tetlock", "Expert Political Judgment"),

    # Gary Klein
    "B000TO0T26": ("klein", "Sources of Power"),
    "B00BWUH1NW": ("klein", "Seeing What Others Don't"),
    "B002SAPU9A": ("klein", "Streetlights and Shadows"),

    # Donella Meadows
    "B005VSRFEA": ("meadows", "Thinking in Systems"),

    # Lao Tzu
    "B003XT5Y8I": ("laotzu", "Tao Te Ching"),

    # Leonardo da Vinci
    "B073ZQWMQP": ("davinci", "Leonardo da Vinci Biography"),
}

# Title-based fallback mapping (for books without ASIN match)
TITLE_PATTERNS = {
    r"48 laws?\s*(of)?\s*power": ("greene", "The 48 Laws of Power"),
    r"art\s*(of)?\s*seduction": ("greene", "The Art of Seduction"),
    r"33 strategies?\s*(of)?\s*war": ("greene", "The 33 Strategies of War"),
    r"mastery": ("greene", "Mastery"),
    r"50th?\s*law": ("greene", "The 50th Law"),
    r"laws?\s*(of)?\s*human\s*nature": ("greene", "The Laws of Human Nature"),
    r"12\s*rules?\s*(for)?\s*life": ("peterson", "12 Rules for Life"),
    r"beyond\s*order": ("peterson", "Beyond Order"),
    r"almanack?\s*(of)?\s*naval": ("naval", "The Almanack of Naval Ravikant"),
    r"creative\s*act": ("rubin", "The Creative Act"),
    r"what\s*i\s*know\s*for\s*sure": ("oprah", "What I Know For Sure"),
    r"man\s*(and)?\s*(his)?\s*symbols": ("jung", "Man and His Symbols"),
    r"red\s*book": ("jung", "The Red Book"),
    r"poor\s*charlie": ("munger", "Poor Charlie's Almanack"),
    r"meditations?": ("aurelius", "Meditations"),
    r"letters?\s*(from)?\s*(a)?\s*stoic": ("seneca", "Letters from a Stoic"),
    r"black\s*swan": ("taleb", "The Black Swan"),
    r"antifragile": ("taleb", "Antifragile"),
    r"fooled\s*(by)?\s*randomness": ("taleb", "Fooled by Randomness"),
    r"six\s*pillars?\s*(of)?\s*self.?esteem": ("branden", "The Six Pillars of Self-Esteem"),
    r"miracle\s*(of)?\s*mindfulness": ("thich", "The Miracle of Mindfulness"),
    r"peace\s*(is)?\s*every\s*step": ("thich", "Peace Is Every Step"),
    r"being\s*peace": ("thich", "Being Peace"),

    # Jon Kabat-Zinn
    r"full\s*catastrophe\s*living": ("kabatzinn", "Full Catastrophe Living"),
    r"wherever\s*you\s*go": ("kabatzinn", "Wherever You Go There You Are"),
    r"mindfulness\s*(for)?\s*beginners": ("kabatzinn", "Mindfulness for Beginners"),

    # Daniel Kahneman
    r"thinking\s*fast\s*(and)?\s*slow": ("kahneman", "Thinking Fast and Slow"),
    r"noise.*kahneman": ("kahneman", "Noise"),

    # Philip Tetlock
    r"superforecasting": ("tetlock", "Superforecasting"),
    r"expert\s*political\s*judgment": ("tetlock", "Expert Political Judgment"),

    # Gary Klein
    r"sources\s*(of)?\s*power": ("klein", "Sources of Power"),
    r"seeing\s*what\s*others\s*don": ("klein", "Seeing What Others Don't"),
    r"streetlights\s*(and)?\s*shadows": ("klein", "Streetlights and Shadows"),

    # Donella Meadows
    r"thinking\s*in\s*systems": ("meadows", "Thinking in Systems"),

    # Lao Tzu
    r"tao\s*te\s*ching": ("laotzu", "Tao Te Ching"),
    r"dao\s*de\s*jing": ("laotzu", "Tao Te Ching"),
}


def extract_epub_text(epub_path: Path) -> str:
    """
    Extract text content from an ePub file.

    Args:
        epub_path: Path to the ePub file

    Returns:
        Extracted text content
    """
    try:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError(
            "ebooklib and beautifulsoup4 are required for ePub processing. "
            "Install with: pip install ebooklib beautifulsoup4"
        )

    book = epub.read_epub(str(epub_path))

    text_parts = []

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')

            # Remove scripts and styles
            for tag in soup(['script', 'style', 'nav']):
                tag.decompose()

            text = soup.get_text(separator='\n')

            # Clean up whitespace
            lines = [line.strip() for line in text.split('\n')]
            text = '\n'.join(line for line in lines if line)

            if text.strip():
                text_parts.append(text)

    return '\n\n'.join(text_parts)


def extract_text_file(txt_path: Path) -> str:
    """Read a plain text file."""
    return txt_path.read_text(encoding='utf-8', errors='replace')


def identify_book(file_path: Path, content: str = "") -> tuple[str, str] | None:
    """
    Identify which elder a book belongs to based on filename or content.

    Args:
        file_path: Path to the book file
        content: Optional content to help identify

    Returns:
        (elder_id, book_title) or None if not identified
    """
    filename = file_path.stem.lower()

    # Check filename against title patterns
    for pattern, (elder_id, title) in TITLE_PATTERNS.items():
        if re.search(pattern, filename, re.IGNORECASE):
            return (elder_id, title)

    # Check content header (first 1000 chars) against patterns
    if content:
        header = content[:1000].lower()
        for pattern, (elder_id, title) in TITLE_PATTERNS.items():
            if re.search(pattern, header, re.IGNORECASE):
                return (elder_id, title)

    return None


def ingest_book(
    file_path: Path,
    elder_id: Optional[str] = None,
    book_title: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """
    Ingest a single book into the knowledge base.

    Args:
        file_path: Path to the ePub or TXT file
        elder_id: Override elder assignment
        book_title: Override book title
        dry_run: If True, don't actually ingest, just report

    Returns:
        Dict with ingestion results
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    # Extract content
    suffix = file_path.suffix.lower()
    if suffix == '.epub':
        content = extract_epub_text(file_path)
    elif suffix in ['.txt', '.text']:
        content = extract_text_file(file_path)
    else:
        return {"success": False, "error": f"Unsupported format: {suffix}"}

    # Identify the book if not specified
    if not elder_id or not book_title:
        identified = identify_book(file_path, content)
        if identified:
            elder_id = elder_id or identified[0]
            book_title = book_title or identified[1]
        else:
            return {
                "success": False,
                "error": f"Could not identify book. Please specify --elder and --title",
                "filename": file_path.name,
            }

    word_count = len(content.split())

    result = {
        "success": True,
        "file": str(file_path),
        "elder_id": elder_id,
        "book_title": book_title,
        "word_count": word_count,
    }

    if dry_run:
        result["dry_run"] = True
        print(f"[DRY RUN] Would ingest: {book_title}")
        print(f"  Elder: {elder_id}")
        print(f"  Words: {word_count:,}")
        return result

    # Ingest into knowledge store
    store = get_knowledge_store()

    metadata = {
        "source": f"kindle:{book_title}",
        "title": book_title,
        "type": "book",
        "format": "kindle",
    }

    chunks_added = store.add_document(elder_id, content, metadata)
    result["chunks_added"] = chunks_added

    print(f"✓ Ingested: {book_title}")
    print(f"  Elder: {elder_id}")
    print(f"  Words: {word_count:,}")
    print(f"  Chunks: {chunks_added}")

    return result


def ingest_directory(
    directory: Path,
    dry_run: bool = False,
) -> list[dict]:
    """
    Ingest all ePub/TXT files from a directory.

    Args:
        directory: Directory containing book files
        dry_run: If True, don't actually ingest

    Returns:
        List of ingestion results
    """
    directory = Path(directory)

    if not directory.is_dir():
        print(f"Error: {directory} is not a directory")
        return []

    # Find all book files
    book_files = list(directory.glob("*.epub")) + list(directory.glob("*.txt"))

    if not book_files:
        print(f"No ePub or TXT files found in {directory}")
        return []

    print(f"Found {len(book_files)} book file(s)")
    print("-" * 50)

    results = []
    for book_file in sorted(book_files):
        result = ingest_book(book_file, dry_run=dry_run)
        results.append(result)
        print()

    # Summary
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    print("=" * 50)
    print(f"Summary: {len(successful)} ingested, {len(failed)} failed")

    if failed:
        print("\nFailed files:")
        for r in failed:
            print(f"  - {r.get('filename', r.get('file', 'unknown'))}: {r.get('error')}")

    if successful and not dry_run:
        total_words = sum(r.get("word_count", 0) for r in successful)
        total_chunks = sum(r.get("chunks_added", 0) for r in successful)
        print(f"\nTotal: {total_words:,} words in {total_chunks:,} chunks")

    return results


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest Kindle books into the Council of Elders knowledge base"
    )

    parser.add_argument(
        "path",
        type=Path,
        nargs='?',
        help="Path to ePub/TXT file or directory containing books"
    )

    parser.add_argument(
        "--elder",
        type=str,
        help="Override elder assignment (e.g., 'greene', 'peterson')"
    )

    parser.add_argument(
        "--title",
        type=str,
        help="Override book title"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be ingested without actually ingesting"
    )

    parser.add_argument(
        "--list-mappings",
        action="store_true",
        help="List all known book-to-elder mappings"
    )

    args = parser.parse_args()

    if args.list_mappings:
        print("Known Book-to-Elder Mappings")
        print("=" * 50)

        # Group by elder
        by_elder = {}
        for asin, (elder_id, title) in BOOK_ELDER_MAP.items():
            if elder_id not in by_elder:
                by_elder[elder_id] = []
            by_elder[elder_id].append((title, asin))

        for elder_id in sorted(by_elder.keys()):
            print(f"\n{elder_id.upper()}:")
            for title, asin in sorted(by_elder[elder_id]):
                print(f"  - {title} ({asin})")

        return

    if args.path is None:
        parser.error("path is required unless using --list-mappings")

    path = args.path

    if path.is_dir():
        ingest_directory(path, dry_run=args.dry_run)
    elif path.is_file():
        ingest_book(path, elder_id=args.elder, book_title=args.title, dry_run=args.dry_run)
    else:
        print(f"Error: {path} does not exist")
        sys.exit(1)


if __name__ == "__main__":
    main()
