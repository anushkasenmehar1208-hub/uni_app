"""Manim renderer with TTS voice-over.

Pipeline per job:
  1. Write scene.py to temp work dir
  2. manim CLI → silent MP4
  3. edge-tts on narration text → narration.mp3  (skipped if no narration)
  4. ffmpeg merge audio + video → final MP4
"""

from __future__ import annotations

import asyncio
import os
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
# 12 minutes ceiling — low-quality 3D should finish in ~2–5 min on Railway
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


async def _merge_audio_video(
    video_path: Path, audio_path: Path, output_path: Path
) -> None:
    """ffmpeg: overlay narration audio on the silent Manim video.

    Uses -shortest so it ends at whichever stream finishes first.
    The LLM is asked to add self.wait(3) at the end so the video is
    typically a few seconds longer than the narration.
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
        "-shortest",
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

    # ── 1. Write scene file ──────────────────────────────────────────────────
    scene_file = job_work / "scene.py"
    scene_file.write_text(scene_code, encoding="utf-8")

    # ── 2. Run Manim ─────────────────────────────────────────────────────────
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
        raise RenderError(
            f"Manim render exceeded {MAX_RENDER_SECONDS}s"
        ) from None

    if proc.returncode != 0:
        tail = (stderr or b"").decode("utf-8", errors="ignore")[-2000:]
        raise RenderError(f"Manim exited {proc.returncode}: {tail}")

    silent_mp4 = _find_mp4(media_dir)
    if silent_mp4 is None:
        listing = "\n".join(str(p) for p in media_dir.rglob("*"))
        raise RenderError(f"No MP4 produced. Tree:\n{listing}")

    final_path = VIDEOS_DIR / f"{job_id}.mp4"

    # ── 3 & 4. TTS + merge (or just copy if no narration) ────────────────────
    if narration_text.strip():
        audio_path = job_work / "narration.mp3"
        await _generate_tts(narration_text, audio_path)
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
