"""
Deep Audit System

A thorough audit that:
1. Verifies source authenticity (is this actually from this person?)
2. Checks quote accuracy against known sources
3. Identifies missing high-value sources
4. Rates corpus completeness per elder
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

from council.config import get_knowledge_dir
from council.llm import chat


@dataclass
class SourceVeracity:
    """Veracity assessment for a single source."""
    filepath: Path
    elder_id: str
    source_type: str
    authenticity_score: int  # 0-100: Is this actually from this person?
    accuracy_notes: str
    questionable_content: list[str] = field(default_factory=list)
    verified_quotes: list[str] = field(default_factory=list)


@dataclass
class ElderCorpusAssessment:
    """Complete assessment of an elder's knowledge corpus."""
    elder_id: str
    elder_name: str
    total_files: int
    total_words: int
    corpus_completeness: int  # 0-100: How complete is their corpus?
    missing_sources: list[str]
    available_free_sources: list[str]
    recommended_paid_sources: list[str]
    veracity_issues: list[str]
    overall_grade: str  # A, B, C, D, F


# Known authoritative sources we should have
CANONICAL_SOURCES = {
    "munger": {
        "essential": [
            "Psychology of Human Misjudgment lecture",
            "USC Law School Commencement",
            "Daily Journal Annual Meeting transcripts",
            "Berkshire Annual Meeting Q&A (with Buffett)",
        ],
        "books": ["Poor Charlie's Almanack"],
        "free_available": [
            "YouTube lectures and interviews",
            "Berkshire meeting transcripts (partial)",
        ],
    },
    "buffett": {
        "essential": [
            "Shareholder Letters (1977-2023)",
            "Berkshire Annual Meeting Q&A",
            "University lectures (Florida, Georgia, Nebraska)",
        ],
        "books": ["The Essays of Warren Buffett"],
        "free_available": [
            "Shareholder letters (berkshirehathaway.com)",
            "CNBC interviews on YouTube",
        ],
    },
    "aurelius": {
        "essential": ["Meditations (complete)"],
        "books": [],
        "free_available": ["Gutenberg - Meditations (multiple translations)"],
    },
    "franklin": {
        "essential": [
            "Autobiography",
            "Poor Richard's Almanack",
            "The Way to Wealth",
            "Selected Letters",
        ],
        "books": [],
        "free_available": ["Gutenberg - all major works"],
    },
    "bruce_lee": {
        "essential": [
            "Pierre Berton Interview (1971)",
            "Longstreet TV appearances",
        ],
        "books": ["Tao of Jeet Kune Do", "Bruce Lee: Artist of Life", "Striking Thoughts"],
        "free_available": ["YouTube interviews and documentaries"],
    },
    "musashi": {
        "essential": ["Book of Five Rings", "Dokkodo (21 Precepts)"],
        "books": [],
        "free_available": ["Gutenberg - Book of Five Rings"],
    },
    "sun_tzu": {
        "essential": ["The Art of War (complete)"],
        "books": [],
        "free_available": ["Gutenberg - Art of War (Giles translation)"],
    },
    "buddha": {
        "essential": ["Dhammapada", "Key Suttas"],
        "books": [],
        "free_available": ["Gutenberg - Dhammapada", "Access to Insight - Suttas"],
    },
    "branden": {
        "essential": ["Six Pillars framework", "Self-esteem lectures"],
        "books": ["The Six Pillars of Self-Esteem", "The Psychology of Self-Esteem"],
        "free_available": ["YouTube lectures (limited)"],
    },
    "peterson": {
        "essential": [
            "Personality lectures (University of Toronto)",
            "Maps of Meaning lectures",
            "Biblical Series",
            "12 Rules content",
        ],
        "books": ["12 Rules for Life", "Beyond Order", "Maps of Meaning"],
        "free_available": ["YouTube - extensive lecture library"],
    },
    "clear": {
        "essential": ["Atomic Habits core concepts", "Habit formation framework"],
        "books": ["Atomic Habits"],
        "free_available": ["YouTube talks", "3-2-1 Newsletter archive", "jamesclear.com articles"],
    },
    "greene": {
        "essential": ["48 Laws framework", "Laws of Human Nature", "Mastery concepts"],
        "books": [
            "The 48 Laws of Power",
            "The Laws of Human Nature",
            "Mastery",
            "The 33 Strategies of War",
            "The Art of Seduction",
        ],
        "free_available": ["YouTube interviews", "Podcast appearances"],
    },
    "naval": {
        "essential": ["How to Get Rich tweetstorm", "Happiness philosophy", "Specific knowledge framework"],
        "books": [],
        "free_available": [
            "Almanack of Naval (free PDF)",
            "Navalmanack.com",
            "YouTube - Joe Rogan, Tim Ferriss",
            "Naval Podcast",
        ],
    },
    "rubin": {
        "essential": ["Creative philosophy", "Production approach"],
        "books": ["The Creative Act: A Way of Being"],
        "free_available": ["YouTube interviews", "Tetragrammaton Podcast", "Huberman Lab episode"],
    },
    "oprah": {
        "essential": ["Life lessons", "Interview wisdom", "Super Soul teachings"],
        "books": ["What I Know For Sure", "The Path Made Clear"],
        "free_available": ["YouTube - speeches, Super Soul Sunday clips"],
    },
    "thich": {
        "essential": ["Mindfulness teachings", "Breathing practices", "Interbeing concept"],
        "books": ["The Miracle of Mindfulness", "Peace Is Every Step", "The Heart of the Buddha's Teaching"],
        "free_available": ["YouTube dharma talks", "Plum Village archives"],
    },
    "jung": {
        "essential": ["Shadow concept", "Archetypes", "Individuation process", "Dream analysis"],
        "books": ["Man and His Symbols", "Memories, Dreams, Reflections", "The Red Book"],
        "free_available": ["BBC Face to Face interview", "Documentary footage"],
    },
    "kinrys": {
        "essential": ["Wing Girl Method", "Female perspective on attraction"],
        "books": [],
        "free_available": ["YouTube channel"],
    },
    "noble": {
        "essential": ["Attraction triggers", "Confidence building"],
        "books": [],
        "free_available": ["YouTube channel"],
    },
    "quinn": {
        "essential": ["Approach techniques", "Connection building"],
        "books": [],
        "free_available": ["YouTube channel", "TEDx talk"],
    },
    "ryan": {
        "essential": ["Standards/boundaries", "Red flag recognition", "Modern dating advice"],
        "books": [],
        "free_available": ["YouTube channel"],
    },
}


# Known famous quotes to verify
VERIFICATION_QUOTES = {
    "munger": [
        ("Invert, always invert", True),
        ("Show me the incentive and I will show you the outcome", True),
        ("I never allow myself to have an opinion on anything that I don't know the other side's argument better than they do", True),
    ],
    "buffett": [
        ("Rule No. 1: Never lose money. Rule No. 2: Never forget Rule No. 1", True),
        ("Be fearful when others are greedy, and greedy when others are fearful", True),
        ("Price is what you pay. Value is what you get", True),
    ],
    "aurelius": [
        ("You have power over your mind - not outside events", True),
        ("The happiness of your life depends upon the quality of your thoughts", True),
    ],
    "bruce_lee": [
        ("Be water, my friend", True),
        ("I fear not the man who has practiced 10,000 kicks once", True),
    ],
    "naval": [
        ("Seek wealth, not money or status", True),
        ("Specific knowledge is found by pursuing your genuine curiosity", True),
    ],
}


def verify_quotes_in_corpus(elder_id: str, content: str) -> tuple[list[str], list[str]]:
    """Check if known quotes appear in the corpus."""
    found = []
    missing = []

    if elder_id not in VERIFICATION_QUOTES:
        return [], []

    for quote, _ in VERIFICATION_QUOTES[elder_id]:
        # Check for approximate match (quotes may vary slightly)
        quote_words = quote.lower().split()[:5]
        pattern = r'\b' + r'\b.*\b'.join(re.escape(w) for w in quote_words) + r'\b'

        if re.search(pattern, content.lower()):
            found.append(quote)
        else:
            missing.append(quote)

    return found, missing


def assess_authenticity(content: str, elder_id: str, source_type: str) -> tuple[int, str, list[str]]:
    """Use LLM to assess if content is authentic to this elder."""

    # Sample the content
    sample = content[:2000] + "\n...\n" + content[-1000:] if len(content) > 3000 else content

    prompt = f"""Assess the authenticity of this text attributed to/about {elder_id}.

Source type: {source_type}
Sample:
---
{sample[:2500]}
---

Evaluate:
1. Does this sound like authentic content from/about this person?
2. Are there any obvious misattributions or errors?
3. Is the content substantive or filler?

Respond with:
SCORE: [0-100] (100 = definitely authentic, 0 = definitely fake/wrong person)
NOTES: [Brief assessment]
ISSUES: [Any specific problems, or "None"]"""

    try:
        messages = [{"role": "user", "content": prompt}]
        response = "".join(chat(messages, stream=True))

        score_match = re.search(r'SCORE:\s*(\d+)', response)
        score = int(score_match.group(1)) if score_match else 70

        notes_match = re.search(r'NOTES:\s*(.+?)(?=ISSUES:|$)', response, re.DOTALL)
        notes = notes_match.group(1).strip() if notes_match else ""

        issues_match = re.search(r'ISSUES:\s*(.+)', response, re.DOTALL)
        issues_text = issues_match.group(1).strip() if issues_match else "None"
        issues = [] if issues_text.lower() == "none" else [issues_text]

        return score, notes, issues
    except Exception as e:
        return 70, f"Assessment failed: {e}", []


def assess_elder_corpus(elder_id: str) -> ElderCorpusAssessment:
    """Perform complete assessment of an elder's corpus."""
    knowledge_dir = get_knowledge_dir() / elder_id

    if not knowledge_dir.exists():
        return ElderCorpusAssessment(
            elder_id=elder_id,
            elder_name=elder_id.title(),
            total_files=0,
            total_words=0,
            corpus_completeness=0,
            missing_sources=CANONICAL_SOURCES.get(elder_id, {}).get("essential", []),
            available_free_sources=CANONICAL_SOURCES.get(elder_id, {}).get("free_available", []),
            recommended_paid_sources=CANONICAL_SOURCES.get(elder_id, {}).get("books", []),
            veracity_issues=["No corpus exists"],
            overall_grade="F"
        )

    # Gather all files
    all_files = list(knowledge_dir.glob("**/*.txt"))
    total_words = 0
    all_content = ""
    veracity_issues = []

    for filepath in all_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            total_words += len(content.split())
            all_content += content + "\n"

    # Check for verified quotes
    found_quotes, missing_quotes = verify_quotes_in_corpus(elder_id, all_content)
    if missing_quotes:
        veracity_issues.append(f"Missing expected quotes: {missing_quotes[:2]}")

    # Determine what sources we have vs what we're missing
    canonical = CANONICAL_SOURCES.get(elder_id, {})
    essential = canonical.get("essential", [])
    books = canonical.get("books", [])
    free_available = canonical.get("free_available", [])

    # Estimate completeness based on what we have
    has_youtube = any("youtube" in str(f) for f in all_files)
    has_books = any(f.stem not in ["Key_Wisdom_and_Quotes"] and "youtube" not in str(f) for f in all_files)
    has_wisdom = any("Key_Wisdom" in f.stem for f in all_files)

    # Calculate completeness
    completeness_factors = []
    if has_wisdom:
        completeness_factors.append(20)  # Embedded wisdom
    if has_youtube:
        completeness_factors.append(30)  # YouTube content
    if has_books:
        completeness_factors.append(40)  # Books/primary sources
    if total_words > 50000:
        completeness_factors.append(10)  # Substantial corpus

    completeness = min(100, sum(completeness_factors))

    # Identify missing sources
    missing = []
    for source in essential:
        source_lower = source.lower()
        content_lower = all_content.lower()
        # Check if we seem to have this source
        key_words = source_lower.split()[:3]
        if not all(w in content_lower for w in key_words):
            missing.append(source)

    # Grade
    if completeness >= 80 and not veracity_issues:
        grade = "A"
    elif completeness >= 60:
        grade = "B"
    elif completeness >= 40:
        grade = "C"
    elif completeness >= 20:
        grade = "D"
    else:
        grade = "F"

    return ElderCorpusAssessment(
        elder_id=elder_id,
        elder_name=elder_id.replace("_", " ").title(),
        total_files=len(all_files),
        total_words=total_words,
        corpus_completeness=completeness,
        missing_sources=missing[:5],  # Top 5 missing
        available_free_sources=free_available,
        recommended_paid_sources=books,
        veracity_issues=veracity_issues,
        overall_grade=grade
    )


def run_deep_audit(verbose: bool = True) -> dict[str, ElderCorpusAssessment]:
    """Run deep audit on all elders."""

    if verbose:
        print("\n" + "=" * 70)
        print("DEEP CORPUS AUDIT - VERACITY & COMPLETENESS")
        print("=" * 70)

    all_elders = list(CANONICAL_SOURCES.keys())
    results = {}

    for elder_id in sorted(all_elders):
        if verbose:
            print(f"\n[{elder_id}] Assessing corpus...")

        assessment = assess_elder_corpus(elder_id)
        results[elder_id] = assessment

        if verbose:
            grade_colors = {"A": "green", "B": "blue", "C": "yellow", "D": "orange", "F": "red"}
            print(f"  Grade: {assessment.overall_grade} | "
                  f"Files: {assessment.total_files} | "
                  f"Words: {assessment.total_words:,} | "
                  f"Completeness: {assessment.corpus_completeness}%")

            if assessment.missing_sources:
                print(f"  Missing: {', '.join(assessment.missing_sources[:3])}")
            if assessment.veracity_issues:
                print(f"  Issues: {assessment.veracity_issues[0]}")

    # Summary
    if verbose:
        print("\n" + "=" * 70)
        print("AUDIT SUMMARY")
        print("=" * 70)

        grades = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for r in results.values():
            grades[r.overall_grade] += 1

        print(f"\nGrade Distribution:")
        for grade, count in sorted(grades.items()):
            bar = "█" * count
            print(f"  {grade}: {bar} ({count})")

        print(f"\nTop Recommendations:")
        # Find elders with most room for improvement
        by_completeness = sorted(results.values(), key=lambda x: x.corpus_completeness)
        for assessment in by_completeness[:5]:
            if assessment.available_free_sources:
                print(f"  {assessment.elder_name}: Add {assessment.available_free_sources[0]}")

        print(f"\nHigh-Value Paid Resources:")
        for assessment in results.values():
            if assessment.recommended_paid_sources and assessment.corpus_completeness < 70:
                print(f"  {assessment.elder_name}: {assessment.recommended_paid_sources[0]}")

    return results


def search_additional_sources(elder_id: str) -> list[str]:
    """Use LLM to suggest additional sources we may have missed."""

    prompt = f"""For {elder_id.replace('_', ' ').title()}, suggest additional FREE sources of their wisdom that could be obtained programmatically:

Consider:
1. Public domain texts
2. YouTube channels/videos with transcripts
3. Podcast appearances
4. Free articles/essays online
5. Archive.org materials
6. University lecture recordings
7. Interview transcripts

For each suggestion, provide:
- The specific source name
- Where to find it (URL pattern or platform)
- Why it's valuable

Focus on sources that can be automatically fetched (not behind paywalls).
List 3-5 specific suggestions."""

    try:
        messages = [{"role": "user", "content": prompt}]
        response = "".join(chat(messages, stream=True))
        return [response]
    except Exception as e:
        return [f"Search failed: {e}"]


if __name__ == "__main__":
    run_deep_audit()
