#!/usr/bin/env python3
"""
Kindle Text Extraction Helper

This script helps extract text from Kindle books by automating
the copy-paste process using macOS accessibility features.

Usage:
    1. Open the book in Kindle app
    2. Run this script
    3. It will guide you through the process
"""

import subprocess
import sys
import os
from pathlib import Path

# Book mappings
BOOKS = {
    "48laws": ("greene", "The 48 Laws of Power"),
    "seduction": ("greene", "The Art of Seduction"),
    "33strategies": ("greene", "The 33 Strategies of War"),
    "mastery": ("greene", "Mastery"),
    "50thlaw": ("greene", "The 50th Law"),
    "12rules": ("peterson", "12 Rules for Life"),
}


def get_clipboard():
    """Get current clipboard content."""
    result = subprocess.run(['pbpaste'], capture_output=True, text=True)
    return result.stdout


def save_chapter(content: str, book_code: str, chapter_num: int, output_dir: Path):
    """Save a chapter to a file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{book_code}_chapter_{chapter_num:02d}.txt"
    filepath.write_text(content, encoding='utf-8')
    print(f"  Saved: {filepath.name} ({len(content):,} chars)")
    return filepath


def extract_book_interactive(book_code: str, output_dir: Path):
    """Interactive extraction for a single book."""
    if book_code not in BOOKS:
        print(f"Unknown book code: {book_code}")
        print(f"Available: {', '.join(BOOKS.keys())}")
        return

    elder_id, book_title = BOOKS[book_code]
    print(f"\n{'='*60}")
    print(f"Extracting: {book_title}")
    print(f"Elder: {elder_id}")
    print(f"{'='*60}")

    print("\nInstructions:")
    print("1. Open the book in Kindle app")
    print("2. Go to the first chapter")
    print("3. Select all text (Cmd+A)")
    print("4. Copy (Cmd+C)")
    print("5. Press Enter here to save the chapter")
    print("6. Navigate to next chapter and repeat")
    print("7. Type 'done' when finished with all chapters")
    print()

    chapter_num = 1
    chapters = []

    while True:
        user_input = input(f"Chapter {chapter_num} - Press Enter after copying (or 'done'): ").strip().lower()

        if user_input == 'done':
            break

        content = get_clipboard()
        if not content or len(content) < 100:
            print("  Warning: Clipboard seems empty or too short. Try again.")
            continue

        filepath = save_chapter(content, book_code, chapter_num, output_dir)
        chapters.append(filepath)
        chapter_num += 1

    # Combine all chapters into one file
    if chapters:
        combined = []
        for chapter_file in sorted(chapters):
            combined.append(chapter_file.read_text())

        final_file = output_dir / f"{book_code}_complete.txt"
        final_file.write_text("\n\n".join(combined))

        total_words = len(" ".join(combined).split())
        print(f"\n✓ Complete! {len(chapters)} chapters, {total_words:,} words")
        print(f"  Final file: {final_file}")

        return final_file

    return None


def quick_paste_mode(output_dir: Path):
    """Quick mode: paste any book content and identify it."""
    print("\n" + "="*60)
    print("Quick Paste Mode")
    print("="*60)
    print("\nCopy an entire book from Kindle (Cmd+A, Cmd+C)")
    print("Then press Enter here. I'll identify the book.\n")

    input("Press Enter after copying book content...")

    content = get_clipboard()

    if not content or len(content) < 500:
        print("Error: Clipboard is empty or too short")
        return

    word_count = len(content.split())
    print(f"Got {word_count:,} words")

    # Try to identify the book
    content_lower = content[:2000].lower()
    detected_book = None

    patterns = {
        "48 laws": "48laws",
        "law 1": "48laws",
        "never outshine": "48laws",
        "art of seduction": "seduction",
        "seducer": "seduction",
        "33 strategies": "33strategies",
        "strategy 1": "33strategies",
        "mastery": "mastery",
        "apprenticeship": "mastery",
        "50th law": "50thlaw",
        "50 cent": "50thlaw",
        "12 rules": "12rules",
        "rule 1": "12rules",
        "jordan peterson": "12rules",
    }

    for pattern, code in patterns.items():
        if pattern in content_lower:
            detected_book = code
            break

    if detected_book:
        elder_id, book_title = BOOKS[detected_book]
        print(f"\nDetected: {book_title}")
        confirm = input("Is this correct? (y/n): ").strip().lower()
        if confirm != 'y':
            detected_book = None

    if not detected_book:
        print("\nAvailable books:")
        for code, (elder, title) in BOOKS.items():
            print(f"  {code}: {title}")
        detected_book = input("\nEnter book code: ").strip().lower()

        if detected_book not in BOOKS:
            print("Unknown book code")
            return

    elder_id, book_title = BOOKS[detected_book]

    # Save the file
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{detected_book}_complete.txt"
    filepath.write_text(content)

    print(f"\n✓ Saved: {filepath}")
    print(f"  Words: {word_count:,}")
    print(f"  Elder: {elder_id}")
    print(f"\nTo ingest into Council:")
    print(f"  python -m council.knowledge.kindle {filepath}")


def main():
    output_dir = Path.home() / "council-of-elders" / "data" / "kindle_exports"

    print("Kindle Text Extraction Helper")
    print("="*60)
    print("\nModes:")
    print("  1. Quick paste (paste entire book at once)")
    print("  2. Chapter-by-chapter extraction")
    print("  3. List available books")

    choice = input("\nChoice (1/2/3): ").strip()

    if choice == "1":
        quick_paste_mode(output_dir)
    elif choice == "2":
        print("\nAvailable books:")
        for code, (elder, title) in BOOKS.items():
            print(f"  {code}: {title}")
        book_code = input("\nEnter book code: ").strip().lower()
        extract_book_interactive(book_code, output_dir)
    elif choice == "3":
        print("\nAvailable books:")
        for code, (elder, title) in BOOKS.items():
            print(f"  {code}: {title} -> {elder}")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
