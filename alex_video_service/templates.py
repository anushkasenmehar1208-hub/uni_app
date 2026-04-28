"""Premium Manim animation templates — fast-rendering, beautiful, reusable.

Each template is a Python function that returns a string of Manim code (the body
of `def construct(self):`).  The composer indents and concatenates these blocks
to build a full scene file.

Design rules for ALL templates:
  • Max 5 mobjects on screen at once
  • No Surface() — too slow on Railway CPU
  • Each template ends with FadeOut so the next starts clean
  • Variable names can be reused across templates (FadeOut clears them)
  • All text labels go through add_fixed_in_frame_mobjects so they stay readable
    while the camera rotates
"""

from __future__ import annotations

import ast
import textwrap
from typing import Callable

# ──────────────────────────────────────────────────────────────────────────
# Registry
# ──────────────────────────────────────────────────────────────────────────

TEMPLATES: dict[str, dict] = {}


def _register(name: str, description: str, params: dict[str, str]):
    """Decorator: register a template function with metadata."""
    def deco(fn: Callable[..., str]):
        TEMPLATES[name] = {
            "fn": fn,
            "description": description,
            "params": params,
        }
        return fn
    return deco


def _code(s: str) -> str:
    """Strip leading/trailing whitespace per line — caller adds final indent."""
    return textwrap.dedent(s).strip()


def _safe(s: str, fallback: str = "") -> str:
    """Sanitize a string for safe insertion into Manim code (escape quotes/newlines)."""
    if s is None:
        return fallback
    s = str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
    return s[:80]  # cap length so labels don't break layout


def _safe_expr(expr: str, var: str = "x", fallback: str = "np.sin(x)") -> str:
    """Validate that `expr` can be the body of a `lambda <var>: ...` AND only
    references known names.  The LLM sometimes:
      - passes textbook equations:  "y = mx + b"   (SyntaxError)
      - passes shorthand variables: "ax + b"       (NameError at runtime)
      - uses ^ instead of **:       "x^2"          (XOR, not power)
    Anything that doesn't parse as a clean math expression in `var` falls back.
    """
    if not expr or not isinstance(expr, str):
        return fallback
    expr = expr.strip()

    # Step 1: must parse as a lambda body
    try:
        tree = ast.parse(f"lambda {var}: {expr}", mode="eval")
    except (SyntaxError, ValueError):
        return fallback

    # Step 2: every Name referenced must be in the allowlist
    # (the lambda var itself, numpy module, common math constants from manim)
    allowed = {var, "np", "PI", "TAU", "E", "DEGREES"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id not in allowed:
            return fallback

    return expr


# ──────────────────────────────────────────────────────────────────────────
# UNIVERSAL — opening, insight, closing
# ──────────────────────────────────────────────────────────────────────────

@_register(
    "intro_hero",
    "Opening shot: a glowing 3D sphere appears with a title. Use as the first scene of nearly every video.",
    {"title": "Main title text", "subtitle": "Subtitle (optional)", "color": "Primary color (e.g. BLUE_D)"},
)
def intro_hero(title: str = "Concept", subtitle: str = "", color: str = "BLUE_D") -> str:
    title = _safe(title, "Concept")
    subtitle = _safe(subtitle, "")
    return _code(f'''
        # Template: intro_hero
        hero = Sphere(radius=1.0, resolution=(10, 10))
        hero.set_color({color})
        hero.set_opacity(0.75)
        glow = Sphere(radius=1.4, resolution=(8, 8))
        glow.set_color({color})
        glow.set_opacity(0.12)
        title_t = Text("{title}", font_size=42, weight=BOLD, color=WHITE)
        sub_t = Text("{subtitle}", font_size=22, color=GREY_B)
        title_grp = VGroup(title_t, sub_t).arrange(DOWN, buff=0.18).to_edge(DOWN, buff=0.8)
        self.add_fixed_in_frame_mobjects(title_grp)
        title_grp.set_opacity(0)
        self.play(GrowFromCenter(glow), GrowFromCenter(hero), run_time=2)
        self.play(title_grp.animate.set_opacity(1), run_time=1)
        self.play(Rotate(hero, angle=TAU, axis=UP), run_time=4, rate_func=linear)
        self.play(FadeOut(hero, glow, title_grp), run_time=0.6)
    ''')


@_register(
    "key_insight",
    "Dramatic reveal moment: object grows then transforms with a flash. Use for the 'aha' beat.",
    {"label": "Short caption shown on screen", "color": "Accent color"},
)
def key_insight(label: str = "Insight", color: str = "GOLD") -> str:
    label = _safe(label, "Insight")
    return _code(f'''
        # Template: key_insight
        core = Cube(side_length=1.4, fill_opacity=0.7).set_color({color})
        ring = Torus(major_radius=2.2, minor_radius=0.08).set_color(TEAL_C)
        cap = Text("{label}", font_size=32, weight=BOLD, color={color}).to_edge(UP, buff=0.6)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(GrowFromCenter(core), run_time=1.2)
        self.play(Create(ring), cap.animate.set_opacity(1), run_time=1.2)
        self.play(Rotate(core, angle=PI, axis=UP+RIGHT), Rotate(ring, angle=PI/2, axis=UP), run_time=3)
        self.play(Indicate(core, color={color}, scale_factor=1.4), run_time=1.5)
        self.play(FadeOut(core, ring, cap), run_time=0.6)
    ''')


@_register(
    "closing_takeaway",
    "Final scene: clean composition with the core takeaway text. Use as the LAST scene.",
    {"takeaway": "1-line summary", "color": "Primary color"},
)
def closing_takeaway(takeaway: str = "Beautiful, isn't it?", color: str = "TEAL_C") -> str:
    takeaway = _safe(takeaway, "Beautiful, isn't it?")
    return _code(f'''
        # Template: closing_takeaway
        s1 = Sphere(radius=0.55, resolution=(8,8)).set_color({color}).set_opacity(0.8).shift(LEFT*1.5)
        s2 = Cube(side_length=0.9, fill_opacity=0.7).set_color(YELLOW_C).rotate(PI/4, axis=UP)
        s3 = Torus(major_radius=0.6, minor_radius=0.15).set_color(PURPLE_B).shift(RIGHT*1.7)
        msg = Text("{takeaway}", font_size=30, color=WHITE).to_edge(DOWN, buff=0.8)
        self.add_fixed_in_frame_mobjects(msg)
        msg.set_opacity(0)
        self.play(LaggedStart(GrowFromCenter(s1), GrowFromCenter(s2), GrowFromCenter(s3),
                              lag_ratio=0.3, run_time=2))
        self.play(msg.animate.set_opacity(1), run_time=1)
        self.play(Rotate(s1, TAU, axis=UP), Rotate(s2, TAU, axis=RIGHT), Rotate(s3, TAU, axis=OUT),
                  run_time=4, rate_func=linear)
        self.play(FadeOut(s1, s2, s3, msg), run_time=0.6)
    ''')


# ──────────────────────────────────────────────────────────────────────────
# MATHEMATICS
# ──────────────────────────────────────────────────────────────────────────

@_register(
    "math_axes_2d_function",
    "2D coordinate axes with an animated function being drawn. Good for: graphs, calculus, functions.",
    {"equation": "Function expression in x (e.g. 'np.sin(x)' or 'x**2')",
     "label": "Function label (e.g. 'y = sin(x)')", "color": "Curve color"},
)
def math_axes_2d_function(equation: str = "np.sin(x)", label: str = "y = sin(x)", color: str = "TEAL_C") -> str:
    label = _safe(label, "y = f(x)")
    equation = _safe_expr(equation, var="x", fallback="np.sin(x)")
    return _code(f'''
        # Template: math_axes_2d_function
        self.move_camera(phi=0, theta=-PI/2, run_time=0.8)
        axes = Axes(x_range=[-4, 4, 1], y_range=[-2.5, 2.5, 1], x_length=8, y_length=5,
                    axis_config={{"color": GREY_B, "stroke_width": 2}})
        graph = axes.plot(lambda x: {equation}, x_range=[-4, 4], color={color}, stroke_width=4)
        lab = Text("{label}", font_size=28, color={color}).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(lab)
        lab.set_opacity(0)
        self.play(Create(axes), run_time=1.5)
        self.play(lab.animate.set_opacity(1), run_time=0.6)
        self.play(Create(graph), run_time=3, rate_func=smooth)
        self.wait(1)
        self.play(FadeOut(axes, graph, lab), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.8)
    ''')


@_register(
    "math_axes_3d_curve",
    "3D axes with an animated parametric curve drawing itself (helix, lissajous, etc.).",
    {"curve_type": "One of: 'helix', 'lissajous', 'spiral', 'knot'", "color": "Curve color", "label": "Curve label"},
)
def math_axes_3d_curve(curve_type: str = "helix", color: str = "BLUE_D", label: str = "3D curve") -> str:
    label = _safe(label, "3D curve")
    eqs = {
        "helix":     "lambda t: np.array([np.cos(t), np.sin(t), 0.25*t])",
        "lissajous": "lambda t: np.array([np.sin(2*t), np.sin(3*t), np.sin(t)])",
        "spiral":    "lambda t: np.array([(0.3+0.2*t)*np.cos(t), (0.3+0.2*t)*np.sin(t), 0.15*t])",
        "knot":      "lambda t: np.array([np.cos(t)*(2+np.cos(2*t)), np.sin(t)*(2+np.cos(2*t)), np.sin(2*t)])",
    }
    eq = eqs.get(curve_type, eqs["helix"])
    t_range = "[0, 4*PI]" if curve_type in ("helix", "spiral") else "[0, 2*PI]"
    return _code(f'''
        # Template: math_axes_3d_curve ({curve_type})
        axes3d = ThreeDAxes(x_range=[-3,3,1], y_range=[-3,3,1], z_range=[-2,2,1],
                            x_length=6, y_length=6, z_length=4)
        curve = ParametricFunction({eq}, t_range={t_range}, color={color}, stroke_width=4)
        curve.set_color_by_gradient({color}, YELLOW_C)
        lab = Text("{label}", font_size=24, color={color}).to_edge(DOWN, buff=0.5)
        self.add_fixed_in_frame_mobjects(lab)
        lab.set_opacity(0)
        self.play(Create(axes3d), run_time=1.5)
        self.play(lab.animate.set_opacity(1), run_time=0.6)
        self.play(Create(curve), run_time=4, rate_func=smooth)
        self.wait(1)
        self.play(FadeOut(axes3d, curve, lab), run_time=0.6)
    ''')


@_register(
    "math_transformation_grid",
    "A grid being transformed by a linear matrix (rotation, shear, scale). Good for: linear algebra.",
    {"transform_type": "One of: 'rotate', 'shear', 'scale', 'flip'", "color": "Grid color"},
)
def math_transformation_grid(transform_type: str = "rotate", color: str = "BLUE_D") -> str:
    matrices = {
        "rotate": "[[np.cos(PI/3), -np.sin(PI/3)], [np.sin(PI/3), np.cos(PI/3)]]",
        "shear":  "[[1, 0.7], [0, 1]]",
        "scale":  "[[1.5, 0], [0, 0.6]]",
        "flip":   "[[1, 0], [0, -1]]",
    }
    M = matrices.get(transform_type, matrices["rotate"])
    return _code(f'''
        # Template: math_transformation_grid ({transform_type})
        self.move_camera(phi=0, theta=-PI/2, run_time=0.8)
        plane = NumberPlane(x_range=[-4,4,1], y_range=[-3,3,1], x_length=7, y_length=5,
                            background_line_style={{"stroke_color": {color}, "stroke_opacity": 0.5}})
        i_hat = Arrow(plane.c2p(0,0), plane.c2p(1,0), color=GREEN_C, buff=0)
        j_hat = Arrow(plane.c2p(0,0), plane.c2p(0,1), color=RED_D, buff=0)
        cap = Text("{transform_type.title()} transformation", font_size=26, color=WHITE).to_edge(UP)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(Create(plane), run_time=1.5)
        self.play(GrowArrow(i_hat), GrowArrow(j_hat), cap.animate.set_opacity(1), run_time=1)
        self.play(plane.animate.apply_matrix({M}),
                  i_hat.animate.apply_matrix({M}),
                  j_hat.animate.apply_matrix({M}),
                  run_time=3, rate_func=smooth)
        self.wait(1)
        self.play(FadeOut(plane, i_hat, j_hat, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.8)
    ''')


@_register(
    "math_geometry_polygons",
    "Rotating 3D platonic solids appearing one by one. Good for: geometry, symmetry.",
    {"label": "Caption (e.g. 'Platonic solids')", "color": "Primary color"},
)
def math_geometry_polygons(label: str = "Symmetry in 3D", color: str = "PURPLE_B") -> str:
    label = _safe(label, "Symmetry in 3D")
    return _code(f'''
        # Template: math_geometry_polygons
        c1 = Cube(side_length=1).set_color({color}).set_fill(opacity=0.6).shift(LEFT*2)
        c2 = Tetrahedron().set_color(YELLOW_C).set_fill(opacity=0.6)
        c3 = Octahedron().set_color(TEAL_C).set_fill(opacity=0.6).shift(RIGHT*2)
        cap = Text("{label}", font_size=28, color=WHITE).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(GrowFromCenter(c1), run_time=0.8)
        self.play(GrowFromCenter(c2), run_time=0.8)
        self.play(GrowFromCenter(c3), cap.animate.set_opacity(1), run_time=0.8)
        self.play(Rotate(c1, TAU, axis=UP), Rotate(c2, TAU, axis=RIGHT), run_time=4, rate_func=linear)
        self.play(Rotate(c3, TAU, axis=UP+RIGHT), run_time=2, rate_func=linear)
        self.play(FadeOut(c1, c2, c3, cap), run_time=0.6)
    ''')


@_register(
    "math_vector_demo",
    "Two vectors being added with the parallelogram rule. Good for: vector algebra, physics intro.",
    {"label_a": "Label for vector A", "label_b": "Label for vector B", "color": "Primary color"},
)
def math_vector_demo(label_a: str = "a", label_b: str = "b", color: str = "TEAL_C") -> str:
    label_a = _safe(label_a, "a")
    label_b = _safe(label_b, "b")
    return _code(f'''
        # Template: math_vector_demo
        self.move_camera(phi=0, theta=-PI/2, run_time=0.8)
        plane = NumberPlane(x_range=[-3,3,1], y_range=[-2,2,1], x_length=7, y_length=5,
                            background_line_style={{"stroke_color": GREY_B, "stroke_opacity": 0.4}})
        a = Arrow(ORIGIN, [2, 0.5, 0], color={color}, buff=0)
        b = Arrow(ORIGIN, [0.7, 1.3, 0], color=YELLOW_C, buff=0)
        a_lab = MathTex(r"\\vec{{{label_a}}}", color={color}).next_to(a.get_end(), UR, buff=0.1)
        b_lab = MathTex(r"\\vec{{{label_b}}}", color=YELLOW_C).next_to(b.get_end(), UR, buff=0.1)
        self.play(Create(plane), run_time=1)
        self.play(GrowArrow(a), Write(a_lab), run_time=1)
        self.play(GrowArrow(b), Write(b_lab), run_time=1)
        b_shifted = Arrow(a.get_end(), a.get_end()+[0.7, 1.3, 0], color=YELLOW_C, buff=0)
        sum_arrow = Arrow(ORIGIN, [2.7, 1.8, 0], color=RED_D, buff=0)
        self.play(TransformFromCopy(b, b_shifted), run_time=1.5)
        self.play(GrowArrow(sum_arrow), run_time=1.5)
        self.wait(1)
        self.play(FadeOut(plane, a, b, a_lab, b_lab, b_shifted, sum_arrow), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.8)
    ''')


# ──────────────────────────────────────────────────────────────────────────
# PHYSICS
# ──────────────────────────────────────────────────────────────────────────

@_register(
    "physics_planet_orbit",
    "A satellite/planet orbiting a central mass with a glowing trail. Good for: gravity, astronomy, atoms.",
    {"central_label": "Label for central body (e.g. 'Sun')", "orbit_label": "Label for orbiter (e.g. 'Earth')",
     "color": "Orbit color"},
)
def physics_planet_orbit(central_label: str = "Sun", orbit_label: str = "Earth", color: str = "BLUE_D") -> str:
    central_label = _safe(central_label, "Sun")
    orbit_label = _safe(orbit_label, "Earth")
    return _code(f'''
        # Template: physics_planet_orbit
        sun = Sphere(radius=0.6, resolution=(8,8)).set_color(YELLOW_C).set_opacity(0.9)
        orbit = ParametricFunction(
            lambda t: np.array([2.5*np.cos(t), 2.5*np.sin(t), 0.3*np.sin(t)]),
            t_range=[0, 2*PI], color={color}, stroke_width=2)
        planet = Dot3D(point=orbit.point_from_proportion(0), radius=0.18, color={color})
        cap = Text("{central_label} & {orbit_label}", font_size=24, color=WHITE).to_edge(DOWN, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(GrowFromCenter(sun), run_time=1.2)
        self.play(Create(orbit), cap.animate.set_opacity(1), run_time=1.2)
        self.play(FadeIn(planet), run_time=0.5)
        self.play(MoveAlongPath(planet, orbit), run_time=8, rate_func=linear)
        self.play(FadeOut(sun, orbit, planet, cap), run_time=0.6)
    ''')


@_register(
    "physics_atom_bohr",
    "Bohr-model atom: nucleus with 2-3 electron orbits. Good for: atomic structure, chemistry intro.",
    {"element": "Element name (e.g. 'Hydrogen', 'Helium')", "color": "Electron color"},
)
def physics_atom_bohr(element: str = "Atom", color: str = "TEAL_C") -> str:
    element = _safe(element, "Atom")
    return _code(f'''
        # Template: physics_atom_bohr
        nucleus = Sphere(radius=0.35, resolution=(8,8)).set_color(RED_D).set_opacity(0.85)
        orbit1 = ParametricFunction(lambda t: np.array([1.2*np.cos(t), 1.2*np.sin(t), 0]),
                                    t_range=[0, 2*PI], color={color}, stroke_width=1.5)
        orbit2 = ParametricFunction(lambda t: np.array([1.9*np.cos(t), 0.4*np.sin(t), 1.0*np.sin(t)]),
                                    t_range=[0, 2*PI], color=PURPLE_B, stroke_width=1.5)
        e1 = Dot3D(point=orbit1.point_from_proportion(0), radius=0.1, color={color})
        e2 = Dot3D(point=orbit2.point_from_proportion(0.5), radius=0.1, color=PURPLE_B)
        cap = Text("{element}", font_size=28, color=WHITE).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(GrowFromCenter(nucleus), cap.animate.set_opacity(1), run_time=1)
        self.play(Create(orbit1), Create(orbit2), run_time=1.5)
        self.play(FadeIn(e1, e2), run_time=0.5)
        self.play(MoveAlongPath(e1, orbit1), MoveAlongPath(e2, orbit2),
                  run_time=7, rate_func=linear)
        self.play(FadeOut(nucleus, orbit1, orbit2, e1, e2, cap), run_time=0.6)
    ''')


@_register(
    "physics_wave_travel",
    "A traveling sinusoidal wave propagating along x-axis. Good for: waves, sound, light, oscillations.",
    {"label": "Wave label (e.g. 'Sound wave')", "color": "Wave color"},
)
def physics_wave_travel(label: str = "Wave", color: str = "BLUE_D") -> str:
    label = _safe(label, "Wave")
    return _code(f'''
        # Template: physics_wave_travel
        self.move_camera(phi=70*DEGREES, theta=-60*DEGREES, run_time=0.6)
        axes = ThreeDAxes(x_range=[-4,4,1], y_range=[-2,2,1], z_range=[-1,1,1],
                          x_length=8, y_length=4, z_length=2)
        phase = ValueTracker(0)
        wave = always_redraw(lambda: ParametricFunction(
            lambda x: np.array([x, np.sin(2*x - phase.get_value()), 0]),
            t_range=[-4, 4, 0.15], color={color}, stroke_width=4))
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(Create(axes), run_time=1)
        self.play(Create(wave), cap.animate.set_opacity(1), run_time=1)
        self.play(phase.animate.set_value(8*PI), run_time=7, rate_func=linear)
        self.play(FadeOut(axes, wave, cap), run_time=0.6)
    ''')


@_register(
    "physics_pendulum",
    "Simple pendulum swinging back and forth. Good for: oscillations, SHM, energy.",
    {"label": "Caption", "color": "Bob color"},
)
def physics_pendulum(label: str = "Simple pendulum", color: str = "GOLD") -> str:
    label = _safe(label, "Simple pendulum")
    return _code(f'''
        # Template: physics_pendulum
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        pivot = Dot3D(point=[0, 2, 0], radius=0.1, color=GREY_B)
        angle = ValueTracker(PI/4)
        rod = always_redraw(lambda: Line(
            start=[0,2,0],
            end=[2*np.sin(angle.get_value()), 2-2*np.cos(angle.get_value()), 0],
            color=GREY_B, stroke_width=3))
        bob = always_redraw(lambda: Sphere(radius=0.25, resolution=(8,8))
            .set_color({color}).set_opacity(0.85)
            .move_to([2*np.sin(angle.get_value()), 2-2*np.cos(angle.get_value()), 0]))
        cap = Text("{label}", font_size=26, color=WHITE).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(FadeIn(pivot), Create(rod), FadeIn(bob), cap.animate.set_opacity(1), run_time=1)
        for _ in range(3):
            self.play(angle.animate.set_value(-PI/4), run_time=1.2, rate_func=there_and_back)
        self.play(angle.animate.set_value(0), run_time=0.8)
        self.play(FadeOut(pivot, rod, bob, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "physics_field_arrows",
    "Vector field with grid of arrows (electric/magnetic/flow). Good for: fields, fluid flow.",
    {"label": "Field label", "color": "Arrow color"},
)
def physics_field_arrows(label: str = "Vector field", color: str = "PURPLE_B") -> str:
    label = _safe(label, "Vector field")
    return _code(f'''
        # Template: physics_field_arrows
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        arrows = VGroup()
        for x in np.linspace(-2.5, 2.5, 5):
            for y in np.linspace(-1.8, 1.8, 4):
                vec = np.array([-y*0.3, x*0.3, 0])
                a = Arrow(start=[x,y,0], end=[x+vec[0], y+vec[1], 0],
                          color={color}, buff=0, stroke_width=2.5)
                arrows.add(a)
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.04, run_time=3))
        self.play(cap.animate.set_opacity(1), run_time=0.6)
        self.play(arrows.animate.rotate(PI/4, about_point=ORIGIN), run_time=2)
        self.wait(1)
        self.play(FadeOut(arrows, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "physics_projectile",
    "Projectile arcing through space (parabola). Good for: kinematics, ballistics, gravity.",
    {"label": "Caption", "color": "Trajectory color"},
)
def physics_projectile(label: str = "Projectile motion", color: str = "RED_D") -> str:
    label = _safe(label, "Projectile motion")
    return _code(f'''
        # Template: physics_projectile
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        ground = Line(start=[-4,-1.5,0], end=[4,-1.5,0], color=GREY_B, stroke_width=2)
        traj = ParametricFunction(
            lambda t: np.array([-3 + 1.5*t, -1.5 + 2*t - 0.4*t*t, 0]),
            t_range=[0, 4], color={color}, stroke_width=3)
        ball = Sphere(radius=0.18, resolution=(8,8)).set_color({color}).set_opacity(0.9)
        ball.move_to(traj.point_from_proportion(0))
        cap = Text("{label}", font_size=26, color=WHITE).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(Create(ground), run_time=0.6)
        self.play(FadeIn(ball), cap.animate.set_opacity(1), run_time=0.6)
        self.play(MoveAlongPath(ball, traj), Create(traj), run_time=4, rate_func=linear)
        self.wait(0.6)
        self.play(FadeOut(ground, traj, ball, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


# ──────────────────────────────────────────────────────────────────────────
# CHEMISTRY
# ──────────────────────────────────────────────────────────────────────────

@_register(
    "chem_molecule_3d",
    "Simple 3D molecule with central atom and 2-4 bonded atoms. Good for: H2O, CH4, NH3, CO2.",
    {"formula": "Molecule formula label (e.g. 'H₂O')", "n_bonds": "Number of bonded atoms (2,3,4)",
     "central_color": "Central atom color", "outer_color": "Outer atoms color"},
)
def chem_molecule_3d(formula: str = "H₂O", n_bonds: int = 3,
                     central_color: str = "RED_D", outer_color: str = "WHITE") -> str:
    formula = _safe(formula, "Molecule")
    try:
        n = max(2, min(4, int(n_bonds)))
    except (ValueError, TypeError):
        n = 3
    # geometry helper
    return _code(f'''
        # Template: chem_molecule_3d ({formula}, n_bonds={n})
        center = Sphere(radius=0.4, resolution=(8,8)).set_color({central_color}).set_opacity(0.9)
        outers = VGroup()
        bonds = VGroup()
        positions_n = {n}
        for i in range(positions_n):
            theta = 2*PI*i/positions_n
            phi = PI/4 if i % 2 == 0 else PI/2
            pos = np.array([1.4*np.sin(phi)*np.cos(theta),
                            1.4*np.sin(phi)*np.sin(theta),
                            1.4*np.cos(phi)*0.6])
            outer = Sphere(radius=0.22, resolution=(8,8)).set_color({outer_color}).set_opacity(0.85).move_to(pos)
            bond = Line(ORIGIN, pos, color=GREY_B, stroke_width=3)
            outers.add(outer)
            bonds.add(bond)
        cap = Text("{formula}", font_size=32, weight=BOLD, color=WHITE).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(GrowFromCenter(center), cap.animate.set_opacity(1), run_time=1)
        self.play(LaggedStart(*[Create(b) for b in bonds], lag_ratio=0.2, run_time=1.5))
        self.play(LaggedStart(*[GrowFromCenter(o) for o in outers], lag_ratio=0.2, run_time=1.5))
        self.play(Rotate(VGroup(center, outers, bonds), angle=TAU, axis=UP), run_time=4, rate_func=linear)
        self.play(FadeOut(center, outers, bonds, cap), run_time=0.6)
    ''')


@_register(
    "chem_bond_form",
    "Two atoms approaching and forming a bond. Good for: bond formation, ionic/covalent bonding.",
    {"atom_a": "Left atom symbol (e.g. 'Na')", "atom_b": "Right atom symbol (e.g. 'Cl')",
     "color_a": "Left atom color", "color_b": "Right atom color"},
)
def chem_bond_form(atom_a: str = "A", atom_b: str = "B",
                   color_a: str = "BLUE_D", color_b: str = "GREEN_C") -> str:
    atom_a = _safe(atom_a, "A")
    atom_b = _safe(atom_b, "B")
    return _code(f'''
        # Template: chem_bond_form
        a = Sphere(radius=0.45, resolution=(8,8)).set_color({color_a}).set_opacity(0.85).shift(LEFT*3)
        b = Sphere(radius=0.45, resolution=(8,8)).set_color({color_b}).set_opacity(0.85).shift(RIGHT*3)
        a_lab = Text("{atom_a}", font_size=24, weight=BOLD, color=WHITE)
        b_lab = Text("{atom_b}", font_size=24, weight=BOLD, color=WHITE)
        self.add_fixed_in_frame_mobjects(a_lab, b_lab)
        a_lab.next_to(a, OUT)
        b_lab.next_to(b, OUT)
        a_lab.set_opacity(0); b_lab.set_opacity(0)
        self.play(GrowFromCenter(a), GrowFromCenter(b),
                  a_lab.animate.set_opacity(1), b_lab.animate.set_opacity(1), run_time=1.2)
        self.play(a.animate.shift(RIGHT*2.2), b.animate.shift(LEFT*2.2), run_time=2)
        bond = Line(a.get_center(), b.get_center(), color=GOLD, stroke_width=4)
        flash = Sphere(radius=0.2, resolution=(8,8)).set_color(GOLD).set_opacity(0.6).move_to(ORIGIN)
        self.play(GrowFromCenter(flash), Create(bond), run_time=0.8)
        self.play(flash.animate.scale(2.5).set_opacity(0), run_time=0.6)
        self.play(Rotate(VGroup(a, b, bond), angle=TAU, axis=UP), run_time=3, rate_func=linear)
        self.play(FadeOut(a, b, bond, a_lab, b_lab), run_time=0.6)
    ''')


@_register(
    "chem_crystal",
    "3x3x3 cubic crystal lattice forming. Good for: solids, crystals, materials science.",
    {"label": "Caption (e.g. 'Cubic lattice')", "color": "Atom color"},
)
def chem_crystal(label: str = "Cubic lattice", color: str = "TEAL_C") -> str:
    label = _safe(label, "Cubic lattice")
    return _code(f'''
        # Template: chem_crystal — 2x2x2 lattice (fast)
        atoms = VGroup()
        for x in range(2):
            for y in range(2):
                for z in range(2):
                    pos = np.array([x-0.5, y-0.5, z-0.5]) * 1.6
                    atom = Sphere(radius=0.28, resolution=(8,8)).set_color({color}).set_opacity(0.85).move_to(pos)
                    atoms.add(atom)
        # add lattice edges (lines) for visual structure
        edges = VGroup()
        for a in atoms:
            for b in atoms:
                d = np.linalg.norm(a.get_center() - b.get_center())
                if 1.5 < d < 1.7:
                    edges.add(Line(a.get_center(), b.get_center(), color=GREY_B, stroke_width=1.5))
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(LaggedStart(*[GrowFromCenter(a) for a in atoms], lag_ratio=0.15, run_time=2))
        self.play(Create(edges), cap.animate.set_opacity(1), run_time=1.5)
        self.play(Rotate(VGroup(atoms, edges), angle=TAU, axis=UP), run_time=4, rate_func=linear)
        self.play(FadeOut(atoms, edges, cap), run_time=0.6)
    ''')


@_register(
    "chem_reaction",
    "Reactants → arrow → products, animated. Good for: chemical reactions, equations.",
    {"reactants": "Reactants text (e.g. '2H₂ + O₂')", "products": "Products text (e.g. '2H₂O')",
     "color": "Accent color"},
)
def chem_reaction(reactants: str = "A + B", products: str = "AB", color: str = "GOLD") -> str:
    reactants = _safe(reactants, "A + B")
    products = _safe(products, "AB")
    return _code(f'''
        # Template: chem_reaction
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        r_ball = Sphere(radius=0.5, resolution=(8,8)).set_color(BLUE_D).set_opacity(0.85).shift(LEFT*3.5)
        p_ball = Sphere(radius=0.5, resolution=(8,8)).set_color({color}).set_opacity(0.85).shift(RIGHT*3.5)
        arrow = Arrow(start=[-1.2,0,0], end=[1.2,0,0], color=YELLOW_C, buff=0, stroke_width=5)
        r_lab = Text("{reactants}", font_size=28, color=WHITE).next_to(r_ball, DOWN, buff=0.5)
        p_lab = Text("{products}", font_size=28, color=WHITE).next_to(p_ball, DOWN, buff=0.5)
        self.add_fixed_in_frame_mobjects(r_lab, p_lab)
        r_lab.set_opacity(0); p_lab.set_opacity(0)
        self.play(GrowFromCenter(r_ball), r_lab.animate.set_opacity(1), run_time=1)
        self.play(GrowArrow(arrow), run_time=1)
        self.play(GrowFromCenter(p_ball), p_lab.animate.set_opacity(1), run_time=1)
        self.play(Indicate(arrow, color=GOLD, scale_factor=1.3), run_time=1.5)
        self.play(Rotate(p_ball, TAU, axis=UP), run_time=3, rate_func=linear)
        self.play(FadeOut(r_ball, p_ball, arrow, r_lab, p_lab), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


# ──────────────────────────────────────────────────────────────────────────
# COMPUTER SCIENCE
# ──────────────────────────────────────────────────────────────────────────

@_register(
    "cs_binary_tree",
    "Binary tree with 7 nodes (3 levels). Good for: data structures, trees, search algorithms.",
    {"label": "Caption", "color": "Node color"},
)
def cs_binary_tree(label: str = "Binary tree", color: str = "BLUE_D") -> str:
    label = _safe(label, "Binary tree")
    return _code(f'''
        # Template: cs_binary_tree
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        positions = [(0,2,0), (-2,0.5,0), (2,0.5,0), (-3,-1,0), (-1,-1,0), (1,-1,0), (3,-1,0)]
        nodes = VGroup(*[Circle(radius=0.35).set_fill({color}, 0.8).set_stroke(WHITE, 2).move_to(p) for p in positions])
        edges = VGroup()
        edge_pairs = [(0,1),(0,2),(1,3),(1,4),(2,5),(2,6)]
        for a, b in edge_pairs:
            edges.add(Line(positions[a], positions[b], color=GREY_B, stroke_width=2))
        cap = Text("{label}", font_size=26, color=WHITE).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(GrowFromCenter(nodes[0]), cap.animate.set_opacity(1), run_time=0.8)
        self.play(LaggedStart(*[Create(e) for e in edges[:2]],
                              GrowFromCenter(nodes[1]), GrowFromCenter(nodes[2]),
                              lag_ratio=0.3, run_time=1.5))
        self.play(LaggedStart(*[Create(e) for e in edges[2:]],
                              *[GrowFromCenter(n) for n in nodes[3:]],
                              lag_ratio=0.15, run_time=2))
        for idx in [0, 1, 3]:
            self.play(Indicate(nodes[idx], color=YELLOW_C, scale_factor=1.4), run_time=0.5)
        self.play(FadeOut(nodes, edges, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "cs_graph_network",
    "Graph with 5 nodes and edges, with traversal highlight. Good for: graphs, networks, BFS/DFS.",
    {"label": "Caption", "color": "Node color"},
)
def cs_graph_network(label: str = "Graph traversal", color: str = "PURPLE_B") -> str:
    label = _safe(label, "Graph traversal")
    return _code(f'''
        # Template: cs_graph_network
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        positions = [(0, 1.5, 0), (-2.2, 0.5, 0), (2.2, 0.5, 0), (-1.2, -1.5, 0), (1.2, -1.5, 0)]
        nodes = VGroup(*[Circle(radius=0.4).set_fill({color}, 0.8).set_stroke(WHITE, 2).move_to(p) for p in positions])
        edges = VGroup()
        edge_pairs = [(0,1),(0,2),(1,3),(2,4),(3,4),(1,2)]
        for a, b in edge_pairs:
            edges.add(Line(positions[a], positions[b], color=GREY_B, stroke_width=2))
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(LaggedStart(*[GrowFromCenter(n) for n in nodes], lag_ratio=0.2, run_time=2))
        self.play(LaggedStart(*[Create(e) for e in edges], lag_ratio=0.15, run_time=2),
                  cap.animate.set_opacity(1))
        for idx in [0, 1, 3, 4, 2]:
            self.play(nodes[idx].animate.set_fill(YELLOW_C, 1.0), run_time=0.4)
        self.play(FadeOut(nodes, edges, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "cs_neural_network",
    "Layered neural network with nodes and connections. Good for: ML, AI, deep learning.",
    {"label": "Caption", "color": "Node color"},
)
def cs_neural_network(label: str = "Neural network", color: str = "TEAL_C") -> str:
    label = _safe(label, "Neural network")
    return _code(f'''
        # Template: cs_neural_network
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        layer_sizes = [3, 4, 3, 2]   # smaller = faster
        layers = []
        for li, sz in enumerate(layer_sizes):
            x = -3 + li*2
            layer = VGroup(*[Circle(radius=0.22).set_fill({color}, 0.85).set_stroke(WHITE, 1.5)
                             .move_to([x, (sz-1)/2 - i, 0]) for i in range(sz)])
            layers.append(layer)
        connections = VGroup()
        for i in range(len(layers)-1):
            for n1 in layers[i]:
                for n2 in layers[i+1]:
                    connections.add(Line(n1.get_center(), n2.get_center(),
                                         color=GREY_B, stroke_width=0.8, stroke_opacity=0.5))
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        for layer in layers:
            self.play(LaggedStart(*[GrowFromCenter(n) for n in layer], lag_ratio=0.1, run_time=0.8))
        self.play(Create(connections), cap.animate.set_opacity(1), run_time=2)
        for idx in range(len(layers)):
            self.play(*[n.animate.set_fill(YELLOW_C, 1.0) for n in layers[idx]], run_time=0.5)
        self.play(FadeOut(*layers, connections, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "cs_sorting_bars",
    "Bars getting sorted (visual sort animation). Good for: sorting algorithms, complexity.",
    {"label": "Caption", "color": "Bar color"},
)
def cs_sorting_bars(label: str = "Sorting", color: str = "BLUE_D") -> str:
    label = _safe(label, "Sorting")
    return _code(f'''
        # Template: cs_sorting_bars
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        heights = [2.0, 0.6, 3.0, 1.2, 2.4, 0.9, 1.7, 2.8]
        bars = VGroup()
        for i, h in enumerate(heights):
            bar = Rectangle(width=0.6, height=h, fill_opacity=0.8, color={color})
            bar.move_to([(i-3.5)*0.75, h/2 - 1.5, 0])
            bars.add(bar)
        cap = Text("{label}", font_size=26, color=WHITE).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.1, run_time=1.5),
                  cap.animate.set_opacity(1))
        sorted_heights = sorted(heights)
        new_bars = VGroup()
        for i, h in enumerate(sorted_heights):
            nb = Rectangle(width=0.6, height=h, fill_opacity=0.8, color=GREEN_C)
            nb.move_to([(i-3.5)*0.75, h/2 - 1.5, 0])
            new_bars.add(nb)
        self.play(Transform(bars, new_bars), run_time=3)
        self.wait(0.6)
        self.play(FadeOut(bars, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "cs_algorithm_steps",
    "Boxes connected by arrows showing algorithm flow. Good for: pseudocode, flowcharts, processes.",
    {"steps": "List of step labels separated by | (e.g. 'Input|Process|Output')",
     "color": "Box color"},
)
def cs_algorithm_steps(steps: str = "Input|Process|Output", color: str = "GOLD") -> str:
    parts = [_safe(p, "step") for p in str(steps).split("|") if p.strip()][:4] or ["Step"]
    n = len(parts)
    return _code(f'''
        # Template: cs_algorithm_steps
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        steps_list = {parts!r}
        boxes = VGroup()
        labels = VGroup()
        gap = 6.0 / max({n}, 1)
        for i, s in enumerate(steps_list):
            box = RoundedRectangle(width=2.0, height=0.9, corner_radius=0.15,
                                   fill_opacity=0.7, color={color})
            box.move_to([-3 + i*gap + gap/2, 0, 0])
            lab = Text(s, font_size=20, color=WHITE).move_to(box.get_center())
            boxes.add(box); labels.add(lab)
        arrows = VGroup()
        for i in range(len(boxes)-1):
            ar = Arrow(boxes[i].get_right(), boxes[i+1].get_left(), color=WHITE, buff=0.1, stroke_width=3)
            arrows.add(ar)
        for b, lab in zip(boxes, labels):
            self.play(GrowFromCenter(b), Write(lab), run_time=0.8)
        for ar in arrows:
            self.play(GrowArrow(ar), run_time=0.5)
        for b in boxes:
            self.play(Indicate(b, color=YELLOW_C, scale_factor=1.1), run_time=0.4)
        self.play(FadeOut(boxes, labels, arrows), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


# ──────────────────────────────────────────────────────────────────────────
# BIOLOGY
# ──────────────────────────────────────────────────────────────────────────

@_register(
    "bio_dna_helix",
    "Rotating DNA double helix with rungs. Good for: DNA, genetics, molecular biology.",
    {"label": "Caption (e.g. 'DNA double helix')", "color": "Backbone color"},
)
def bio_dna_helix(label: str = "DNA", color: str = "TEAL_C") -> str:
    label = _safe(label, "DNA")
    return _code(f'''
        # Template: bio_dna_helix
        helix1 = ParametricFunction(
            lambda t: np.array([0.6*np.cos(t), 0.6*np.sin(t), 0.25*t - 1.5]),
            t_range=[0, 4*PI], color={color}, stroke_width=4)
        helix2 = ParametricFunction(
            lambda t: np.array([0.6*np.cos(t+PI), 0.6*np.sin(t+PI), 0.25*t - 1.5]),
            t_range=[0, 4*PI], color=PURPLE_B, stroke_width=4)
        rungs = VGroup()
        for t in np.linspace(0, 4*PI, 7):
            p1 = np.array([0.6*np.cos(t), 0.6*np.sin(t), 0.25*t - 1.5])
            p2 = np.array([0.6*np.cos(t+PI), 0.6*np.sin(t+PI), 0.25*t - 1.5])
            rungs.add(Line(p1, p2, color=YELLOW_C, stroke_width=2))
        cap = Text("{label}", font_size=26, color=WHITE).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(Create(helix1), Create(helix2), run_time=2)
        self.play(LaggedStart(*[Create(r) for r in rungs], lag_ratio=0.08, run_time=2),
                  cap.animate.set_opacity(1))
        self.play(Rotate(VGroup(helix1, helix2, rungs), angle=TAU, axis=OUT), run_time=4, rate_func=linear)
        self.play(FadeOut(helix1, helix2, rungs, cap), run_time=0.6)
    ''')


@_register(
    "bio_cell_simple",
    "Cell with nucleus and organelles. Good for: cells, biology basics.",
    {"label": "Caption", "color": "Membrane color"},
)
def bio_cell_simple(label: str = "Cell", color: str = "GREEN_C") -> str:
    label = _safe(label, "Cell")
    return _code(f'''
        # Template: bio_cell_simple
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        membrane = Circle(radius=2.5, color={color}, stroke_width=4).set_fill({color}, 0.15)
        nucleus = Circle(radius=0.7, color=PURPLE_B, stroke_width=3).set_fill(PURPLE_B, 0.5)
        org1 = Circle(radius=0.25, color=RED_D).set_fill(RED_D, 0.7).shift(LEFT*1.3 + UP*0.6)
        org2 = Circle(radius=0.3, color=YELLOW_C).set_fill(YELLOW_C, 0.7).shift(RIGHT*1.4 + DOWN*0.4)
        org3 = Circle(radius=0.22, color=BLUE_D).set_fill(BLUE_D, 0.7).shift(DOWN*1.2 + LEFT*0.5)
        cap = Text("{label}", font_size=26, color=WHITE).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(Create(membrane), cap.animate.set_opacity(1), run_time=1.2)
        self.play(GrowFromCenter(nucleus), run_time=0.8)
        self.play(LaggedStart(GrowFromCenter(org1), GrowFromCenter(org2), GrowFromCenter(org3),
                              lag_ratio=0.3, run_time=1.5))
        self.play(Indicate(nucleus, color=YELLOW_C, scale_factor=1.3), run_time=1)
        self.wait(0.8)
        self.play(FadeOut(membrane, nucleus, org1, org2, org3, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "bio_neuron",
    "Neuron with cell body, dendrites, axon, and a signal pulse traveling. Good for: neurons, nervous system.",
    {"label": "Caption", "color": "Neuron color"},
)
def bio_neuron(label: str = "Neuron firing", color: str = "PURPLE_B") -> str:
    label = _safe(label, "Neuron firing")
    return _code(f'''
        # Template: bio_neuron
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        body = Circle(radius=0.5, color={color}).set_fill({color}, 0.7).shift(LEFT*2)
        dendrites = VGroup(*[Line(body.get_center()+0.5*UR, body.get_center()+1.5*UR+0.2*i*UP,
                                  color={color}, stroke_width=3) for i in [-1,0,1]])
        axon = Line(body.get_right(), [3, 0, 0], color={color}, stroke_width=4)
        terminal = Circle(radius=0.18, color=YELLOW_C).set_fill(YELLOW_C, 0.7).move_to([3,0,0])
        pulse = Dot(radius=0.18, color=GOLD).move_to(body.get_right())
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(GrowFromCenter(body), cap.animate.set_opacity(1), run_time=1)
        self.play(LaggedStart(*[Create(d) for d in dendrites], lag_ratio=0.2, run_time=1))
        self.play(Create(axon), run_time=1.2)
        self.play(GrowFromCenter(terminal), run_time=0.5)
        for _ in range(2):
            pulse.move_to(body.get_right())
            self.play(FadeIn(pulse), run_time=0.2)
            self.play(pulse.animate.move_to(terminal.get_center()),
                      Indicate(terminal, color=GOLD), run_time=1.2)
            self.play(FadeOut(pulse), run_time=0.2)
        self.play(FadeOut(body, dendrites, axon, terminal, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


# ──────────────────────────────────────────────────────────────────────────
# GENERAL / ARTS / HISTORY
# ──────────────────────────────────────────────────────────────────────────

@_register(
    "general_timeline",
    "Horizontal timeline with up to 4 markers + dates. Good for: history, evolution, milestones.",
    {"events": "Events separated by | (e.g. '1492 Columbus|1776 Independence|1969 Moon')",
     "color": "Timeline color"},
)
def general_timeline(events: str = "Start|Middle|End", color: str = "GOLD") -> str:
    parts = [_safe(p, "event") for p in str(events).split("|") if p.strip()][:4] or ["Event"]
    return _code(f'''
        # Template: general_timeline
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        ev = {parts!r}
        line = Line([-4,0,0], [4,0,0], color={color}, stroke_width=3)
        markers = VGroup()
        labels = VGroup()
        for i, e in enumerate(ev):
            x = -3.5 + 7*i/max(len(ev)-1, 1)
            m = Dot([x, 0, 0], radius=0.15, color=YELLOW_C)
            l = Text(e, font_size=18, color=WHITE).move_to([x, 0.6 if i % 2 == 0 else -0.6, 0])
            markers.add(m); labels.add(l)
        cap = Text("Timeline", font_size=24, color={color}).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(Create(line), cap.animate.set_opacity(1), run_time=1.5)
        for m, l in zip(markers, labels):
            self.play(GrowFromCenter(m), Write(l), run_time=0.8)
        self.wait(1)
        self.play(FadeOut(line, markers, labels, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "general_comparison",
    "Two 3D objects side-by-side with labels for comparison. Good for: contrasting concepts.",
    {"left_label": "Left object label", "right_label": "Right object label",
     "left_color": "Left color", "right_color": "Right color"},
)
def general_comparison(left_label: str = "A", right_label: str = "B",
                       left_color: str = "BLUE_D", right_color: str = "RED_D") -> str:
    left_label = _safe(left_label, "A")
    right_label = _safe(right_label, "B")
    return _code(f'''
        # Template: general_comparison
        left = Sphere(radius=0.8, resolution=(8,8)).set_color({left_color}).set_opacity(0.85).shift(LEFT*2.2)
        right = Cube(side_length=1.4).set_color({right_color}).set_fill(opacity=0.7).shift(RIGHT*2.2)
        l_lab = Text("{left_label}", font_size=28, color={left_color}, weight=BOLD)
        r_lab = Text("{right_label}", font_size=28, color={right_color}, weight=BOLD)
        l_lab.to_edge(DOWN).shift(LEFT*3)
        r_lab.to_edge(DOWN).shift(RIGHT*3)
        self.add_fixed_in_frame_mobjects(l_lab, r_lab)
        l_lab.set_opacity(0); r_lab.set_opacity(0)
        vs = Text("vs", font_size=32, color=WHITE)
        self.add_fixed_in_frame_mobjects(vs)
        vs.set_opacity(0)
        self.play(GrowFromCenter(left), l_lab.animate.set_opacity(1), run_time=1.2)
        self.play(GrowFromCenter(right), r_lab.animate.set_opacity(1), run_time=1.2)
        self.play(vs.animate.set_opacity(1), run_time=0.5)
        self.play(Rotate(left, TAU, axis=UP), Rotate(right, TAU, axis=UP), run_time=4, rate_func=linear)
        self.play(FadeOut(left, right, l_lab, r_lab, vs), run_time=0.6)
    ''')


@_register(
    "general_globe",
    "Rotating 3D globe with up to 3 highlighted points. Good for: geography, world events, climate.",
    {"label": "Caption", "color": "Globe color"},
)
def general_globe(label: str = "Global view", color: str = "BLUE_D") -> str:
    label = _safe(label, "Global view")
    return _code(f'''
        # Template: general_globe
        globe = Sphere(radius=1.5, resolution=(12,12)).set_color({color}).set_opacity(0.7)
        latitude = ParametricFunction(
            lambda t: np.array([1.5*np.cos(t), 1.5*np.sin(t), 0]),
            t_range=[0, 2*PI], color=GREY_B, stroke_width=1.5)
        longitude = ParametricFunction(
            lambda t: np.array([1.5*np.cos(t), 0, 1.5*np.sin(t)]),
            t_range=[0, 2*PI], color=GREY_B, stroke_width=1.5)
        markers = VGroup(
            Dot3D(point=[1.5*np.cos(0.5)*np.cos(0.7), 1.5*np.cos(0.5)*np.sin(0.7), 1.5*np.sin(0.5)],
                  radius=0.1, color=YELLOW_C),
            Dot3D(point=[1.5*np.cos(-0.3)*np.cos(2.1), 1.5*np.cos(-0.3)*np.sin(2.1), 1.5*np.sin(-0.3)],
                  radius=0.1, color=RED_D),
            Dot3D(point=[1.5*np.cos(0.8)*np.cos(-1.2), 1.5*np.cos(0.8)*np.sin(-1.2), 1.5*np.sin(0.8)],
                  radius=0.1, color=GREEN_C),
        )
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(GrowFromCenter(globe), cap.animate.set_opacity(1), run_time=1.5)
        self.play(Create(latitude), Create(longitude), run_time=1.2)
        self.play(LaggedStart(*[GrowFromCenter(m) for m in markers], lag_ratio=0.3, run_time=1.5))
        self.play(Rotate(VGroup(globe, latitude, longitude, markers), angle=TAU, axis=UP),
                  run_time=5, rate_func=linear)
        self.play(FadeOut(globe, latitude, longitude, markers, cap), run_time=0.6)
    ''')


@_register(
    "general_blocks_build",
    "Cubes stacking up to build a structure. Good for: layered concepts, foundations, architecture.",
    {"label": "Caption", "color": "Block color"},
)
def general_blocks_build(label: str = "Building blocks", color: str = "TEAL_C") -> str:
    label = _safe(label, "Building blocks")
    return _code(f'''
        # Template: general_blocks_build
        blocks = VGroup()
        positions = [(-1,0,0),(0,0,0),(1,0,0),(-0.5,1,0),(0.5,1,0),(0,2,0)]
        for x, y, z in positions:
            b = Cube(side_length=0.9).set_color({color}).set_fill(opacity=0.7).move_to([x, y-1, z])
            blocks.add(b)
        cap = Text("{label}", font_size=28, color=WHITE).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        for i, b in enumerate(blocks):
            target = b.get_center().copy()
            b.shift(UP*5)
            self.play(b.animate.move_to(target), run_time=0.6)
            if i == 0:
                self.play(cap.animate.set_opacity(1), run_time=0.4)
        self.play(Rotate(blocks, angle=TAU, axis=UP), run_time=4, rate_func=linear)
        self.play(FadeOut(blocks, cap), run_time=0.6)
    ''')


@_register(
    "general_concept_map",
    "Central concept with 4 connected sub-concepts radiating outward. Good for: mind maps, taxonomy.",
    {"center": "Central concept", "branches": "Branch labels separated by | (up to 4)",
     "color": "Center color"},
)
def general_concept_map(center: str = "Idea", branches: str = "A|B|C|D", color: str = "GOLD") -> str:
    center = _safe(center, "Idea")
    parts = [_safe(p, "x") for p in str(branches).split("|") if p.strip()][:4] or ["A","B","C","D"]
    while len(parts) < 4:
        parts.append("")
    return _code(f'''
        # Template: general_concept_map
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        br = {parts!r}
        center_circ = Circle(radius=0.7, color={color}, stroke_width=3).set_fill({color}, 0.4)
        center_lab = Text("{center}", font_size=22, color=WHITE, weight=BOLD).move_to(ORIGIN)
        positions = [UP*2.2, RIGHT*2.8, DOWN*2.2, LEFT*2.8]
        colors = [BLUE_D, RED_D, GREEN_C, PURPLE_B]
        nodes = VGroup()
        edges = VGroup()
        labels = VGroup()
        for i, b in enumerate(br):
            if not b:
                continue
            n = Circle(radius=0.45, color=colors[i], stroke_width=2).set_fill(colors[i], 0.4).move_to(positions[i])
            l = Text(b, font_size=18, color=WHITE).move_to(n.get_center())
            e = Line(ORIGIN, positions[i], color=GREY_B, stroke_width=2)
            nodes.add(n); edges.add(e); labels.add(l)
        self.play(GrowFromCenter(center_circ), Write(center_lab), run_time=1)
        for n, e, l in zip(nodes, edges, labels):
            self.play(Create(e), GrowFromCenter(n), Write(l), run_time=0.8)
        self.wait(1)
        self.play(FadeOut(center_circ, center_lab, nodes, edges, labels), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


# ──────────────────────────────────────────────────────────────────────────
# MATHEMATICS — advanced
# ──────────────────────────────────────────────────────────────────────────

@_register(
    "math_derivative_tangent",
    "Tangent line slides along a parabola showing instantaneous slope changing. Good for: derivatives, calculus, rates of change.",
    {"color": "Curve color", "label": "Caption e.g. 'f prime = slope'"},
)
def math_derivative_tangent(color: str = "TEAL_C", label: str = "f'(x) = slope") -> str:
    label = _safe(label, "f'(x) = slope")
    return _code(f'''
        # Template: math_derivative_tangent
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        axes = Axes(x_range=[-3, 3, 1], y_range=[-0.5, 3, 1], x_length=7, y_length=4,
                    axis_config={{"color": GREY_B, "stroke_width": 2}})
        curve = axes.plot(lambda x: 0.4*x**2, color={color}, stroke_width=3)
        cap = Text("{label}", font_size=26, color=GOLD).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(Create(axes), Create(curve), cap.animate.set_opacity(1), run_time=1.5)
        dot = Dot(axes.c2p(-2.5, 0.4*2.5**2), color=GOLD, radius=0.10)
        x_vals = [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]
        tang = None
        self.add(dot)
        for xv in x_vals:
            yv = 0.4*xv**2
            slope = 0.8*xv
            arr = np.array([1.0, slope, 0.0])
            arr = arr / np.linalg.norm(arr) * 1.6
            p = axes.c2p(xv, yv)
            new_line = Line(p - arr, p + arr, color=GOLD, stroke_width=3)
            new_dot = Dot(p, color=GOLD, radius=0.10)
            if tang is None:
                tang = new_line
                self.add(tang)
                self.play(Transform(dot, new_dot), run_time=0.4)
            else:
                self.play(Transform(tang, new_line), Transform(dot, new_dot), run_time=0.6)
        self.wait(0.5)
        self.play(FadeOut(axes, curve, tang, dot, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "math_integral_area",
    "Shaded area grows under a sine curve as the integral accumulates. Good for: integrals, area under curve, calculus.",
    {"color": "Fill color", "label": "Caption e.g. 'Area = integral'"},
)
def math_integral_area(color: str = "BLUE_D", label: str = "∫f(x)dx = area") -> str:
    label = _safe(label, "∫f(x)dx = area")
    return _code(f'''
        # Template: math_integral_area
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        axes = Axes(x_range=[0, 2*PI, PI/2], y_range=[-1.5, 1.5, 1], x_length=8, y_length=4,
                    axis_config={{"color": GREY_B, "stroke_width": 2}})
        curve = axes.plot(lambda x: np.sin(x), color={color}, stroke_width=3)
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(Create(axes), Create(curve), run_time=1.5)
        self.play(cap.animate.set_opacity(1), run_time=0.5)
        area = axes.get_area(curve, x_range=[0, 2*PI], color={color}, opacity=0.5)
        self.play(Create(area), run_time=3, rate_func=smooth)
        self.wait(1)
        self.play(FadeOut(axes, curve, area, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "math_pythagorean",
    "Right triangle appears with colored squares on each side — visualizes a² + b² = c². Good for: Pythagorean theorem, geometry.",
    {"color": "Hypotenuse color", "label": "Caption"},
)
def math_pythagorean(color: str = "PURPLE_B", label: str = "a² + b² = c²") -> str:
    label = _safe(label, "a² + b² = c²")
    return _code(f'''
        # Template: math_pythagorean
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        A = np.array([-1.5, -1.0, 0])
        B = np.array([ 1.5, -1.0, 0])
        C = np.array([-1.5,  1.5, 0])
        tri = Polygon(A, B, C, color=WHITE, stroke_width=3, fill_color=WHITE, fill_opacity=0.08)
        sq_a = Square(side_length=3.0, color=GREEN_C, fill_opacity=0.35).set_stroke(GREEN_C, 2)
        sq_a.move_to((A+B)/2 + np.array([0, -1.5, 0]))
        sq_b = Square(side_length=2.5, color=BLUE_D, fill_opacity=0.35).set_stroke(BLUE_D, 2)
        sq_b.move_to((A+C)/2 + np.array([-1.25, 0, 0]))
        hyp_len = np.linalg.norm(B - C)
        sq_c = Square(side_length=round(hyp_len, 2), color={color}, fill_opacity=0.35).set_stroke({color}, 2)
        sq_c.move_to((B+C)/2 + np.array([1.3, 0.4, 0]))
        cap = Text("{label}", font_size=30, weight=BOLD, color=WHITE).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(Create(tri), run_time=1)
        self.play(GrowFromCenter(sq_a), GrowFromCenter(sq_b), run_time=1.2)
        self.play(GrowFromCenter(sq_c), cap.animate.set_opacity(1), run_time=1.2)
        self.wait(2)
        self.play(FadeOut(tri, sq_a, sq_b, sq_c, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "math_fourier_waves",
    "Multiple sine waves stack together to build a complex waveform — visualizes Fourier series. Good for: signals, waves, frequency decomposition.",
    {"color": "Primary wave color", "label": "Caption e.g. 'Fourier Series'"},
)
def math_fourier_waves(color: str = "BLUE_D", label: str = "Fourier Series") -> str:
    label = _safe(label, "Fourier Series")
    return _code(f'''
        # Template: math_fourier_waves
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        axes = Axes(x_range=[0, 2*PI, PI/2], y_range=[-2.5, 2.5, 1], x_length=8, y_length=4,
                    axis_config={{"color": GREY_B, "stroke_width": 2}})
        cap = Text("{label}", font_size=28, color={color}).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        w1 = axes.plot(lambda x: np.sin(x), color={color}, stroke_width=3)
        w2 = axes.plot(lambda x: np.sin(x) + 0.5*np.sin(3*x), color=TEAL_C, stroke_width=3)
        w3 = axes.plot(lambda x: np.sin(x) + 0.5*np.sin(3*x) + 0.33*np.sin(5*x), color=GOLD, stroke_width=3)
        self.play(Create(axes), cap.animate.set_opacity(1), run_time=1.0)
        self.play(Create(w1), run_time=1.5)
        self.play(Transform(w1, w2), run_time=1.5)
        self.play(Transform(w1, w3), run_time=1.5)
        self.wait(1)
        self.play(FadeOut(axes, w1, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "math_normal_distribution",
    "Bell curve draws itself with mean and standard deviation marked — visualizes probability distributions. Good for: statistics, normal distribution.",
    {"color": "Curve color", "label": "Caption e.g. 'Normal Distribution'"},
)
def math_normal_distribution(color: str = "TEAL_C", label: str = "Normal Distribution") -> str:
    label = _safe(label, "Normal Distribution")
    return _code(f'''
        # Template: math_normal_distribution
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        axes = Axes(x_range=[-3.5, 3.5, 1], y_range=[0, 0.5, 0.1], x_length=8, y_length=4,
                    axis_config={{"color": GREY_B, "stroke_width": 2}})
        bell = axes.plot(lambda x: (1/(2*PI)**0.5)*np.exp(-0.5*x**2),
                         color={color}, stroke_width=4)
        area_c = axes.get_area(bell, x_range=[-1, 1], color={color}, opacity=0.4)
        mean_line = DashedLine(axes.c2p(0, 0), axes.c2p(0, 0.42), color=WHITE, stroke_width=2)
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.5)
        sig = Text("68%  within  ±1σ", font_size=20, color=GREY_B).to_edge(DOWN, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap, sig)
        cap.set_opacity(0); sig.set_opacity(0)
        self.play(Create(axes), cap.animate.set_opacity(1), run_time=1.0)
        self.play(Create(bell), run_time=2.5)
        self.play(Create(area_c), Create(mean_line), sig.animate.set_opacity(1), run_time=1.2)
        self.wait(1.5)
        self.play(FadeOut(axes, bell, area_c, mean_line, cap, sig), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "math_euler_identity",
    "Unit circle on complex plane with rotating point tracing e^(iθ) — visualizes Euler's formula. Good for: complex numbers, trigonometry.",
    {"color": "Primary color", "label": "Caption e.g. 'e^(iπ) + 1 = 0'"},
)
def math_euler_identity(color: str = "GOLD", label: str = "e^(iθ) = cos θ + i·sin θ") -> str:
    label = _safe(label, "Euler's Formula")
    return _code(f'''
        # Template: math_euler_identity
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        axes = Axes(x_range=[-1.8, 1.8, 1], y_range=[-1.8, 1.8, 1], x_length=5, y_length=5,
                    axis_config={{"color": GREY_B, "stroke_width": 2}})
        circle = Circle(radius=axes.get_x_axis().get_unit_size(), color=BLUE_D,
                        stroke_width=2).move_to(axes.c2p(0, 0))
        cap = Text("{label}", font_size=24, color={color}).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(Create(axes), Create(circle), cap.animate.set_opacity(1), run_time=1.5)
        dot = Dot(axes.c2p(1, 0), color={color}, radius=0.12)
        radius_line = Line(axes.c2p(0, 0), axes.c2p(1, 0), color={color}, stroke_width=2)
        self.play(GrowFromCenter(dot), Create(radius_line), run_time=0.5)
        trace = TracedPath(dot.get_center, stroke_color={color}, stroke_width=3)
        self.add(trace)
        for angle in [PI/2, PI, 3*PI/2, 2*PI]:
            new_pos = axes.c2p(np.cos(angle), np.sin(angle))
            self.play(
                dot.animate.move_to(new_pos),
                radius_line.animate.put_start_and_end_on(axes.c2p(0, 0), new_pos),
                run_time=1.0, rate_func=linear
            )
        self.wait(0.5)
        self.play(FadeOut(axes, circle, dot, radius_line, trace, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "math_limit_zoom",
    "Zooms into a point on a curve to show the curve becoming straight — visualizes limits and continuity. Good for: limits, epsilon-delta, continuity.",
    {"color": "Curve color", "label": "Caption"},
)
def math_limit_zoom(color: str = "TEAL_C", label: str = "Limit: zoom in to a point") -> str:
    label = _safe(label, "Limit: zoom in to a point")
    return _code(f'''
        # Template: math_limit_zoom
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        axes = Axes(x_range=[-4, 4, 1], y_range=[-1, 4, 1], x_length=7, y_length=4,
                    axis_config={{"color": GREY_B, "stroke_width": 2}})
        curve = axes.plot(lambda x: 0.5*x**2, color={color}, stroke_width=3)
        highlight = Dot(axes.c2p(1, 0.5), color=GOLD, radius=0.15)
        cap = Text("{label}", font_size=24, color={color}).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(Create(axes), Create(curve), cap.animate.set_opacity(1), run_time=1.5)
        self.play(GrowFromCenter(highlight), run_time=0.6)
        axes2 = Axes(x_range=[0.5, 1.5, 0.25], y_range=[0, 1, 0.25], x_length=7, y_length=4,
                     axis_config={{"color": GREY_B, "stroke_width": 2}})
        curve2 = axes2.plot(lambda x: 0.5*x**2, color={color}, stroke_width=3)
        self.play(Transform(axes, axes2), Transform(curve, curve2), FadeOut(highlight), run_time=2.0)
        local_line = axes2.plot(lambda x: 1.0*x - 0.5, color=GOLD, stroke_width=3, x_range=[0.6, 1.4])
        self.play(Create(local_line), run_time=1.0)
        self.wait(1)
        self.play(FadeOut(axes, curve, local_line, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


# ──────────────────────────────────────────────────────────────────────────
# PHYSICS — advanced
# ──────────────────────────────────────────────────────────────────────────

@_register(
    "physics_magnetic_field",
    "Bar magnet with curved field lines flowing from north to south pole. Good for: magnetism, electromagnetism, field lines.",
    {"color": "Field line color", "label": "Caption e.g. 'Magnetic field'"},
)
def physics_magnetic_field(color: str = "BLUE_D", label: str = "Magnetic field lines") -> str:
    label = _safe(label, "Magnetic field lines")
    return _code(f'''
        # Template: physics_magnetic_field
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        magnet_n = Rectangle(width=0.8, height=1.6, fill_opacity=0.9, fill_color=RED_D).set_stroke(WHITE, 1)
        magnet_s = Rectangle(width=0.8, height=1.6, fill_opacity=0.9, fill_color=BLUE_D).set_stroke(WHITE, 1)
        magnet_n.move_to(LEFT*0.4)
        magnet_s.move_to(RIGHT*0.4)
        n_lab = Text("N", font_size=24, weight=BOLD, color=WHITE).move_to(magnet_n.get_center())
        s_lab = Text("S", font_size=24, weight=BOLD, color=WHITE).move_to(magnet_s.get_center())
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(GrowFromCenter(magnet_n), GrowFromCenter(magnet_s), Write(n_lab), Write(s_lab),
                  cap.animate.set_opacity(1), run_time=1.2)
        curves = VGroup()
        for h in [-1.2, -0.6, 0.0, 0.6, 1.2]:
            ctrl = np.array([0, h * 2.2 + 0.1, 0])
            c = CubicBezier(
                np.array([-0.4, h, 0]),
                np.array([-1.5, h + 0.8 * np.sign(h + 0.01), 0]),
                np.array([1.5, h + 0.8 * np.sign(h + 0.01), 0]),
                np.array([0.4, h, 0]),
                stroke_color={color}, stroke_width=2
            )
            curves.add(c)
        self.play(LaggedStart(*[Create(c) for c in curves], lag_ratio=0.2, run_time=3))
        self.wait(1)
        self.play(FadeOut(magnet_n, magnet_s, n_lab, s_lab, curves, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "physics_refraction",
    "Light ray hits a glass surface and bends — shows Snell's law refraction. Good for: optics, light, refraction, Snell's law.",
    {"color": "Light ray color", "label": "Caption e.g. 'Light bends at boundary'"},
)
def physics_refraction(color: str = "YELLOW_C", label: str = "Snell's Law: light bends") -> str:
    label = _safe(label, "Snell's Law: light bends")
    return _code(f'''
        # Template: physics_refraction
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        surface = Line(LEFT*4, RIGHT*4, color=BLUE_D, stroke_width=2)
        glass = Rectangle(width=8, height=2.5, fill_color=BLUE_D, fill_opacity=0.15).set_stroke(width=0)
        glass.next_to(surface, DOWN, buff=0)
        glass_lab = Text("Glass  (n=1.5)", font_size=20, color=BLUE_D).to_edge(DOWN, buff=0.5)
        air_lab = Text("Air  (n=1.0)", font_size=20, color=WHITE).to_edge(UP, buff=0.5)
        cap = Text("{label}", font_size=26, color={color}).to_corner(UR, buff=0.3)
        self.add_fixed_in_frame_mobjects(glass_lab, air_lab, cap)
        glass_lab.set_opacity(0); air_lab.set_opacity(0); cap.set_opacity(0)
        self.play(Create(surface), FadeIn(glass), run_time=0.8)
        self.play(glass_lab.animate.set_opacity(1), air_lab.animate.set_opacity(1),
                  cap.animate.set_opacity(1), run_time=0.6)
        incident = Arrow(LEFT*2.5 + UP*2.5, ORIGIN, color={color}, buff=0, stroke_width=3)
        refracted = Arrow(ORIGIN, RIGHT*1.8 + DOWN*2.3, color={color}, buff=0, stroke_width=3)
        normal = DashedLine(UP*2, DOWN*2, color=GREY_B, stroke_width=1.5).move_to(ORIGIN)
        self.play(Create(normal), run_time=0.5)
        self.play(GrowArrow(incident), run_time=1.2)
        self.play(GrowArrow(refracted), run_time=1.2)
        self.wait(1.5)
        self.play(FadeOut(surface, glass, incident, refracted, normal,
                          glass_lab, air_lab, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "physics_spring_oscillation",
    "Mass hanging on a spring oscillates up and down — shows simple harmonic motion. Good for: springs, SHM, Hooke's law, oscillations.",
    {"color": "Spring color", "label": "Caption e.g. 'Simple Harmonic Motion'"},
)
def physics_spring_oscillation(color: str = "TEAL_C", label: str = "Simple Harmonic Motion") -> str:
    label = _safe(label, "Simple Harmonic Motion")
    return _code(f'''
        # Template: physics_spring_oscillation
        anchor = np.array([0, 2.8, 0])
        anchor_dot = Dot3D(point=anchor, color=GREY_B, radius=0.12)
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(GrowFromCenter(anchor_dot), cap.animate.set_opacity(1), run_time=0.8)
        t = ValueTracker(0)
        def get_mass_pos():
            return np.array([0, 2.8 - 1.8 - 0.8*np.sin(2*t.get_value()), 0])
        def get_spring():
            top = anchor
            bot = get_mass_pos() + np.array([0, 0.25, 0])
            n_coils = 8
            pts = []
            for i in range(n_coils * 4 + 1):
                frac = i / (n_coils * 4)
                y = top[1] + (bot[1] - top[1]) * frac
                x = 0.18 * np.sin(i * PI / 2) * (1 - abs(frac - 0.5))
                pts.append([x, y, 0])
            return VMobject(stroke_color={color}, stroke_width=2.5).set_points_as_corners(
                [np.array(p) for p in pts])
        def get_mass():
            return Square(side_length=0.5, fill_color=RED_D, fill_opacity=0.9).move_to(get_mass_pos())
        spring = always_redraw(get_spring)
        mass = always_redraw(get_mass)
        self.add(spring, mass)
        self.play(t.animate.set_value(3*PI), run_time=6, rate_func=linear)
        self.play(FadeOut(spring, mass, anchor_dot, cap), run_time=0.6)
    ''')


@_register(
    "physics_two_body_collision",
    "Two spheres approach, collide, and bounce away — shows conservation of momentum. Good for: momentum, elastic collision, Newton's laws.",
    {"color": "Primary sphere color", "label": "Caption"},
)
def physics_two_body_collision(color: str = "ORANGE", label: str = "Conservation of Momentum") -> str:
    label = _safe(label, "Conservation of Momentum")
    return _code(f'''
        # Template: physics_two_body_collision
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        s1 = Sphere(radius=0.45, resolution=(8,8)).set_color({color}).set_opacity(0.85).move_to(LEFT*3.5)
        s2 = Sphere(radius=0.55, resolution=(8,8)).set_color(BLUE_D).set_opacity(0.85).move_to(RIGHT*3.5)
        arr1 = Arrow(s1.get_center() + LEFT*0.8, s1.get_center(), color=YELLOW_C, buff=0)
        arr2 = Arrow(s2.get_center() + RIGHT*0.8, s2.get_center(), color=YELLOW_C, buff=0)
        self.play(GrowFromCenter(s1), GrowFromCenter(s2),
                  GrowArrow(arr1), GrowArrow(arr2), cap.animate.set_opacity(1), run_time=1.0)
        self.play(
            s1.animate.move_to(LEFT*0.5), arr1.animate.shift(RIGHT*3),
            s2.animate.move_to(RIGHT*0.6), arr2.animate.shift(LEFT*3),
            run_time=1.5, rate_func=smooth
        )
        flash = Flash(ORIGIN, color=YELLOW_C, line_length=0.4, flash_radius=1.0)
        self.play(flash, FadeOut(arr1, arr2), run_time=0.4)
        arr3 = Arrow(s1.get_center(), s1.get_center() + LEFT*2.0, color=TEAL_C, buff=0)
        arr4 = Arrow(s2.get_center(), s2.get_center() + RIGHT*2.0, color=TEAL_C, buff=0)
        self.play(
            s1.animate.move_to(LEFT*3.5), GrowArrow(arr3),
            s2.animate.move_to(RIGHT*3.5), GrowArrow(arr4),
            run_time=1.5, rate_func=smooth
        )
        self.wait(0.5)
        self.play(FadeOut(s1, s2, arr3, arr4, cap), run_time=0.6)
    ''')


@_register(
    "physics_electric_circuit",
    "Simple DC circuit with battery and resistor — current flows as animated dots. Good for: circuits, Ohm's law, current, voltage.",
    {"color": "Circuit color", "label": "Caption e.g. 'V = IR'"},
)
def physics_electric_circuit(color: str = "YELLOW_C", label: str = "Ohm's Law: V = IR") -> str:
    label = _safe(label, "Ohm's Law: V = IR")
    return _code(f'''
        # Template: physics_electric_circuit
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        loop = Square(side_length=3.5, color={color}, stroke_width=2.5).move_to(ORIGIN)
        bat_body = Rectangle(width=0.35, height=0.9, fill_color=GREY_B, fill_opacity=0.8).move_to(loop.get_left())
        plus = Text("+", font_size=22, color=RED_D).next_to(bat_body, UP, buff=0.05)
        minus = Text("−", font_size=22, color=BLUE_D).next_to(bat_body, DOWN, buff=0.05)
        res = Rectangle(width=0.7, height=0.32, fill_color=ORANGE, fill_opacity=0.8).move_to(loop.get_right())
        res_lab = Text("R", font_size=20, color=WHITE).move_to(res.get_center())
        cap = Text("{label}", font_size=28, weight=BOLD, color={color}).to_edge(UP, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap, plus, minus, res_lab)
        cap.set_opacity(0)
        self.play(Create(loop), GrowFromCenter(bat_body), GrowFromCenter(res),
                  Write(plus), Write(minus), Write(res_lab), cap.animate.set_opacity(1), run_time=1.5)
        path_pts = [loop.get_top(), loop.get_right(), loop.get_bottom(), loop.get_left(), loop.get_top()]
        for _ in range(2):
            for j in range(len(path_pts)-1):
                e_dot = Dot(path_pts[j], color={color}, radius=0.09)
                self.add(e_dot)
                self.play(e_dot.animate.move_to(path_pts[j+1]), run_time=0.6, rate_func=linear)
                self.remove(e_dot)
        self.wait(0.5)
        self.play(FadeOut(loop, bat_body, res, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


# ──────────────────────────────────────────────────────────────────────────
# CHEMISTRY — advanced
# ──────────────────────────────────────────────────────────────────────────

@_register(
    "chem_orbital_shapes",
    "s orbital (sphere) morphs into p orbital (dumbbell shape) — shows atomic orbital geometry. Good for: quantum chemistry, orbitals, electron shells.",
    {"color": "Orbital color", "label": "Caption"},
)
def chem_orbital_shapes(color: str = "TEAL_C", label: str = "Atomic Orbitals") -> str:
    label = _safe(label, "Atomic Orbitals")
    return _code(f'''
        # Template: chem_orbital_shapes
        cap = Text("{label}", font_size=28, color={color}).to_edge(UP, buff=0.4)
        s_lab = Text("s orbital", font_size=22, color=GREY_B).to_edge(DOWN, buff=0.6)
        self.add_fixed_in_frame_mobjects(cap, s_lab)
        cap.set_opacity(0); s_lab.set_opacity(0)
        s_orb = Sphere(radius=1.1, resolution=(10,10)).set_color({color}).set_opacity(0.55)
        self.play(GrowFromCenter(s_orb), cap.animate.set_opacity(1), s_lab.animate.set_opacity(1), run_time=1.2)
        self.play(Rotate(s_orb, TAU*0.5, axis=UP), run_time=2.0)
        p_lab = Text("p orbital", font_size=22, color=GREY_B).to_edge(DOWN, buff=0.6)
        self.add_fixed_in_frame_mobjects(p_lab)
        p_lab.set_opacity(0)
        lobe1 = Sphere(radius=0.65, resolution=(10,10)).set_color({color}).set_opacity(0.7).shift(UP*1.0)
        lobe2 = Sphere(radius=0.65, resolution=(10,10)).set_color(GOLD).set_opacity(0.7).shift(DOWN*1.0)
        node = Sphere(radius=0.12, resolution=(6,6)).set_color(WHITE).set_opacity(0.9)
        self.play(Transform(s_orb, lobe1), GrowFromCenter(lobe2), GrowFromCenter(node),
                  FadeOut(s_lab), p_lab.animate.set_opacity(1), run_time=1.5)
        self.play(Rotate(lobe1, TAU*0.6, axis=UP), Rotate(lobe2, TAU*0.6, axis=UP),
                  run_time=2.5, rate_func=linear)
        self.play(FadeOut(s_orb, lobe2, node, cap, p_lab), run_time=0.6)
    ''')


@_register(
    "chem_state_matter",
    "Atoms transition from tightly packed solid lattice → loose liquid → flying gas. Good for: states of matter, phase changes, thermodynamics.",
    {"color": "Atom color", "label": "Caption e.g. 'Phase Transitions'"},
)
def chem_state_matter(color: str = "BLUE_D", label: str = "States of Matter") -> str:
    label = _safe(label, "States of Matter")
    return _code(f'''
        # Template: chem_state_matter
        cap = Text("{label}", font_size=28, color={color}).to_edge(UP, buff=0.4)
        state_lab = Text("SOLID", font_size=28, weight=BOLD, color={color}).to_edge(DOWN, buff=0.5)
        self.add_fixed_in_frame_mobjects(cap, state_lab)
        cap.set_opacity(0); state_lab.set_opacity(0)
        lattice_pos = [np.array([x*0.7-1.05, y*0.7-1.05, 0]) for x in range(4) for y in range(4)]
        solid_atoms = VGroup(*[Sphere(radius=0.22, resolution=(6,6)).set_color({color}).set_opacity(0.85).move_to(p)
                                for p in lattice_pos])
        self.play(LaggedStart(*[GrowFromCenter(a) for a in solid_atoms], lag_ratio=0.05),
                  cap.animate.set_opacity(1), state_lab.animate.set_opacity(1), run_time=1.5)
        self.wait(0.8)
        liquid_pos = [np.array([(x*0.7-1.05)*1.3 + 0.15*(x % 2),
                                 (y*0.7-1.05)*1.1 - 0.1*(y % 3), 0])
                      for x in range(4) for y in range(4)]
        liq_lab = Text("LIQUID", font_size=28, weight=BOLD, color=TEAL_C).to_edge(DOWN, buff=0.5)
        self.add_fixed_in_frame_mobjects(liq_lab)
        liq_lab.set_opacity(0)
        self.play(*[solid_atoms[i].animate.move_to(liquid_pos[i]) for i in range(len(lattice_pos))],
                  FadeOut(state_lab), liq_lab.animate.set_opacity(1), run_time=1.5, rate_func=smooth)
        self.wait(0.5)
        gas_pos = [np.array([(i % 4 - 1.5)*1.6, (i // 4 - 1.5)*1.6 + 0.3, 0]) for i in range(16)]
        gas_lab = Text("GAS", font_size=28, weight=BOLD, color=ORANGE).to_edge(DOWN, buff=0.5)
        self.add_fixed_in_frame_mobjects(gas_lab)
        gas_lab.set_opacity(0)
        self.play(*[solid_atoms[i].animate.move_to(gas_pos[i]) for i in range(len(lattice_pos))],
                  FadeOut(liq_lab), gas_lab.animate.set_opacity(1), run_time=1.5, rate_func=smooth)
        self.wait(0.5)
        self.play(FadeOut(solid_atoms, cap, gas_lab), run_time=0.6)
    ''')


@_register(
    "chem_water_molecule",
    "Water molecule forms with correct 104.5° bond angle — oxygen and two hydrogens assemble. Good for: water, molecular geometry, VSEPR, polarity.",
    {"color": "Bond color", "label": "Caption"},
)
def chem_water_molecule(color: str = "BLUE_D", label: str = "Water: H₂O (104.5°)") -> str:
    label = _safe(label, "Water: H₂O")
    return _code(f'''
        # Template: chem_water_molecule
        cap = Text("{label}", font_size=28, color={color}).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        angle = 104.5 * DEGREES / 2
        O = Sphere(radius=0.55, resolution=(10,10)).set_color(RED_D).set_opacity(0.85).move_to(ORIGIN)
        H1_pos = np.array([np.sin(angle)*1.4, -np.cos(angle)*1.4, 0])
        H2_pos = np.array([-np.sin(angle)*1.4, -np.cos(angle)*1.4, 0])
        H1 = Sphere(radius=0.32, resolution=(8,8)).set_color(WHITE).set_opacity(0.85).move_to(H1_pos)
        H2 = Sphere(radius=0.32, resolution=(8,8)).set_color(WHITE).set_opacity(0.85).move_to(H2_pos)
        bond1 = Line(ORIGIN, H1_pos, color={color}, stroke_width=4)
        bond2 = Line(ORIGIN, H2_pos, color={color}, stroke_width=4)
        o_lab = Text("O", font_size=24, weight=BOLD, color=WHITE).move_to(O.get_center())
        h1_lab = Text("H", font_size=20, color=GREY_B).move_to(H1.get_center())
        h2_lab = Text("H", font_size=20, color=GREY_B).move_to(H2.get_center())
        self.play(GrowFromCenter(O), Write(o_lab), cap.animate.set_opacity(1), run_time=1.0)
        self.play(Create(bond1), Create(bond2), GrowFromCenter(H1), GrowFromCenter(H2),
                  Write(h1_lab), Write(h2_lab), run_time=1.5)
        mol = VGroup(O, H1, H2, bond1, bond2)
        self.play(Rotate(mol, TAU, axis=UP), run_time=4, rate_func=linear)
        self.play(FadeOut(O, H1, H2, bond1, bond2, o_lab, h1_lab, h2_lab, cap), run_time=0.6)
    ''')


@_register(
    "chem_ionic_bond",
    "Electron dot jumps from metal atom to nonmetal — shows ionic bond formation with charges. Good for: ionic bonds, electron transfer, electronegativity.",
    {"color": "Highlight color", "label": "Caption"},
)
def chem_ionic_bond(color: str = "YELLOW_C", label: str = "Ionic Bond: electron transfer") -> str:
    label = _safe(label, "Ionic Bond: electron transfer")
    return _code(f'''
        # Template: chem_ionic_bond
        metal = Sphere(radius=0.75, resolution=(10,10)).set_color(ORANGE).set_opacity(0.85).move_to(LEFT*2.5)
        nonmetal = Sphere(radius=0.55, resolution=(10,10)).set_color(TEAL_C).set_opacity(0.85).move_to(RIGHT*2.5)
        met_lab = Text("Na", font_size=26, weight=BOLD, color=WHITE).move_to(metal.get_center())
        nm_lab  = Text("Cl", font_size=26, weight=BOLD, color=WHITE).move_to(nonmetal.get_center())
        electron = Dot3D(metal.get_right() + LEFT*0.1, color={color}, radius=0.14)
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap, met_lab, nm_lab)
        cap.set_opacity(0)
        self.play(GrowFromCenter(metal), GrowFromCenter(nonmetal),
                  Write(met_lab), Write(nm_lab), GrowFromCenter(electron),
                  cap.animate.set_opacity(1), run_time=1.2)
        self.wait(0.5)
        self.play(electron.animate.move_to(nonmetal.get_left() + RIGHT*0.1),
                  run_time=1.5, rate_func=smooth)
        plus_lab = Text("+", font_size=28, weight=BOLD, color=RED_D).next_to(metal, UP, buff=0.15)
        neg_lab  = Text("−", font_size=28, weight=BOLD, color=BLUE_D).next_to(nonmetal, UP, buff=0.15)
        self.add_fixed_in_frame_mobjects(plus_lab, neg_lab)
        self.play(Write(plus_lab), Write(neg_lab), run_time=0.8)
        attract = Arrow(metal.get_right(), nonmetal.get_left(), color=GREY_B, buff=0.1)
        self.play(GrowArrow(attract), run_time=0.8)
        self.wait(1)
        self.play(FadeOut(metal, nonmetal, electron, attract, cap, plus_lab, neg_lab), run_time=0.6)
    ''')


@_register(
    "chem_polymer_chain",
    "Monomer units snap together one by one to form a polymer chain. Good for: polymers, polymerization, plastics, proteins, DNA backbone.",
    {"color": "Monomer color", "label": "Caption"},
)
def chem_polymer_chain(color: str = "GREEN_C", label: str = "Polymerization") -> str:
    label = _safe(label, "Polymerization")
    return _code(f'''
        # Template: chem_polymer_chain
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        cap = Text("{label}", font_size=28, color={color}).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(cap.animate.set_opacity(1), run_time=0.5)
        n_mono = 6
        monomer_colors = [{color}, TEAL_C, GOLD, {color}, TEAL_C, GOLD]
        final_positions = [np.array([-3.0 + i*1.2, 0, 0]) for i in range(n_mono)]
        monomers = VGroup()
        bonds = VGroup()
        for i in range(n_mono):
            start_pos = np.array([-3.0 + i*1.2, -2.5 + i*0.5, 0])
            m = Circle(radius=0.35, fill_color=monomer_colors[i], fill_opacity=0.8,
                       stroke_color=WHITE, stroke_width=2).move_to(start_pos)
            lbl = Text("M", font_size=18, color=WHITE).move_to(m.get_center())
            self.play(GrowFromCenter(m), run_time=0.3)
            self.play(m.animate.move_to(final_positions[i]), run_time=0.5)
            if i > 0:
                b = Line(final_positions[i-1], final_positions[i], color=WHITE, stroke_width=3)
                self.play(Create(b), run_time=0.25)
                bonds.add(b)
            monomers.add(m)
        self.wait(1.0)
        self.play(FadeOut(monomers, bonds, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


# ──────────────────────────────────────────────────────────────────────────
# BIOLOGY — advanced
# ──────────────────────────────────────────────────────────────────────────

@_register(
    "bio_mitosis",
    "Cell (circle) divides — nucleus splits and two daughter cells separate. Good for: mitosis, cell division, reproduction, cancer.",
    {"color": "Cell color", "label": "Caption"},
)
def bio_mitosis(color: str = "GREEN_C", label: str = "Mitosis: Cell Division") -> str:
    label = _safe(label, "Mitosis: Cell Division")
    return _code(f'''
        # Template: bio_mitosis
        cap = Text("{label}", font_size=28, color={color}).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        cell = Circle(radius=1.3, color={color}, fill_opacity=0.25, stroke_width=3)
        nucleus = Circle(radius=0.45, color=PURPLE_B, fill_opacity=0.7, stroke_width=2)
        self.play(GrowFromCenter(cell), GrowFromCenter(nucleus),
                  cap.animate.set_opacity(1), run_time=1.2)
        chrom1 = Rectangle(width=0.12, height=0.4, fill_color=RED_D, fill_opacity=0.9).shift(LEFT*0.15)
        chrom2 = Rectangle(width=0.12, height=0.4, fill_color=BLUE_D, fill_opacity=0.9).shift(RIGHT*0.15)
        self.play(Transform(nucleus, VGroup(chrom1, chrom2)), run_time=0.8)
        self.play(chrom1.animate.shift(UP*0.6), chrom2.animate.shift(DOWN*0.6), run_time=1.0)
        daughter1 = Circle(radius=0.75, color={color}, fill_opacity=0.25, stroke_width=3).shift(UP*1.3)
        daughter2 = Circle(radius=0.75, color={color}, fill_opacity=0.25, stroke_width=3).shift(DOWN*1.3)
        nuc1 = Circle(radius=0.28, color=PURPLE_B, fill_opacity=0.7).shift(UP*1.3)
        nuc2 = Circle(radius=0.28, color=PURPLE_B, fill_opacity=0.7).shift(DOWN*1.3)
        self.play(Transform(cell, VGroup(daughter1, daughter2)),
                  GrowFromCenter(nuc1), GrowFromCenter(nuc2),
                  FadeOut(chrom1, chrom2), run_time=1.5)
        self.wait(1)
        self.play(FadeOut(cell, nuc1, nuc2, cap), run_time=0.6)
    ''')


@_register(
    "bio_food_chain",
    "Sun → plants → herbivore → carnivore linked by arrows showing energy flow. Good for: food chains, ecosystems, energy transfer, trophic levels.",
    {"label_a": "Producer (e.g. Grass)", "label_b": "Herbivore (e.g. Rabbit)",
     "label_c": "Carnivore (e.g. Fox)", "color": "Arrow color"},
)
def bio_food_chain(label_a: str = "Grass", label_b: str = "Rabbit",
                   label_c: str = "Fox", color: str = "GREEN_C") -> str:
    label_a = _safe(label_a, "Plant")
    label_b = _safe(label_b, "Herbivore")
    label_c = _safe(label_c, "Carnivore")
    return _code(f'''
        # Template: bio_food_chain
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        positions = [LEFT*4.2, LEFT*1.4, RIGHT*1.4, RIGHT*4.2]
        colors_list = [YELLOW_C, {color}, ORANGE, RED_D]
        labels_list = ["Sun", "{label_a}", "{label_b}", "{label_c}"]
        nodes = VGroup()
        labs = VGroup()
        cap = Text("Energy Flow", font_size=26, color={color}).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(cap.animate.set_opacity(1), run_time=0.5)
        for i, (pos, col, txt) in enumerate(zip(positions, colors_list, labels_list)):
            n = Circle(radius=0.55, fill_color=col, fill_opacity=0.75, stroke_color=WHITE,
                       stroke_width=2).move_to(pos)
            l = Text(txt, font_size=18, color=WHITE).move_to(pos)
            nodes.add(n); labs.add(l)
            self.add_fixed_in_frame_mobjects(l)
            self.play(GrowFromCenter(n), Write(l), run_time=0.5)
            if i > 0:
                arr = Arrow(positions[i-1]+RIGHT*0.6, pos+LEFT*0.6, color={color}, buff=0)
                self.play(GrowArrow(arr), run_time=0.5)
        self.wait(1.5)
        self.play(FadeOut(nodes, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "bio_dna_replication",
    "Double helix unzips and two new strands synthesize — shows DNA replication. Good for: DNA replication, semiconservative replication, genetics.",
    {"color": "Strand color", "label": "Caption"},
)
def bio_dna_replication(color: str = "BLUE_D", label: str = "DNA Replication") -> str:
    label = _safe(label, "DNA Replication")
    return _code(f'''
        # Template: bio_dna_replication
        cap = Text("{label}", font_size=28, color={color}).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        strand1 = ParametricFunction(
            lambda t: np.array([np.cos(t)*0.8, t*0.35 - 3.0, np.sin(t)*0.8]),
            t_range=[-PI, PI*3], color={color}, stroke_width=4)
        strand2 = ParametricFunction(
            lambda t: np.array([np.cos(t+PI)*0.8, t*0.35 - 3.0, np.sin(t+PI)*0.8]),
            t_range=[-PI, PI*3], color=TEAL_C, stroke_width=4)
        self.play(Create(strand1), Create(strand2), cap.animate.set_opacity(1), run_time=2.0)
        self.wait(0.5)
        new1 = ParametricFunction(
            lambda t: np.array([np.cos(t)*0.8 + 1.5, t*0.35 - 3.0, np.sin(t)*0.8]),
            t_range=[-PI, PI*3], color={color}, stroke_width=4)
        new2 = ParametricFunction(
            lambda t: np.array([np.cos(t+PI)*0.8 - 1.5, t*0.35 - 3.0, np.sin(t+PI)*0.8]),
            t_range=[-PI, PI*3], color=TEAL_C, stroke_width=4)
        self.play(strand1.animate.shift(RIGHT*1.5), strand2.animate.shift(LEFT*1.5), run_time=1.5)
        fill1 = ParametricFunction(
            lambda t: np.array([np.cos(t+PI)*0.8 + 1.5, t*0.35 - 3.0, np.sin(t+PI)*0.8]),
            t_range=[-PI, PI*3], color=GOLD, stroke_width=4)
        fill2 = ParametricFunction(
            lambda t: np.array([np.cos(t)*0.8 - 1.5, t*0.35 - 3.0, np.sin(t)*0.8]),
            t_range=[-PI, PI*3], color=GOLD, stroke_width=4)
        self.play(Create(fill1), Create(fill2), run_time=2.0)
        self.wait(0.5)
        self.play(FadeOut(strand1, strand2, fill1, fill2, cap), run_time=0.6)
    ''')


@_register(
    "bio_neuron_signal",
    "Action potential travels along a neuron — axon lights up in sequence. Good for: neurons, action potential, nervous system, synapses.",
    {"color": "Signal color", "label": "Caption"},
)
def bio_neuron_signal(color: str = "YELLOW_C", label: str = "Action Potential") -> str:
    label = _safe(label, "Action Potential")
    return _code(f'''
        # Template: bio_neuron_signal
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        soma = Circle(radius=0.55, fill_color=GREEN_C, fill_opacity=0.7, stroke_color=WHITE, stroke_width=2)
        soma.move_to(LEFT*4.5)
        axon = Rectangle(width=5.5, height=0.3, fill_color=GREEN_D, fill_opacity=0.6,
                         stroke_color=WHITE, stroke_width=1).move_to(LEFT*1.5)
        term1 = Circle(radius=0.25, fill_color=TEAL_C, fill_opacity=0.8).move_to(RIGHT*1.5 + UP*0.6)
        term2 = Circle(radius=0.25, fill_color=TEAL_C, fill_opacity=0.8).move_to(RIGHT*1.5 + DOWN*0.6)
        term3 = Circle(radius=0.25, fill_color=TEAL_C, fill_opacity=0.8).move_to(RIGHT*2.2)
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(GrowFromCenter(soma), Create(axon), GrowFromCenter(term1),
                  GrowFromCenter(term2), GrowFromCenter(term3), cap.animate.set_opacity(1), run_time=1.2)
        signal = Dot(soma.get_right(), color={color}, radius=0.18)
        self.add(signal)
        self.play(signal.animate.move_to(axon.get_right()), run_time=2.0, rate_func=smooth)
        self.play(Flash(axon.get_right(), color={color}, line_length=0.3, flash_radius=0.6),
                  signal.animate.scale(0), run_time=0.6)
        self.play(Flash(term1.get_center(), color={color}, flash_radius=0.4),
                  Flash(term2.get_center(), color={color}, flash_radius=0.4),
                  Flash(term3.get_center(), color={color}, flash_radius=0.4), run_time=0.5)
        self.wait(1)
        self.play(FadeOut(soma, axon, term1, term2, term3, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "bio_evolution_tree",
    "Phylogenetic tree branches from a common ancestor — shows evolutionary divergence. Good for: evolution, phylogeny, speciation, Darwin.",
    {"color": "Branch color", "label": "Caption"},
)
def bio_evolution_tree(color: str = "GREEN_C", label: str = "Phylogenetic Tree") -> str:
    label = _safe(label, "Phylogenetic Tree")
    return _code(f'''
        # Template: bio_evolution_tree
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        cap = Text("{label}", font_size=28, color={color}).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(cap.animate.set_opacity(1), run_time=0.5)
        root = np.array([0, -2.8, 0])
        trunk = Line(root, root + UP*1.5, color={color}, stroke_width=3)
        self.play(Create(trunk), run_time=0.5)
        branch_data = [
            (root + UP*1.5, UP*1.5 + LEFT*2.2, UP*1.5 + RIGHT*2.2),
            (root + UP*1.5 + UP*1.5 + LEFT*2.2, UP*0.8+LEFT*1.0, UP*0.8+RIGHT*1.0),
            (root + UP*1.5 + UP*1.5 + RIGHT*2.2, UP*0.8+LEFT*1.0, UP*0.8+RIGHT*1.0),
        ]
        leaf_cols = [YELLOW_C, ORANGE, TEAL_C, RED_D, PURPLE_B, GREEN_D]
        leaf_idx = 0
        for base, left_d, right_d in branch_data:
            bl = Line(base, base + left_d, color={color}, stroke_width=2.5)
            br = Line(base, base + right_d, color={color}, stroke_width=2.5)
            self.play(Create(bl), Create(br), run_time=0.5)
            for tip in [base + left_d, base + right_d]:
                lf = Dot(tip, color=leaf_cols[leaf_idx % len(leaf_cols)], radius=0.2)
                self.play(GrowFromCenter(lf), run_time=0.3)
                leaf_idx += 1
        self.wait(1.5)
        self.play(FadeOut(*self.mobjects), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


# ──────────────────────────────────────────────────────────────────────────
# COMPUTER SCIENCE — advanced
# ──────────────────────────────────────────────────────────────────────────

@_register(
    "cs_recursion_tree",
    "Recursive function calls expand as a tree — shows how recursion branches. Good for: recursion, Fibonacci, divide-and-conquer, call stack.",
    {"color": "Node color", "label": "Caption e.g. 'Recursion'"},
)
def cs_recursion_tree(color: str = "TEAL_C", label: str = "Recursion: branching calls") -> str:
    label = _safe(label, "Recursion")
    return _code(f'''
        # Template: cs_recursion_tree
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(cap.animate.set_opacity(1), run_time=0.5)
        nodes_data = [
            (np.array([0, 2.5, 0]), "f(4)", WHITE, None),
            (np.array([-2.0, 1.0, 0]), "f(3)", {color}, np.array([0, 2.5, 0])),
            (np.array([ 2.0, 1.0, 0]), "f(3)", {color}, np.array([0, 2.5, 0])),
            (np.array([-3.0,-0.5, 0]), "f(2)", TEAL_C, np.array([-2.0, 1.0, 0])),
            (np.array([-1.0,-0.5, 0]), "f(2)", TEAL_C, np.array([-2.0, 1.0, 0])),
            (np.array([ 1.0,-0.5, 0]), "f(2)", TEAL_C, np.array([ 2.0, 1.0, 0])),
            (np.array([ 3.0,-0.5, 0]), "f(2)", TEAL_C, np.array([ 2.0, 1.0, 0])),
        ]
        for pos, txt, col, parent in nodes_data:
            circ = Circle(radius=0.38, fill_color=col, fill_opacity=0.7,
                          stroke_color=WHITE, stroke_width=1.5).move_to(pos)
            lbl = Text(txt, font_size=16, color=WHITE).move_to(pos)
            anims = [GrowFromCenter(circ), Write(lbl)]
            if parent is not None:
                edge = Line(parent, pos, color=GREY_B, stroke_width=1.5)
                anims.append(Create(edge))
            self.play(*anims, run_time=0.5)
        self.wait(1.5)
        self.play(FadeOut(*self.mobjects), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "cs_hash_table",
    "Keys are hashed and mapped into a table — shows how hash tables work. Good for: hash tables, dictionaries, data structures, time complexity.",
    {"color": "Highlight color", "label": "Caption"},
)
def cs_hash_table(color: str = "GOLD", label: str = "Hash Table: O(1) lookup") -> str:
    label = _safe(label, "Hash Table")
    return _code(f'''
        # Template: cs_hash_table
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(cap.animate.set_opacity(1), run_time=0.5)
        n_buckets = 5
        bucket_h = 0.55
        table_x = 1.5
        buckets = VGroup()
        for i in range(n_buckets):
            y = (n_buckets/2 - i) * bucket_h
            b = Rectangle(width=1.5, height=bucket_h-0.05, fill_color=GREY_B,
                          fill_opacity=0.3, stroke_color=WHITE, stroke_width=1.5)
            b.move_to(np.array([table_x, y, 0]))
            idx_lab = Text(str(i), font_size=18, color=GREY_B).next_to(b, LEFT, buff=0.2)
            buckets.add(b)
            self.add_fixed_in_frame_mobjects(idx_lab)
            self.play(GrowFromCenter(b), Write(idx_lab), run_time=0.2)
        key_data = [("name", 2), ("age", 4), ("city", 1), ("score", 0)]
        for key, bucket_idx in key_data:
            key_box = Rectangle(width=1.0, height=0.42, fill_color={color},
                                fill_opacity=0.7, stroke_color=WHITE, stroke_width=1.5)
            key_lab = Text(key, font_size=18, color=WHITE)
            key_box.move_to(np.array([-2.8, 0.8 - key_data.index((key, bucket_idx))*0.55, 0]))
            key_lab.move_to(key_box.get_center())
            self.add_fixed_in_frame_mobjects(key_lab)
            target_y = (n_buckets/2 - bucket_idx) * bucket_h
            self.play(GrowFromCenter(key_box), run_time=0.3)
            arr = Arrow(key_box.get_right(), np.array([table_x-0.75, target_y, 0]),
                        color={color}, buff=0.05, stroke_width=2)
            self.play(GrowArrow(arr), run_time=0.4)
            self.play(FadeOut(arr, key_box), run_time=0.2)
        self.wait(1)
        self.play(FadeOut(*self.mobjects), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "cs_stack_operations",
    "Stack data structure with push and pop — plates stack up and come off. Good for: stacks, LIFO, function calls, undo operations.",
    {"color": "Stack color", "label": "Caption"},
)
def cs_stack_operations(color: str = "TEAL_C", label: str = "Stack: Last In, First Out") -> str:
    label = _safe(label, "Stack: LIFO")
    return _code(f'''
        # Template: cs_stack_operations
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.4)
        push_lab = Text("PUSH →", font_size=20, color=GREEN_C).to_corner(UL, buff=0.6)
        pop_lab  = Text("← POP",  font_size=20, color=RED_D).to_corner(UR, buff=0.6)
        self.add_fixed_in_frame_mobjects(cap, push_lab, pop_lab)
        cap.set_opacity(0); push_lab.set_opacity(0); pop_lab.set_opacity(0)
        base = Line(LEFT*1.2, RIGHT*1.2, color=WHITE, stroke_width=3).move_to(DOWN*2.5)
        self.play(Create(base), cap.animate.set_opacity(1), push_lab.animate.set_opacity(1), run_time=0.8)
        items = ["A", "B", "C", "D"]
        rects = []
        item_h = 0.65
        for i, item in enumerate(items):
            r = Rectangle(width=1.8, height=item_h, fill_color=color, fill_opacity=0.75,
                          stroke_color=WHITE, stroke_width=1.5)
            r.move_to(np.array([0, -2.2 + i*item_h + item_h/2, 0]))
            lbl = Text(item, font_size=22, color=WHITE).move_to(r.get_center())
            self.add_fixed_in_frame_mobjects(lbl)
            self.play(r.animate.move_to(np.array([0, -2.2 + i*item_h + item_h/2, 0])),
                      GrowFromCenter(r), Write(lbl), run_time=0.4)
            rects.append(r)
        self.wait(0.4)
        self.play(pop_lab.animate.set_opacity(1), run_time=0.4)
        for r in reversed(rects[-2:]):
            self.play(r.animate.shift(RIGHT*3).set_opacity(0), run_time=0.5)
        self.wait(0.8)
        self.play(FadeOut(*self.mobjects), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "cs_bfs_search",
    "Breadth-first search colors nodes level by level — shows graph traversal. Good for: BFS, graph algorithms, shortest path, tree search.",
    {"color": "Visited color", "label": "Caption"},
)
def cs_bfs_search(color: str = "TEAL_C", label: str = "Breadth-First Search") -> str:
    label = _safe(label, "BFS")
    return _code(f'''
        # Template: cs_bfs_search
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        node_pos = {{
            0: np.array([0, 2.2, 0]),
            1: np.array([-2.2, 0.6, 0]),
            2: np.array([ 2.2, 0.6, 0]),
            3: np.array([-3.0,-1.2, 0]),
            4: np.array([-1.0,-1.2, 0]),
            5: np.array([ 1.0,-1.2, 0]),
            6: np.array([ 3.0,-1.2, 0]),
        }}
        edges = [(0,1),(0,2),(1,3),(1,4),(2,5),(2,6)]
        edge_lines = VGroup(*[Line(node_pos[a], node_pos[b], color=GREY_B, stroke_width=1.5)
                               for a, b in edges])
        node_circles = VGroup(*[Circle(radius=0.32, fill_color=GREY_B, fill_opacity=0.6,
                                       stroke_color=WHITE, stroke_width=1.5).move_to(node_pos[i])
                                 for i in range(7)])
        self.play(Create(edge_lines), LaggedStart(*[GrowFromCenter(n) for n in node_circles],
                                                   lag_ratio=0.1), cap.animate.set_opacity(1), run_time=1.5)
        bfs_order = [[0], [1, 2], [3, 4, 5, 6]]
        for level in bfs_order:
            self.play(*[node_circles[i].animate.set_fill({color}, 0.85) for i in level], run_time=0.7)
        self.wait(1)
        self.play(FadeOut(*self.mobjects), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


# ──────────────────────────────────────────────────────────────────────────
# GENERAL — advanced layouts
# ──────────────────────────────────────────────────────────────────────────

@_register(
    "general_venn_diagram",
    "Two overlapping circles with labeled regions — shows intersection, union, and difference. Good for: set theory, comparisons, logic, relationships.",
    {"label_a": "Left set label", "label_b": "Right set label",
     "label_ab": "Overlap label", "color": "Primary color"},
)
def general_venn_diagram(label_a: str = "Set A", label_b: str = "Set B",
                          label_ab: str = "Both", color: str = "BLUE_D") -> str:
    label_a  = _safe(label_a, "A")
    label_b  = _safe(label_b, "B")
    label_ab = _safe(label_ab, "∩")
    return _code(f'''
        # Template: general_venn_diagram
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        cap = Text("Venn Diagram", font_size=28, color={color}).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        circ_a = Circle(radius=1.5, fill_color={color}, fill_opacity=0.35,
                        stroke_color={color}, stroke_width=2.5).move_to(LEFT*1.0)
        circ_b = Circle(radius=1.5, fill_color=TEAL_C, fill_opacity=0.35,
                        stroke_color=TEAL_C, stroke_width=2.5).move_to(RIGHT*1.0)
        la = Text("{label_a}", font_size=22, color=WHITE).move_to(LEFT*2.4)
        lb = Text("{label_b}", font_size=22, color=WHITE).move_to(RIGHT*2.4)
        lab = Text("{label_ab}", font_size=20, color=YELLOW_C).move_to(ORIGIN)
        self.add_fixed_in_frame_mobjects(la, lb, lab)
        la.set_opacity(0); lb.set_opacity(0); lab.set_opacity(0)
        self.play(GrowFromCenter(circ_a), GrowFromCenter(circ_b), cap.animate.set_opacity(1), run_time=1.2)
        self.play(la.animate.set_opacity(1), lb.animate.set_opacity(1),
                  lab.animate.set_opacity(1), run_time=0.8)
        self.wait(2)
        self.play(FadeOut(circ_a, circ_b, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "general_pyramid_hierarchy",
    "Pyramid with labeled tiers builds from base to apex — shows hierarchies, rankings. Good for: Maslow's hierarchy, taxonomies, management layers.",
    {"label_a": "Base tier", "label_b": "Middle tier", "label_c": "Top tier", "color": "Primary color"},
)
def general_pyramid_hierarchy(label_a: str = "Foundation", label_b: str = "Growth",
                               label_c: str = "Peak", color: str = "GOLD") -> str:
    label_a = _safe(label_a, "Base")
    label_b = _safe(label_b, "Middle")
    label_c = _safe(label_c, "Top")
    return _code(f'''
        # Template: general_pyramid_hierarchy
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        cap = Text("Hierarchy", font_size=28, color={color}).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        tier_data = [
            (3.5, 0.8, BLUE_D, "{label_a}", DOWN*1.4),
            (2.2, 0.8, TEAL_C, "{label_b}", ORIGIN),
            (1.0, 0.8, {color}, "{label_c}", UP*1.4),
        ]
        self.play(cap.animate.set_opacity(1), run_time=0.5)
        for width, height, col, txt, center in tier_data:
            tier = Rectangle(width=width, height=height, fill_color=col,
                             fill_opacity=0.7, stroke_color=WHITE, stroke_width=1.5)
            tier.move_to(center)
            lbl = Text(txt, font_size=20, color=WHITE).move_to(center)
            self.add_fixed_in_frame_mobjects(lbl)
            self.play(GrowFromCenter(tier), Write(lbl), run_time=0.7)
        self.wait(2)
        self.play(FadeOut(*self.mobjects), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "general_cause_effect",
    "A chain of labeled boxes connected by arrows — shows cause and effect flow. Good for: causality, process steps, historical events, logic chains.",
    {"label_a": "Cause", "label_b": "Effect 1", "label_c": "Effect 2", "color": "Arrow color"},
)
def general_cause_effect(label_a: str = "Cause", label_b: str = "Effect 1",
                          label_c: str = "Effect 2", color: str = "ORANGE") -> str:
    label_a = _safe(label_a, "Cause")
    label_b = _safe(label_b, "Effect 1")
    label_c = _safe(label_c, "Effect 2")
    return _code(f'''
        # Template: general_cause_effect
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        cap = Text("Cause & Effect", font_size=28, color={color}).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(cap.animate.set_opacity(1), run_time=0.5)
        items = [
            (np.array([-4.0, 0, 0]), "{label_a}", RED_D),
            (np.array([ 0.0, 0, 0]), "{label_b}", {color}),
            (np.array([ 4.0, 0, 0]), "{label_c}", GREEN_C),
        ]
        prev_right = None
        for pos, txt, col in items:
            box = Rectangle(width=2.2, height=0.9, fill_color=col, fill_opacity=0.6,
                            stroke_color=WHITE, stroke_width=1.5).move_to(pos)
            lbl = Text(txt, font_size=20, color=WHITE).move_to(pos)
            self.add_fixed_in_frame_mobjects(lbl)
            anims = [GrowFromCenter(box), Write(lbl)]
            if prev_right is not None:
                arr = Arrow(prev_right, pos + LEFT*1.1, color={color}, buff=0.05)
                anims.append(GrowArrow(arr))
            self.play(*anims, run_time=0.7)
            prev_right = pos + RIGHT*1.1
        self.wait(2)
        self.play(FadeOut(*self.mobjects), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


@_register(
    "general_wave_spectrum",
    "Waves of different frequencies represent the electromagnetic spectrum. Good for: EM spectrum, light, physics, radiation, waves.",
    {"color": "Primary color", "label": "Caption"},
)
def general_wave_spectrum(color: str = "PURPLE_B", label: str = "Electromagnetic Spectrum") -> str:
    label = _safe(label, "EM Spectrum")
    return _code(f'''
        # Template: general_wave_spectrum
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        cap = Text("{label}", font_size=26, color={color}).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        wave_data = [
            (0.3, 1.0, PURPLE_B, "Gamma"),
            (0.6, 0.9, BLUE_D, "X-ray"),
            (1.0, 0.85, TEAL_C, "UV"),
            (1.6, 0.8, GREEN_C, "Visible"),
            (2.5, 0.7, YELLOW_C, "Infrared"),
            (4.0, 0.6, ORANGE, "Microwave"),
            (6.5, 0.5, RED_D, "Radio"),
        ]
        self.play(cap.animate.set_opacity(1), run_time=0.5)
        y_positions = np.linspace(2.2, -2.2, len(wave_data))
        for (freq, amp, col, name), y in zip(wave_data, y_positions):
            wave = ParametricFunction(
                lambda t, f=freq, a=amp: np.array([t*1.2 - 3.5, y + a*0.4*np.sin(f*t*2), 0]),
                t_range=[0, 2*PI], color=col, stroke_width=2.5
            )
            wlab = Text(name, font_size=16, color=col).move_to(np.array([3.8, y, 0]))
            self.add_fixed_in_frame_mobjects(wlab)
            self.play(Create(wave), Write(wlab), run_time=0.35)
        self.wait(1.5)
        self.play(FadeOut(*self.mobjects), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


# ──────────────────────────────────────────────────────────────────────────
# ARTS & HUMANITIES
# ──────────────────────────────────────────────────────────────────────────

@_register(
    "arts_color_theory",
    "Color wheel segments appear with primary and secondary colors — shows color relationships. Good for: color theory, art, design, pigments.",
    {"label": "Caption", "color": "Highlight color"},
)
def arts_color_theory(label: str = "Color Theory", color: str = "GOLD") -> str:
    label = _safe(label, "Color Theory")
    return _code(f'''
        # Template: arts_color_theory
        cap = Text("{label}", font_size=28, color={color}).to_edge(UP, buff=0.4)
        self.add_fixed_in_frame_mobjects(cap)
        cap.set_opacity(0)
        self.play(cap.animate.set_opacity(1), run_time=0.5)
        wheel_colors = [RED_D, ORANGE, YELLOW_C, GREEN_C, BLUE_D, PURPLE_B]
        sectors = VGroup()
        for i, col in enumerate(wheel_colors):
            angle = i * TAU / len(wheel_colors)
            sector = AnnularSector(inner_radius=0.5, outer_radius=1.8,
                                   angle=TAU/len(wheel_colors) - 0.08,
                                   start_angle=angle,
                                   fill_color=col, fill_opacity=0.85, stroke_width=0)
            sectors.add(sector)
        self.play(LaggedStart(*[GrowFromCenter(s) for s in sectors], lag_ratio=0.12, run_time=2.5))
        self.play(Rotate(sectors, TAU/3, axis=OUT), run_time=3, rate_func=smooth)
        self.wait(0.5)
        self.play(FadeOut(sectors, cap), run_time=0.6)
    ''')


@_register(
    "arts_perspective_lines",
    "Vanishing point perspective lines converge to a horizon — shows linear perspective. Good for: art, perspective drawing, geometry, architecture.",
    {"color": "Line color", "label": "Caption"},
)
def arts_perspective_lines(color: str = "GOLD", label: str = "Linear Perspective") -> str:
    label = _safe(label, "Linear Perspective")
    return _code(f'''
        # Template: arts_perspective_lines
        self.move_camera(phi=0, theta=-PI/2, run_time=0.6)
        cap = Text("{label}", font_size=28, color={color}).to_edge(UP, buff=0.4)
        horizon = Line(LEFT*5, RIGHT*5, color=GREY_B, stroke_width=1.5)
        vp = Dot(ORIGIN, color={color}, radius=0.15)
        vp_lab = Text("VP", font_size=18, color={color}).next_to(vp, UP, buff=0.15)
        self.add_fixed_in_frame_mobjects(cap, vp_lab)
        cap.set_opacity(0)
        self.play(Create(horizon), GrowFromCenter(vp), Write(vp_lab),
                  cap.animate.set_opacity(1), run_time=1.0)
        endpoints = [
            LEFT*5 + UP*3, LEFT*3 + UP*3, ORIGIN + UP*3,
            LEFT*5 + DOWN*3, LEFT*3 + DOWN*3, ORIGIN + DOWN*3,
            RIGHT*5 + UP*3, RIGHT*3 + UP*3,
            RIGHT*5 + DOWN*3, RIGHT*3 + DOWN*3,
        ]
        lines = VGroup(*[Line(ORIGIN, ep, color={color}, stroke_width=1.5,
                              stroke_opacity=0.7) for ep in endpoints])
        self.play(LaggedStart(*[Create(l) for l in lines], lag_ratio=0.08, run_time=2.5))
        self.wait(1.5)
        self.play(FadeOut(horizon, vp, lines, cap), run_time=0.6)
        self.move_camera(phi=70*DEGREES, theta=-45*DEGREES, run_time=0.6)
    ''')


# ──────────────────────────────────────────────────────────────────────────
# Catalog generator (for LLM prompt)
# ──────────────────────────────────────────────────────────────────────────

def get_template_catalog() -> str:
    """Return a markdown catalog of every template — used in the LLM system prompt."""
    lines = []
    for name, info in TEMPLATES.items():
        lines.append(f"• **{name}** — {info['description']}")
        if info["params"]:
            param_list = ", ".join(f"{k}" for k in info["params"].keys())
            lines.append(f"  params: {param_list}")
    return "\n".join(lines)


def list_template_names() -> list[str]:
    return list(TEMPLATES.keys())


# ──────────────────────────────────────────────────────────────────────────
# Custom scene: LLM-generated topic-specific Manim code (Part B)
# ──────────────────────────────────────────────────────────────────────────

def validate_custom_scene(code: str) -> str | None:
    """Validate a block of LLM-generated Manim code for safety and syntax.

    Returns None if valid, or an error string describing the problem.
    Checks:
      1. Parses as valid Python
      2. Doesn't use dangerous operations (file I/O, subprocess, etc.)
      3. Doesn't use Surface() (too slow)
      4. Doesn't import anything outside the manim/numpy whitelist
    """
    import ast as _ast
    BANNED_NAMES = {
        "open", "exec", "eval", "__import__", "compile",
        "subprocess", "os", "sys", "shutil", "socket",
        "Surface",  # too slow on Railway
    }
    import textwrap as _tw
    code = _tw.dedent(code)
    try:
        tree = _ast.parse(code)
    except SyntaxError as e:
        return f"SyntaxError: {e}"

    for node in _ast.walk(tree):
        # Block dangerous function calls
        if isinstance(node, _ast.Call):
            fn = node.func
            name = None
            if isinstance(fn, _ast.Name):
                name = fn.id
            elif isinstance(fn, _ast.Attribute):
                name = fn.attr
            if name in BANNED_NAMES:
                return f"Blocked: '{name}' is not allowed in custom scenes"
        # Block imports of non-whitelisted modules
        if isinstance(node, (_ast.Import, _ast.ImportFrom)):
            return "Blocked: import statements not allowed in custom scenes"

    return None  # all good


def register_custom_scene(name: str, code_block: str, params: dict | None = None) -> bool:
    """Register a one-off LLM-generated scene as a template.

    The code_block is a string of indented Manim code (same format as regular
    template functions). It is validated before registration.

    Returns True if registered successfully, False if validation failed.
    """
    error = validate_custom_scene(code_block)
    if error:
        return False

    # Wrap the raw code block in a function
    def _custom_fn(**kwargs) -> str:
        return code_block

    TEMPLATES[name] = {
        "fn": _custom_fn,
        "description": f"Custom LLM-generated scene: {name}",
        "params": params or {},
    }
    return True
    return list(TEMPLATES.keys())
