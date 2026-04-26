"""Manim renderer.

Writes the generated scene to a temp directory, invokes the manim CLI in a
subprocess with a hard timeout, and returns the resulting MP4 path.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path

VIDEOS_DIR = Path(os.environ.get("VIDEOS_DIR", "/tmp/alex_videos"))
WORK_DIR = Path(os.environ.get("WORK_DIR", "/tmp/alex_work"))
QUALITY_FLAG = {
    "low": "-ql",
    "medium": "-qm",
    "high": "-qh",
}.get(os.environ.get("RENDER_QUALITY", "medium"), "-qm")
MAX_RENDER_SECONDS = int(os.environ.get("MAX_RENDER_SECONDS", "180"))

VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
WORK_DIR.mkdir(parents=True, exist_ok=True)


class RenderError(RuntimeError):
    pass


async def render_scene(job_id: str, scene_code: str) -> Path:
    """Render the given scene code to MP4 and return its final path."""

    job_work = WORK_DIR / job_id
    if job_work.exists():
        shutil.rmtree(job_work, ignore_errors=True)
    job_work.mkdir(parents=True, exist_ok=True)

    scene_file = job_work / "scene.py"
    scene_file.write_text(scene_code, encoding="utf-8")

    media_dir = job_work / "media"
    cmd = [
        "manim",
        QUALITY_FLAG,
        "--media_dir",
        str(media_dir),
        "--disable_caching",
        str(scene_file),
        "MainScene",
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(job_work),
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=MAX_RENDER_SECONDS
        )
    except asyncio.TimeoutError:
        proc.kill()
        raise RenderError(f"Manim render exceeded {MAX_RENDER_SECONDS}s") from None

    if proc.returncode != 0:
        tail = (stderr or b"").decode("utf-8", errors="ignore")[-2000:]
        raise RenderError(f"Manim exited {proc.returncode}: {tail}")

    mp4 = _find_mp4(media_dir)
    if mp4 is None:
        listing = "\n".join(str(p) for p in media_dir.rglob("*"))
        raise RenderError(f"No MP4 produced. Tree:\n{listing}")

    final_path = VIDEOS_DIR / f"{job_id}.mp4"
    shutil.copy2(mp4, final_path)
    shutil.rmtree(job_work, ignore_errors=True)
    return final_path


def _find_mp4(root: Path) -> Path | None:
    candidates = sorted(root.rglob("MainScene.mp4"), key=lambda p: p.stat().st_mtime)
    if candidates:
        return candidates[-1]
    any_mp4 = sorted(root.rglob("*.mp4"), key=lambda p: p.stat().st_mtime)
    return any_mp4[-1] if any_mp4 else None
