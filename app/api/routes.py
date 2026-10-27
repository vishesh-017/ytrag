from fastapi import APIRouter, HTTPException, status
from app.core.config import settings
from app.db.vector_store import add_chunks, delete_video, get_all_indexed_videos
from app.models.schemas import (
    AskRequest,
    AskResponse,
    DeleteResponse,
    HealthResponse,
    IndexRequest,
    IndexResponse,
    VideoListResponse,
    VideoSummary,
)
from app.services.chunking import create_chunks
from app.services.embeddings import generate_embeddings_batch
from app.services.rag import answer_research_question
from app.services.transcript import extract_video_id, fetch_transcript

router = APIRouter(prefix="/api", tags=["Research Assistant"])


@router.get("/health", response_model=HealthResponse, summary="Check API Health Status")
async def check_health():
    """Returns application status and indicates whether API keys are loaded."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        groq_configured=bool(settings.GROQ_API_KEY),
        gemini_configured=bool(settings.GEMINI_API_KEY),
    )


@router.post(
    "/index",
    response_model=IndexResponse,
    status_code=status.HTTP_200_OK,
    summary="Index YouTube Video Transcript",
)
async def index_video(payload: IndexRequest):
    """
    Ingests, chunks, embeds, and stores a YouTube transcript for grounded retrieval.
    """
    try:
        video_id = extract_video_id(payload.url)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )

    try:
        raw_segments = fetch_transcript(payload.url)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transcript extraction failed: {str(err)}",
        )

    chunks = create_chunks(raw_segments)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript was empty or could not be segmented into chunks.",
        )

    try:
        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = generate_embeddings_batch(chunk_texts)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector embedding generation failed: {str(err)}",
        )

    try:
        add_chunks(video_id=video_id, chunks=chunks, embeddings=embeddings)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database indexing failed: {str(err)}",
        )

    return IndexResponse(
        status="success",
        video_id=video_id,
        total_transcript_segments=len(raw_segments),
        total_chunks_indexed=len(chunks),
        message=f"Video '{video_id}' successfully indexed with {len(chunks)} searchable chunks.",
    )


@router.post(
    "/ask",
    response_model=AskResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask Grounded Research Question",
)
async def ask_question(payload: AskRequest):
    """
    Performs vector similarity search and synthesizes an answer strictly grounded in transcript chunks.
    """
    try:
        result = answer_research_question(
            question=payload.question,
            video_id=payload.video_id,
            top_k=payload.top_k,
        )
        return AskResponse(
            answer=result["answer"],
            sources=result["sources"],
            video_id=result["video_id"],
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing Q&A research query: {str(err)}",
        )


@router.get(
    "/videos",
    response_model=VideoListResponse,
    summary="List All Indexed Videos",
)
async def list_videos():
    """Retrieves all indexed video IDs and their chunk counts from the vector store."""
    try:
        counts = get_all_indexed_videos()
        summaries = [
            VideoSummary(video_id=vid, chunk_count=count)
            for vid, count in counts.items()
        ]
        return VideoListResponse(total_videos=len(summaries), videos=summaries)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading indexed video catalogue: {str(err)}",
        )


@router.delete(
    "/videos/{video_id}",
    response_model=DeleteResponse,
    summary="Delete Video From Index",
)
async def remove_video(video_id: str):
    """Removes all stored vectors and metadata for a specific video ID."""
    try:
        deleted_count = delete_video(video_id)
        return DeleteResponse(
            status="success",
            video_id=video_id,
            deleted_chunks=deleted_count,
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove video '{video_id}' from index: {str(err)}",
        )
