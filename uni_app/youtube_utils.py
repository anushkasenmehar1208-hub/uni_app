"""YouTube helpers: URL parsing, video ID extraction, transcript fetching.

The transcript fetcher uses youtube-transcript-api which scrapes the public
captions endpoint. No API key required. Returns plain text or None on failure.
"""

from __future__ import annotations

import logging
import re
from typing import Optional
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)

# Match shapes:
#   https://www.youtube.com/watch?v=VIDEO_ID
#   https://youtu.be/VIDEO_ID
#   https://www.youtube.com/embed/VIDEO_ID
#   https://www.youtube.com/shorts/VIDEO_ID
#   https://m.youtube.com/watch?v=VIDEO_ID
_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extract_video_id(url: str) -> Optional[str]:
    """Pull the 11-char video ID out of any common YouTube URL shape.

    Returns None if the URL doesn't look like a YouTube link.
    Accepts a bare video ID too (e.g. 'dQw4w9WgXcQ').
    """
    if not url:
        return None
    s = url.strip()

    # Bare video ID
    if _VIDEO_ID_RE.match(s):
        return s

    # Add scheme if user pasted "youtube.com/..."
    if not s.startswith(("http://", "https://")):
        s = "https://" + s

    try:
        parsed = urlparse(s)
    except Exception:
        return None

    host = (parsed.hostname or "").lower().lstrip("www.")

    # youtu.be/VIDEO_ID
    if host == "youtu.be":
        candidate = parsed.path.strip("/").split("/")[0]
        return candidate if _VIDEO_ID_RE.match(candidate) else None

    # youtube.com / m.youtube.com
    if host in ("youtube.com", "m.youtube.com", "music.youtube.com"):
        # /watch?v=VIDEO_ID
        if parsed.path == "/watch":
            qs = parse_qs(parsed.query)
            vlist = qs.get("v") or []
            if vlist and _VIDEO_ID_RE.match(vlist[0]):
                return vlist[0]
        # /embed/VIDEO_ID  or  /shorts/VIDEO_ID  or  /live/VIDEO_ID
        for prefix in ("/embed/", "/shorts/", "/live/", "/v/"):
            if parsed.path.startswith(prefix):
                candidate = parsed.path[len(prefix):].split("/")[0]
                if _VIDEO_ID_RE.match(candidate):
                    return candidate

    return None


def embed_url(video_id: str) -> str:
    """Build a YouTube embed URL for an iframe with sensible defaults."""
    if not _VIDEO_ID_RE.match(video_id):
        return ""
    # rel=0 hides related videos; modestbranding for less YT chrome.
    return f"https://www.youtube.com/embed/{video_id}?rel=0&modestbranding=1"


def thumbnail_url(video_id: str) -> str:
    """Highest-resolution thumbnail YouTube provides for the given video."""
    if not _VIDEO_ID_RE.match(video_id):
        return ""
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"


def fetch_transcript(video_id: str, lang_priority: tuple[str, ...] = ("en", "en-US", "en-GB")) -> Optional[str]:
    """Fetch the transcript as a single plain-text string.

    Tries languages in priority order, then falls back to whatever's available
    (auto-generated included). Returns None if no transcript exists or the
    library isn't installed.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        logger.warning("youtube-transcript-api not installed; transcripts disabled")
        return None

    try:
        # New API: instance-based, returns FetchedTranscript
        api = YouTubeTranscriptApi()
        try:
            fetched = api.fetch(video_id, languages=list(lang_priority))
        except Exception:
            # Last resort — list available, take the first
            transcript_list = api.list(video_id)
            available = list(transcript_list)
            if not available:
                return None
            fetched = available[0].fetch()

        # FetchedTranscript supports iteration; each item has .text
        parts: list[str] = []
        for snippet in fetched:
            text = getattr(snippet, "text", None) or (snippet.get("text") if isinstance(snippet, dict) else None)
            if text:
                parts.append(text.strip())
        return " ".join(parts).strip() or None
    except Exception as e:
        logger.info(f"transcript fetch failed for {video_id}: {e}")
        return None


def truncate_for_llm(text: str, max_chars: int = 12000) -> str:
    """Truncate transcript to fit comfortably in an LLM context.

    Cuts at a sentence boundary when possible.
    """
    if not text or len(text) <= max_chars:
        return text or ""
    cut = text[:max_chars]
    # Try to end on a sentence
    last_period = cut.rfind(". ")
    if last_period > max_chars * 0.7:
        cut = cut[:last_period + 1]
    return cut + "  […truncated]"
