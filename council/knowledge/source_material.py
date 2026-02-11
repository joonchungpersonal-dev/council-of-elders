"""Source material ingestion for custom elders.

Saves raw files to ~/.council/knowledge/{elder_id}/sources/,
indexes text into ChromaDB (if available), and updates elder metadata.
Falls back gracefully: even without ChromaDB, raw .txt files in the
sources directory are picked up by get_elder_knowledge()'s glob fallback.
"""

import json
import logging
import re
import time
from pathlib import Path

from council.config import get_knowledge_dir
from council.llm import chat

logger = logging.getLogger(__name__)


def vet_source_material(elder_id: str, text: str, source_name: str) -> dict:
    """Use LLM to assess the genuineness and quality of uploaded source material.

    Returns {"confidence": int, "assessment": str, "warnings": list[str]}.
    """
    sample = text[:3000]
    prompt = (
        f"You are evaluating source material uploaded for the knowledge base of "
        f"'{elder_id}'. The material is named '{source_name}'.\n\n"
        f"Text sample:\n---\n{sample}\n---\n\n"
        f"Evaluate this text for:\n"
        f"1. Does it appear to be genuine writing/speech by or about this person?\n"
        f"2. Are there misattributed quotes or fabricated content?\n"
        f"3. Is the style consistent and coherent?\n"
        f"4. Any red flags (spam, nonsense, AI-generated filler, promotional content)?\n\n"
        f"Respond in EXACTLY this format:\n"
        f"CONFIDENCE: [0-100]\n"
        f"ASSESSMENT: [2-3 sentence assessment]\n"
        f"WARNINGS: [comma-separated list, or 'none']"
    )

    try:
        messages = [{"role": "user", "content": prompt}]
        response = "".join(chat(messages, stream=True))

        confidence = 50
        m = re.search(r"CONFIDENCE:\s*(\d+)", response)
        if m:
            confidence = max(0, min(100, int(m.group(1))))

        assessment = ""
        m = re.search(r"ASSESSMENT:\s*(.+?)(?=\nWARNINGS:|\Z)", response, re.DOTALL)
        if m:
            assessment = m.group(1).strip()

        warnings: list[str] = []
        m = re.search(r"WARNINGS:\s*(.+)", response, re.DOTALL)
        if m:
            raw = m.group(1).strip()
            if raw.lower() != "none":
                warnings = [w.strip() for w in raw.split(",") if w.strip()]

        return {"confidence": confidence, "assessment": assessment, "warnings": warnings}
    except Exception as e:
        logger.debug("Source material vetting failed: %s", e)
        return {"confidence": 50, "assessment": "Vetting unavailable", "warnings": []}


def get_sources_dir(elder_id: str) -> Path:
    """Return (and create) the sources directory for an elder."""
    sources_dir = get_knowledge_dir() / elder_id / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)
    return sources_dir


def extract_file_text(file_path: Path) -> str:
    """Extract plain text from a .txt, .md, or .pdf file."""
    suffix = file_path.suffix.lower()

    if suffix in (".txt", ".md"):
        return file_path.read_text(encoding="utf-8", errors="replace")

    if suffix == ".pdf":
        try:
            import fitz  # pymupdf

            doc = fitz.open(str(file_path))
            pages = [page.get_text() for page in doc]
            doc.close()
            return "\n\n".join(pages)
        except ImportError:
            raise ImportError(
                "PDF support requires pymupdf. "
                "Install it with: pip install 'council-of-elders[pdf]'"
            )

    raise ValueError(f"Unsupported file type: {suffix}")


def index_text_for_elder(
    elder_id: str,
    text: str,
    source_name: str,
    extra_metadata: dict | None = None,
) -> int:
    """Index text into ChromaDB via KnowledgeStore.add_document().

    Returns the number of chunks added, or 0 if ChromaDB is unavailable.
    """
    if not text.strip():
        return 0

    try:
        from council.knowledge.store import get_knowledge_store

        store = get_knowledge_store()
        metadata = {"source": source_name}
        if extra_metadata:
            metadata.update(extra_metadata)
        return store.add_document(elder_id, text, metadata=metadata)
    except ImportError:
        return 0
    except Exception:
        return 0


def ingest_source_material(
    elder_id: str,
    source_text: str = "",
    files: list[tuple[str, bytes]] | None = None,
) -> dict:
    """Main entry point: save source material and index it.

    Args:
        elder_id: The custom elder ID.
        source_text: Pasted text from the user.
        files: List of (filename, file_bytes) tuples.

    Returns:
        Dict with keys: files_saved, chunks_indexed, source_materials.
    """
    sources_dir = get_sources_dir(elder_id)
    saved_files: list[dict] = []
    total_chunks = 0

    # 1. Save and index pasted text
    if source_text and source_text.strip():
        filename = f"pasted_{int(time.time())}.txt"
        filepath = sources_dir / filename
        filepath.write_text(source_text, encoding="utf-8")

        vetting = vet_source_material(elder_id, source_text, filename)
        entry = {
            "name": filename,
            "type": "pasted_text",
            "confidence": vetting["confidence"],
            "assessment": vetting["assessment"],
            "warnings": vetting["warnings"],
        }
        saved_files.append(entry)
        total_chunks += index_text_for_elder(
            elder_id, source_text, filename,
            extra_metadata={"vetting_confidence": vetting["confidence"]},
        )

    # 2. Save and index uploaded files
    for filename, file_bytes in (files or []):
        # Sanitize filename
        safe_name = Path(filename).name
        filepath = sources_dir / safe_name
        filepath.write_bytes(file_bytes)

        try:
            text = extract_file_text(filepath)
        except (ImportError, ValueError):
            # PDF not supported or unsupported file type — raw file still saved
            saved_files.append({"name": safe_name, "type": "uploaded_file"})
            continue

        vetting = vet_source_material(elder_id, text, safe_name)
        entry = {
            "name": safe_name,
            "type": "uploaded_file",
            "confidence": vetting["confidence"],
            "assessment": vetting["assessment"],
            "warnings": vetting["warnings"],
        }
        saved_files.append(entry)
        total_chunks += index_text_for_elder(
            elder_id, text, safe_name,
            extra_metadata={"vetting_confidence": vetting["confidence"]},
        )

    # 3. Update elder JSON metadata with source_materials list
    _update_elder_sources(elder_id, saved_files)

    # 4. Compute vetting summary
    confidences = [f["confidence"] for f in saved_files if "confidence" in f]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    low_confidence_files = [
        f["name"] for f in saved_files
        if f.get("confidence", 100) < 50
    ]

    return {
        "files_saved": len(saved_files),
        "chunks_indexed": total_chunks,
        "source_materials": saved_files,
        "vetting": {
            "average_confidence": round(avg_confidence, 1),
            "low_confidence_files": low_confidence_files,
        },
    }


def _update_elder_sources(elder_id: str, new_sources: list[dict]) -> None:
    """Append source material entries to the elder's JSON file."""
    from council.elders.custom import get_custom_elder_data, update_custom_elder

    data = get_custom_elder_data(elder_id)
    if data is None:
        return

    existing = data.get("source_materials", [])
    existing.extend(new_sources)
    update_custom_elder(elder_id, {"source_materials": existing})
