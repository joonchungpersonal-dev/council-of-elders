"""Background enrichment orchestrator for nominated/custom elders.

Runs in a background thread (via TaskManager) to research a person:
1. Biography (Wikipedia + LLM)
2. YouTube search → download → vet → save transcripts
3. ChromaDB indexing (with audit metadata)
4. Book discovery (with Open Library verification)
5. Quote verification (fire-and-forget background task)
"""

import logging

from council.config import get_config_value
from council.knowledge.biography import get_biography
from council.knowledge.youtube import (
    clean_transcript,
    get_video_info,
    save_transcript,
    search_youtube,
    vet_transcript,
)
from council.tasks import TaskProgress

logger = logging.getLogger(__name__)


def enrich_elder(
    *,
    elder_id: str,
    name: str,
    expertise: str,
    progress: TaskProgress,
) -> dict:
    """Research and enrich an elder's knowledge base.

    Designed to run inside TaskManager.submit().
    Updates *progress* throughout so the frontend can poll for status.

    Returns a summary dict of what was accomplished.
    """
    max_videos = get_config_value("enrichment_youtube_max", 5)
    result = {
        "biography": None,
        "youtube_transcripts": 0,
        "books_discovered": 0,
    }

    # ---- Step 1: Biography ------------------------------------------------
    progress.message = f"Fetching biography for {name}..."
    progress.progress = 0.05
    progress.substeps = [{"step": "biography", "status": "running"}]

    try:
        bio = get_biography(name, expertise)
        result["biography"] = bio
        progress.substeps[0]["status"] = "done"
    except Exception as e:
        progress.substeps[0]["status"] = f"failed: {e}"

    # ---- Step 2: YouTube search + transcripts -----------------------------
    progress.message = f"Searching YouTube for {name}..."
    progress.progress = 0.10
    progress.substeps.append({"step": "youtube_search", "status": "running"})

    queries = [
        f'"{name}" interview',
        f'"{name}" {expertise}',
        f'"{name}" lecture',
    ]
    video_urls: list[str] = []
    for q in queries:
        found = search_youtube(q, max_results=3)
        for url in found:
            if url not in video_urls:
                video_urls.append(url)
        if len(video_urls) >= max_videos:
            break

    video_urls = video_urls[:max_videos]
    progress.substeps[-1] = {
        "step": "youtube_search",
        "status": "done",
        "found": len(video_urls),
    }

    # Process each video
    saved_count = 0
    # Use the canonical elder ID for storage (strip "custom_" prefix if present)
    storage_id = elder_id.replace("custom_", "").replace("nominated_", "")

    for i, url in enumerate(video_urls):
        step_progress = 0.15 + (0.60 * (i / max(len(video_urls), 1)))
        progress.progress = step_progress
        progress.message = f"Processing video {i + 1}/{len(video_urls)}..."
        progress.substeps.append({
            "step": f"video_{i + 1}",
            "status": "running",
            "url": url,
        })

        try:
            video_info = get_video_info(url)
            if not video_info:
                progress.substeps[-1]["status"] = "skipped: no transcript"
                continue

            video_info.transcript = clean_transcript(video_info.transcript)

            is_valid, _ = vet_transcript(
                video_info.transcript, storage_id, video_info.title
            )
            if not is_valid:
                progress.substeps[-1]["status"] = "skipped: failed vetting"
                continue

            saved_path = save_transcript(storage_id, video_info)

            # Run rule-based transcript audit (no LLM — already vetted above)
            audit_passed = True
            quality_score = 70
            try:
                from council.knowledge.audit import audit_transcript

                audit = audit_transcript(saved_path, use_llm=False)
                audit_passed = audit.passed
                quality_score = audit.quality_score
                progress.substeps[-1]["audit_passed"] = audit_passed
                progress.substeps[-1]["quality_score"] = quality_score
                if not audit_passed:
                    progress.substeps[-1]["low_quality"] = True
            except Exception:
                pass

            # Index in ChromaDB with audit metadata
            try:
                from council.knowledge.store import get_knowledge_store

                store = get_knowledge_store()
                store.add_document(
                    storage_id,
                    video_info.transcript,
                    metadata={
                        "source": video_info.url,
                        "type": "youtube",
                        "channel": video_info.channel,
                        "title": video_info.title,
                        "duration": str(video_info.duration // 60),
                        "audit_passed": str(audit_passed),
                        "quality_score": str(quality_score),
                    },
                )
            except Exception:
                pass  # ChromaDB optional

            saved_count += 1
            progress.substeps[-1]["status"] = "done"
            progress.substeps[-1]["title"] = video_info.title

        except Exception as e:
            progress.substeps[-1]["status"] = f"error: {e}"

    result["youtube_transcripts"] = saved_count

    # ---- Step 3: Book discovery -------------------------------------------
    progress.progress = 0.85
    progress.message = f"Discovering books by and about {name}..."
    progress.substeps.append({"step": "books", "status": "running"})

    try:
        from council.knowledge.books import discover_books

        books = discover_books(name, expertise)
        result["books_discovered"] = len(books)
        result["books"] = books
        progress.substeps[-1] = {
            "step": "books",
            "status": "done",
            "count": len(books),
        }
    except Exception as e:
        progress.substeps[-1] = {"step": "books", "status": f"failed: {e}"}

    # ---- Step 4: Quote verification (fire-and-forget) ---------------------
    try:
        from council.knowledge.verify_quotes import verify_elder_quotes
        from council.tasks import get_task_manager

        tm = get_task_manager()
        tm.submit(
            verify_elder_quotes,
            task_id=f"quotes_{elder_id}",
            elder_id=elder_id,
            elder_name=name,
        )
        progress.substeps.append({"step": "quote_verification", "status": "submitted"})
    except Exception as e:
        logger.debug("Quote verification kick-off failed: %s", e)

    # ---- Done -------------------------------------------------------------
    progress.progress = 1.0
    progress.message = f"Enrichment complete for {name}"

    # Collect transcript audit summaries
    transcript_audits = [
        {
            "url": s.get("url", ""),
            "title": s.get("title", ""),
            "audit_passed": s.get("audit_passed", True),
            "quality_score": s.get("quality_score", 70),
        }
        for s in progress.substeps
        if s.get("step", "").startswith("video_") and s.get("status") == "done"
    ]

    # Update the custom elder file if it exists
    try:
        from council.elders.custom import update_custom_elder

        update_custom_elder(elder_id, {
            "biography": result.get("biography", {}),
            "books": result.get("books", []),
            "enrichment": {
                "status": "completed",
                "youtube_transcripts": saved_count,
                "books_discovered": result.get("books_discovered", 0),
                "transcript_audits": transcript_audits,
            },
        })
    except Exception:
        pass

    return result
