from typing import Any, Dict, List
from app.core.config import settings


def create_chunks(
    transcript_segments: List[Dict[str, Any]],
    chunk_size: int = settings.CHUNK_SIZE,
    chunk_overlap: int = settings.CHUNK_OVERLAP,
) -> List[Dict[str, Any]]:
    """
    Partitions timestamped transcript segments into overlapping chunks.
    Preserves exact start and end timestamps from the underlying snippets.

    Returns:
        List of dicts:
        [
            {
                "text": "...",
                "start": float,
                "end": float,
                "token_estimate": int
            },
            ...
        ]
    """
    if not transcript_segments:
        return []

    chunks: List[Dict[str, Any]] = []
    current_snippets: List[Dict[str, Any]] = []
    current_length = 0

    for snippet in transcript_segments:
        text = snippet.get("text", "").strip()
        if not text:
            continue

        current_snippets.append(snippet)
        current_length += len(text) + 1  # count space separator

        if current_length >= chunk_size:
            chunk_start = current_snippets[0]["start"]
            last_snippet = current_snippets[-1]
            chunk_end = round(
                last_snippet["start"] + last_snippet.get("duration", 0.0), 2
            )
            merged_text = " ".join(s["text"].strip() for s in current_snippets)

            chunks.append(
                {
                    "text": merged_text,
                    "start": round(chunk_start, 2),
                    "end": chunk_end,
                    "token_estimate": len(merged_text.split()),
                }
            )

            # Build overlapping tail
            overlap_snippets: List[Dict[str, Any]] = []
            overlap_len = 0

            for s in reversed(current_snippets):
                s_len = len(s.get("text", "").strip()) + 1
                if overlap_len + s_len > chunk_overlap:
                    break
                overlap_snippets.insert(0, s)
                overlap_len += s_len

            current_snippets = overlap_snippets
            current_length = overlap_len

    # Add final remainder chunk
    if current_snippets:
        chunk_start = current_snippets[0]["start"]
        last_snippet = current_snippets[-1]
        chunk_end = round(
            last_snippet["start"] + last_snippet.get("duration", 0.0), 2
        )
        merged_text = " ".join(s["text"].strip() for s in current_snippets)

        # Avoid creating tiny redundant duplicate chunks if overlap was almost the full chunk
        if not chunks or merged_text != chunks[-1]["text"]:
            chunks.append(
                {
                    "text": merged_text,
                    "start": round(chunk_start, 2),
                    "end": chunk_end,
                    "token_estimate": len(merged_text.split()),
                }
            )

    return chunks
