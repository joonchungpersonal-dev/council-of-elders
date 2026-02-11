"""Multi-agent quote cross-check system.

Three-stage pipeline:
1. extract_quotes — LLM extracts direct quotes from source material
2. attribution_agent — Round 1: identifies likely original source for each quote
3. skeptic_agent — Round 2: challenges attributions, returns verdict

Entry point: verify_elder_quotes() (designed for TaskManager.submit()).
"""

import json
import logging
import re
from pathlib import Path

from council.config import get_knowledge_dir
from council.llm import chat
from council.tasks import TaskProgress

logger = logging.getLogger(__name__)


def extract_quotes(text: str, elder_name: str, max_quotes: int = 10) -> list[dict]:
    """Extract direct quotes attributed to a person from text.

    Returns list of {"quote": str, "context": str}.
    """
    sample = text[:6000]
    prompt = (
        f"Extract up to {max_quotes} direct quotes attributed to {elder_name} "
        f"from the following text. Only include quotes that are presented as direct "
        f"speech or writing by {elder_name}.\n\n"
        f"Text:\n---\n{sample}\n---\n\n"
        f"For each quote, provide:\n"
        f"QUOTE: [the exact quote]\n"
        f"CONTEXT: [1-sentence context of where/when this was said]\n\n"
        f"If no direct quotes are found, respond with: NO QUOTES FOUND"
    )

    try:
        messages = [{"role": "user", "content": prompt}]
        response = "".join(chat(messages, stream=True))

        if "NO QUOTES FOUND" in response.upper():
            return []

        quotes = []
        for m in re.finditer(
            r"QUOTE:\s*(.+?)(?=\nCONTEXT:)",
            response,
            re.DOTALL,
        ):
            quote_text = m.group(1).strip().strip('"').strip("'")
            # Find the matching CONTEXT line
            ctx_match = re.search(
                r"CONTEXT:\s*(.+?)(?=\nQUOTE:|\Z)",
                response[m.end():],
                re.DOTALL,
            )
            context = ctx_match.group(1).strip() if ctx_match else ""
            if quote_text and len(quote_text) > 10:
                quotes.append({"quote": quote_text, "context": context})

        return quotes[:max_quotes]
    except Exception as e:
        logger.debug("Quote extraction failed: %s", e)
        return []


def attribution_agent(quotes: list[dict], elder_name: str) -> list[dict]:
    """Round 1: For each quote, identify the likely original source.

    Returns the quotes list with added "attribution" and "source" fields.
    """
    if not quotes:
        return quotes

    quote_list = "\n".join(
        f'{i+1}. "{q["quote"]}"'
        for i, q in enumerate(quotes)
    )

    prompt = (
        f"You are an attribution specialist. For each quote below attributed to "
        f"{elder_name}, identify the most likely original source (book, speech, "
        f"interview, letter, etc.).\n\n"
        f"Quotes:\n{quote_list}\n\n"
        f"For each quote, respond:\n"
        f"[number]. SOURCE: [book/speech/interview title or 'unknown']\n"
        f"ATTRIBUTION: [confirmed/likely/uncertain/misattributed]\n"
        f"NOTES: [brief explanation]\n"
    )

    try:
        messages = [{"role": "user", "content": prompt}]
        response = "".join(chat(messages, stream=True))

        # Parse attributions back onto quotes
        for i, q in enumerate(quotes):
            pattern = rf"{i+1}\.\s*SOURCE:\s*(.+?)(?=\n)"
            source_match = re.search(pattern, response)
            attr_match = re.search(
                rf"{i+1}\.\s*.*?ATTRIBUTION:\s*(\w+)",
                response,
                re.DOTALL,
            )
            notes_match = re.search(
                rf"{i+1}\.\s*.*?NOTES:\s*(.+?)(?=\n\d+\.|\Z)",
                response,
                re.DOTALL,
            )

            q["source"] = source_match.group(1).strip() if source_match else "unknown"
            q["attribution"] = attr_match.group(1).strip().lower() if attr_match else "uncertain"
            q["attribution_notes"] = notes_match.group(1).strip() if notes_match else ""

        return quotes
    except Exception as e:
        logger.debug("Attribution agent failed: %s", e)
        for q in quotes:
            q.setdefault("source", "unknown")
            q.setdefault("attribution", "uncertain")
            q.setdefault("attribution_notes", "Attribution check failed")
        return quotes


def skeptic_agent(attributed_quotes: list[dict], elder_name: str) -> list[dict]:
    """Round 2: Challenge attributions and return final verdict.

    Adds "verdict" (confirmed/disputed/uncertain) and "skeptic_notes" to each quote.
    """
    if not attributed_quotes:
        return attributed_quotes

    quote_summaries = "\n".join(
        f'{i+1}. "{q["quote"]}" — attributed to: {q.get("source", "unknown")} '
        f'(confidence: {q.get("attribution", "uncertain")})'
        for i, q in enumerate(attributed_quotes)
    )

    prompt = (
        f"You are a skeptical fact-checker. Review these quotes attributed to "
        f"{elder_name} and challenge each attribution.\n\n"
        f"For each quote, consider:\n"
        f"- Is this quote commonly misattributed?\n"
        f"- Does the language/style match {elder_name}'s known writing style?\n"
        f"- Is the claimed source plausible?\n\n"
        f"Quotes:\n{quote_summaries}\n\n"
        f"For each, respond:\n"
        f"[number]. VERDICT: [confirmed/disputed/uncertain]\n"
        f"REASON: [1-sentence explanation]\n"
    )

    try:
        messages = [{"role": "user", "content": prompt}]
        response = "".join(chat(messages, stream=True))

        for i, q in enumerate(attributed_quotes):
            verdict_match = re.search(
                rf"{i+1}\.\s*VERDICT:\s*(\w+)",
                response,
            )
            reason_match = re.search(
                rf"{i+1}\.\s*.*?REASON:\s*(.+?)(?=\n\d+\.|\Z)",
                response,
                re.DOTALL,
            )

            q["verdict"] = verdict_match.group(1).strip().lower() if verdict_match else "uncertain"
            q["skeptic_notes"] = reason_match.group(1).strip() if reason_match else ""

        return attributed_quotes
    except Exception as e:
        logger.debug("Skeptic agent failed: %s", e)
        for q in attributed_quotes:
            q.setdefault("verdict", "uncertain")
            q.setdefault("skeptic_notes", "Skeptic check failed")
        return attributed_quotes


def verify_elder_quotes(
    *,
    elder_id: str,
    elder_name: str,
    progress: TaskProgress,
) -> dict:
    """Main entry point for quote verification.

    Gathers text from knowledge dir, runs the three-stage pipeline,
    saves results and updates elder metadata.
    """
    progress.message = f"Verifying quotes for {elder_name}..."
    progress.progress = 0.1

    # Gather source text
    knowledge_dir = get_knowledge_dir() / elder_id.replace("custom_", "").replace("nominated_", "")
    all_text = []

    for subdir in ("sources", "youtube"):
        target = knowledge_dir / subdir
        if target.exists():
            for txt_file in sorted(target.glob("*.txt"))[:10]:
                try:
                    all_text.append(txt_file.read_text(encoding="utf-8", errors="replace"))
                except Exception:
                    pass

    if not all_text:
        progress.message = "No source material found for quote verification"
        return {"quotes_checked": 0, "status": "no_material"}

    combined_text = "\n\n---\n\n".join(all_text)

    # Stage 1: Extract quotes
    progress.message = "Extracting quotes..."
    progress.progress = 0.3
    quotes = extract_quotes(combined_text, elder_name)

    if not quotes:
        progress.message = "No direct quotes found to verify"
        return {"quotes_checked": 0, "status": "no_quotes"}

    # Stage 2: Attribution
    progress.message = f"Checking attribution for {len(quotes)} quotes..."
    progress.progress = 0.5
    quotes = attribution_agent(quotes, elder_name)

    # Stage 3: Skeptic review
    progress.message = "Running skeptic review..."
    progress.progress = 0.7
    quotes = skeptic_agent(quotes, elder_name)

    # Save results
    progress.message = "Saving verification results..."
    progress.progress = 0.9

    results = {
        "elder_id": elder_id,
        "elder_name": elder_name,
        "quotes_checked": len(quotes),
        "quotes": quotes,
        "summary": {
            "confirmed": sum(1 for q in quotes if q.get("verdict") == "confirmed"),
            "disputed": sum(1 for q in quotes if q.get("verdict") == "disputed"),
            "uncertain": sum(1 for q in quotes if q.get("verdict") == "uncertain"),
        },
    }

    # Save to file
    output_path = knowledge_dir / "quote_verification.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Update elder metadata
    try:
        from council.elders.custom import update_custom_elder

        update_custom_elder(elder_id, {
            "quote_verification": results["summary"],
        })
    except Exception:
        pass

    progress.message = (
        f"Quote verification complete: {results['summary']['confirmed']} confirmed, "
        f"{results['summary']['disputed']} disputed, "
        f"{results['summary']['uncertain']} uncertain"
    )

    return results
