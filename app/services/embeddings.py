from typing import List, Optional
from google import genai
from app.core.config import settings

_client: Optional[genai.Client] = None


def get_genai_client() -> genai.Client:
    """Returns a singleton Google GenAI client instance."""
    global _client
    if _client is None:
        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not configured in environment or .env file. "
                "Please configure a valid Gemini API key to generate vector embeddings."
            )
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def generate_embedding(text: str) -> List[float]:
    """Generates a dense vector embedding for a single text chunk using Gemini."""
    client = get_genai_client()
    response = client.models.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        contents=text,
    )
    return response.embeddings[0].values


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Generates dense vector embeddings for a list of text chunks."""
    if not texts:
        return []
    client = get_genai_client()
    embeddings: List[List[float]] = []

    # Process chunks sequentially or in batches
    for text in texts:
        res = client.models.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            contents=text,
        )
        embeddings.append(res.embeddings[0].values)

    return embeddings
