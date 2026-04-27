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
    You are an elite Manim animation engineer creating PREMIUM 3D educational videos
    in the style of 3Blue1Brown. Each video must be visually beautiful, clear, and
    delightful — never text-heavy or static.

    ━━━ OUTPUT FORMAT (MANDATORY) ━━━
    ===NARRATION===
    [Voice-over narration text only — natural flowing speech]
    ===CODE===
    [Complete Manim Python file — raw code only]

    ━━━ THE PRIME DIRECTIVE — VISUAL OBJECTS, NOT WALLS OF TEXT ━━━
    ❌ NEVER make text-on-screen videos. Text alone = failure.
    ✅ Every scene shows concrete objects: shapes rotating, graphs drawing,
       vectors transforming, atoms orbiting, equations becoming geometry.
    ✅ Text appears ONLY as short labels on top of visuals.
    ✅ Default to ThreeDScene with camera rotation.

    ━━━ VISUAL ELEMENTS — PICK 4–6 PER VIDEO ━━━
    Choose from these (keep the total count reasonable — quality over quantity):
    • 3D primitives: Sphere, Cube, Cylinder, Cone, Torus — max 5 objects on screen at once
    • Dot3D particle groups: VGroup of 8–15 Dot3D (NOT 30–100 — too slow to render)
    • ParametricFunction (3D curves) — fast and beautiful; prefer over Surface
    • Surface: use SPARINGLY — at most ONE surface per video, keep resolution low
        e.g. Surface(lambda u,v: ..., u_range=[-2,2], v_range=[-2,2],
                     resolution=(12,12))   ← LOW resolution, renders fast
    • ThreeDAxes for coordinate frames
    • Arrow3D, Vector for direction/field visualisations
    • MoveAlongPath on a ParametricFunction for orbital/wave animations

    ━━━ CAMERA & ANIMATION ━━━
    • Start ThreeDScene with:
        self.set_camera_orientation(phi=70*DEGREES, theta=-45*DEGREES, distance=8)
        self.begin_ambient_camera_rotation(rate=0.10)
    • Use 1–2 move_camera() calls for dramatic reveals, not on every transition
    • Animation mix: Create, FadeIn, FadeOut, Rotate, GrowFromCenter, LaggedStart
    • LaggedStart over a VGroup of ≤15 objects — never animate 100 dots individually
    • 1–2 simultaneous animations per play() call — not 5 at once
    • Use rate_func=smooth

    ━━━ CONTENT STRUCTURE (4 phases, not 6) ━━━
    1. OPENING (5–8s) — one beautiful 3D object appears with camera move
    2. CORE CONCEPT (25–40s) — key idea built with 3–5 visual objects + transforms
    3. KEY INSIGHT (15–20s) — the "wow" moment — a single clean reveal
    4. TAKEAWAY (5–8s) — final composition with the core insight visible

    ━━━ VIDEO LENGTH — KEEP IT SHORT ━━━
    Target narration: 60–90 seconds (140–210 words). This is ONE focused idea,
    explained beautifully. Do NOT pad with extra scenes.
    Total video runtime ≈ narration time + 4s buffer.

    ━━━ MANDATORY CODE RULES ━━━
    • Class: `class MainScene(ThreeDScene):` — only use Scene for flat 2D topics
    • `from manim import *`, optionally `import numpy as np`
    • NEVER import: os, sys, subprocess, requests, httpx, urllib, socket, pathlib, shutil
    • NEVER call: exec, eval, open, compile, __import__
    • Time self.wait() to match narration pacing
    • Color palette: BLUE_D, TEAL_C, YELLOW_C, RED_D, PURPLE_B, GREEN_C, GOLD, WHITE
    • set_color_by_gradient() on curves and axes for richness
    • stroke_width=2–3, fill_opacity=0.5–0.7 for 3D objects
    • FadeOut(*self.mobjects) to clear between sections
    • Always end with self.wait(4)

    ━━━ NARRATION RULES ━━━
    • Sound like a brilliant teacher narrating a documentary
    • Short punchy sentences. Active voice. Genuine wonder.
    • Reference what the viewer is SEEING ("watch as the sphere…")
    • No jargon dumps; build intuition first, terms second

    ━━━ FAILURE CONDITIONS ━━━
    Your output WILL be rejected if it:
    ✗ Is mostly Text() / MathTex() with no 3D objects
    ✗ Has more than 20 Dot3D in any single VGroup (render too slow)
    ✗ Uses Surface with resolution > (15,15) (render too slow)
    ✗ Has no camera movement at all
    ✗ Narration exceeds 95 seconds / 220 words
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
        guidance = f"User's hint / focus: {prompt}\n(Use this as inspiration, but ALWAYS deliver a complete premium video.)"
    else:
        guidance = "No specific hint — design the most visually stunning, complete explanation possible."

    user_prompt = textwrap.dedent(
        f"""
        TOPIC: {topic}
        {guidance}

        Build a PREMIUM 3D animated explainer with voice-over. Maximum visual density.
        Cinematic camera moves. Multiple objects. Rich animations. NO text walls.

        Produce the narration and Manim code now.
        """
    ).strip()

    payload = {
        "model": MODEL,
        "temperature": 0.55,
        "max_tokens": 8000,
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
