"""
Podcast Transcript Pipeline

Downloads transcripts from podcasts featuring council elders.
Uses YouTube for video podcasts (Lex Fridman, etc.) since they have transcripts.
"""

import re
from pathlib import Path

from council.config import get_knowledge_dir
from council.knowledge.youtube import get_video_info, save_transcript, vet_transcript, VideoInfo


# Known podcast episodes featuring elders
# These are YouTube versions of podcasts with available transcripts
PODCAST_EPISODES = {
    "munger": [
        # Acquired Podcast
        {
            "url": "https://www.youtube.com/watch?v=nF5LVBUCKMA",
            "podcast": "Acquired",
            "title": "Charlie Munger",
        },
        # CNBC interviews
        {
            "url": "https://www.youtube.com/watch?v=PGOxHAVM3QA",
            "podcast": "CNBC",
            "title": "Charlie Munger Interview",
        },
    ],
    "buffett": [
        # Various CNBC appearances
        {
            "url": "https://www.youtube.com/watch?v=69rm13iUOok",
            "podcast": "CNBC",
            "title": "Warren Buffett Interview",
        },
        {
            "url": "https://www.youtube.com/watch?v=9-uo5b1wkE8",
            "podcast": "Yahoo Finance",
            "title": "Warren Buffett Full Interview",
        },
    ],
    "peterson": [
        # Lex Fridman Podcast
        {
            "url": "https://www.youtube.com/watch?v=buD2RM0xChM",
            "podcast": "Lex Fridman Podcast",
            "title": "Jordan Peterson: Life, Death, Power, Fame, and Meaning",
        },
        {
            "url": "https://www.youtube.com/watch?v=W3QXLU4xj1A",
            "podcast": "Lex Fridman Podcast",
            "title": "Jordan Peterson: Life, Death, Power",
        },
        # Joe Rogan
        {
            "url": "https://www.youtube.com/watch?v=vIeFt88Hm8s",
            "podcast": "Joe Rogan Experience",
            "title": "Jordan Peterson",
        },
        # Jocko Podcast
        {
            "url": "https://www.youtube.com/watch?v=WGZxKOH0Gl0",
            "podcast": "Jocko Podcast",
            "title": "Jordan Peterson and Jocko",
        },
    ],
    "clear": [
        # Various podcast appearances
        {
            "url": "https://www.youtube.com/watch?v=s9uDVVUD3Rk",
            "podcast": "Rich Roll Podcast",
            "title": "James Clear: Atomic Habits",
        },
        {
            "url": "https://www.youtube.com/watch?v=_BfpjEkOGkg",
            "podcast": "Impact Theory",
            "title": "James Clear on Habits",
        },
    ],
    "bruce_lee": [
        # Documentaries and interviews
        {
            "url": "https://www.youtube.com/watch?v=18Hd8Pxlct4",
            "podcast": "Documentary",
            "title": "Bruce Lee Documentary",
        },
    ],
    "branden": [
        # Interviews
        {
            "url": "https://www.youtube.com/watch?v=G6FFaJxyJ0E",
            "podcast": "Interview",
            "title": "Nathaniel Branden Interview",
        },
    ],
}


def fetch_podcast_episode(
    elder_id: str,
    episode: dict,
    verbose: bool = True
) -> Path | None:
    """
    Fetch a single podcast episode transcript.

    Args:
        elder_id: The elder this episode is for
        episode: Dict with url, podcast, title
        verbose: Print progress

    Returns:
        Path to saved file or None
    """
    url = episode["url"]
    podcast = episode.get("podcast", "Podcast")

    if verbose:
        print(f"    Fetching: {episode.get('title', url)[:50]}...")

    # Get video info and transcript
    video_info = get_video_info(url)

    if not video_info:
        if verbose:
            print(f"      ✗ Could not get transcript")
        return None

    if verbose:
        print(f"      Duration: {video_info.duration // 60} min")

    # Vet the transcript
    is_valid, result = vet_transcript(
        video_info.transcript,
        elder_id,
        video_info.title
    )

    if not is_valid:
        if verbose:
            print(f"      ✗ Rejected: {result[:50]}")
        return None

    # Save to podcasts subdirectory
    knowledge_dir = get_knowledge_dir() / elder_id / "podcasts"
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    # Create safe filename
    safe_title = re.sub(r'[^\w\s-]', '', video_info.title)[:50].strip().replace(' ', '_')
    safe_podcast = re.sub(r'[^\w\s-]', '', podcast).strip().replace(' ', '_')
    filepath = knowledge_dir / f"{safe_podcast}_{safe_title}.txt"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# {video_info.title}\n")
        f.write(f"Podcast: {podcast}\n")
        f.write(f"Source: {video_info.url}\n")
        f.write(f"Duration: {video_info.duration // 60} minutes\n")
        f.write(f"\n---\n\n")
        f.write(video_info.transcript)

    if verbose:
        print(f"      ✓ Saved")

    return filepath


def fetch_elder_podcasts(
    elder_id: str,
    verbose: bool = True
) -> list[Path]:
    """
    Fetch all podcast episodes for an elder.

    Args:
        elder_id: The elder to fetch podcasts for
        verbose: Print progress

    Returns:
        List of saved file paths
    """
    if elder_id not in PODCAST_EPISODES:
        if verbose:
            print(f"  No podcast episodes configured for {elder_id}")
        return []

    episodes = PODCAST_EPISODES[elder_id]

    if verbose:
        print(f"  Found {len(episodes)} episodes to fetch")

    results = []

    for episode in episodes:
        filepath = fetch_podcast_episode(elder_id, episode, verbose)
        if filepath:
            results.append(filepath)

    return results


def setup_all_podcasts(
    elder_ids: list[str] | None = None,
    verbose: bool = True
) -> dict[str, list[Path]]:
    """
    Fetch all configured podcast episodes.

    Args:
        elder_ids: Specific elders to fetch, or None for all
        verbose: Print progress

    Returns:
        Dict mapping elder_id to list of saved paths
    """
    if verbose:
        print("\n" + "=" * 60)
        print("PODCAST TRANSCRIPT PIPELINE")
        print("=" * 60 + "\n")

    if elder_ids is None:
        elder_ids = list(PODCAST_EPISODES.keys())

    results = {}

    for elder_id in elder_ids:
        if elder_id not in PODCAST_EPISODES:
            continue

        if verbose:
            print(f"\nProcessing {elder_id}...")
            print("-" * 40)

        paths = fetch_elder_podcasts(elder_id, verbose)
        results[elder_id] = paths

    # Summary
    if verbose:
        print("\n" + "=" * 60)
        print("PODCAST PIPELINE COMPLETE")
        print("=" * 60)

        total = sum(len(p) for p in results.values())
        print(f"\n  Total transcripts saved: {total}")

        for elder_id, paths in results.items():
            if paths:
                print(f"    {elder_id}: {len(paths)} episodes")

        print(f"\n  Saved to: ~/.council/knowledge/*/podcasts/")

    return results


if __name__ == "__main__":
    setup_all_podcasts()
