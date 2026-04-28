"""Manim renderer with TTS voice-over.

Pipeline per job:
  1. Generate TTS narration.mp3 first  (so we know exact audio duration)
  2. Patch scene_code: extend final self.wait() so video ≥ audio length
  3. Write scene.py → manim CLI → silent MP4
  4. ffmpeg: merge audio + video → final MP4 (audio drives duration)
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
from pathlib import Path

import edge_tts

VIDEOS_DIR = Path(os.environ.get("VIDEOS_DIR", "/tmp/alex_videos"))
WORK_DIR = Path(os.environ.get("WORK_DIR", "/tmp/alex_work"))
QUALITY_FLAG = {
    "low": "-ql",
    "medium": "-qm",
    "high": "-qh",
    "production": "-qp",
}.get(os.environ.get("RENDER_QUALITY", "low"), "-ql")
MAX_RENDER_SECONDS = int(os.environ.get("MAX_RENDER_SECONDS", "720"))
TTS_VOICE = os.environ.get("TTS_VOICE", "en-US-AndrewNeural")

VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
WORK_DIR.mkdir(parents=True, exist_ok=True)


class RenderError(RuntimeError):
    pass


async def _generate_tts(text: str, out_path: Path) -> None:
    """Convert narration text → MP3 using Microsoft Edge neural TTS (free)."""
    communicate = edge_tts.Communicate(text, TTS_VOICE)
    await communicate.save(str(out_path))


async def _get_audio_duration(audio_path: Path) -> float:
    """Return exact duration of an audio file in seconds via ffprobe."""
    proc = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        str(audio_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
    try:
        data = json.loads(stdout)
        return float(data["streams"][0]["duration"])
    except Exception:
        # Fallback: estimate from word count (~140 wpm)
        return 0.0


def _patch_video_length(code: str, min_seconds: float) -> str:
    """Ensure the Manim scene is at least min_seconds long.

    Replaces ONLY the final self.wait(N) with self.wait(min_seconds+2).
    Mid-scene waits inside templates are left untouched — replacing them all
    was the bug that made the 2nd scene fill the entire video.
    """
    tail = int(min_seconds) + 2          # 2s grace on top of audio length
    stripped = code.rstrip()

    # Find ALL occurrences, then replace only the very last one
    matches = list(re.finditer(r'self\.wait\s*\(\s*\d+(?:\.\d+)?\s*\)', stripped))
    if matches:
        last = matches[-1]
        patched = stripped[:last.start()] + f'self.wait({tail})' + stripped[last.end():]
    else:
        # No self.wait at all — append one at the end
        patched = stripped + f'\n        self.wait({tail})'

    return patched


async def _merge_audio_video(
    video_path: Path, audio_path: Path, output_path: Path
) -> None:
    """ffmpeg: lay audio over the silent Manim video.

    Video is always longer than audio (we patched it), so -shortest cuts
    at the audio end — perfect sync.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "128k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",          # stop at audio end (video is padded longer)
        str(output_path),
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
    except asyncio.TimeoutError:
        proc.kill()
        raise RenderError("ffmpeg merge timed out") from None

    if proc.returncode != 0:
        err = (stderr or b"").decode("utf-8", errors="ignore")[-1000:]
        raise RenderError(f"ffmpeg merge failed (exit {proc.returncode}): {err}")


async def render_scene(
    job_id: str,
    scene_code: str,
    narration_text: str = "",
) -> Path:
    """Render scene code (+ optional narration) to a final MP4. Returns path."""

    job_work = WORK_DIR / job_id
    if job_work.exists():
        shutil.rmtree(job_work, ignore_errors=True)
    job_work.mkdir(parents=True, exist_ok=True)

    audio_path: Path | None = None

    # ── 1. TTS first (so we know exact audio length before rendering) ─────────
    if narration_text.strip():
        audio_path = job_work / "narration.mp3"
        await _generate_tts(narration_text, audio_path)

        audio_duration = await _get_audio_duration(audio_path)
        if audio_duration < 5:
            # ffprobe failed — fall back to word-count estimate (140 wpm)
            audio_duration = len(narration_text.split()) / 2.33

        # Patch the scene so the silent video is always longer than the audio
        scene_code = _patch_video_length(scene_code, audio_duration)

    # ── 2. Write (patched) scene file ─────────────────────────────────────────
    scene_file = job_work / "scene.py"
    scene_file.write_text(scene_code, encoding="utf-8")

    # ── 3. Run Manim ──────────────────────────────────────────────────────────
    media_dir = job_work / "media"
    manim_cmd = [
        "manim",
        QUALITY_FLAG,
        "--media_dir", str(media_dir),
        "--disable_caching",
        str(scene_file),
        "MainScene",
    ]

    proc = await asyncio.create_subprocess_exec(
        *manim_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(job_work),
    )
    try:
        _, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=MAX_RENDER_SECONDS
        )
    except asyncio.TimeoutError:
        proc.kill()
        raise RenderError(f"Manim render exceeded {MAX_RENDER_SECONDS}s") from None

    if proc.returncode != 0:
        tail = (stderr or b"").decode("utf-8", errors="ignore")[-2000:]
        raise RenderError(f"Manim exited {proc.returncode}: {tail}")

    silent_mp4 = _find_mp4(media_dir)
    if silent_mp4 is None:
        listing = "\n".join(str(p) for p in media_dir.rglob("*"))
        raise RenderError(f"No MP4 produced. Tree:\n{listing}")

    final_path = VIDEOS_DIR / f"{job_id}.mp4"

    # ── 4. Merge audio + video ────────────────────────────────────────────────
    if audio_path and audio_path.exists():
        await _merge_audio_video(silent_mp4, audio_path, final_path)
    else:
        shutil.copy2(silent_mp4, final_path)

    shutil.rmtree(job_work, ignore_errors=True)
    return final_path


def _find_mp4(root: Path) -> Path | None:
    candidates = sorted(
        root.rglob("MainScene.mp4"), key=lambda p: p.stat().st_mtime
    )
    if candidates:
        return candidates[-1]
    any_mp4 = sorted(root.rglob("*.mp4"), key=lambda p: p.stat().st_mtime)
    return any_mp4[-1] if any_mp4 else None
