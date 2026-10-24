from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional
import chromadb
from app.core.config import settings

# Ensure persistent storage directory exists
settings.CHROMA_PERSIST_DIRECTORY.mkdir(parents=True, exist_ok=True)

_client = chromadb.PersistentClient(path=str(settings.CHROMA_PERSIST_DIRECTORY))
_collection = _client.get_or_create_collection(
    name="youtube_transcripts",
    metadata={"hnsw:space": "cosine"},
)


def get_collection() -> chromadb.Collection:
    """Returns the ChromaDB collection instance."""
    return _collection


def add_chunks(
    video_id: str,
    chunks: List[Dict[str, Any]],
    embeddings: List[List[float]],
) -> None:
    """
    Persists transcript chunks with metadata into ChromaDB.
    Uses upsert so re-indexing safely updates existing chunk documents.
    """
    ids = [f"{video_id}_{idx}" for idx in range(len(chunks))]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [
        {
            "video_id": video_id,
            "start": float(chunk["start"]),
            "end": float(chunk["end"]),
            "chunk_index": idx,
        }
        for idx, chunk in enumerate(chunks)
    ]

    _collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def search_chunks(
    query_embedding: List[float],
    n_results: int = 4,
    video_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes cosine similarity search over indexed chunks.
    Optionally scopes results to a specific video ID.
    """
    where_filter = {"video_id": video_id} if video_id else None

    return _collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )


def get_all_indexed_videos() -> Dict[str, int]:
    """Inspects ChromaDB collection metadatas and returns video IDs with their chunk count."""
    records = _collection.get(include=["metadatas"])
    metadatas = records.get("metadatas", []) or []

    counts: Counter = Counter()
    for meta in metadatas:
        if meta and "video_id" in meta:
            counts[meta["video_id"]] += 1

    return dict(counts)


def delete_video(video_id: str) -> int:
    """Removes all indexed chunks for a given video ID and returns the count removed."""
    records = _collection.get(
        where={"video_id": video_id},
        include=["metadatas"],
    )
    ids = records.get("ids", [])
    if ids:
        _collection.delete(ids=ids)
    return len(ids)
