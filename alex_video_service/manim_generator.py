"""LLM-driven Manim scene generator — premium 3D explainer videos.

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
MODEL = "openai/gpt-4o"

# ── Topic validation ────────────────────────────────────────────────────────

# Common profanity / inappropriate words (lowercase)
_PROFANITY = {
    "fuck", "fucking", "fucked", "fucker", "shit", "shitting", "shitty",
    "bitch", "bitches", "bastard", "asshole", "ass", "arse", "damn",
    "cunt", "dick", "cock", "pussy", "piss", "pissed", "crap",
    "nigger", "nigga", "faggot", "fag", "slut", "whore", "porn",
    "sex", "naked", "nude", "rape", "kill", "murder", "suicide",
    "terrorist", "bomb", "drug", "drugs", "cocaine", "heroin", "meth",
    "weed", "cannabis",   # educational uses will still pass gibberish check
}

def _is_gibberish(word: str) -> bool:
    """Return True if a word looks like random keystrokes."""
    if len(word) <= 2:
        return False          # single chars / abbreviations are fine
    vowels = set("aeiouAEIOU")
    vowel_count = sum(c in vowels for c in word)
    # Fewer than 15% vowels in a word longer than 4 chars → gibberish
    if len(word) > 4 and vowel_count / len(word) < 0.15:
        return True
    # More than 4 consecutive consonants → very likely gibberish
    consonants_run = max(
        (len(m.group()) for m in __import__("re").finditer(r"[^aeiouAEIOU\W\d_]+", word)),
        default=0,
    )
    if consonants_run >= 5:
        return True
    return False


def validate_topic(topic: str) -> None:
    """Raise GenerationError if topic is inappropriate or gibberish."""
    import re as _re

    stripped = topic.strip()
    if not stripped:
        raise GenerationError("Please enter a topic.")

    # Extract words
    words = _re.findall(r"[a-zA-Z]+", stripped)

    # 1. Profanity / inappropriate content check
    for w in words:
        if w.lower() in _PROFANITY:
            raise GenerationError(
                "Topic contains inappropriate content. "
                "Please enter an educational topic (e.g. Quantum Mechanics, Black Holes, DNA)."
            )

    # 2. Non-alphabetic ratio check — "....erf,@#$" style
    alpha_chars = sum(c.isalpha() for c in stripped)
    if len(stripped) > 0 and alpha_chars / len(stripped) < 0.4:
        raise GenerationError(
            "Topic looks like random characters. "
            "Please enter a real subject (e.g. Calculus, The French Revolution, Photosynthesis)."
        )

    # 3. Gibberish word check — if MOST words look like random keystrokes
    if words:
        gibberish_count = sum(1 for w in words if _is_gibberish(w))
        if gibberish_count / len(words) >= 0.6:
            raise GenerationError(
                "Topic doesn't look like a real subject. "
                "Please enter something educational (e.g. Machine Learning, Roman Empire, Relativity)."
            )


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
    You are a Manim animation engineer. Create a SHORT, FAST-RENDERING 3D educational
    video in the style of 3Blue1Brown. Beautiful, clear, never text-heavy.

    ━━━ OUTPUT FORMAT (MANDATORY) ━━━
    ===NARRATION===
    [Voice-over text — natural speech, max 100 words]
    ===CODE===
    [Complete Manim Python file]

    ━━━ SPEED RULES — THESE ARE HARD LIMITS ━━━
    The video renders on a slow server. Violating these = timeout = failure:
    ✗ NO Surface() at all — forbidden, always too slow
    ✗ NO Dot3D groups larger than 5 objects
    ✗ NO more than 4 total mobjects on screen at once
    ✗ NO more than 2 animations in a single self.play() call
    ✗ Total video length: MAX 45 seconds (narration + 4s tail)
    ✗ Narration: MAX 100 words

    ━━━ WHAT TO USE INSTEAD ━━━
    ✅ ThreeDScene with 2–3 simple primitives: Sphere, Cube, Torus, Cylinder, Cone
    ✅ ParametricFunction for curves/paths (fast, beautiful)
    ✅ ThreeDAxes for coordinate systems
    ✅ Arrow3D or Line for vectors (max 3)
    ✅ MathTex labels (short, max 2 per scene)
    ✅ Ambient camera rotation + 1 move_camera() call
    ✅ Color: BLUE_D, TEAL_C, YELLOW_C, RED_D, PURPLE_B, GOLD

    ━━━ STRUCTURE (3 beats, ~45s total) ━━━
    Beat 1 — OPEN (8s): one 3D object appears, camera settles
    Beat 2 — EXPLAIN (25s): 1–2 more objects join, key transform happens
    Beat 3 — CLOSE (8s): clean final composition, fade out

    ━━━ CODE RULES ━━━
    • class MainScene(ThreeDScene):
    • Start: self.set_camera_orientation(phi=70*DEGREES, theta=-45*DEGREES)
             self.begin_ambient_camera_rotation(rate=0.10)
    • from manim import *  (optionally import numpy as np)
    • NEVER import os, sys, subprocess, requests, httpx, pathlib, shutil
    • NEVER call exec, eval, open, compile, __import__
    • End with self.wait(4)

    ━━━ NARRATION STYLE ━━━
    Brilliant teacher. Short punchy sentences. Reference what's on screen.
    Max 100 words. No jargon.
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
    prompt: str = "",
    style: str = "",         # ignored — kept for compat
    use_3d: bool = True,     # ignored — always premium 3D
) -> tuple[str, str]:
    """Returns (narration_text, manim_code) — always premium 3D explainers."""
    # Validate before spending any API credits
    validate_topic(topic)

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise GenerationError("OPENROUTER_API_KEY is not set")

    if prompt.strip():
        guidance = f"Focus hint from user: {prompt}"
    else:
        guidance = "No specific hint — pick the single most insightful angle for this topic."

    user_prompt = textwrap.dedent(
        f"""
        TOPIC: {topic}
        {guidance}

        Create a SHORT 3D explainer: max 45 seconds, max 100 words narration,
        NO Surface(), max 4 objects, simple and beautiful.

        Produce the narration and Manim code now.
        """
    ).strip()

    payload = {
        "model": MODEL,
        "temperature": 0.55,
        "max_tokens": 3000,
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

    async with httpx.AsyncClient(timeout=240.0) as client:
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
