"""LLM-driven Manim scene generator.

Single LLM call returns BOTH narration script (for TTS) and Manim Python code,
naturally synchronized because the LLM writes them together.

Output format the LLM must produce:
    ===NARRATION===
    <voice-over text>
    ===CODE===
    <python code>
"""

from __future__ import annotations

import os
import re
import textwrap

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-3.5-sonnet-20241022"

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
    You are an expert educational video creator producing 3Blue1Brown-style explainers.
    Your response MUST contain exactly two sections with these exact markers:

    ===NARRATION===
    [Voice-over narration text only — natural flowing speech, no stage directions,
     no code, no "(pause)" notes, no timestamps. Just what the narrator says.]
    ===CODE===
    [Complete Manim Python file — raw code only, no markdown fences, no prose]

    ━━━ CONTENT PHILOSOPHY ━━━
    • Study the topic deeply. The user's prompt is a HINT, not a limit.
      Always deliver a COMPLETE, well-structured educational explanation.
    • Structure every video:
        1. Hook — a surprising or motivating question
        2. Motivation — why this topic matters
        3. Core concept — the main idea built up step by step
        4. Key insight — the "aha" moment
        5. Worked example — concrete numbers / visuals
        6. Takeaway — one memorable sentence
    • Narration: brilliant enthusiastic teacher, not a textbook.
      Short punchy sentences. Active voice. Genuine wonder.
    • Adaptive length (estimate 140 words per minute for TTS):
        - Simple / intro topics  → 45–70 s  (~100–165 words)
        - Intermediate topics    → 90–120 s (~210–280 words)
        - Deep / multi-part      → 120–180 s (~280–420 words)

    ━━━ MANIM CODE RULES ━━━
    • Class: `class MainScene(Scene):` (or `ThreeDScene` when 3D is needed)
    • Imports: `from manim import *` and optionally `import numpy as np`
    • NEVER import: os, sys, subprocess, requests, httpx, urllib, socket, pathlib, shutil
    • NEVER call: exec, eval, open, compile, __import__
    • Timing: total Manim runtime ≈ narration duration + 3 s tail buffer.
      Distribute `self.wait(n)` between beats so animations match speech.
    • Palette: BLUE_D, TEAL, YELLOW_C, RED_D, PURPLE_B, GREEN_C, ORANGE, WHITE
    • Animations: Create, Write, FadeIn, FadeOut, Transform, ReplacementTransform,
      Indicate, GrowArrow, Circumscribe, Flash, MoveAlongPath
    • Math: `MathTex(r"...")` with raw strings; prose: `Text("...")`
    • Layout: VGroup + .arrange() / .next_to() — no overlaps allowed
    • Transitions: clear between major sections with
      `self.play(FadeOut(*self.mobjects))`
    • Always end with `self.wait(3)` as audio tail buffer
    • 3D: `self.set_camera_orientation(phi=75*DEGREES, theta=-45*DEGREES)`
      and `self.begin_ambient_camera_rotation(rate=0.1)`
    """
).strip()


class GenerationError(RuntimeError):
    pass


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def _parse_response(raw: str) -> tuple[str, str]:
    """Split LLM output into (narration, manim_code)."""
    if "===CODE===" not in raw:
        raise GenerationError("LLM response missing ===CODE=== marker")

    parts = raw.split("===CODE===", 1)
    narration = parts[0].replace("===NARRATION===", "").strip()
    code = _strip_fences(parts[1].strip())
    return narration, code


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
) -> tuple[str, str]:
    """Ask the LLM to write narration + Manim scene.

    Returns (narration_text, python_code).
    prompt is optional — if empty the LLM builds the full curriculum itself.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise GenerationError("OPENROUTER_API_KEY is not set")

    if prompt.strip():
        guidance = f"User's guidance / focus: {prompt}"
    else:
        guidance = (
            "No specific guidance provided — build the best possible complete "
            "explanation for this topic from scratch."
        )

    user_prompt = textwrap.dedent(
        f"""
        TOPIC: {topic}
        {guidance}
        STYLE: {style}
        DIMENSION: {"3D — use ThreeDScene" if use_3d else "2D — use Scene"}

        Produce the narration and Manim code now.
        """
    ).strip()

    payload = {
        "model": MODEL,
        "temperature": 0.45,
        "max_tokens": 7000,
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

    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(OPENROUTER_URL, json=payload, headers=headers)
        if resp.status_code != 200:
            raise GenerationError(
                f"OpenRouter {resp.status_code} for model {MODEL}: {resp.text[:600]}"
            )
        data = resp.json()

    try:
        raw = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise GenerationError(f"Unexpected LLM response shape: {data}") from e

    narration, code = _parse_response(raw)
    _validate(code)
    return narration, code
