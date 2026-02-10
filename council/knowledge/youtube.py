"""
Automated YouTube transcript pipeline.

Finds, downloads, vets, cleans, and adds YouTube transcripts to elder knowledge bases.
"""

import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from council.config import get_knowledge_dir
from council.llm import chat

# Known high-quality video sources for each elder
YOUTUBE_SOURCES = {
    "munger": {
        "search_queries": [
            "Charlie Munger interview",
            "Charlie Munger Berkshire Hathaway",
            "Charlie Munger Daily Journal",
            "Charlie Munger wisdom",
            "Charlie Munger psychology of human misjudgment",
            "Charlie Munger mental models",
        ],
        "known_channels": [
            "Investor Archive",
            "YAPSS",
        ],
        "known_videos": [
            # Psychology of Human Misjudgment - full lecture
            "https://www.youtube.com/watch?v=pqzcCfUglws",
            # Charlie Munger: A Lesson on Elementary Worldly Wisdom
            "https://www.youtube.com/watch?v=zZKuXY2oltc",
            # Charlie Munger Interview
            "https://www.youtube.com/watch?v=5U0TE4oqj24",
            # Mental Models series
            "https://www.youtube.com/watch?v=ywyQ_eNNCJU",
            "https://www.youtube.com/watch?v=BRgnIyjRxmU",
            "https://www.youtube.com/watch?v=4KfmkjmjJgI",
            "https://www.youtube.com/watch?v=cgfuEEnsuAc",
            "https://www.youtube.com/watch?v=ZZFbDrenepY",
            "https://www.youtube.com/watch?v=0GNF9hvt768",
            "https://www.youtube.com/watch?v=T5-re2X-YSY",
            "https://www.youtube.com/watch?v=tcq6ZyfQV2w",
            "https://www.youtube.com/watch?v=S15XpqbUFFA",
            "https://www.youtube.com/watch?v=aqpU2yFuuvA",
            "https://www.youtube.com/watch?v=lqqRzNC3QyU",
            "https://www.youtube.com/watch?v=vP2QPLGnjGo",
        ],
    },
    "buffett": {
        "search_queries": [
            "Warren Buffett interview",
            "Warren Buffett Berkshire Hathaway meeting",
            "Warren Buffett CNBC",
            "Warren Buffett advice",
        ],
        "known_channels": [
            "CNBC",
            "Yahoo Finance",
        ],
        "known_videos": [
            # HBO Documentary
            "https://www.youtube.com/watch?v=PB5krSvFAPY",
            # Warren Buffett on investing
            "https://www.youtube.com/watch?v=2a9Lx9J8uSs",
        ],
    },
    "bruce_lee": {
        "search_queries": [
            "Bruce Lee interview",
            "Bruce Lee philosophy",
            "Bruce Lee Pierre Berton",
        ],
        "known_videos": [
            # Pierre Berton interview
            "https://www.youtube.com/watch?v=uk1lzkH-e4U",
            # Lost interview
            "https://www.youtube.com/watch?v=EcKURf83R9Y",
        ],
    },
    "branden": {
        "search_queries": [
            "Nathaniel Branden lecture",
            "Nathaniel Branden self-esteem",
            "Nathaniel Branden interview",
        ],
        "known_videos": [],
    },
    "clear": {
        "search_queries": [
            "James Clear atomic habits",
            "James Clear interview",
            "James Clear habits",
            "James Clear 1 percent better",
        ],
        "known_channels": [
            "James Clear",
        ],
        "known_videos": [
            "https://www.youtube.com/watch?v=mNeXuCYiE0U",
            "https://www.youtube.com/watch?v=U_nzqnXWvSo",
            "https://www.youtube.com/watch?v=PZ7lDrwYdZc",
        ],
    },
    "greene": {
        "search_queries": [
            "Robert Greene interview",
            "Robert Greene 48 laws of power",
            "Robert Greene mastery",
            "Robert Greene human nature",
            "Robert Greene strategy",
        ],
        "known_channels": [
            "Robert Greene",
        ],
        "known_videos": [
            # Robert Greene on the Tim Ferriss Show
            "https://www.youtube.com/watch?v=BjKmOChcpCs",
            # Robert Greene on Impact Theory
            "https://www.youtube.com/watch?v=HpvamxKZS3w",
            # Laws of Human Nature
            "https://www.youtube.com/watch?v=87CXTnQoLKQ",
        ],
    },
    "naval": {
        "search_queries": [
            "Naval Ravikant interview",
            "Naval Ravikant wealth happiness",
            "Naval Ravikant Joe Rogan",
            "Naval Ravikant how to get rich",
        ],
        "known_videos": [
            # Joe Rogan Experience
            "https://www.youtube.com/watch?v=3qHkcs3kG44",
            # How to Get Rich
            "https://www.youtube.com/watch?v=1-TZqOsVCNM",
            # Naval on Tim Ferriss
            "https://www.youtube.com/watch?v=-7J-Gwc9pVg",
        ],
    },
    "rubin": {
        "search_queries": [
            "Rick Rubin interview",
            "Rick Rubin creative act",
            "Rick Rubin producing",
            "Rick Rubin meditation",
            "Tetragrammaton podcast",
        ],
        "known_videos": [
            # 60 Minutes interview
            "https://www.youtube.com/watch?v=QJe_6rR7nHQ",
            # Rick Rubin on creativity
            "https://www.youtube.com/watch?v=H_szemxPcTI",
            # Huberman Lab
            "https://www.youtube.com/watch?v=GpgqXCkRO-w",
        ],
    },
    "oprah": {
        "search_queries": [
            "Oprah interview wisdom",
            "Oprah super soul sunday",
            "Oprah life lessons",
            "Oprah masterclass",
        ],
        "known_videos": [
            # Stanford Commencement
            "https://www.youtube.com/watch?v=FnmM52vVGbM",
            # Super Soul conversations
            "https://www.youtube.com/watch?v=qlqC1WNqAas",
        ],
    },
    "thich": {
        "search_queries": [
            "Thich Nhat Hanh lecture",
            "Thich Nhat Hanh mindfulness",
            "Thich Nhat Hanh meditation",
            "Thich Nhat Hanh Plum Village",
        ],
        "known_videos": [
            # Oprah interview
            "https://www.youtube.com/watch?v=NJ9UtuWfs3U",
            # The Art of Mindful Living
            "https://www.youtube.com/watch?v=dDW6FYdIoYE",
            # Google Talk
            "https://www.youtube.com/watch?v=SGJBGV2Ym94",
        ],
    },
    "jung": {
        "search_queries": [
            "Carl Jung interview",
            "Carl Jung BBC",
            "Carl Jung Face to Face",
            "Carl Jung documentary",
        ],
        "known_videos": [
            # BBC Face to Face interview (historic)
            "https://www.youtube.com/watch?v=2AMu-G51yTY",
            # Matter of Heart documentary
            "https://www.youtube.com/watch?v=WY3yKmIVfHw",
        ],
    },
    "kabatzinn": {
        "search_queries": [
            "Jon Kabat-Zinn mindfulness",
            "Jon Kabat-Zinn MBSR",
            "Jon Kabat-Zinn meditation",
            "Jon Kabat-Zinn Google Talk",
        ],
        "known_videos": [
            # Google Talk
            "https://www.youtube.com/watch?v=3nwwKbM_vJc",
            # Mindfulness-Based Stress Reduction
            "https://www.youtube.com/watch?v=_If4a-gHg_I",
            # Interview
            "https://www.youtube.com/watch?v=sN6HmcWKJPc",
        ],
    },
    "kahneman": {
        "search_queries": [
            "Daniel Kahneman interview",
            "Daniel Kahneman thinking fast and slow",
            "Daniel Kahneman behavioral economics",
            "Daniel Kahneman Nobel",
        ],
        "known_videos": [
            # Google Talk
            "https://www.youtube.com/watch?v=CjVQJdIrDJ0",
            # Talks at Google
            "https://www.youtube.com/watch?v=1M7TKeCgJw4",
        ],
    },
    "tetlock": {
        "search_queries": [
            "Philip Tetlock superforecasting",
            "Philip Tetlock prediction",
            "Philip Tetlock forecasting",
        ],
        "known_videos": [
            # Long Now Foundation
            "https://www.youtube.com/watch?v=xBXDTQdmNyw",
            # Google Talk
            "https://www.youtube.com/watch?v=m5pM8CvSz_4",
        ],
    },
    "klein": {
        "search_queries": [
            "Gary Klein decision making",
            "Gary Klein intuition",
            "Gary Klein sources of power",
            "Gary Klein recognition primed decision",
        ],
        "known_videos": [
            # Decision Making Research
            "https://www.youtube.com/watch?v=LHMAo9GzJdw",
        ],
    },
    "meadows": {
        "search_queries": [
            "Donella Meadows systems thinking",
            "Donella Meadows limits to growth",
            "Dana Meadows lecture",
        ],
        "known_videos": [
            # Leverage Points lecture
            "https://www.youtube.com/watch?v=HMmChiLZZHg",
        ],
    },
    "tubman": {
        "search_queries": [
            "Harriet Tubman documentary",
            "Harriet Tubman biography",
            "Underground Railroad documentary",
        ],
        "known_videos": [
            # Harriet documentary clips
            "https://www.youtube.com/watch?v=GR0Xp5TnTDw",
        ],
    },
    "hannibal": {
        "search_queries": [
            "Hannibal Barca documentary",
            "Hannibal tactics",
            "Battle of Cannae",
            "Hannibal Alps",
        ],
        "known_videos": [
            # History Channel documentary
            "https://www.youtube.com/watch?v=EbBHk_zLTmY",
            # Kings and Generals
            "https://www.youtube.com/watch?v=kBxcmNuzSIY",
        ],
    },
    "boudicca": {
        "search_queries": [
            "Boudicca documentary",
            "Boudica rebellion",
            "Iceni queen",
            "Boudicca history",
        ],
        "known_videos": [
            # BBC Documentary
            "https://www.youtube.com/watch?v=7eK9T7U4Yl0",
        ],
    },
    "genghis": {
        "search_queries": [
            "Genghis Khan documentary",
            "Mongol Empire history",
            "Genghis Khan tactics",
        ],
        "known_videos": [
            # Documentary
            "https://www.youtube.com/watch?v=NLNwPMh92F4",
            # Extra History series
            "https://www.youtube.com/watch?v=Eq-Wk3YqeH4",
        ],
    },
    "lauder": {
        "search_queries": [
            "Estee Lauder documentary",
            "Estee Lauder biography",
            "Estee Lauder business story",
        ],
        "known_videos": [
            # Biography
            "https://www.youtube.com/watch?v=ByQP-A7qVzk",
        ],
    },
}


@dataclass
class VideoInfo:
    """Information about a YouTube video."""
    url: str
    title: str
    channel: str
    duration: int  # seconds
    transcript: str
    language: str


def get_video_info(url: str) -> VideoInfo | None:
    """
    Get video information and transcript using yt-dlp.
    """
    try:
        # Get video metadata
        result = subprocess.run(
            [
                "yt-dlp",
                "--dump-json",
                "--no-download",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            print(f"Error getting video info: {result.stderr}")
            return None

        info = json.loads(result.stdout)

        title = info.get("title", "Unknown")
        channel = info.get("channel", info.get("uploader", "Unknown"))
        duration = info.get("duration", 0)

        # Get transcript
        transcript = get_transcript(url)

        if not transcript:
            return None

        return VideoInfo(
            url=url,
            title=title,
            channel=channel,
            duration=duration,
            transcript=transcript,
            language="en",
        )

    except subprocess.TimeoutExpired:
        print(f"Timeout getting video info for {url}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_transcript(url: str) -> str | None:
    """
    Download transcript/subtitles for a video.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Try to get auto-generated or manual subtitles
            result = subprocess.run(
                [
                    "yt-dlp",
                    "--write-auto-sub",
                    "--write-sub",
                    "--sub-lang", "en",
                    "--sub-format", "vtt",
                    "--skip-download",
                    "-o", f"{tmpdir}/%(id)s.%(ext)s",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Find the subtitle file
            vtt_files = list(Path(tmpdir).glob("*.vtt"))

            if not vtt_files:
                # Try SRT format
                result = subprocess.run(
                    [
                        "yt-dlp",
                        "--write-auto-sub",
                        "--write-sub",
                        "--sub-lang", "en",
                        "--sub-format", "srt",
                        "--skip-download",
                        "-o", f"{tmpdir}/%(id)s.%(ext)s",
                        url,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                vtt_files = list(Path(tmpdir).glob("*.srt"))

            if not vtt_files:
                print(f"No subtitles found for {url}")
                return None

            # Read and clean the transcript
            with open(vtt_files[0], 'r', encoding='utf-8') as f:
                raw_transcript = f.read()

            return clean_transcript(raw_transcript)

        except subprocess.TimeoutExpired:
            print(f"Timeout downloading transcript for {url}")
            return None
        except Exception as e:
            print(f"Error getting transcript: {e}")
            return None


def clean_transcript(raw_text: str) -> str:
    """
    Clean up a VTT/SRT transcript to plain text.
    """
    lines = raw_text.split('\n')
    cleaned_lines = []
    seen_lines = set()

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Skip VTT header
        if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue

        # Skip timestamp lines (00:00:00.000 --> 00:00:00.000)
        if re.match(r'^\d{2}:\d{2}:\d{2}', line):
            continue

        # Skip numeric-only lines (SRT sequence numbers)
        if re.match(r'^\d+$', line):
            continue

        # Remove VTT positioning tags
        line = re.sub(r'<[^>]+>', '', line)

        # Remove speaker tags like [Music] or [Applause]
        line = re.sub(r'\[[^\]]+\]', '', line)

        # Remove timestamp tags
        line = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', line)

        line = line.strip()

        # Skip if empty after cleaning
        if not line:
            continue

        # Deduplicate (auto-subs often repeat lines)
        if line.lower() in seen_lines:
            continue
        seen_lines.add(line.lower())

        cleaned_lines.append(line)

    # Join into paragraphs (combine lines until we hit a sentence ending)
    paragraphs = []
    current_para = []

    for line in cleaned_lines:
        current_para.append(line)

        # If line ends with sentence-ending punctuation, start new paragraph
        if line.rstrip()[-1:] in '.!?':
            paragraphs.append(' '.join(current_para))
            current_para = []

    # Don't forget the last paragraph
    if current_para:
        paragraphs.append(' '.join(current_para))

    return '\n\n'.join(paragraphs)


def vet_transcript(transcript: str, elder_id: str, title: str) -> tuple[bool, str]:
    """
    Use LLM to vet if transcript is relevant and high quality.

    Returns (is_valid, cleaned_transcript or reason for rejection)
    """
    prompt = f"""You are vetting a transcript for the Council of Elders knowledge base.

Elder: {elder_id}
Video Title: {title}

Transcript (first 2000 chars):
{transcript[:2000]}

Please evaluate:
1. Is this transcript actually about or by this person? (not just mentioning them)
2. Is the transcript quality readable (not garbled auto-captions)?
3. Does it contain substantive wisdom, insights, or teachings?

Respond with ONLY:
ACCEPT - if it passes all criteria
REJECT: [brief reason] - if it fails

Your verdict:"""

    messages = [{"role": "user", "content": prompt}]
    response = "".join(chat(messages, stream=True))

    if response.strip().startswith("ACCEPT"):
        return True, transcript
    else:
        return False, response


def save_transcript(elder_id: str, video_info: VideoInfo) -> Path:
    """Save a vetted transcript to the knowledge base."""
    knowledge_dir = get_knowledge_dir() / elder_id / "youtube"
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    # Create safe filename
    safe_title = re.sub(r'[^\w\s-]', '', video_info.title)[:50].strip().replace(' ', '_')
    filepath = knowledge_dir / f"{safe_title}.txt"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# {video_info.title}\n")
        f.write(f"Source: {video_info.url}\n")
        f.write(f"Channel: {video_info.channel}\n")
        f.write(f"Duration: {video_info.duration // 60} minutes\n")
        f.write(f"\n---\n\n")
        f.write(video_info.transcript)

    return filepath


def search_youtube(query: str, max_results: int = 5) -> list[str]:
    """
    Search YouTube and return video URLs.
    """
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                f"ytsearch{max_results}:{query}",
                "--get-id",
                "--no-download",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            return []

        video_ids = result.stdout.strip().split('\n')
        return [f"https://www.youtube.com/watch?v={vid}" for vid in video_ids if vid]

    except Exception as e:
        print(f"Search error: {e}")
        return []


def get_video_links(elder_id: str, max_results: int = 8) -> list[dict]:
    """Get watchable YouTube video links with metadata (no transcript download).

    Returns a list of dicts with title, url, channel, duration, and thumbnail.
    Uses known videos from YOUTUBE_SOURCES and optionally searches for more.
    """
    if elder_id not in YOUTUBE_SOURCES:
        return []

    sources = YOUTUBE_SOURCES[elder_id]
    video_urls = list(sources.get("known_videos", []))

    # Search for additional videos if we don't have enough known ones
    if len(video_urls) < max_results:
        for query in sources.get("search_queries", [])[:2]:
            found = search_youtube(query, max_results=3)
            for url in found:
                if url not in video_urls:
                    video_urls.append(url)
            if len(video_urls) >= max_results:
                break

    video_urls = video_urls[:max_results]

    def _fetch_metadata(url):
        """Fetch metadata for a single video URL."""
        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-download", url],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return None
            info = json.loads(result.stdout)
            video_id = info.get("id", "")
            return {
                "title": info.get("title", "Unknown"),
                "url": url,
                "channel": info.get("channel", info.get("uploader", "Unknown")),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail", f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"),
            }
        except (subprocess.TimeoutExpired, Exception):
            return None

    from concurrent.futures import ThreadPoolExecutor

    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        for item in executor.map(_fetch_metadata, video_urls):
            if item is not None:
                results.append(item)

    return results


def process_elder_youtube(
    elder_id: str,
    max_videos: int = 10,
    use_known_only: bool = False,
    verbose: bool = True
) -> list[Path]:
    """
    Process YouTube videos for an elder.

    Args:
        elder_id: The elder to process
        max_videos: Maximum videos to process
        use_known_only: Only use known video URLs, don't search
        verbose: Print progress

    Returns:
        List of saved transcript paths
    """
    if elder_id not in YOUTUBE_SOURCES:
        if verbose:
            print(f"No YouTube sources configured for {elder_id}")
        return []

    sources = YOUTUBE_SOURCES[elder_id]
    video_urls = set()

    # Add known videos
    video_urls.update(sources.get("known_videos", []))

    # Search for more if not using known only
    if not use_known_only:
        for query in sources.get("search_queries", [])[:3]:  # Limit queries
            if verbose:
                print(f"  Searching: {query}")
            found = search_youtube(query, max_results=3)
            video_urls.update(found)

            if len(video_urls) >= max_videos:
                break

    video_urls = list(video_urls)[:max_videos]

    if verbose:
        print(f"  Found {len(video_urls)} videos to process")

    saved_paths = []

    for i, url in enumerate(video_urls):
        if verbose:
            print(f"\n  [{i+1}/{len(video_urls)}] Processing: {url}")

        # Get video info and transcript
        video_info = get_video_info(url)

        if not video_info:
            if verbose:
                print(f"    ✗ Could not get transcript")
            continue

        if verbose:
            print(f"    Title: {video_info.title}")
            print(f"    Duration: {video_info.duration // 60} min")

        # Vet the transcript
        if verbose:
            print(f"    Vetting transcript...")

        is_valid, result = vet_transcript(
            video_info.transcript,
            elder_id,
            video_info.title
        )

        if not is_valid:
            if verbose:
                print(f"    ✗ Rejected: {result}")
            continue

        # Save
        filepath = save_transcript(elder_id, video_info)
        saved_paths.append(filepath)

        if verbose:
            print(f"    ✓ Saved to {filepath}")

    return saved_paths


def setup_youtube_knowledge(
    elder_ids: list[str] | None = None,
    max_videos_per_elder: int = 5,
    use_known_only: bool = True,
    verbose: bool = True
) -> dict[str, list[Path]]:
    """
    Run complete YouTube knowledge setup.

    Args:
        elder_ids: List of elders to process, or None for all configured
        max_videos_per_elder: Max videos per elder
        use_known_only: Only use known video URLs
        verbose: Print progress

    Returns:
        Dict mapping elder_id to list of saved paths
    """
    if elder_ids is None:
        elder_ids = list(YOUTUBE_SOURCES.keys())

    if verbose:
        print("\n" + "=" * 60)
        print("YOUTUBE TRANSCRIPT PIPELINE")
        print("=" * 60 + "\n")

    results = {}

    for elder_id in elder_ids:
        if verbose:
            print(f"\nProcessing {elder_id}...")
            print("-" * 40)

        paths = process_elder_youtube(
            elder_id,
            max_videos=max_videos_per_elder,
            use_known_only=use_known_only,
            verbose=verbose
        )

        results[elder_id] = paths

    # Summary
    if verbose:
        print("\n" + "=" * 60)
        print("YOUTUBE PIPELINE COMPLETE")
        print("=" * 60)

        total = sum(len(p) for p in results.values())
        print(f"\n  Total transcripts saved: {total}")

        for elder_id, paths in results.items():
            print(f"    {elder_id}: {len(paths)} transcripts")

        print(f"\n  Knowledge stored in: ~/.council/knowledge/*/youtube/")
        print()

    return results
