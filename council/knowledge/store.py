"""Knowledge store using ChromaDB for RAG."""

import hashlib
from pathlib import Path
from typing import Any

from council.config import get_knowledge_dir


class KnowledgeStore:
    """
    Local knowledge store using ChromaDB for retrieval-augmented generation.

    This allows adding custom documents (books, speeches, letters) for each elder
    to enhance their responses with specific knowledge.
    """

    def __init__(self):
        self._client = None
        self._collections: dict[str, Any] = {}

    @property
    def client(self):
        """Lazy-load ChromaDB client."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings

                persist_dir = get_knowledge_dir() / "chromadb"
                persist_dir.mkdir(parents=True, exist_ok=True)

                self._client = chromadb.PersistentClient(
                    path=str(persist_dir),
                    settings=Settings(anonymized_telemetry=False),
                )
            except ImportError:
                raise ImportError(
                    "ChromaDB is required for knowledge storage. "
                    "Install it with: pip install chromadb"
                )
        return self._client

    def get_collection(self, elder_id: str):
        """Get or create a collection for an elder."""
        if elder_id not in self._collections:
            self._collections[elder_id] = self.client.get_or_create_collection(
                name=f"elder_{elder_id}",
                metadata={"description": f"Knowledge base for {elder_id}"},
            )
        return self._collections[elder_id]

    def add_document(
        self,
        elder_id: str,
        content: str,
        metadata: dict | None = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> int:
        """
        Add a document to an elder's knowledge base.

        Args:
            elder_id: The elder this document is for
            content: The document text
            metadata: Optional metadata (source, title, etc.)
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks

        Returns:
            Number of chunks added
        """
        collection = self.get_collection(elder_id)

        # Simple chunking
        chunks = self._chunk_text(content, chunk_size, chunk_overlap)

        # Generate IDs based on content hash
        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_hash = hashlib.md5(chunk.encode()).hexdigest()[:12]
            chunk_id = f"{elder_id}_{chunk_hash}_{i}"
            ids.append(chunk_id)
            documents.append(chunk)
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata["chunk_index"] = i
            metadatas.append(chunk_metadata)

        collection.add(ids=ids, documents=documents, metadatas=metadatas)

        return len(chunks)

    def add_file(
        self,
        elder_id: str,
        file_path: str | Path,
        metadata: dict | None = None,
    ) -> int:
        """
        Add a text file to an elder's knowledge base.

        Args:
            elder_id: The elder this document is for
            file_path: Path to the text file
            metadata: Optional additional metadata

        Returns:
            Number of chunks added
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")

        file_metadata = metadata or {}
        file_metadata["source"] = str(file_path)
        file_metadata["filename"] = file_path.name

        return self.add_document(elder_id, content, file_metadata)

    def query(
        self,
        elder_id: str,
        query: str,
        n_results: int = 5,
    ) -> list[dict]:
        """
        Query an elder's knowledge base.

        Args:
            elder_id: The elder to query
            query: The search query
            n_results: Number of results to return

        Returns:
            List of matching documents with metadata
        """
        collection = self.get_collection(elder_id)

        results = collection.query(query_texts=[query], n_results=n_results)

        # Format results
        formatted = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                formatted.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })

        return formatted

    def get_context(self, elder_id: str, query: str, max_tokens: int = 2000) -> str:
        """
        Get relevant context for a query to include in the prompt.

        Args:
            elder_id: The elder to get context for
            query: The user's query
            max_tokens: Approximate max tokens of context

        Returns:
            Formatted context string
        """
        results = self.query(elder_id, query, n_results=5)

        if not results:
            return ""

        context_parts = []
        total_length = 0

        for result in results:
            content = result["content"]
            # Rough token estimate (4 chars per token)
            if total_length + len(content) / 4 > max_tokens:
                break
            context_parts.append(content)
            total_length += len(content) / 4

        if not context_parts:
            return ""

        return (
            "\n\n[Relevant knowledge from your writings and teachings:]\n\n"
            + "\n---\n".join(context_parts)
            + "\n\n[End of relevant knowledge]\n"
        )

    def list_documents(self, elder_id: str) -> list[dict]:
        """List all documents in an elder's knowledge base."""
        collection = self.get_collection(elder_id)
        results = collection.get()

        # Group by source
        sources = {}
        for i, metadata in enumerate(results.get("metadatas", [])):
            source = metadata.get("source", "unknown")
            if source not in sources:
                sources[source] = {"source": source, "chunks": 0, "metadata": metadata}
            sources[source]["chunks"] += 1

        return list(sources.values())

    def clear_elder(self, elder_id: str) -> None:
        """Clear all knowledge for an elder."""
        try:
            self.client.delete_collection(f"elder_{elder_id}")
            if elder_id in self._collections:
                del self._collections[elder_id]
        except Exception:
            pass  # Collection might not exist

    def _chunk_text(
        self, text: str, chunk_size: int, chunk_overlap: int
    ) -> list[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to end at a sentence or paragraph boundary
            if end < len(text):
                # Look for paragraph break
                para_break = text.rfind("\n\n", start, end)
                if para_break > start + chunk_size // 2:
                    end = para_break + 2
                else:
                    # Look for sentence break
                    for sep in [". ", ".\n", "! ", "? "]:
                        sent_break = text.rfind(sep, start, end)
                        if sent_break > start + chunk_size // 2:
                            end = sent_break + len(sep)
                            break

            chunks.append(text[start:end].strip())
            start = end - chunk_overlap

        return [c for c in chunks if c]


# Global instance
_knowledge_store: KnowledgeStore | None = None


def get_knowledge_store() -> KnowledgeStore:
    """Get the global knowledge store instance."""
    global _knowledge_store
    if _knowledge_store is None:
        _knowledge_store = KnowledgeStore()
    return _knowledge_store
