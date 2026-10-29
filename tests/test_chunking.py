from app.services.chunking import create_chunks


def test_create_chunks_empty():
    assert create_chunks([]) == []


def test_create_chunks_single_short():
    snippets = [
        {"text": "Hello world.", "start": 0.0, "duration": 2.5}
    ]
    chunks = create_chunks(snippets, chunk_size=100, chunk_overlap=20)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "Hello world."
    assert chunks[0]["start"] == 0.0
    assert chunks[0]["end"] == 2.5


def test_create_chunks_sliding_window():
    snippets = [
        {"text": "Sentence number one explaining RAG concepts.", "start": 0.0, "duration": 5.0},
        {"text": "Sentence number two diving into embeddings and vectors.", "start": 5.0, "duration": 5.0},
        {"text": "Sentence number three detailing ChromaDB storage.", "start": 10.0, "duration": 5.0},
        {"text": "Sentence number four covering prompt engineering.", "start": 15.0, "duration": 5.0},
    ]

    # Force smaller chunk size to trigger window splitting
    chunks = create_chunks(snippets, chunk_size=60, chunk_overlap=30)
    assert len(chunks) >= 2

    # Verify every chunk has text and valid chronological timestamps
    for ch in chunks:
        assert len(ch["text"]) > 0
        assert ch["start"] >= 0.0
        assert ch["end"] > ch["start"]
        assert "token_estimate" in ch
