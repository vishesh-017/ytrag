from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class IndexRequest(BaseModel):
    """Payload for indexing a YouTube video."""

    url: str = Field(
        ...,
        description="YouTube video URL or 11-character video ID",
        examples=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
    )


class IndexResponse(BaseModel):
    """Response returned upon indexing transcript."""

    status: str = Field(..., examples=["success"])
    video_id: str = Field(..., examples=["dQw4w9WgXcQ"])
    total_transcript_segments: int = Field(
        ..., description="Raw subtitle segments retrieved"
    )
    total_chunks_indexed: int = Field(
        ..., description="Total overlapping semantic chunks indexed"
    )
    message: str = Field(...)


class AskRequest(BaseModel):
    """Payload for asking a research question."""

    question: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="The research question to answer",
        examples=["What is the main argument regarding neural network scaling?"],
    )
    video_id: Optional[str] = Field(
        default=None,
        description="Optional video ID to scope retrieval to a single video",
    )
    top_k: int = Field(
        default=4,
        ge=1,
        le=15,
        description="Number of most relevant transcript chunks to retrieve",
    )


class SourceCitation(BaseModel):
    """Source reference for grounded citation."""

    video_id: str
    start: float
    end: float
    timestamp_label: str
    youtube_url: str
    text_snippet: str
    distance: Optional[float] = None


class AskResponse(BaseModel):
    """Answer response along with precise timestamp source citations."""

    answer: str
    sources: List[SourceCitation]
    video_id: Optional[str] = None


class VideoSummary(BaseModel):
    """Summary of an indexed video."""

    video_id: str
    chunk_count: int
    title: Optional[str] = None


class VideoListResponse(BaseModel):
    """List of all indexed videos in the vector store."""

    total_videos: int
    videos: List[VideoSummary]


class DeleteResponse(BaseModel):
    """Response after deleting a video from the index."""

    status: str
    video_id: str
    deleted_chunks: int


class HealthResponse(BaseModel):
    """API health status response."""

    status: str
    version: str
    groq_configured: bool
    gemini_configured: bool
