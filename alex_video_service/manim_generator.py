"""LLM-driven recipe generator → composes premium Manim videos from templates.

Pipeline:
  1. Validate topic (profanity / gibberish guard)
  2. Ask LLM for a JSON recipe + narration text
  3. Compose recipe → full Manim scene code
  4. Return (narration_text, scene_code) — renderer takes it from here
"""

from __future__ import annotations

import json
import os
import re
import textwrap

import httpx

from composer import RecipeError, compose_scene
from templates import TEMPLATES, get_template_catalog, list_template_names

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o"


# ──────────────────────────────────────────────────────────────────────────
# Topic validation (profanity / gibberish)
# ──────────────────────────────────────────────────────────────────────────

_PROFANITY = {
    "fuck", "fucking", "fucked", "fucker", "shit", "shitting", "shitty",
    "bitch", "bitches", "bastard", "asshole", "ass", "arse", "damn",
    "cunt", "dick", "cock", "pussy", "piss", "pissed", "crap",
    "nigger", "nigga", "faggot", "fag", "slut", "whore", "porn",
    "sex", "naked", "nude", "rape", "kill", "murder", "suicide",
    "terrorist", "bomb", "drug", "drugs", "cocaine", "heroin", "meth",
    "weed", "cannabis",
}


def _is_gibberish(word: str) -> bool:
    if len(word) <= 2:
        return False
    vowels = set("aeiouAEIOU")
    vowel_count = sum(c in vowels for c in word)
    if len(word) > 4 and vowel_count / len(word) < 0.15:
        return True
    consonants_run = max(
        (len(m.group()) for m in re.finditer(r"[^aeiouAEIOU\W\d_]+", word)),
        default=0,
    )
    return consonants_run >= 5


def validate_topic(topic: str) -> None:
    """Raise GenerationError if topic is inappropriate or gibberish."""
    stripped = topic.strip()
    if not stripped:
        raise GenerationError("Please enter a topic.")

    words = re.findall(r"[a-zA-Z]+", stripped)
    for w in words:
        if w.lower() in _PROFANITY:
            raise GenerationError(
                "Topic contains inappropriate content. "
                "Please enter an educational topic (e.g. Quantum Mechanics, Black Holes, DNA)."
            )

    alpha_chars = sum(c.isalpha() for c in stripped)
    if len(stripped) > 0 and alpha_chars / len(stripped) < 0.4:
        raise GenerationError(
            "Topic looks like random characters. "
            "Please enter a real subject (e.g. Calculus, The French Revolution, Photosynthesis)."
        )

    if words:
        gibberish_count = sum(1 for w in words if _is_gibberish(w))
        if gibberish_count / len(words) >= 0.6:
            raise GenerationError(
                "Topic doesn't look like a real subject. "
                "Please enter something educational (e.g. Machine Learning, Roman Empire, Relativity)."
            )


class GenerationError(RuntimeError):
    pass


# ──────────────────────────────────────────────────────────────────────────
# LLM prompt
# ──────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = textwrap.dedent(
    f"""
    You are a director of premium 3D educational videos in the style of 3Blue1Brown.
    You DO NOT write Python code. You SELECT templates and write narration.

    ━━━ HOW IT WORKS ━━━
    A renderer composes the final video from pre-built, fast-rendering 3D animation
    templates. Your job: pick the right templates and parameters for the topic,
    and write a beautiful voice-over.

    ━━━ OUTPUT FORMAT (MANDATORY) ━━━
    ===NARRATION===
    [Voice-over text, 200–240 words, natural flowing speech]
    ===RECIPE===
    {{
      "scenes": [
        {{
          "template": "<name>",
          "heading": "Big concept name (≤45 chars) shown LARGE at top",
          "subtext": "One-line explanation (≤70 chars) shown small at bottom",
          "params": {{...}}
        }},
        ...
      ]
    }}

    ━━━ HEADING + SUBTEXT — THESE TEACH THE CONCEPT ━━━
    Each scene gets a BIG heading at the top and a caption at the bottom.
    The heading dominates the screen — it's the title of what we're showing.
    The subtext explains what the visual means in plain words.
    The 3D visual underneath illustrates the heading.
    Think: textbook chapter title + diagram + caption.

    GOOD heading examples:
      "The Double Helix"  /  "Newton's Second Law"  /  "Electron Orbitals"
      "Photosynthesis: Light → Sugar"  /  "The Pythagorean Theorem"

    GOOD subtext examples:
      "Two strands of DNA twist around a common axis"
      "Force equals mass times acceleration"
      "Plants convert sunlight into chemical energy"

    ━━━ STRUCTURE — EXACTLY 6 scenes ━━━
    1. Scene 1: `intro_hero` (set up the topic)
    2. Scene 2: subject-specific template (introduce the core mechanism)
    3. Scene 3: subject-specific template (deepen the explanation)
    4. Scene 4: subject-specific template (a different angle / consequence)
    5. Scene 5: `key_insight` (the "aha" beat)
    6. Scene 6: `closing_takeaway` (final takeaway)

    HARD RULE: You MUST output exactly 6 scenes. Not 5, not 4, not 3 — six.
    Each scene MUST use a DIFFERENT template — never repeat template names.

    ━━━ AVAILABLE TEMPLATES ━━━
    {get_template_catalog()}

    ━━━ COLOR PALETTE (use Manim color names) ━━━
    BLUE_D, BLUE_E, TEAL_C, TEAL_D, GREEN_C, GREEN_D,
    YELLOW_C, GOLD, ORANGE, RED_D, MAROON_C, PINK,
    PURPLE_B, WHITE, GREY_B

    ━━━ NARRATION RULES ━━━
    • 200–240 words (~90 seconds of audio)
    • Brilliant teacher tone — short punchy sentences, genuine wonder
    • Reference what the viewer SEES ("watch as the helix unwinds…")
    • Build intuition first, terms second
    • The narration must flow naturally with the scenes you picked

    ━━━ STRICT RULES ━━━
    • Use ONLY templates from the list above — invented names will fail
    • Match parameters from each template's `params` list exactly
    • Pick subject-appropriate templates (don't use cs_neural_network for chemistry)
    • EVERY scene MUST have `heading` (≤45 chars) AND `subtext` (≤70 chars)
    • Labels inside `params` should be short (≤30 chars)
    • Output the recipe as VALID JSON inside ===RECIPE===

    ━━━ EXAMPLE ━━━
    Topic: Photosynthesis
    ===NARRATION===
    Watch a leaf catch sunlight... [200 words about photosynthesis]
    ===RECIPE===
    {{
      "scenes": [
        {{
          "template": "intro_hero",
          "heading": "Photosynthesis",
          "subtext": "How plants turn sunlight into life itself",
          "params": {{"title": "Photosynthesis", "subtitle": "Life from light", "color": "GREEN_C"}}
        }},
        {{
          "template": "bio_cell_simple",
          "heading": "Inside a Plant Cell",
          "subtext": "Chloroplasts capture photons and start the reaction",
          "params": {{"label": "Plant cell", "color": "GREEN_C"}}
        }},
        {{
          "template": "chem_reaction",
          "heading": "The Core Equation",
          "subtext": "Carbon dioxide + water become glucose + oxygen",
          "params": {{"reactants": "CO₂ + H₂O", "products": "Glucose + O₂", "color": "GOLD"}}
        }},
        {{
          "template": "physics_wave_travel",
          "heading": "Sunlight as Waves",
          "subtext": "Photons in the visible spectrum drive the reaction",
          "params": {{"label": "Visible light", "color": "YELLOW_C"}}
        }},
        {{
          "template": "key_insight",
          "heading": "Light → Energy",
          "subtext": "Photons supply the energy that bonds the atoms together",
          "params": {{"label": "Light → Energy", "color": "YELLOW_C"}}
        }},
        {{
          "template": "closing_takeaway",
          "heading": "Life Runs on Light",
          "subtext": "Every breath you take, a leaf made possible",
          "params": {{"takeaway": "Every breath you take, a leaf made possible.", "color": "GREEN_C"}}
        }}
      ]
    }}
    """
).strip()


# ──────────────────────────────────────────────────────────────────────────
# Parsing
# ──────────────────────────────────────────────────────────────────────────

def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def _parse_response(raw: str) -> tuple[str, dict]:
    """Split LLM output into narration + recipe dict."""
    if "===RECIPE===" not in raw:
        raise GenerationError("LLM response missing ===RECIPE=== marker")

    parts = raw.split("===RECIPE===", 1)
    narration = parts[0].replace("===NARRATION===", "").strip()

    recipe_str = _strip_fences(parts[1].strip())
    # If the model wrapped the JSON in any extra commentary, try to extract { ... }
    if not recipe_str.startswith("{"):
        m = re.search(r"\{[\s\S]*\}", recipe_str)
        if not m:
            raise GenerationError(f"Could not find JSON object in recipe: {recipe_str[:200]}")
        recipe_str = m.group(0)

    try:
        recipe = json.loads(recipe_str)
    except json.JSONDecodeError as e:
        raise GenerationError(f"Recipe JSON invalid: {e}\n\n{recipe_str[:400]}") from e

    return narration, recipe


# ──────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────

async def generate_scene_code(
    topic: str,
    prompt: str = "",
    style: str = "",         # ignored — kept for API compat
    use_3d: bool = True,     # ignored — always premium 3D
) -> tuple[str, str]:
    """Returns (narration_text, manim_code) — composed from templates."""
    validate_topic(topic)

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise GenerationError("OPENROUTER_API_KEY is not set")

    if prompt.strip():
        guidance = f"Focus hint from user: {prompt}"
    else:
        guidance = "No specific hint — pick the most insightful angle for this topic."

    user_prompt = textwrap.dedent(
        f"""
        TOPIC: {topic}
        {guidance}

        Build a 6-scene premium video for this topic using ONLY the templates
        listed in the system prompt. You MUST use exactly 6 scenes — never fewer.
        Pick subject-appropriate templates and use a DIFFERENT template for each scene.
        Every scene MUST have a `heading` (big text on top) and `subtext` (caption).
        Write 200–240 words of natural voice-over narration that flows with the scenes.

        Output narration and recipe now.
        """
    ).strip()

    payload = {
        "model": MODEL,
        "temperature": 0.55,
        "max_tokens": 2500,
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

    narration, recipe = _parse_response(raw)

    # Compose recipe → real Manim code
    try:
        code = compose_scene(recipe)
    except RecipeError as e:
        # Fallback: if the LLM hallucinated a template, try a safe minimal recipe
        raise GenerationError(f"Recipe invalid: {e}") from e

    return narration, code
