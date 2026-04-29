"""YouTube helpers: URL parsing, video ID extraction, transcript fetching.

The transcript fetcher tries multiple strategies in order:
  1. Supadata API (cloud-safe, needs SUPADATA_API_KEY env var)
  2. youtube-transcript-api with optional proxy config
  3. Raw httpx fetch of YouTube's timedtext XML endpoint

Returns plain text or (None, reason) on failure.
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from html import unescape
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


def watch_url(video_id: str) -> str:
    """Standard YouTube watch URL."""
    return f"https://www.youtube.com/watch?v={video_id}"


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 1: Supadata API  (requires SUPADATA_API_KEY env var)
# ─────────────────────────────────────────────────────────────────────────────

def _try_supadata(video_id: str) -> Optional[str]:
    """Fetch transcript via Supadata.ai API (cloud-friendly).

    Returns plain text on success, None on failure.
    Requires env var SUPADATA_API_KEY.
    """
    import os
    api_key = os.getenv("SUPADATA_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        import httpx
        url = f"https://api.supadata.ai/v1/youtube/transcript"
        headers = {
            "x-api-key": api_key,
            "User-Agent": "Mozilla/5.0 (compatible; AlexApp/1.0)",
        }
        params = {"url": f"https://www.youtube.com/watch?v={video_id}", "text": "true"}
        r = httpx.get(url, headers=headers, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            content = data.get("content") or ""
            if isinstance(content, list):
                content = " ".join(
                    seg.get("text", "") for seg in content if isinstance(seg, dict)
                ).strip()
            return content.strip() or None
        logger.info(f"Supadata returned {r.status_code}: {r.text[:200]}")
    except Exception as e:
        logger.info(f"Supadata fetch error: {e!r}"[:300])
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 2: youtube-transcript-api  (may be blocked on cloud IPs)
# ─────────────────────────────────────────────────────────────────────────────

def _build_proxy_config():
    """Build a youtube-transcript-api proxy config from env vars, if set.

    Supports:
      - YOUTUBE_TRANSCRIPT_PROXY_URL: a single http(s) proxy URL
      - WEBSHARE_PROXY_USERNAME + WEBSHARE_PROXY_PASSWORD: Webshare residential
        proxy auth (the library has built-in support)

    Returns a ProxyConfig instance the api accepts, or None.
    """
    import os
    try:
        from youtube_transcript_api.proxies import GenericProxyConfig, WebshareProxyConfig
    except Exception:
        return None

    ws_user = os.getenv("WEBSHARE_PROXY_USERNAME", "").strip()
    ws_pass = os.getenv("WEBSHARE_PROXY_PASSWORD", "").strip()
    if ws_user and ws_pass:
        try:
            return WebshareProxyConfig(proxy_username=ws_user, proxy_password=ws_pass)
        except Exception as e:
            logger.warning(f"WebshareProxyConfig init failed: {e}")

    proxy_url = os.getenv("YOUTUBE_TRANSCRIPT_PROXY_URL", "").strip()
    if proxy_url:
        try:
            return GenericProxyConfig(http_url=proxy_url, https_url=proxy_url)
        except Exception as e:
            logger.warning(f"GenericProxyConfig init failed: {e}")

    return None


def _try_ytapi(video_id: str, lang_priority: tuple[str, ...]) -> tuple[Optional[str], str]:
    """Fetch via youtube-transcript-api library.

    Returns (text, reason). On success: (text, ""). On failure: (None, reason).
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None, "library_missing"

    proxy_config = _build_proxy_config()
    try:
        api = YouTubeTranscriptApi(proxy_config=proxy_config) if proxy_config else YouTubeTranscriptApi()
        try:
            fetched = api.fetch(video_id, languages=list(lang_priority))
        except Exception as inner:
            try:
                transcript_list = api.list(video_id)
                available = list(transcript_list)
                if not available:
                    return None, "no_transcript"
                fetched = available[0].fetch()
            except Exception:
                raise inner

        parts: list[str] = []
        for snippet in fetched:
            text = getattr(snippet, "text", None) or (snippet.get("text") if isinstance(snippet, dict) else None)
            if text:
                parts.append(text.strip())
        joined = " ".join(parts).strip()
        if joined:
            return joined, ""
        return None, "empty_transcript"
    except Exception as e:
        msg = str(e).lower()
        if "blocking" in msg or "blocked" in msg or "ipblocked" in msg or "requestblocked" in msg:
            return None, "youtube_blocked"
        elif "transcriptsdisabled" in msg or "no transcripts" in msg:
            return None, "no_transcript"
        elif "videounavailable" in msg or "video unavailable" in msg:
            return None, "video_unavailable"
        else:
            return None, "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# Strategy 3: Raw httpx timedtext fetch (browser-impersonation)
# ─────────────────────────────────────────────────────────────────────────────

def _try_timedtext(video_id: str) -> Optional[str]:
    """Try fetching auto-captions via YouTube's timedtext XML endpoint.

    This uses a browser-like User-Agent and may succeed even when the
    youtube-transcript-api library is blocked.
    """
    try:
        import httpx

        # First, try to get the page to find the actual timedtext URL
        watch_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        # Try a set of common timedtext URLs for auto-generated captions
        lang_codes = ["en", "en-US", "en-GB"]
        for lang in lang_codes:
            url = (
                f"https://www.youtube.com/api/timedtext"
                f"?v={video_id}&lang={lang}&fmt=json3&asr_langs=en&kind=asr"
            )
            try:
                r = httpx.get(url, headers=watch_headers, timeout=10, follow_redirects=True)
                if r.status_code == 200 and r.text.strip():
                    data = r.json()
                    events = data.get("events", [])
                    parts = []
                    for ev in events:
                        segs = ev.get("segs", [])
                        for seg in segs:
                            t = seg.get("utf8", "").replace("\n", " ").strip()
                            if t and t != "\n":
                                parts.append(t)
                    text = " ".join(parts).strip()
                    if text:
                        return text
            except Exception:
                pass

        # Fallback: try plain XML timedtext
        for lang in lang_codes:
            url = f"https://www.youtube.com/api/timedtext?v={video_id}&lang={lang}"
            try:
                r = httpx.get(url, headers=watch_headers, timeout=10, follow_redirects=True)
                if r.status_code == 200 and r.text.strip():
                    root = ET.fromstring(r.text)
                    parts = [unescape(text.text or "") for text in root.findall("text")]
                    joined = " ".join(p.strip() for p in parts if p.strip())
                    if joined:
                        return joined
            except Exception:
                pass

    except Exception as e:
        logger.debug(f"timedtext fetch error: {e!r}"[:200])

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def fetch_transcript(
    video_id: str,
    lang_priority: tuple[str, ...] = ("en", "en-US", "en-GB"),
) -> tuple[Optional[str], str]:
    """Fetch the transcript using multiple strategies in order.

    Returns (text, reason). On success: (text, ""). On failure: (None, reason).

    Strategy order:
      1. Supadata API  (cloud-safe, requires SUPADATA_API_KEY env var)
      2. youtube-transcript-api  (may be blocked on Railway/AWS/GCP IPs)
      3. Raw httpx timedtext fetch with browser headers

    The first strategy that returns text wins.
    """
    # 1. Supadata (cloud-safe, key optional)
    text = _try_supadata(video_id)
    if text:
        logger.info(f"transcript via Supadata OK ({len(text)} chars)")
        return text, ""

    # 2. youtube-transcript-api
    text, reason = _try_ytapi(video_id, lang_priority)
    if text:
        logger.info(f"transcript via ytapi OK ({len(text)} chars)")
        return text, ""
    ytapi_reason = reason  # remember why it failed

    # If the video itself has no captions or is unavailable, don't bother
    # with the httpx fallback — it won't help.
    if ytapi_reason in ("no_transcript", "video_unavailable"):
        return None, ytapi_reason

    # 3. Raw timedtext (browser impersonation)
    text = _try_timedtext(video_id)
    if text:
        logger.info(f"transcript via timedtext OK ({len(text)} chars)")
        return text, ""

    # All strategies failed
    logger.info(f"all transcript strategies failed for {video_id}; last reason: {ytapi_reason}")
    return None, ytapi_reason or "youtube_blocked"


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
