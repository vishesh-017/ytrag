import pytest
from app.services.transcript import extract_video_id


@pytest.mark.parametrize(
    "url,expected_id",
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("http://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120s&list=xyz", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ?si=abcdef12345", "dQw4w9WgXcQ"),
        ("dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ],
)
def test_extract_video_id_valid_formats(url, expected_id):
    assert extract_video_id(url) == expected_id


@pytest.mark.parametrize(
    "invalid_url",
    [
        ("https://example.com/not-a-video"),
        ("https://vimeo.com/12345678"),
        (""),
        ("too_short"),
        ("https://www.youtube.com/watch?invalid=true"),
    ],
)
def test_extract_video_id_invalid_formats(invalid_url):
    with pytest.raises(ValueError):
        extract_video_id(invalid_url)
