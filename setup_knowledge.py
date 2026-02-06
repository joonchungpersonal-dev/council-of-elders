#!/usr/bin/env python3
"""
Council of Elders - Automated Knowledge Setup

This script automatically:
1. Saves embedded wisdom (key quotes) for all elders
2. Fetches public domain texts (Meditations, Art of War, etc.)
3. Downloads and processes YouTube transcripts

Run with: python setup_knowledge.py

Options:
  --skip-youtube    Skip YouTube transcript download
  --youtube-only    Only download YouTube transcripts
  --elder ELDER     Process only specific elder
  --max-videos N    Max YouTube videos per elder (default: 5)
  --search          Also search YouTube (not just known videos)
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Setup Council of Elders knowledge base")
    parser.add_argument("--skip-youtube", action="store_true", help="Skip YouTube downloads")
    parser.add_argument("--youtube-only", action="store_true", help="Only do YouTube downloads")
    parser.add_argument("--elder", type=str, help="Process only specific elder")
    parser.add_argument("--max-videos", type=int, default=5, help="Max YouTube videos per elder")
    parser.add_argument("--search", action="store_true", help="Search YouTube for more videos")

    args = parser.parse_args()

    console.clear()
    console.print(Panel.fit(
        "[bold]Council of Elders - Knowledge Setup[/bold]\n"
        "[dim]Automated wisdom collection[/dim]",
        border_style="green"
    ))

    results = {
        "embedded_wisdom": {},
        "public_sources": {},
        "youtube": {},
        "errors": [],
    }

    # Import here to avoid circular imports
    from council.knowledge.fetcher import save_embedded_wisdom, fetch_all_public_sources
    from council.knowledge.youtube import setup_youtube_knowledge, YOUTUBE_SOURCES

    if not args.youtube_only:
        # Step 1: Embedded Wisdom
        console.print("\n[bold cyan]Step 1: Saving Embedded Wisdom[/bold cyan]")
        console.print("[dim]Key quotes and passages for all elders[/dim]\n")

        try:
            results["embedded_wisdom"] = save_embedded_wisdom(
                elder_id=args.elder,
                verbose=True
            )
            console.print(f"[green]✓ Saved wisdom for {len(results['embedded_wisdom'])} elders[/green]")
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            results["errors"].append(str(e))

        # Step 2: Public Domain Texts
        console.print("\n[bold cyan]Step 2: Fetching Public Domain Texts[/bold cyan]")
        console.print("[dim]Meditations, Art of War, Dhammapada, etc.[/dim]\n")

        try:
            results["public_sources"] = fetch_all_public_sources(
                elder_id=args.elder,
                verbose=True
            )
            total = sum(len(f) for f in results["public_sources"].values())
            console.print(f"[green]✓ Downloaded {total} public domain texts[/green]")
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            results["errors"].append(str(e))

    if not args.skip_youtube:
        # Step 3: YouTube Transcripts
        console.print("\n[bold cyan]Step 3: YouTube Transcripts[/bold cyan]")
        console.print("[dim]Interviews, lectures, and speeches[/dim]\n")

        elder_ids = [args.elder] if args.elder else None

        try:
            results["youtube"] = setup_youtube_knowledge(
                elder_ids=elder_ids,
                max_videos_per_elder=args.max_videos,
                use_known_only=not args.search,
                verbose=True
            )
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            results["errors"].append(str(e))

    # Final Summary
    console.print("\n" + "=" * 60)
    console.print("[bold green]KNOWLEDGE SETUP COMPLETE[/bold green]")
    console.print("=" * 60)

    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Embedded wisdom files: {len(results['embedded_wisdom'])}")
    console.print(f"  Public domain texts:   {sum(len(f) for f in results['public_sources'].values())}")
    console.print(f"  YouTube transcripts:   {sum(len(f) for f in results['youtube'].values())}")

    if results["errors"]:
        console.print(f"\n[yellow]Warnings/Errors: {len(results['errors'])}[/yellow]")

    console.print(f"\n[dim]Knowledge stored in: ~/.council/knowledge/[/dim]")
    console.print("[dim]This knowledge will enhance elder responses.[/dim]\n")


if __name__ == "__main__":
    main()
