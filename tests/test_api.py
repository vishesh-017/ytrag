from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert "groq_configured" in data
    assert "gemini_configured" in data


def test_list_videos_endpoint():
    response = client.get("/api/videos")
    assert response.status_code == 200
    data = response.json()
    assert "total_videos" in data
    assert "videos" in data
    assert isinstance(data["videos"], list)


def test_index_invalid_url():
    response = client.post(
        "/api/index",
        json={"url": "https://invalid-non-youtube-domain.com/video"},
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_ask_validation_empty_question():
    response = client.post(
        "/api/ask",
        json={"question": "", "top_k": 4},
    )
    assert response.status_code == 422


def test_ask_validation_invalid_top_k():
    response = client.post(
        "/api/ask",
        json={"question": "What is discussed?", "top_k": 0},
    )
    assert response.status_code == 422


def test_delete_video_non_existent():
    response = client.delete("/api/videos/non_existent_123")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["video_id"] == "non_existent_123"
    assert data["deleted_chunks"] == 0
