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
    """Validate that `expr` can be the body of a `lambda <var>: ...`.

    The LLM sometimes passes textbook equations like "y = mx + b" instead of a
    Python expression. Anything that fails to compile as a lambda body is
    replaced with a safe default.
    """
    if not expr or not isinstance(expr, str):
        return fallback
    expr = expr.strip()
    # Try to compile as a lambda body — catches "y = mx + b", bare names, etc.
    try:
        compile(f"lambda {var}: {expr}", "<expr-check>", "eval")
        return expr
    except (SyntaxError, ValueError):
        return fallback


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
