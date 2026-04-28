"""Recipe → full Manim scene file.

The LLM emits a recipe (JSON) like:
    {
      "scenes": [
        {
          "template": "intro_hero",
          "heading": "DNA: The Code of Life",
          "subtext": "Every cell carries this molecular library",
          "params": {"title": "DNA", "color": "BLUE_D"}
        },
        ...
      ]
    }

Each scene gets a slide-style wrapper: a big heading at the top + a caption at
the bottom that stay on screen while the 3D template plays.  The wrapper also
adds a 3-second hold so the visual lingers — viewers absorb what they're seeing
before it fades to the next scene.
"""

from __future__ import annotations

import textwrap

from templates import TEMPLATES, _safe, validate_custom_scene


class RecipeError(ValueError):
    pass


_HEADER = textwrap.dedent('''
    from manim import *
    import numpy as np


    class MainScene(ThreeDScene):
        def construct(self):
            # Default to FLAT 2D camera. 2D works better for most diagrams
            # (graphs, equations, flowcharts, cells, molecules-from-the-side).
            # Scenes that genuinely need 3D set their own camera explicitly.
            self.set_camera_orientation(phi=0, theta=-PI/2, distance=10)
            # NO ambient rotation — it makes 2D diagrams unreadable.
''').strip()


def _wrap_slide(i: int, heading: str, subtext: str, template_body: str) -> str:
    """Wrap a template body with heading + subtext + hold.

    Layout (fixed in frame, doesn't rotate with camera):
      ┌──────────────────────────────────┐
      │   BIG HEADING (top, font 38)     │
      │                                  │
      │       [3D template visual]       │
      │                                  │
      │   subtext (bottom, font 20)      │
      └──────────────────────────────────┘

    Heading appears first, template plays, subtext appears mid-scene, then a 3s
    hold lets the viewer absorb the visual before everything fades out.
    """
    heading = _safe(heading, "")
    subtext = _safe(subtext, "")

    # Unique mobject names per scene so they don't clash across scenes
    h, s = f"slide_h_{i}", f"slide_s_{i}"

    pre = textwrap.dedent(f'''
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # SLIDE {i}: {heading[:50]}
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {h} = Text("{heading}", font_size=38, weight=BOLD, color=WHITE)
        {h}.to_edge(UP, buff=0.18)
        {s} = Text("{subtext}", font_size=22, color=GREY_B)
        {s}.to_edge(DOWN, buff=0.22)
        self.add_fixed_in_frame_mobjects({h}, {s})
        {h}.set_opacity(0)
        {s}.set_opacity(0)
        # Heading + subtext fade in TOGETHER, before the visual builds.
        # Both stay on screen while the template plays underneath.
        self.play({h}.animate.set_opacity(1), {s}.animate.set_opacity(1), run_time=0.8)
    ''').strip()

    # After template plays, hold heading+subtext on screen for a beat, then fade.
    # 3s hold lets the audience absorb what they just saw before the next scene.
    post = textwrap.dedent(f'''
        self.wait(3)
        self.play(FadeOut({h}), FadeOut({s}), run_time=0.5)
    ''').strip()

    return pre + "\n" + template_body + "\n" + post


def compose_scene(recipe: dict) -> str:
    """Build a full Manim scene file from a recipe dict.

    Raises RecipeError if the recipe is malformed or references unknown templates.
    """
    if not isinstance(recipe, dict):
        raise RecipeError("Recipe must be a JSON object")

    scenes = recipe.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise RecipeError("Recipe must contain a non-empty 'scenes' list")
    if len(scenes) < 4:
        raise RecipeError(
            f"Recipe has only {len(scenes)} scene(s) — minimum is 4. "
            "The LLM must output at least 4 scenes for a quality video."
        )

    body_blocks = []
    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            raise RecipeError(f"Scene #{i} must be an object")

        tname = scene.get("template")
        if not tname:
            raise RecipeError(f"Scene #{i} missing 'template' field")

        # ── Custom LLM-generated scene ────────────────────────────────────
        if tname == "custom":
            import textwrap as _tw
            raw_code = scene.get("code", "") or ""
            raw_code = _tw.dedent(raw_code).strip()   # normalise to 0-indent (composer adds 8 later)
            if not raw_code:
                raise RecipeError(f"Scene #{i} has template='custom' but no 'code' field")
            error = validate_custom_scene(raw_code)
            if error:
                raise RecipeError(f"Scene #{i} custom code rejected: {error}")
            block = raw_code  # composer's textwrap.indent adds the 8-space indent
        # ── Standard template ─────────────────────────────────────────────
        else:
            if tname not in TEMPLATES:
                raise RecipeError(
                    f"Unknown template '{tname}'. Available: {sorted(TEMPLATES.keys())}"
                )

            params = scene.get("params", {}) or {}
            if not isinstance(params, dict):
                raise RecipeError(f"Scene #{i} 'params' must be an object")

            # Filter to only the params this template accepts (LLM might add extras)
            accepted = set(TEMPLATES[tname]["params"].keys())
            clean_params = {k: v for k, v in params.items() if k in accepted}

            try:
                block = TEMPLATES[tname]["fn"](**clean_params)
            except Exception as e:
                raise RecipeError(
                    f"Template '{tname}' failed with params {clean_params}: {e}"
                ) from e

        # Wrap the template with heading + subtext + hold
        heading = scene.get("heading", "") or ""
        subtext = scene.get("subtext", "") or ""
        wrapped = _wrap_slide(i, heading, subtext, block)

        body_blocks.append(textwrap.indent(wrapped, "        "))

    # Final wait — renderer auto-extends this to match audio length
    body_blocks.append("        self.wait(4)")

    return _HEADER + "\n" + "\n\n".join(body_blocks) + "\n"
