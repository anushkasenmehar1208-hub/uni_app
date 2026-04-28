"""Recipe → full Manim scene file.

The LLM emits a recipe (JSON) like:
    {
      "scenes": [
        {"template": "intro_hero", "params": {"title": "Photosynthesis", "color": "GREEN_C"}},
        {"template": "bio_cell_simple", "params": {"label": "Plant cell"}},
        {"template": "closing_takeaway", "params": {"takeaway": "Life is light."}}
      ]
    }

This module composes that recipe into a runnable Manim scene file.
"""

from __future__ import annotations

import textwrap

from templates import TEMPLATES


class RecipeError(ValueError):
    pass


_HEADER = textwrap.dedent('''
    from manim import *
    import numpy as np


    class MainScene(ThreeDScene):
        def construct(self):
            self.set_camera_orientation(phi=70*DEGREES, theta=-45*DEGREES, distance=8)
            self.begin_ambient_camera_rotation(rate=0.10)
''').strip()


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

        body_blocks.append(textwrap.indent(block, "        "))

    # Final wait — renderer auto-extends this to match audio length
    body_blocks.append("        self.wait(6)")

    return _HEADER + "\n" + "\n\n".join(body_blocks) + "\n"
