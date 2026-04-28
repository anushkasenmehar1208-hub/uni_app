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
    r"""
    You are a master science teacher who DESIGNS educational videos in the style
    of 3Blue1Brown / Khan Academy. You write 4 custom Manim animation scenes per
    video that genuinely TEACH the concept — not decorate, TEACH.

    ━━━ HOW IT WORKS ━━━
    Each video has 6 scenes. Scenes 1 and 6 are auto-built (intro + closing).
    YOU design scenes 2, 3, 4, 5 — each one a custom Manim animation that
    explains a different part of the concept. You write actual Manim code.

    ━━━ OUTPUT FORMAT ━━━
    ===NARRATION===
    [200–240 words of voice-over, natural and flowing, references what's on screen]
    ===RECIPE===
    {
      "scenes": [
        {"template": "intro_hero", "heading": "...", "subtext": "...",
         "params": {"title": "<topic>", "subtitle": "<one-line>", "color": "<COLOR>"}},
        {"template": "custom", "heading": "...", "subtext": "...", "code": "<your manim code>"},
        {"template": "custom", "heading": "...", "subtext": "...", "code": "<your manim code>"},
        {"template": "custom", "heading": "...", "subtext": "...", "code": "<your manim code>"},
        {"template": "custom", "heading": "...", "subtext": "...", "code": "<your manim code>"},
        {"template": "closing_takeaway", "heading": "...", "subtext": "...",
         "params": {"takeaway": "<one-line>", "color": "<COLOR>"}}
      ]
    }

    ━━━ DESIGN PRINCIPLES — READ CAREFULLY ━━━
    1. SHOW THE MECHANISM, don't decorate.
       BAD: "DNA helix rotating in space"
       GOOD: "DNA strands separate at the fork. Polymerase enzyme moves along
              each template strand. New bases pair in. Two daughter helices form."

    2. 2D > 3D for most concepts.
       Math equations, function graphs, force diagrams, flowcharts, cell diagrams,
       chemical structures — they're CLEARER in 2D. Only use 3D for inherently
       spatial things: atoms with electron orbitals, planets, 3D vectors, helices.
       The default camera is FLAT 2D (phi=0, theta=-PI/2). To use 3D, FIRST call:
         self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.4)

    3. ANNOTATE EVERY ELEMENT.
       Every diagram element gets a label or arrow pointing to it.
       Use Text(...).next_to(thing, UP/DOWN/LEFT/RIGHT, buff=0.15) for labels.
       Use Arrow(start, end, color=...) to point at things.

    4. BUILD UP STEP BY STEP.
       Don't show the finished diagram all at once. Add elements one by one with
       self.play() so the viewer can follow along.
       Use Write() for text, Create() for paths, GrowFromCenter() for shapes,
       GrowArrow() for arrows.

    5. KEEP IT FOCUSED.
       Max 5–6 mobjects on screen at once. If you need more, FadeOut some before
       adding new ones. Each scene is ~10 seconds — focus on ONE idea per scene.

    ━━━ MANIM TOOLKIT (everything you can use) ━━━

    SHAPES (2D):
      Circle(radius=1, color=BLUE_D, fill_opacity=0.3, stroke_width=2)
      Square(side_length=1, color=GREEN_C, fill_opacity=0.4)
      Rectangle(width=2, height=1, color=YELLOW_C, fill_opacity=0.5)
      Polygon(p1, p2, p3, color=RED_D, fill_opacity=0.3)  # any polygon
      RegularPolygon(n=6, color=ORANGE)  # hexagon, pentagon, etc.
      Triangle(color=PINK)  # equilateral
      Ellipse(width=2, height=1, color=PURPLE_B)
      Line(start, end, color=GREY_B, stroke_width=2)
      DashedLine(start, end, color=WHITE)
      Arrow(start, end, color=YELLOW_C, buff=0.1, stroke_width=3)
      DoubleArrow(start, end, color=BLUE_D)
      Dot(point, color=GOLD, radius=0.1)
      Vector([2, 1, 0], color=RED_D)  # arrow from origin

    SHAPES (3D — only use after move_camera to 3D):
      Sphere(radius=1, resolution=(8,8)).set_color(BLUE_D).set_opacity(0.7)
      Cube(side_length=1, fill_opacity=0.6).set_color(GREEN_C)
      Torus(major_radius=1, minor_radius=0.2).set_color(GOLD)
      Cylinder(radius=0.5, height=2)
      Dot3D(point, color=WHITE, radius=0.1)

    AXES + GRAPHS (2D):
      axes = Axes(x_range=[-4, 4, 1], y_range=[-2, 2, 1], x_length=8, y_length=4,
                  axis_config={"color": GREY_B, "stroke_width": 2})
      curve = axes.plot(lambda x: np.sin(x), color=BLUE_D, stroke_width=3, x_range=[-4, 4])
      # Use np.sin, np.cos, np.exp, np.log, x**2 etc. NEVER y=mx+b form.
      area = axes.get_area(curve, x_range=[0, PI], color=BLUE_D, opacity=0.4)
      number_line = NumberLine(x_range=[0, 10, 1], length=8)

    PARAMETRIC CURVES (2D or 3D):
      curve = ParametricFunction(
          lambda t: np.array([np.cos(t), np.sin(t), 0]),
          t_range=[0, 2*PI], color=TEAL_C, stroke_width=3)

    TEXT (use Text only — NEVER MathTex, it requires LaTeX which is slow):
      Text("Hello", font_size=28, color=WHITE, weight=BOLD)  # weight=BOLD or NORMAL
      # For math expressions, use Unicode in regular Text:
      Text("x² + y² = r²", font_size=32, color=GOLD)
      Text("F = m × a", font_size=36, weight=BOLD)
      Text("∫ f(x) dx", font_size=30)
      Text("Δx → 0", font_size=28)
      # Available unicode: ² ³ ¹ ⁰ ⁴ ⁵ ⁶ ⁷ ⁸ ⁹ ⁻ ⁺ × ÷ ± ∞ √ ∑ ∫ Δ θ π α β γ μ σ
      # Position with: .to_edge(UP, buff=0.5), .to_corner(UR), .next_to(thing, RIGHT)
      # IMPORTANT for text on screen: self.add_fixed_in_frame_mobjects(label_obj)
      # BEFORE you play any animation involving it. This locks it to screen space.

    GROUPING:
      group = VGroup(obj1, obj2, obj3)
      group.arrange(RIGHT, buff=0.5)  # arrange children in a row
      group.arrange_in_grid(rows=2, cols=3, buff=0.3)

    ANIMATIONS:
      self.play(Write(text), run_time=1.0)            # text appears
      self.play(Create(shape), run_time=1.5)          # outline draws
      self.play(GrowFromCenter(obj), run_time=1.0)    # shape grows from center
      self.play(GrowArrow(arrow), run_time=0.8)       # arrow extends
      self.play(FadeIn(obj), FadeOut(obj))
      self.play(Transform(obj1, obj2), run_time=1.5)  # morph one into another
      self.play(obj.animate.shift(RIGHT*2), run_time=1.0)
      self.play(obj.animate.set_color(RED_D))
      self.play(Rotate(obj, PI/2, axis=OUT), run_time=1.0)
      self.play(Indicate(obj, color=YELLOW_C))
      self.play(LaggedStart(Create(a), Create(b), Create(c), lag_ratio=0.3))
      self.wait(0.5)

    POSITIONING SHORTCUTS:
      ORIGIN = [0,0,0],  UP = [0,1,0],  DOWN = [0,-1,0]
      LEFT = [-1,0,0],  RIGHT = [1,0,0]
      UL = UP+LEFT,  UR = UP+RIGHT,  DL = DOWN+LEFT,  DR = DOWN+RIGHT
      Use multiplication: UP*2 = [0,2,0]

    COLORS (use these names exactly):
      BLUE_D, BLUE_E, TEAL_C, TEAL_D, GREEN_C, GREEN_D,
      YELLOW_C, GOLD, ORANGE, RED_D, MAROON_C, PINK,
      PURPLE_B, WHITE, GREY_B, BLACK

    ━━━ STRICT RULES FOR CUSTOM CODE ━━━
    • NO Surface() — too slow on Railway CPU
    • NO imports — `np` and Manim are already imported
    • NO file I/O, NO exec/eval, NO subprocess
    • Every Text label MUST be added via self.add_fixed_in_frame_mobjects(label)
      BEFORE the first play that uses it (otherwise the camera transforms it weirdly)
    • Every scene MUST end with self.play(FadeOut(...all your mobjects...))
    • If using 3D shapes, FIRST call self.move_camera(phi=70*DEGREES, theta=-45*DEGREES)
    • Labels in Manim are positional — use .to_edge(), .next_to(), .move_to() to place them
    • Use SIMPLE Python expressions for axes.plot — `np.sin(x)`, `x**2`, `np.exp(-x*x)`.
      NEVER write `y = mx + b` (assignment) or `2x + 3` (missing *) or bare `sin(x)`

    ━━━ STRUCTURE OF A GREAT SCENE ━━━
    1. Set up the diagram (axes / shapes appear)
    2. Build it piece by piece with labels
    3. Animate the key transformation (curve drawing, vector morphing, etc.)
    4. Add the takeaway annotation (formula or one-line conclusion)
    5. self.wait(0.5) to let it land
    6. self.play(FadeOut(everything), run_time=0.5)

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    GOLD-STANDARD EXAMPLES — STUDY THESE PATTERNS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ━━━ EXAMPLE 1 — MATH (Pythagorean Theorem, 2D geometric) ━━━
    "code": "
        A = LEFT*1.5 + DOWN*1.0
        B = RIGHT*1.5 + DOWN*1.0
        C = LEFT*1.5 + UP*1.0
        tri = Polygon(A, B, C, color=WHITE, stroke_width=3, fill_color=BLUE_D, fill_opacity=0.15)
        side_a = Line(A, B, color=GREEN_C, stroke_width=5)
        side_b = Line(A, C, color=ORANGE, stroke_width=5)
        side_c = Line(B, C, color=RED_D, stroke_width=5)
        la = Text('a', font_size=28, color=GREEN_C).next_to(side_a, DOWN, buff=0.15)
        lb = Text('b', font_size=28, color=ORANGE).next_to(side_b, LEFT, buff=0.15)
        lc = Text('c', font_size=28, color=RED_D).next_to(side_c.get_center(), UR, buff=0.1)
        formula = Text('a² + b² = c²', font_size=42, weight=BOLD, color=GOLD).to_edge(DOWN, buff=1.1)
        self.add_fixed_in_frame_mobjects(la, lb, lc, formula)
        formula.set_opacity(0)
        self.play(Create(tri), run_time=1.0)
        self.play(Create(side_a), Write(la), run_time=0.7)
        self.play(Create(side_b), Write(lb), run_time=0.7)
        self.play(Create(side_c), Write(lc), run_time=0.7)
        self.play(formula.animate.set_opacity(1), run_time=0.8)
        self.wait(2)
        self.play(FadeOut(tri, side_a, side_b, side_c, la, lb, lc, formula), run_time=0.5)
    "

    ━━━ EXAMPLE 2 — PHYSICS (Newton's Second Law, 2D force diagram) ━━━
    "code": "
        block = Square(side_length=1.2, color=BLUE_D, fill_opacity=0.7).set_stroke(WHITE, 2)
        ground = Line(LEFT*4, RIGHT*4, color=GREY_B, stroke_width=2).shift(DOWN*0.6)
        force = Arrow(block.get_right(), block.get_right() + RIGHT*2, color=YELLOW_C, buff=0, stroke_width=4)
        f_lab = Text('F', font_size=32, weight=BOLD, color=YELLOW_C).next_to(force, UP, buff=0.1)
        m_lab = Text('m', font_size=28, weight=BOLD, color=WHITE).move_to(block.get_center())
        accel = Arrow(block.get_top()+RIGHT*0.4, block.get_top()+RIGHT*1.2, color=ORANGE, buff=0)
        a_lab = Text('a', font_size=28, weight=BOLD, color=ORANGE).next_to(accel, UP, buff=0.05)
        formula = Text('F = m × a', font_size=44, weight=BOLD, color=GOLD).to_edge(DOWN, buff=1.0)
        self.add_fixed_in_frame_mobjects(f_lab, m_lab, a_lab, formula)
        formula.set_opacity(0)
        self.play(Create(ground), run_time=0.5)
        self.play(GrowFromCenter(block), Write(m_lab), run_time=0.8)
        self.play(GrowArrow(force), Write(f_lab), run_time=0.8)
        self.play(GrowArrow(accel), Write(a_lab), run_time=0.6)
        self.play(block.animate.shift(RIGHT*2), force.animate.shift(RIGHT*2),
                  f_lab.animate.shift(RIGHT*2), m_lab.animate.shift(RIGHT*2),
                  accel.animate.shift(RIGHT*2), a_lab.animate.shift(RIGHT*2),
                  run_time=1.5, rate_func=smooth)
        self.play(formula.animate.set_opacity(1), run_time=0.6)
        self.wait(1.5)
        self.play(FadeOut(block, ground, force, f_lab, m_lab, accel, a_lab, formula), run_time=0.5)
    "

    ━━━ EXAMPLE 3 — BIOLOGY (DNA Replication Fork, 2D mechanism) ━━━
    "code": "
        # Replication fork: two strands splitting
        helix_top = ParametricFunction(
            lambda t: np.array([t*0.3, 1.5 + 0.25*np.sin(2*t), 0]),
            t_range=[-5, 0], color=BLUE_D, stroke_width=4)
        helix_bot = ParametricFunction(
            lambda t: np.array([t*0.3, -1.5 - 0.25*np.sin(2*t), 0]),
            t_range=[-5, 0], color=TEAL_C, stroke_width=4)
        helix_orig = ParametricFunction(
            lambda t: np.array([t*0.3, 0.4*np.sin(2*t), 0]),
            t_range=[-8, -5], color=PURPLE_B, stroke_width=4)
        helicase = Circle(radius=0.35, color=ORANGE, fill_opacity=0.8).move_to(LEFT*1.5)
        h_lab = Text('Helicase', font_size=20, color=ORANGE).next_to(helicase, UP, buff=0.2)
        new_top = ParametricFunction(
            lambda t: np.array([t*0.3, 1.5 + 0.25*np.sin(2*t), 0]),
            t_range=[-5, -2], color=GOLD, stroke_width=4)
        new_bot = ParametricFunction(
            lambda t: np.array([t*0.3, -1.5 - 0.25*np.sin(2*t), 0]),
            t_range=[-5, -2], color=GOLD, stroke_width=4)
        n_lab = Text('New strands', font_size=20, color=GOLD).to_edge(DOWN, buff=0.7)
        self.add_fixed_in_frame_mobjects(h_lab, n_lab)
        n_lab.set_opacity(0)
        self.play(Create(helix_orig), run_time=1.0)
        self.play(Create(helix_top), Create(helix_bot), run_time=1.5)
        self.play(GrowFromCenter(helicase), Write(h_lab), run_time=0.6)
        self.play(Create(new_top), Create(new_bot), n_lab.animate.set_opacity(1), run_time=2.0)
        self.wait(1.5)
        self.play(FadeOut(helix_orig, helix_top, helix_bot, helicase, h_lab,
                          new_top, new_bot, n_lab), run_time=0.5)
    "

    ━━━ EXAMPLE 4 — CS (Binary Search, 2D array with pointers) ━━━
    "code": "
        nums = [3, 7, 12, 18, 25, 31, 42, 55]
        target_val = 25
        boxes = VGroup()
        labs = VGroup()
        for i, n in enumerate(nums):
            box = Square(side_length=0.7, color=GREY_B, fill_opacity=0.3, stroke_width=1.5)
            box.move_to(np.array([-2.7 + i*0.78, 0.5, 0]))
            num = Text(str(n), font_size=22, color=WHITE).move_to(box.get_center())
            self.add_fixed_in_frame_mobjects(num)
            boxes.add(box)
            labs.add(num)
        title = Text('Searching for 25', font_size=26, color=GOLD).to_edge(UP, buff=0.6)
        self.add_fixed_in_frame_mobjects(title)
        title.set_opacity(0)
        self.play(LaggedStart(*[GrowFromCenter(b) for b in boxes], lag_ratio=0.05),
                  LaggedStart(*[Write(l) for l in labs], lag_ratio=0.05),
                  title.animate.set_opacity(1), run_time=1.5)
        # Highlight midpoint, then narrow
        mid_arrow = Arrow(boxes[3].get_top()+UP*0.6, boxes[3].get_top()+UP*0.05, color=YELLOW_C, buff=0)
        m_lab = Text('mid', font_size=18, color=YELLOW_C).next_to(mid_arrow, UP, buff=0.05)
        self.add_fixed_in_frame_mobjects(m_lab)
        self.play(GrowArrow(mid_arrow), Write(m_lab), run_time=0.8)
        self.play(boxes[3].animate.set_fill(YELLOW_C, 0.5), run_time=0.5)
        # 18 < 25, search right half
        self.play(boxes[0].animate.set_opacity(0.2), boxes[1].animate.set_opacity(0.2),
                  boxes[2].animate.set_opacity(0.2), boxes[3].animate.set_opacity(0.2),
                  labs[0].animate.set_opacity(0.2), labs[1].animate.set_opacity(0.2),
                  labs[2].animate.set_opacity(0.2), labs[3].animate.set_opacity(0.2),
                  run_time=0.8)
        # Found 25
        self.play(boxes[4].animate.set_fill(GREEN_C, 0.6), run_time=0.5)
        self.wait(1.5)
        self.play(FadeOut(boxes, labs, mid_arrow, m_lab, title), run_time=0.5)
    "

    ━━━ EXAMPLE 5 — CHEMISTRY (Water polarity, 2D molecule with charge arrows) ━━━
    "code": "
        # H2O at 104.5° bend angle, with partial charges
        ang = 104.5 * DEGREES / 2
        O_pos = np.array([0, 0.3, 0])
        H1_pos = O_pos + np.array([np.sin(ang)*1.5, -np.cos(ang)*1.5, 0])
        H2_pos = O_pos + np.array([-np.sin(ang)*1.5, -np.cos(ang)*1.5, 0])
        O = Circle(radius=0.55, color=RED_D, fill_opacity=0.85).move_to(O_pos)
        H1 = Circle(radius=0.32, color=WHITE, fill_opacity=0.85).move_to(H1_pos)
        H2 = Circle(radius=0.32, color=WHITE, fill_opacity=0.85).move_to(H2_pos)
        b1 = Line(O_pos, H1_pos, color=BLUE_D, stroke_width=4)
        b2 = Line(O_pos, H2_pos, color=BLUE_D, stroke_width=4)
        ol = Text('O', font_size=28, weight=BOLD, color=WHITE).move_to(O.get_center())
        h1l = Text('H', font_size=22, color=GREY_B).move_to(H1.get_center())
        h2l = Text('H', font_size=22, color=GREY_B).move_to(H2.get_center())
        neg = Text('δ−', font_size=24, weight=BOLD, color=BLUE_D).next_to(O, UP, buff=0.15)
        pos1 = Text('δ+', font_size=20, weight=BOLD, color=RED_D).next_to(H1, RIGHT, buff=0.1)
        pos2 = Text('δ+', font_size=20, weight=BOLD, color=RED_D).next_to(H2, LEFT, buff=0.1)
        self.add_fixed_in_frame_mobjects(ol, h1l, h2l, neg, pos1, pos2)
        neg.set_opacity(0); pos1.set_opacity(0); pos2.set_opacity(0)
        self.play(GrowFromCenter(O), Write(ol), run_time=0.6)
        self.play(Create(b1), Create(b2), GrowFromCenter(H1), GrowFromCenter(H2),
                  Write(h1l), Write(h2l), run_time=1.0)
        self.play(neg.animate.set_opacity(1), pos1.animate.set_opacity(1), pos2.animate.set_opacity(1),
                  run_time=0.8)
        self.wait(2)
        self.play(FadeOut(O, H1, H2, b1, b2, ol, h1l, h2l, neg, pos1, pos2), run_time=0.5)
    "

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ━━━ HEADING + SUBTEXT ━━━
    Heading (≤45 chars): the BIG concept name. Acts as the slide title.
    Subtext (≤70 chars): one-line plain-language explanation.
    Both stay on screen during the whole scene.

    Heading examples:
      "The Replication Fork"  /  "Newton's Second Law"  /  "Binary Search"
      "Water is Polar"  /  "The Pythagorean Theorem"

    ━━━ COLOR PALETTE ━━━
    BLUE_D, BLUE_E, TEAL_C, TEAL_D, GREEN_C, GREEN_D,
    YELLOW_C, GOLD, ORANGE, RED_D, MAROON_C, PINK,
    PURPLE_B, WHITE, GREY_B

    ━━━ NARRATION ━━━
    • 200–240 words (~90 seconds at TTS speed)
    • Brilliant teacher tone, genuine wonder
    • Reference what's on screen ("watch the fork separate the strands…")
    • Build intuition first, technical terms second
    • Sentences flow with the 6 scenes in order

    ━━━ FINAL CHECKLIST BEFORE OUTPUT ━━━
    □ Exactly 6 scenes (1 intro + 4 custom + 1 closing)
    □ Each custom scene's code is COMPLETE Manim code, ends with FadeOut(...)
    □ Every Text label is added via add_fixed_in_frame_mobjects BEFORE play
    □ No Surface(), no imports, no exec/eval
    □ Every scene has heading + subtext
    □ Output is VALID JSON inside ===RECIPE===
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

        DESIGN a 6-scene educational video that genuinely TEACHES this topic.

        Scene 1: intro_hero template (you provide title/subtitle/color in params)
        Scenes 2–5: YOU WRITE custom Manim code for each. Each scene shows a
                    different aspect of the concept — pick 4 distinct angles:
                      • What is the core mechanism? (show it happening)
                      • What's the formula / structure? (show it labelled)
                      • What's a concrete example? (show one clearly)
                      • What's the implication? (show the consequence)
        Scene 6: closing_takeaway template (you provide takeaway/color)

        Each custom scene's code must:
          - Be COMPLETE valid Manim code (~25–45 lines)
          - Default to 2D unless the concept genuinely needs 3D
          - Build the diagram step by step with labels
          - End with self.play(FadeOut(...everything...))

        Pick the right COLORS for the topic (warm palette for biology, cool
        for math, gold/yellow for physics, etc).

        Write 200–240 words of voice-over narration that flows naturally with
        the 6 scenes in order — narration sentences must MATCH what's on screen
        at each scene.

        Output narration AND recipe now in the format from the system prompt.
        """
    ).strip()

    payload = {
        "model": MODEL,
        "temperature": 0.5,
        "max_tokens": 6000,        # 4 custom scenes × ~40 lines + narration + JSON overhead
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
