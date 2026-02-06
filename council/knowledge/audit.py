"""
Transcript Audit System

Thoroughly audits all knowledge base transcripts for:
- Accuracy and coherence
- Formatting consistency
- Common transcript issues (garbled text, repetition, missing content)
- Readability assessment
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from council.config import get_knowledge_dir
from council.llm import chat


@dataclass
class TranscriptIssue:
    """A single issue found in a transcript."""
    severity: Literal["error", "warning", "info"]
    category: str
    description: str
    line_number: int | None = None
    sample: str = ""


@dataclass
class TranscriptAudit:
    """Complete audit results for a single transcript."""
    filepath: Path
    elder_id: str
    source_type: str  # youtube, letters, podcasts, books, wisdom
    file_size: int
    line_count: int
    word_count: int
    issues: list[TranscriptIssue] = field(default_factory=list)
    quality_score: int = 0  # 0-100
    llm_assessment: str = ""
    passed: bool = True

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")


def check_garbled_text(content: str) -> list[TranscriptIssue]:
    """Check for garbled/corrupted text patterns."""
    issues = []
    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        # Check for excessive special characters
        special_ratio = len(re.findall(r'[^\w\s.,!?\'"-]', line)) / max(len(line), 1)
        if special_ratio > 0.3 and len(line) > 20:
            issues.append(TranscriptIssue(
                severity="warning",
                category="garbled_text",
                description="High ratio of special characters detected",
                line_number=i,
                sample=line[:80]
            ))

        # Check for repeated characters (stutter in auto-captions)
        if re.search(r'(.)\1{5,}', line):
            issues.append(TranscriptIssue(
                severity="warning",
                category="garbled_text",
                description="Repeated character sequence detected",
                line_number=i,
                sample=line[:80]
            ))

        # Check for word fragments typical of bad auto-captions
        if re.search(r'\b[a-z]{1,2}\b\s+\b[a-z]{1,2}\b\s+\b[a-z]{1,2}\b', line.lower()):
            # Multiple short words in a row might be fragmented speech
            short_words = re.findall(r'\b[a-z]{1,2}\b', line.lower())
            if len(short_words) > 5:
                issues.append(TranscriptIssue(
                    severity="info",
                    category="possible_fragmentation",
                    description="Multiple short word fragments detected",
                    line_number=i,
                    sample=line[:80]
                ))

    return issues


def check_repetition(content: str) -> list[TranscriptIssue]:
    """Check for excessive repetition (common in auto-captions)."""
    issues = []
    lines = content.split('\n')

    # Check for duplicate lines
    seen_lines = {}
    for i, line in enumerate(lines, 1):
        clean_line = line.strip().lower()
        if len(clean_line) > 20:  # Only check substantial lines
            if clean_line in seen_lines:
                issues.append(TranscriptIssue(
                    severity="warning",
                    category="duplicate_line",
                    description=f"Duplicate of line {seen_lines[clean_line]}",
                    line_number=i,
                    sample=line[:80]
                ))
            else:
                seen_lines[clean_line] = i

    # Check for repeated phrases within paragraphs
    paragraphs = content.split('\n\n')
    for para_idx, para in enumerate(paragraphs):
        words = para.lower().split()
        if len(words) > 10:
            # Check for 3+ word phrases repeated
            for i in range(len(words) - 6):
                phrase = ' '.join(words[i:i+3])
                remaining = ' '.join(words[i+3:])
                if phrase in remaining and len(phrase) > 10:
                    issues.append(TranscriptIssue(
                        severity="info",
                        category="repeated_phrase",
                        description=f"Phrase repeated: '{phrase}'",
                        line_number=None,
                        sample=para[:100]
                    ))
                    break  # Only report once per paragraph

    return issues


def check_formatting(content: str, source_type: str) -> list[TranscriptIssue]:
    """Check formatting consistency and structure."""
    issues = []
    lines = content.split('\n')

    # Check for header
    if not content.startswith('#'):
        issues.append(TranscriptIssue(
            severity="warning",
            category="missing_header",
            description="File doesn't start with a markdown header",
            line_number=1,
            sample=lines[0][:80] if lines else ""
        ))

    # Check for source attribution
    if 'Source:' not in content[:500] and 'source:' not in content[:500].lower():
        issues.append(TranscriptIssue(
            severity="info",
            category="missing_source",
            description="No source attribution found in header",
            line_number=None,
            sample=""
        ))

    # Check for reasonable paragraph structure
    very_long_paragraphs = []
    for i, para in enumerate(content.split('\n\n')):
        if len(para) > 3000:
            very_long_paragraphs.append(i + 1)

    if very_long_paragraphs:
        issues.append(TranscriptIssue(
            severity="info",
            category="long_paragraphs",
            description=f"Very long paragraphs at positions: {very_long_paragraphs[:5]}",
            line_number=None,
            sample=""
        ))

    # Check for leftover timestamp artifacts
    timestamp_patterns = [
        r'\d{2}:\d{2}:\d{2}',
        r'\[\d+:\d+\]',
        r'^\d+$',  # Standalone numbers (SRT sequence)
    ]

    for i, line in enumerate(lines, 1):
        for pattern in timestamp_patterns:
            if re.match(pattern, line.strip()):
                issues.append(TranscriptIssue(
                    severity="warning",
                    category="timestamp_artifact",
                    description="Leftover timestamp or sequence number",
                    line_number=i,
                    sample=line[:80]
                ))
                break

    return issues


def check_content_quality(content: str) -> list[TranscriptIssue]:
    """Check for content quality issues."""
    issues = []

    # Check minimum length
    word_count = len(content.split())
    if word_count < 100:
        issues.append(TranscriptIssue(
            severity="error",
            category="too_short",
            description=f"Content too short ({word_count} words)",
            line_number=None,
            sample=""
        ))

    # Check for placeholder content
    placeholder_patterns = [
        r'\[.*transcript.*\]',
        r'\[.*unavailable.*\]',
        r'\[.*error.*\]',
        r'transcript not available',
    ]

    for pattern in placeholder_patterns:
        if re.search(pattern, content.lower()):
            issues.append(TranscriptIssue(
                severity="error",
                category="placeholder_content",
                description="Contains placeholder or error text",
                line_number=None,
                sample=re.search(pattern, content.lower()).group()[:80]
            ))

    # Check for [Music] [Applause] etc. spam
    bracket_tags = re.findall(r'\[([^\]]+)\]', content)
    if len(bracket_tags) > 20:
        issues.append(TranscriptIssue(
            severity="warning",
            category="excessive_tags",
            description=f"Many bracket tags found ({len(bracket_tags)})",
            line_number=None,
            sample=str(bracket_tags[:5])
        ))

    return issues


def assess_with_llm(content: str, elder_id: str, filepath: Path) -> tuple[int, str]:
    """Use LLM to assess transcript quality. Returns (score, assessment)."""
    # Take a sample from different parts of the transcript
    lines = content.split('\n')
    total_lines = len(lines)

    sample_parts = []
    # Beginning (after header)
    start_idx = min(10, total_lines)
    sample_parts.append('\n'.join(lines[start_idx:start_idx+15]))

    # Middle
    mid_idx = total_lines // 2
    sample_parts.append('\n'.join(lines[mid_idx:mid_idx+15]))

    # End
    end_idx = max(0, total_lines - 20)
    sample_parts.append('\n'.join(lines[end_idx:end_idx+15]))

    sample = '\n\n[...]\n\n'.join(sample_parts)

    prompt = f"""You are auditing a transcript from the Council of Elders knowledge base.

Elder: {elder_id}
File: {filepath.name}

Sample from transcript (beginning, middle, end):
---
{sample[:3000]}
---

Please evaluate:
1. Is the text readable and coherent?
2. Does it appear to be actual content from/about this person?
3. Are there obvious transcription errors or garbled sections?
4. Is the formatting reasonable?

Respond with:
SCORE: [0-100]
ASSESSMENT: [2-3 sentence summary of quality and any issues]

Be strict - only high quality, readable transcripts should score above 70."""

    try:
        messages = [{"role": "user", "content": prompt}]
        response = "".join(chat(messages, stream=True))

        # Parse score
        score_match = re.search(r'SCORE:\s*(\d+)', response)
        score = int(score_match.group(1)) if score_match else 50

        # Parse assessment
        assessment_match = re.search(r'ASSESSMENT:\s*(.+)', response, re.DOTALL)
        assessment = assessment_match.group(1).strip() if assessment_match else response

        return score, assessment[:500]
    except Exception as e:
        return 50, f"LLM assessment failed: {e}"


def audit_transcript(filepath: Path, use_llm: bool = True) -> TranscriptAudit:
    """Perform complete audit on a single transcript."""
    # Determine elder and source type from path
    parts = filepath.relative_to(get_knowledge_dir()).parts
    elder_id = parts[0] if parts else "unknown"

    if len(parts) > 1 and parts[1] in ["youtube", "letters", "podcasts"]:
        source_type = parts[1]
    elif "Key_Wisdom" in filepath.name:
        source_type = "wisdom"
    else:
        source_type = "books"

    # Read content
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Basic stats
    file_size = filepath.stat().st_size
    line_count = len(content.split('\n'))
    word_count = len(content.split())

    # Collect all issues
    issues = []
    issues.extend(check_garbled_text(content))
    issues.extend(check_repetition(content))
    issues.extend(check_formatting(content, source_type))
    issues.extend(check_content_quality(content))

    # LLM assessment
    if use_llm:
        quality_score, llm_assessment = assess_with_llm(content, elder_id, filepath)
    else:
        quality_score = 70  # Default if no LLM
        llm_assessment = "LLM assessment skipped"

    # Determine pass/fail
    error_count = sum(1 for i in issues if i.severity == "error")
    passed = error_count == 0 and quality_score >= 50

    return TranscriptAudit(
        filepath=filepath,
        elder_id=elder_id,
        source_type=source_type,
        file_size=file_size,
        line_count=line_count,
        word_count=word_count,
        issues=issues,
        quality_score=quality_score,
        llm_assessment=llm_assessment,
        passed=passed
    )


def run_full_audit(
    elder_ids: list[str] | None = None,
    use_llm: bool = True,
    verbose: bool = True
) -> list[TranscriptAudit]:
    """Run audit on all transcripts in knowledge base."""
    knowledge_dir = get_knowledge_dir()

    if not knowledge_dir.exists():
        print("Knowledge directory not found!")
        return []

    # Find all transcript files
    all_files = list(knowledge_dir.glob("**/*.txt"))

    if elder_ids:
        all_files = [f for f in all_files if any(
            f.relative_to(knowledge_dir).parts[0] == eid for eid in elder_ids
        )]

    if verbose:
        print("\n" + "=" * 70)
        print("TRANSCRIPT AUDIT")
        print("=" * 70)
        print(f"\nFound {len(all_files)} transcript files to audit")
        print("-" * 70)

    results = []

    for i, filepath in enumerate(sorted(all_files)):
        rel_path = filepath.relative_to(knowledge_dir)

        if verbose:
            print(f"\n[{i+1}/{len(all_files)}] Auditing: {rel_path}")

        try:
            audit = audit_transcript(filepath, use_llm=use_llm)
            results.append(audit)

            if verbose:
                status = "✓ PASS" if audit.passed else "✗ FAIL"
                print(f"  {status} | Score: {audit.quality_score}/100 | "
                      f"Words: {audit.word_count:,} | "
                      f"Errors: {audit.error_count} | Warnings: {audit.warning_count}")

                if audit.llm_assessment and use_llm:
                    print(f"  Assessment: {audit.llm_assessment[:100]}...")

                # Show critical issues
                for issue in audit.issues:
                    if issue.severity == "error":
                        print(f"  ❌ ERROR: {issue.category} - {issue.description}")
                    elif issue.severity == "warning" and verbose:
                        print(f"  ⚠️  WARNING: {issue.category} - {issue.description}")

        except Exception as e:
            if verbose:
                print(f"  ❌ Failed to audit: {e}")

    # Summary report
    if verbose:
        generate_summary_report(results)

    return results


def generate_summary_report(results: list[TranscriptAudit]) -> str:
    """Generate a summary report of the audit."""
    report_lines = []

    report_lines.append("\n" + "=" * 70)
    report_lines.append("AUDIT SUMMARY REPORT")
    report_lines.append("=" * 70)

    # Overall stats
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    avg_score = sum(r.quality_score for r in results) / max(total, 1)
    total_words = sum(r.word_count for r in results)

    report_lines.append(f"\nOverall Results:")
    report_lines.append(f"  Total files audited: {total}")
    report_lines.append(f"  Passed: {passed} ({100*passed/max(total,1):.1f}%)")
    report_lines.append(f"  Failed: {failed} ({100*failed/max(total,1):.1f}%)")
    report_lines.append(f"  Average quality score: {avg_score:.1f}/100")
    report_lines.append(f"  Total word count: {total_words:,}")

    # By elder
    report_lines.append(f"\nBy Elder:")
    elder_stats = {}
    for r in results:
        if r.elder_id not in elder_stats:
            elder_stats[r.elder_id] = {"count": 0, "passed": 0, "words": 0, "score_sum": 0}
        elder_stats[r.elder_id]["count"] += 1
        elder_stats[r.elder_id]["passed"] += 1 if r.passed else 0
        elder_stats[r.elder_id]["words"] += r.word_count
        elder_stats[r.elder_id]["score_sum"] += r.quality_score

    for elder_id in sorted(elder_stats.keys()):
        stats = elder_stats[elder_id]
        avg = stats["score_sum"] / stats["count"]
        report_lines.append(
            f"  {elder_id:12} | Files: {stats['count']:2} | "
            f"Pass: {stats['passed']}/{stats['count']} | "
            f"Avg: {avg:.0f} | Words: {stats['words']:,}"
        )

    # By source type
    report_lines.append(f"\nBy Source Type:")
    source_stats = {}
    for r in results:
        if r.source_type not in source_stats:
            source_stats[r.source_type] = {"count": 0, "passed": 0, "score_sum": 0}
        source_stats[r.source_type]["count"] += 1
        source_stats[r.source_type]["passed"] += 1 if r.passed else 0
        source_stats[r.source_type]["score_sum"] += r.quality_score

    for source_type in sorted(source_stats.keys()):
        stats = source_stats[source_type]
        avg = stats["score_sum"] / stats["count"]
        report_lines.append(
            f"  {source_type:12} | Files: {stats['count']:2} | "
            f"Pass: {stats['passed']}/{stats['count']} | Avg score: {avg:.0f}"
        )

    # Common issues
    report_lines.append(f"\nMost Common Issues:")
    issue_counts = {}
    for r in results:
        for issue in r.issues:
            key = f"{issue.severity}:{issue.category}"
            issue_counts[key] = issue_counts.get(key, 0) + 1

    for key, count in sorted(issue_counts.items(), key=lambda x: -x[1])[:10]:
        severity, category = key.split(":")
        report_lines.append(f"  {severity:8} {category:25} ({count} occurrences)")

    # Failed files
    failed_files = [r for r in results if not r.passed]
    if failed_files:
        report_lines.append(f"\nFailed Files ({len(failed_files)}):")
        for r in failed_files[:20]:
            report_lines.append(f"  ✗ {r.filepath.relative_to(get_knowledge_dir())}")
            report_lines.append(f"    Score: {r.quality_score}, Errors: {r.error_count}")
            if r.llm_assessment:
                report_lines.append(f"    {r.llm_assessment[:80]}...")

    # Low scoring files (passed but borderline)
    low_scoring = [r for r in results if r.passed and r.quality_score < 60]
    if low_scoring:
        report_lines.append(f"\nLow Scoring Files (review recommended):")
        for r in sorted(low_scoring, key=lambda x: x.quality_score)[:10]:
            report_lines.append(
                f"  ⚠️  {r.filepath.relative_to(get_knowledge_dir())} "
                f"(score: {r.quality_score})"
            )

    report_lines.append("\n" + "=" * 70)

    report = '\n'.join(report_lines)
    print(report)

    # Save report
    report_path = get_knowledge_dir() / "audit_report.txt"
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")

    return report


def fix_common_issues(filepath: Path, dry_run: bool = True) -> list[str]:
    """Attempt to fix common formatting issues in a transcript."""
    fixes_made = []

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Remove leftover timestamp lines
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        # Skip standalone timestamps
        if re.match(r'^\d{2}:\d{2}:\d{2}', line.strip()):
            fixes_made.append(f"Removed timestamp line: {line[:40]}")
            continue
        # Skip standalone numbers (SRT sequence)
        if re.match(r'^\d+$', line.strip()):
            fixes_made.append(f"Removed sequence number: {line}")
            continue
        cleaned_lines.append(line)

    content = '\n'.join(cleaned_lines)

    # Remove excessive blank lines
    while '\n\n\n' in content:
        content = content.replace('\n\n\n', '\n\n')
        if "blank lines" not in str(fixes_made):
            fixes_made.append("Normalized excessive blank lines")

    # Remove [Music] and similar tags
    tag_pattern = r'\[(?:Music|Applause|Laughter|Silence)\]'
    if re.search(tag_pattern, content, re.IGNORECASE):
        content = re.sub(tag_pattern, '', content, flags=re.IGNORECASE)
        fixes_made.append("Removed audio annotation tags")

    if content != original and not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        fixes_made.append("Changes saved to file")
    elif content != original:
        fixes_made.append("(dry run - changes not saved)")

    return fixes_made


if __name__ == "__main__":
    import sys

    # Parse simple command line args
    use_llm = "--no-llm" not in sys.argv
    elder_filter = None

    for i, arg in enumerate(sys.argv):
        if arg == "--elder" and i + 1 < len(sys.argv):
            elder_filter = [sys.argv[i + 1]]

    print(f"Running audit (LLM: {'enabled' if use_llm else 'disabled'})...")
    run_full_audit(elder_ids=elder_filter, use_llm=use_llm)
