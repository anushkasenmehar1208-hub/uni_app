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
    that look like a Pixar-meets-3Blue1Brown production. Each video MUST feel cinematic,
    visually rich, and delightful — never text-heavy or static.

    ━━━ OUTPUT FORMAT (MANDATORY) ━━━
    ===NARRATION===
    [Voice-over narration text only — natural flowing speech]
    ===CODE===
    [Complete Manim Python file — raw code only]

    ━━━ THE PRIME DIRECTIVE — VISUAL DENSITY ━━━
    ❌ NEVER make text-on-screen videos. Text alone = failure.
    ✅ EVERY scene must show concrete VISUAL OBJECTS doing something:
       3D shapes rotating, surfaces morphing, particles flowing, graphs drawing
       themselves, vectors transforming, atoms orbiting, planets moving,
       cells dividing, equations geometrically interpreted, etc.
    ✅ Text appears ONLY as labels for visuals — never as the main content.
    ✅ Always use ThreeDScene unless the topic is purely 1D/2D abstract.
       Default = ThreeDScene with camera rotation.

    ━━━ REQUIRED VISUAL ELEMENTS (USE LOTS) ━━━
    For EVERY video, mix several of these:
    • 3D primitives — Sphere, Cube, Cylinder, Cone, Torus, Prism, Dot3D
    • Surfaces — Surface, ParametricFunction (3D), use checkerboard_colors
    • Axes — ThreeDAxes() with NumberPlane for floor reference
    • Particle / dot fields — VGroup of 30–100 Dot3D scattered, animated
    • Vector fields, arrows (Arrow3D, Vector)
    • Orbital paths, MoveAlongPath with traced ParametricFunction
    • Wireframes, glowing strokes (set stroke_width + opacity layers)
    • Camera moves: begin_ambient_camera_rotation(rate=0.15),
      move_camera(phi=…, theta=…, run_time=…)
    • Color gradients via set_color_by_gradient(BLUE_D, TEAL, PURPLE_B)
    • Glow effects: Circle/Sphere with low opacity larger versions behind objects

    ━━━ ANIMATION VOCABULARY (USE RICHLY) ━━━
    Create, Write, FadeIn, FadeOut, Transform, ReplacementTransform,
    Rotate, Indicate, Flash, Circumscribe, GrowFromCenter, GrowFromPoint,
    SpinInFromNothing, MoveAlongPath, ApplyMethod, ApplyWave,
    ShowPassingFlash, ShowIncreasingSubsets, LaggedStart, AnimationGroup
    ALWAYS layer 2-3 animations together with AnimationGroup or LaggedStart
    for cinematic feel. Use rate_func=smooth or there_and_back where appropriate.

    ━━━ CONTENT STRUCTURE ━━━
    Every video MUST have these visual phases:
    1. OPENING SHOT — a beautiful 3D object/scene appears with camera move (3–5s)
    2. HOOK — a question posed visually (5–8s)
    3. CORE CONCEPT — built up with multiple visual objects, transformations (30–60s)
    4. KEY INSIGHT — the "wow" moment, often a transformation or reveal (15–25s)
    5. WORKED EXAMPLE — concrete numbers/visuals demonstrating the idea (20–40s)
    6. TAKEAWAY — final beautiful composition + key insight visualized (5–10s)

    Adaptive total length (140 words/min for narration timing):
    • Simple topics → 60–90s of narration (~140–210 words)
    • Most topics → 100–140s of narration (~230–320 words)
    • Deep topics → 140–180s of narration (~320–420 words)

    ━━━ MANDATORY CODE RULES ━━━
    • Class: PREFER `class MainScene(ThreeDScene):` — only fall back to Scene
      if topic is genuinely flat (e.g. pure logic). Default to 3D.
    • For ThreeDScene: ALWAYS start with
        `self.set_camera_orientation(phi=70*DEGREES, theta=-45*DEGREES, distance=8)`
        `self.begin_ambient_camera_rotation(rate=0.12)`
    • `from manim import *`, optionally `import numpy as np`
    • NEVER import: os, sys, subprocess, requests, httpx, urllib, socket, pathlib, shutil
    • NEVER call: exec, eval, open, compile, __import__
    • Time `self.wait()` to match narration; total runtime ≈ narration + 4s buffer
    • Use VGroup heavily; arrange with .arrange() / .next_to()
    • Color palette (mix lavishly): BLUE_D, TEAL_C, YELLOW_C, RED_D, PURPLE_B,
      GREEN_C, ORANGE, PINK, GOLD, MAROON_C, WHITE
    • Apply set_color_by_gradient() to surfaces and curves for visual richness
    • Add stroke_width=2-4 and consider fill_opacity=0.6 for 3D objects
    • Clear scenes between sections with `self.play(FadeOut(*self.mobjects))`
    • Always end with `self.wait(4)` as audio tail buffer

    ━━━ NARRATION RULES ━━━
    • Sound like a brilliant teacher narrating a documentary
    • Short punchy sentences. Active voice. Genuine wonder.
    • Reference what the viewer is SEEING ("watch as the sphere unfolds…")
    • No jargon dumps; build intuition first, terms second

    ━━━ FAILURE CONDITIONS ━━━
    Your output WILL be rejected if it:
    ✗ Has fewer than 5 distinct visual objects/scenes throughout the video
    ✗ Is mostly Text() / MathTex() with little else
    ✗ Lacks any 3D objects when topic could support them
    ✗ Has no camera movement or rotation
    ✗ Has flat colors with no gradients
    ✗ Doesn't synchronize narration to visual beats
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
