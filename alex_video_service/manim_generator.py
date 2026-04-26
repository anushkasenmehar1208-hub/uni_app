"""LLM-driven Manim scene generator.

Calls OpenRouter (claude-opus-4-7) with a strict system prompt and returns
a Python source string that defines a single `MainScene(Scene)` class.
The output is sanity-checked for forbidden APIs before being written to disk.
"""

from __future__ import annotations

import os
import re
import textwrap

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-opus-4-7"

FORBIDDEN_PATTERNS = [
    r"\bos\.system\b",
    r"\bsubprocess\b",
    r"\b__import__\b",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bopen\s*\(",
    r"\bcompile\s*\(",
    r"\bsocket\b",
    r"\brequests\b",
    r"\bhttpx\b",
    r"\burllib\b",
    r"\bshutil\b",
    r"\bpathlib\b",
    r"\bPath\s*\(",
]

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are a Manim animation engineer creating cinematic 3Blue1Brown-style
    educational videos. Output ONLY valid Manim Community Edition Python code.

    Hard requirements:
    - The file must define exactly one class: `class MainScene(Scene):` (or
      `ThreeDScene` when 3D is needed).
    - Inside, define `def construct(self):` with the full animation.
    - Import only from `manim` (e.g. `from manim import *`). Use `numpy as np`
      if needed. NEVER import os, sys, subprocess, requests, httpx, urllib,
      socket, pathlib, shutil. Never call exec, eval, open, compile, __import__.
    - Total runtime should be 15-30 seconds. Use `self.wait(...)` between beats.
    - Use rich color palettes (BLUE_D, TEAL, YELLOW, RED_D, PURPLE_B, etc).
    - For math, use `MathTex(r"...")` with raw strings; for body text use `Text`.
    - Animate with `Create`, `Write`, `FadeIn`, `Transform`, `ReplacementTransform`,
      `Indicate`, `MoveAlongPath`, `Rotate`. Pace beats with `run_time`.
    - For 3D, set `self.set_camera_orientation(phi=..., theta=...)` and
      `self.begin_ambient_camera_rotation(rate=0.1)` for cinematic feel.
    - Group related Mobjects with `VGroup` and arrange with `.arrange()` or
      `.next_to()`. Avoid overlapping labels; clear scene between sections with
      `FadeOut(*self.mobjects)` when changing topic.
    - Output MUST be a single Python file with no markdown fences, no prose,
      no comments outside code, and no extra classes.

    The user prompt contains the topic and any style notes. Build the most
    beautiful explanation you can within those bounds.
    """
).strip()


class GenerationError(RuntimeError):
    pass


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n", "", text)
        text = re.sub(r"\n```\s*$", "", text)
    return text.strip()


def _validate(code: str) -> None:
    if "class MainScene" not in code:
        raise GenerationError("LLM output is missing `class MainScene`")
    if "def construct" not in code:
        raise GenerationError("LLM output is missing `def construct`")
    for pat in FORBIDDEN_PATTERNS:
        if re.search(pat, code):
            raise GenerationError(f"Forbidden pattern in generated code: {pat}")


async def generate_scene_code(
    topic: str,
    prompt: str,
    style: str = "cinematic",
    use_3d: bool = False,
) -> str:
    """Ask the LLM to write a Manim scene; return the validated Python source."""

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise GenerationError("OPENROUTER_API_KEY is not set")

    user_prompt = textwrap.dedent(
        f"""
        TOPIC: {topic}

        EXPLANATION REQUEST:
        {prompt}

        STYLE: {style}
        DIMENSION: {"3D (use ThreeDScene)" if use_3d else "2D (use Scene)"}

        Build the animation now. Return ONLY the Python file contents.
        """
    ).strip()

    payload = {
        "model": MODEL,
        "temperature": 0.4,
        "max_tokens": 4000,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://alexstudies.com",
        "X-Title": "Alex Video Service",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(OPENROUTER_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    try:
        raw = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise GenerationError(f"Unexpected LLM response shape: {data}") from e

    code = _strip_fences(raw)
    _validate(code)
    return code
