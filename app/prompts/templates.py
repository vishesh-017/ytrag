from typing import Any, Dict, List

SYSTEM_GROUNDED_RAG_PROMPT = """You are YTRAG, a rigorous and grounded YouTube Video Research Assistant.

Your objective is to answer the user's research question strictly using facts directly supported by the provided transcript context snippets.

Strict Operational Guidelines:
1. Strict Grounding: Rely exclusively on statements made in the context excerpts. Do not infer unstated facts or introduce external world knowledge.
2. Timestamp Citations: Whenever presenting a factual answer, cite the corresponding timestamp range from the excerpt header (e.g., [12:30 - 13:15] or [04:10]). Use only the timestamp boundaries given.
3. Fallback Protocol: If the provided transcript context does not contain sufficient facts to answer the question, respond with exactly:
   "The provided video context does not contain sufficient information to answer this question."
4. Structure: Present your answer clearly in concise, well-formatted markdown paragraphs or bullet points. Avoid conversational filler.
"""

USER_QA_PROMPT_TEMPLATE = """TRANSCRIPT CONTEXT:
{context}

---
USER QUESTION:
{question}

INSTRUCTIONS:
Provide a grounded, comprehensive answer citing exact timestamp intervals from the provided excerpts above.
"""

TOPIC_SUMMARY_PROMPT_TEMPLATE = """TRANSCRIPT CONTEXT:
{context}

---
TASK:
Analyze the indexed video transcript excerpts and generate an executive outline of topics covered.
Format your response as 3 to 6 bullet points with timestamp intervals [MM:SS - MM:SS] and a 1-sentence synopsis.
"""


def format_seconds(seconds: float) -> str:
    """Converts a second offset into HH:MM:SS or MM:SS timestamp string."""
    tot_sec = max(0, int(seconds))
    hrs = tot_sec // 3600
    mins = (tot_sec % 3600) // 60
    secs = tot_sec % 60

    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def build_context_block(
    documents: List[str], metadatas: List[Dict[str, Any]]
) -> str:
    """Combines documents and metadata into tagged context blocks for the LLM."""
    blocks: List[str] = []

    for doc, meta in zip(documents, metadatas):
        start_fmt = format_seconds(meta.get("start", 0.0))
        end_fmt = format_seconds(meta.get("end", 0.0))
        video_id = meta.get("video_id", "Unknown")

        header = f"[Video ID: {video_id} | Timestamp: {start_fmt} - {end_fmt}]"
        blocks.append(f"{header}\n{doc.strip()}")

    return "\n\n".join(blocks)
