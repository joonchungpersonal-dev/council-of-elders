"""
Multi-Agent YouTube Transcript Pipeline

This module implements a three-agent workflow for acquiring and verifying
YouTube transcripts for council elders:

1. Discovery Agent: Finds highly-rated videos/interviews for each elder
2. Verification Agent: Checks transcript quality and authenticity
3. Human Review: Presents verified transcripts for final approval

Usage:
    python -m council.knowledge.youtube_agents --elder munger
    python -m council.knowledge.youtube_agents --all --dry-run
"""

import json
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Generator

from council.config import get_knowledge_dir
from council.llm import chat


@dataclass
class VideoCandidate:
    """A candidate video found by the discovery agent."""
    url: str
    title: str
    channel: str
    view_count: int
    like_count: int
    duration: int  # seconds
    upload_date: str
    description: str = ""

    @property
    def rating_score(self) -> float:
        """Calculate a quality score based on views and engagement."""
        if self.view_count == 0:
            return 0
        # Simple heuristic: likes per 1000 views, scaled by total views
        engagement = (self.like_count / self.view_count) * 1000 if self.view_count > 0 else 0
        popularity = min(self.view_count / 100000, 10)  # Cap at 1M views
        return engagement * 0.6 + popularity * 0.4


@dataclass
class TranscriptResult:
    """Result of transcript extraction and verification."""
    video: VideoCandidate
    transcript: str
    verification_status: str  # 'pending', 'verified', 'rejected', 'needs_review'
    verification_notes: str = ""
    confidence_score: float = 0.0
    human_approved: bool = False


@dataclass
class AgentWorkflow:
    """Orchestrates the multi-agent YouTube pipeline."""

    elder_id: str
    results: list[TranscriptResult] = field(default_factory=list)
    verbose: bool = True

    def log(self, message: str, level: str = "info"):
        """Log a message if verbose mode is on."""
        if self.verbose:
            prefix = {"info": "[INFO]", "warn": "[WARN]", "error": "[ERROR]", "agent": "[AGENT]"}
            print(f"{prefix.get(level, '[LOG]')} {message}")

    # =========================================================================
    # AGENT 1: DISCOVERY AGENT
    # =========================================================================

    def discovery_agent(self, max_videos: int = 10) -> list[VideoCandidate]:
        """
        Discovery Agent: Find highly-rated videos featuring or about the elder.

        Strategy:
        - Search YouTube with multiple query variations
        - Filter by view count and engagement
        - Prefer interviews, lectures, and long-form content
        - Return top candidates ranked by quality score
        """
        self.log(f"Discovery Agent: Searching for videos about {self.elder_id}", "agent")

        # Build search queries based on elder
        queries = self._get_search_queries()

        all_videos = []
        seen_urls = set()

        for query in queries[:5]:  # Limit queries to avoid rate limiting
            self.log(f"  Searching: '{query}'")
            videos = self._search_youtube(query, max_results=5)

            for video in videos:
                if video.url not in seen_urls:
                    seen_urls.add(video.url)
                    all_videos.append(video)

        # Sort by rating score and return top candidates
        all_videos.sort(key=lambda v: v.rating_score, reverse=True)
        candidates = all_videos[:max_videos]

        self.log(f"Discovery Agent: Found {len(candidates)} candidate videos", "agent")
        for i, v in enumerate(candidates, 1):
            self.log(f"  {i}. [{v.rating_score:.1f}] {v.title[:60]}... ({v.view_count:,} views)")

        return candidates

    def _get_search_queries(self) -> list[str]:
        """Generate search queries for the elder."""
        # Map elder IDs to their full names and relevant search terms
        elder_names = {
            "munger": ("Charlie Munger", ["interview", "Berkshire Hathaway", "mental models", "wisdom"]),
            "buffett": ("Warren Buffett", ["interview", "Berkshire Hathaway", "investing advice", "CNBC"]),
            "aurelius": ("Marcus Aurelius", ["stoicism", "meditations", "philosophy"]),
            "buddha": ("Buddha", ["dharma talk", "buddhism", "teachings"]),
            "franklin": ("Benjamin Franklin", ["documentary", "biography", "history"]),
            "sun_tzu": ("Sun Tzu", ["Art of War", "strategy", "documentary"]),
            "musashi": ("Miyamoto Musashi", ["Book of Five Rings", "samurai", "documentary"]),
            "bruce_lee": ("Bruce Lee", ["interview", "philosophy", "Pierre Berton"]),
            "branden": ("Nathaniel Branden", ["self-esteem", "lecture", "psychology"]),
            "clear": ("James Clear", ["Atomic Habits", "interview", "habits"]),
            "greene": ("Robert Greene", ["48 Laws of Power", "interview", "mastery"]),
            "naval": ("Naval Ravikant", ["interview", "wealth", "happiness", "Joe Rogan"]),
            "rubin": ("Rick Rubin", ["interview", "creativity", "Huberman", "60 Minutes"]),
            "oprah": ("Oprah Winfrey", ["interview", "Super Soul", "masterclass"]),
            "thich": ("Thich Nhat Hanh", ["mindfulness", "dharma talk", "Plum Village"]),
            "jung": ("Carl Jung", ["interview", "psychology", "documentary", "BBC"]),
            "kabatzinn": ("Jon Kabat-Zinn", ["mindfulness", "MBSR", "meditation", "Google Talk"]),
            "kahneman": ("Daniel Kahneman", ["Thinking Fast and Slow", "interview", "Nobel"]),
            "tetlock": ("Philip Tetlock", ["Superforecasting", "prediction", "interview"]),
            "klein": ("Gary Klein", ["decision making", "intuition", "Sources of Power"]),
            "meadows": ("Donella Meadows", ["systems thinking", "lecture", "sustainability"]),
            "tubman": ("Harriet Tubman", ["documentary", "Underground Railroad", "biography"]),
            "hannibal": ("Hannibal Barca", ["documentary", "Carthage", "Battle of Cannae"]),
            "boudicca": ("Boudicca", ["documentary", "Iceni", "Roman Britain"]),
            "genghis": ("Genghis Khan", ["documentary", "Mongol Empire", "history"]),
            "lauder": ("Estée Lauder", ["documentary", "biography", "business"]),
            "laotzu": ("Lao Tzu", ["Tao Te Ching", "Taoism", "documentary"]),
            "davinci": ("Leonardo da Vinci", ["documentary", "Renaissance", "genius"]),
        }

        name, terms = elder_names.get(self.elder_id, (self.elder_id, ["interview", "lecture"]))

        queries = [f"{name} interview"]
        for term in terms[:3]:
            queries.append(f"{name} {term}")
        queries.append(f"{name} full lecture")

        return queries

    def _search_youtube(self, query: str, max_results: int = 5) -> list[VideoCandidate]:
        """Search YouTube and return video candidates with metadata."""
        try:
            # Use yt-dlp to search and get video info
            result = subprocess.run(
                [
                    "yt-dlp",
                    f"ytsearch{max_results}:{query}",
                    "--dump-json",
                    "--no-download",
                    "--flat-playlist",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                return []

            videos = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    info = json.loads(line)
                    # Get full video info for detailed metadata
                    full_info = self._get_video_details(info.get('url', f"https://www.youtube.com/watch?v={info.get('id', '')}"))
                    if full_info:
                        videos.append(full_info)
                except json.JSONDecodeError:
                    continue

            return videos

        except subprocess.TimeoutExpired:
            self.log(f"Search timeout for: {query}", "warn")
            return []
        except Exception as e:
            self.log(f"Search error: {e}", "error")
            return []

    def _get_video_details(self, url: str) -> VideoCandidate | None:
        """Get detailed information about a single video."""
        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-download", url],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return None

            info = json.loads(result.stdout)

            return VideoCandidate(
                url=info.get('webpage_url', url),
                title=info.get('title', 'Unknown'),
                channel=info.get('channel', info.get('uploader', 'Unknown')),
                view_count=info.get('view_count', 0) or 0,
                like_count=info.get('like_count', 0) or 0,
                duration=info.get('duration', 0) or 0,
                upload_date=info.get('upload_date', ''),
                description=info.get('description', '')[:500],
            )

        except Exception:
            return None

    # =========================================================================
    # AGENT 2: VERIFICATION AGENT
    # =========================================================================

    def verification_agent(self, video: VideoCandidate, transcript: str) -> TranscriptResult:
        """
        Verification Agent: Assess transcript quality and authenticity.

        Checks:
        - Is this actually about/by the elder?
        - Is the transcript readable (not garbled)?
        - Does it contain substantive content?
        - Is the content authentic to the elder's known views?
        """
        self.log(f"Verification Agent: Analyzing '{video.title[:50]}...'", "agent")

        # Build verification prompt
        prompt = f"""You are a verification agent for the Council of Elders knowledge base.

ELDER: {self.elder_id}
VIDEO TITLE: {video.title}
CHANNEL: {video.channel}
VIEWS: {video.view_count:,}
DURATION: {video.duration // 60} minutes

TRANSCRIPT SAMPLE (first 3000 chars):
{transcript[:3000]}

Please evaluate this transcript on the following criteria:

1. RELEVANCE (1-10): Is this actually about or featuring {self.elder_id}?
   - Direct interview/lecture = 10
   - Documentary about them = 8
   - Someone analyzing their work = 6
   - Only briefly mentioned = 2
   - Not relevant = 0

2. QUALITY (1-10): Is the transcript readable and coherent?
   - Clean, well-formatted = 10
   - Minor issues = 7
   - Significant errors but understandable = 5
   - Garbled/unusable = 0

3. SUBSTANCE (1-10): Does it contain valuable wisdom, insights, or teachings?
   - Deep insights, memorable quotes = 10
   - Good educational content = 7
   - Surface-level discussion = 4
   - No real value = 0

4. AUTHENTICITY (1-10): Does the content align with the elder's known views and style?
   - Clearly authentic = 10
   - Likely authentic = 7
   - Uncertain = 5
   - Appears misattributed/fake = 0

Respond in this exact format:
RELEVANCE: [score]
QUALITY: [score]
SUBSTANCE: [score]
AUTHENTICITY: [score]
VERDICT: [VERIFIED/NEEDS_REVIEW/REJECTED]
NOTES: [Brief explanation of your assessment]
"""

        messages = [{"role": "user", "content": prompt}]
        response = "".join(chat(messages, stream=True))

        # Parse the response
        scores = {}
        verdict = "needs_review"
        notes = ""

        for line in response.split('\n'):
            line = line.strip()
            if line.startswith("RELEVANCE:"):
                scores['relevance'] = self._parse_score(line)
            elif line.startswith("QUALITY:"):
                scores['quality'] = self._parse_score(line)
            elif line.startswith("SUBSTANCE:"):
                scores['substance'] = self._parse_score(line)
            elif line.startswith("AUTHENTICITY:"):
                scores['authenticity'] = self._parse_score(line)
            elif line.startswith("VERDICT:"):
                v = line.split(":", 1)[1].strip().upper()
                if "VERIFIED" in v:
                    verdict = "verified"
                elif "REJECTED" in v:
                    verdict = "rejected"
                else:
                    verdict = "needs_review"
            elif line.startswith("NOTES:"):
                notes = line.split(":", 1)[1].strip()

        # Calculate confidence score
        if scores:
            confidence = sum(scores.values()) / (len(scores) * 10)
        else:
            confidence = 0.5

        self.log(f"  Verdict: {verdict.upper()} (confidence: {confidence:.0%})", "agent")
        self.log(f"  Notes: {notes[:100]}...")

        return TranscriptResult(
            video=video,
            transcript=transcript,
            verification_status=verdict,
            verification_notes=notes,
            confidence_score=confidence,
        )

    def _parse_score(self, line: str) -> int:
        """Parse a score from a line like 'RELEVANCE: 8'."""
        try:
            parts = line.split(":")
            if len(parts) >= 2:
                return int(re.search(r'\d+', parts[1]).group())
        except:
            pass
        return 5  # Default middle score

    # =========================================================================
    # TRANSCRIPT EXTRACTION
    # =========================================================================

    def get_transcript(self, video: VideoCandidate) -> str | None:
        """Download and clean transcript for a video."""
        self.log(f"Extracting transcript: {video.title[:50]}...")

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Download subtitles
                result = subprocess.run(
                    [
                        "yt-dlp",
                        "--write-auto-sub",
                        "--write-sub",
                        "--sub-lang", "en",
                        "--sub-format", "vtt",
                        "--skip-download",
                        "-o", f"{tmpdir}/%(id)s.%(ext)s",
                        video.url,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                # Find subtitle file
                vtt_files = list(Path(tmpdir).glob("*.vtt"))
                if not vtt_files:
                    # Try SRT
                    subprocess.run(
                        [
                            "yt-dlp",
                            "--write-auto-sub",
                            "--write-sub",
                            "--sub-lang", "en",
                            "--sub-format", "srt",
                            "--skip-download",
                            "-o", f"{tmpdir}/%(id)s.%(ext)s",
                            video.url,
                        ],
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    vtt_files = list(Path(tmpdir).glob("*.srt"))

                if not vtt_files:
                    self.log("  No subtitles found", "warn")
                    return None

                # Read and clean
                with open(vtt_files[0], 'r', encoding='utf-8') as f:
                    raw = f.read()

                return self._clean_transcript(raw)

            except subprocess.TimeoutExpired:
                self.log("  Transcript download timeout", "warn")
                return None
            except Exception as e:
                self.log(f"  Transcript error: {e}", "error")
                return None

    def _clean_transcript(self, raw: str) -> str:
        """Clean VTT/SRT transcript to plain text."""
        lines = raw.split('\n')
        cleaned = []
        seen = set()

        for line in lines:
            line = line.strip()

            # Skip metadata and timestamps
            if not line:
                continue
            if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
                continue
            if re.match(r'^\d{2}:\d{2}:\d{2}', line):
                continue
            if re.match(r'^\d+$', line):
                continue

            # Clean tags
            line = re.sub(r'<[^>]+>', '', line)
            line = re.sub(r'\[[^\]]+\]', '', line)
            line = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', line)
            line = line.strip()

            if not line:
                continue

            # Deduplicate
            if line.lower() in seen:
                continue
            seen.add(line.lower())
            cleaned.append(line)

        # Join into paragraphs
        paragraphs = []
        current = []

        for line in cleaned:
            current.append(line)
            if line.rstrip()[-1:] in '.!?':
                paragraphs.append(' '.join(current))
                current = []

        if current:
            paragraphs.append(' '.join(current))

        return '\n\n'.join(paragraphs)

    # =========================================================================
    # HUMAN REVIEW INTERFACE
    # =========================================================================

    def present_for_review(self, result: TranscriptResult) -> bool:
        """
        Present a verified transcript to the human for final approval.
        Returns True if approved, False if rejected.
        """
        print("\n" + "=" * 70)
        print("HUMAN REVIEW REQUIRED")
        print("=" * 70)
        print(f"\nELDER: {self.elder_id}")
        print(f"VIDEO: {result.video.title}")
        print(f"CHANNEL: {result.video.channel}")
        print(f"URL: {result.video.url}")
        print(f"VIEWS: {result.video.view_count:,}")
        print(f"DURATION: {result.video.duration // 60} minutes")
        print(f"\nVERIFICATION STATUS: {result.verification_status.upper()}")
        print(f"CONFIDENCE: {result.confidence_score:.0%}")
        print(f"NOTES: {result.verification_notes}")
        print("\n" + "-" * 70)
        print("TRANSCRIPT PREVIEW (first 1500 chars):")
        print("-" * 70)
        print(result.transcript[:1500])
        print("\n" + "-" * 70)

        while True:
            response = input("\nApprove this transcript? [y/n/s(kip)/q(uit)]: ").lower().strip()
            if response == 'y':
                return True
            elif response == 'n':
                return False
            elif response == 's':
                return None  # Skip
            elif response == 'q':
                raise KeyboardInterrupt("User quit review")
            else:
                print("Please enter 'y', 'n', 's', or 'q'")

    # =========================================================================
    # MAIN WORKFLOW
    # =========================================================================

    def run(
        self,
        max_videos: int = 10,
        auto_approve_threshold: float = 0.8,
        require_human_review: bool = True,
        dry_run: bool = False,
    ) -> list[TranscriptResult]:
        """
        Run the complete multi-agent workflow.

        Args:
            max_videos: Maximum videos to process
            auto_approve_threshold: Confidence threshold for auto-approval
            require_human_review: Whether to require human review for all
            dry_run: If True, don't save transcripts

        Returns:
            List of processed TranscriptResults
        """
        print("\n" + "=" * 70)
        print(f"YOUTUBE TRANSCRIPT PIPELINE: {self.elder_id.upper()}")
        print("=" * 70 + "\n")

        # Phase 1: Discovery
        candidates = self.discovery_agent(max_videos)

        if not candidates:
            self.log("No videos found. Exiting.", "warn")
            return []

        # Phase 2: Extract and Verify
        for video in candidates:
            print("\n" + "-" * 50)

            # Get transcript
            transcript = self.get_transcript(video)
            if not transcript:
                continue

            # Verify
            result = self.verification_agent(video, transcript)

            # Skip rejected
            if result.verification_status == "rejected":
                self.log(f"Rejected: {video.title[:40]}...", "warn")
                continue

            # Phase 3: Human Review (or auto-approve in non-interactive mode)
            if require_human_review:
                try:
                    approved = self.present_for_review(result)
                    if approved is None:  # Skip
                        continue
                    result.human_approved = approved
                except (KeyboardInterrupt, EOFError):
                    print("\nReview interrupted. Saving approved transcripts...")
                    break
            elif result.confidence_score >= auto_approve_threshold:
                result.human_approved = True
                self.log(f"Auto-approved (confidence: {result.confidence_score:.0%})")
            elif result.verification_status == "verified":
                result.human_approved = True
                self.log(f"Verified by agent (confidence: {result.confidence_score:.0%})")

            if result.human_approved:
                self.results.append(result)

                # Save transcript
                if not dry_run:
                    self._save_transcript(result)

        # Summary
        print("\n" + "=" * 70)
        print("PIPELINE COMPLETE")
        print("=" * 70)
        print(f"Videos processed: {len(candidates)}")
        print(f"Transcripts approved: {len(self.results)}")

        if self.results and not dry_run:
            print(f"\nSaved to: ~/.council/knowledge/{self.elder_id}/youtube/")

        return self.results

    def _save_transcript(self, result: TranscriptResult) -> Path:
        """Save an approved transcript to the knowledge base."""
        knowledge_dir = get_knowledge_dir() / self.elder_id / "youtube"
        knowledge_dir.mkdir(parents=True, exist_ok=True)

        # Create safe filename
        safe_title = re.sub(r'[^\w\s-]', '', result.video.title)[:50].strip().replace(' ', '_')
        filepath = knowledge_dir / f"{safe_title}.txt"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {result.video.title}\n")
            f.write(f"Source: {result.video.url}\n")
            f.write(f"Channel: {result.video.channel}\n")
            f.write(f"Duration: {result.video.duration // 60} minutes\n")
            f.write(f"Views: {result.video.view_count:,}\n")
            f.write(f"Verification: {result.verification_status} ({result.confidence_score:.0%})\n")
            f.write(f"Approved: {datetime.now().isoformat()}\n")
            f.write(f"\n---\n\n")
            f.write(result.transcript)

        self.log(f"Saved: {filepath}")
        return filepath


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Multi-Agent YouTube Transcript Pipeline for Council of Elders"
    )

    parser.add_argument(
        "--elder",
        type=str,
        help="Elder ID to process (e.g., 'munger', 'aurelius')"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all configured elders"
    )

    parser.add_argument(
        "--max-videos",
        type=int,
        default=5,
        help="Maximum videos to process per elder (default: 5)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't save transcripts, just show what would be processed"
    )

    parser.add_argument(
        "--auto-approve",
        type=float,
        default=0.8,
        help="Auto-approve threshold (0-1, default: 0.8)"
    )

    parser.add_argument(
        "--no-review",
        action="store_true",
        help="Skip human review (use auto-approve threshold only)"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output"
    )

    args = parser.parse_args()

    if args.all:
        # All configured elders
        elders = [
            "munger", "buffett", "naval", "lauder",
            "aurelius", "buddha", "franklin", "laotzu",
            "thich", "kabatzinn",
            "jung", "branden",
            "kahneman", "tetlock", "klein", "meadows",
            "davinci", "rubin",
            "sun_tzu", "bruce_lee", "musashi", "greene",
            "clear", "oprah",
            "tubman", "hannibal", "boudicca", "genghis",
        ]
    elif args.elder:
        elders = [args.elder]
    else:
        parser.error("Please specify --elder or --all")

    all_results = {}

    for elder_id in elders:
        workflow = AgentWorkflow(
            elder_id=elder_id,
            verbose=not args.quiet,
        )

        results = workflow.run(
            max_videos=args.max_videos,
            auto_approve_threshold=args.auto_approve,
            require_human_review=not args.no_review,
            dry_run=args.dry_run,
        )

        all_results[elder_id] = results

    # Final summary
    print("\n" + "=" * 70)
    print("ALL ELDERS PROCESSED")
    print("=" * 70)

    total = sum(len(r) for r in all_results.values())
    print(f"\nTotal transcripts approved: {total}")

    for elder_id, results in all_results.items():
        if results:
            print(f"  {elder_id}: {len(results)} transcripts")


if __name__ == "__main__":
    main()
