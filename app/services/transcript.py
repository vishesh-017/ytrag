import re
from typing import Any, Dict, List
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)


def extract_video_id(youtube_url: str) -> str:
    """
    Extracts the 11-character YouTube video ID from various URL formats
    or validates a raw video ID.
    
    Supported formats:
    - Standard: https://www.youtube.com/watch?v=dQw4w9WgXcQ
    - Short: https://youtu.be/dQw4w9WgXcQ
    - Shorts: https://www.youtube.com/shorts/dQw4w9WgXcQ
    - Embed: https://www.youtube.com/embed/dQw4w9WgXcQ
    - Mobile: https://m.youtube.com/watch?v=dQw4w9WgXcQ
    - Raw ID: dQw4w9WgXcQ
    """
    cleaned_input = youtube_url.strip()

    # Raw 11-char ID check
    if re.fullmatch(r"[a-zA-Z0-9_-]{11}", cleaned_input):
        return cleaned_input

    patterns = [
        r"(?:v=|\/v\/|embed\/|shorts\/)([\w-]{11})",
        r"youtu\.be\/([\w-]{11})",
        r"youtube\.com\/watch\?.*v=([\w-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, cleaned_input)
        if match:
            return match.group(1)

    raise ValueError(
        f"Unable to extract a valid 11-character YouTube video ID from '{youtube_url}'"
    )


def fetch_transcript(youtube_url_or_id: str) -> List[Dict[str, Any]]:
    """
    Pulls timestamped transcript segments for a given YouTube URL or ID.
    Attempts English subtitles first, then falls back to available language tracks.
    """
    video_id = extract_video_id(youtube_url_or_id)

    try:
        # In newer versions of youtube-transcript-api, instance or class methods are available
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Priority: manually created English, generated English, or any available transcript
        try:
            transcript = transcript_list.find_transcript(["en", "en-US", "en-GB"])
        except NoTranscriptFound:
            # Fallback to any transcript or auto-generated translation
            transcript = next(iter(transcript_list))
            
        data = transcript.fetch()

        return [
            {
                "text": segment["text"].replace("\n", " ").strip(),
                "start": float(segment["start"]),
                "duration": float(segment["duration"]),
            }
            for segment in data
            if segment.get("text", "").strip()
        ]

    except TranscriptsDisabled:
        raise RuntimeError(f"Subtitles/transcripts are disabled for video {video_id}.")
    except NoTranscriptFound:
        raise RuntimeError(f"No suitable transcript found for video {video_id}.")
    except Exception as e:
        # Fallback to direct get_transcript if list_transcripts fails
        try:
            raw_data = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
            return [
                {
                    "text": segment["text"].replace("\n", " ").strip(),
                    "start": float(segment["start"]),
                    "duration": float(segment["duration"]),
                }
                for segment in raw_data
                if segment.get("text", "").strip()
            ]
        except Exception:
            raise RuntimeError(
                f"Failed to fetch transcript for video '{video_id}': {str(e)}"
            )
