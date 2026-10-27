from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.core.config import settings

app = FastAPI(
    title="YTRAG - YouTube Research Assistant API",
    description="Grounded RAG backend for semantic YouTube video indexing and timestamped citation retrieval.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for local development and client integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API endpoints
app.include_router(router)

# Mount web client static assets
static_dir = Path("./app/static")
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
