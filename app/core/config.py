from dataclasses import dataclass, field
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment definitions from .env if present
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Centralized configuration for YTRAG application."""

    # API Keys
    GROQ_API_KEY: str = field(
        default_factory=lambda: os.getenv("GROQ_API_KEY", "")
    )
    GEMINI_API_KEY: str = field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY", "")
    )

    # Model Specifications
    GROQ_MODEL: str = field(
        default_factory=lambda: os.getenv(
            "GROQ_MODEL", "llama-3.3-70b-versatile"
        )
    )
    GEMINI_EMBEDDING_MODEL: str = field(
        default_factory=lambda: os.getenv(
            "GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"
        )
    )
    TEMPERATURE: float = field(
        default_factory=lambda: float(os.getenv("TEMPERATURE", "0.1"))
    )

    # Retrieval and Chunking Configurations
    CHUNK_SIZE: int = field(
        default_factory=lambda: int(os.getenv("CHUNK_SIZE", "1000"))
    )
    CHUNK_OVERLAP: int = field(
        default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "200"))
    )
    DEFAULT_TOP_K: int = field(
        default_factory=lambda: int(os.getenv("DEFAULT_TOP_K", "4"))
    )

    # Storage Settings
    CHROMA_PERSIST_DIRECTORY: Path = field(
        default_factory=lambda: Path(
            os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")
        )
    )
    STATIC_DIRECTORY: Path = field(
        default_factory=lambda: Path("./app/static")
    )


settings = Settings()
