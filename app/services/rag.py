from typing import Any, Dict, List, Optional
from groq import Groq
from app.core.config import settings
from app.db.vector_store import search_chunks
from app.services.embeddings import generate_embedding
from app.prompts.templates import (
    SYSTEM_GROUNDED_RAG_PROMPT,
    USER_QA_PROMPT_TEMPLATE,
    build_context_block,
    format_seconds,
)

_groq_client: Optional[Groq] = None


def get_groq_client() -> Groq:
    """Returns singleton Groq client instance."""
    global _groq_client
    if _groq_client is None:
        if not settings.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is not configured in environment or .env file. "
                "Please configure a valid Groq API key to generate grounded answers."
            )
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    return _groq_client


def answer_research_question(
    question: str,
    video_id: Optional[str] = None,
    top_k: int = settings.DEFAULT_TOP_K,
) -> Dict[str, Any]:
    """
    Orchestrates the Grounded RAG workflow:
    1. Embeds the user question.
    2. Retrieves top-k matching transcript chunks from ChromaDB.
    3. Assembles prompt context with exact timestamp metadata.
    4. Invokes Groq LLM to synthesize answer strictly grounded in transcript.
    5. Formats answer and creates interactive timestamp citation links.
    """
    # Step 1: Embed question
    query_vector = generate_embedding(question)

    # Step 2: Retrieve relevant chunks
    search_res = search_chunks(
        query_embedding=query_vector,
        n_results=top_k,
        video_id=video_id,
    )

    documents: List[str] = search_res.get("documents", [[]])[0]
    metadatas: List[Dict[str, Any]] = search_res.get("metadatas", [[]])[0]
    distances: List[Optional[float]] = (
        search_res.get("distances", [[]])[0] or [None] * len(documents)
    )

    if not documents:
        return {
            "answer": "No relevant transcript context was found in the indexed videos for your question.",
            "sources": [],
            "video_id": video_id,
        }

    # Step 3: Build context block
    context = build_context_block(documents, metadatas)
    user_prompt = USER_QA_PROMPT_TEMPLATE.format(
        context=context,
        question=question,
    )

    # Step 4: Groq Completion
    client = get_groq_client()
    completion = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_GROUNDED_RAG_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=settings.TEMPERATURE,
    )

    answer_text = completion.choices[0].message.content.strip()

    fallback_phrase = (
        "The provided video context does not contain sufficient information "
        "to answer this question."
    )

    # If LLM triggered fallback, omit sources to prevent misleading citation
    if fallback_phrase in answer_text:
        return {
            "answer": answer_text,
            "sources": [],
            "video_id": video_id,
        }

    # Step 5: Format source citations
    sources: List[Dict[str, Any]] = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        start_sec = meta.get("start", 0.0)
        end_sec = meta.get("end", 0.0)
        target_vid = meta.get("video_id", video_id or "")
        start_int = int(start_sec)

        sources.append(
            {
                "video_id": target_vid,
                "start": start_sec,
                "end": end_sec,
                "timestamp_label": f"{format_seconds(start_sec)} - {format_seconds(end_sec)}",
                "youtube_url": f"https://www.youtube.com/watch?v=f{target_vid}&t={start_int}s",
                "text_snippet": (doc[:180] + "...") if len(doc) > 180 else doc,
                "distance": round(dist, 4) if dist is not None else None,
            }
        )

    return {
        "answer": answer_text,
        "sources": sources,
        "video_id": video_id,
    }
