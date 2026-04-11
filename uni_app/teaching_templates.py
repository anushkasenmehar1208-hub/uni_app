"""
Deterministic SVG teaching scenes for common STEM subjects.
Matched before LLM diagram generation for consistent layout and labels.
"""

from __future__ import annotations

import re
from collections.abc import Callable

W, H = 600, 440
BG = "#f0f4f8"


def _esc(s: str) -> str:
    t = str(s or "")
    return (
        t.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _wrap(title: str, body: str, caption: str = "") -> str:
    te, ce = _esc(title), _esc(caption)
    cap = (
        f"<text x='300' y='418' text-anchor='middle' font-size='12' fill='#64748b' font-family='sans-serif'>{ce}</text>"
        if caption
        else ""
    )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}'>"
        f"<rect width='{W}' height='{H}' fill='{BG}'/>"
        f"<text x='300' y='34' text-anchor='middle' font-family='sans-serif' font-size='18' font-weight='700' fill='#0f172a'>{te}</text>"
        f"{body}{cap}</svg>"
    )


def _label(x: int, y: int, text: str, *, anchor: str = "start", size: int = 12, bold: bool = False) -> str:
    fw = "700" if bold else "500"
    return (
        f"<text x='{x}' y='{y}' text-anchor='{anchor}' font-family='sans-serif' "
        f"font-size='{size}' fill='#1e293b' font-weight='{fw}'>{_esc(text)}</text>"
    )


def _leader(x1: int, y1: int, x2: int, y2: int, color: str = "#64748b") -> str:
    return (
        f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='{color}' stroke-width='1.5' stroke-dasharray='4 3'/>"
    )


# --- Scene builders (return inner SVG only, no root) ---


def _scene_tree() -> str:
    return (
        "<line x1='60' y1='360' x2='540' y2='360' stroke='#78716c' stroke-width='3'/>"
        "<rect x='268' y='240' width='64' height='122' rx='6' fill='#92400e' stroke='#1e293b' stroke-width='3'/>"
        "<circle cx='220' cy='160' r='58' fill='#22c55e' stroke='#14532d' stroke-width='3'/>"
        "<circle cx='300' cy='130' r='72' fill='#16a34a' stroke='#14532d' stroke-width='3'/>"
        "<circle cx='385' cy='165' r='52' fill='#4ade80' stroke='#14532d' stroke-width='3'/>"
        + _leader(95, 120, 168, 145)
        + _label(30, 125, "Leaves (photosynthesis)", size=11)
        + _leader(520, 200, 340, 220)
        + _label(400, 205, "Trunk / stem", anchor="end", size=11)
        + _leader(300, 400, 300, 362)
        + _label(230, 395, "Roots (anchor & water)", anchor="middle", size=11)
    )


def _scene_flower() -> str:
    return (
        "<rect x='250' y='280' width='14' height='80' rx='4' fill='#15803d' stroke='#14532d' stroke-width='2'/>"
        "<ellipse cx='210' cy='310' rx='28' ry='14' fill='#22c55e' stroke='#14532d' stroke-width='2'/>"
        "<ellipse cx='350' cy='305' rx='32' ry='15' fill='#22c55e' stroke='#14532d' stroke-width='2'/>"
        "<circle cx='257' cy='257' r='22' fill='#fbbf24' stroke='#b45309' stroke-width='2'/>"
        + "".join(
            f"<ellipse cx='257' cy='175' rx='18' ry='44' fill='#f472b6' stroke='#9d174d' stroke-width='2' transform='rotate({a} 257 257)'/>"
            for a in (0, 60, 120, 180, 240, 300)
        )
        + _leader(120, 100, 240, 200)
        + _label(35, 105, "Petals", size=11)
        + _leader(480, 120, 275, 240)
        + _label(390, 125, "Stigma / style", anchor="end", size=11)
        + _leader(480, 260, 320, 305)
        + _label(395, 265, "Ovary (center)", anchor="end", size=11)
        + _leader(140, 380, 257, 355)
        + _label(35, 385, "Stem", size=11)
    )


def _scene_plant_sun() -> str:
    return (
        "<circle cx='480' cy='110' r='42' fill='#fde047' stroke='#ca8a04' stroke-width='3'/>"
        "<line x1='480' y1='68' x2='480' y2='55' stroke='#ca8a04' stroke-width='3'/>"
        "<line x1='480' y1='165' x2='480' y2='178' stroke='#ca8a04' stroke-width='3'/>"
        "<line x1='438' y1='110' x2='425' y2='110' stroke='#ca8a04' stroke-width='3'/>"
        "<line x1='522' y1='110' x2='535' y2='110' stroke='#ca8a04' stroke-width='3'/>"
        "<rect x='120' y='320' width='360' height='50' rx='8' fill='#d6d3d1' stroke='#57534e' stroke-width='2'/>"
        "<rect x='285' y='220' width='12' height='102' rx='3' fill='#166534' stroke='#14532d' stroke-width='2'/>"
        "<ellipse cx='240' cy='250' rx='36' ry='18' fill='#22c55e' stroke='#14532d' stroke-width='2'/>"
        "<ellipse cx='340' cy='245' rx='40' ry='20' fill='#22c55e' stroke='#14532d' stroke-width='2'/>"
        "<path d='M 291 220 Q 260 150 230 130 Q 260 160 291 200 Z' fill='#4ade80' stroke='#14532d' stroke-width='2'/>"
        "<path d='M 291 220 Q 320 150 355 128 Q 330 165 300 205 Z' fill='#4ade80' stroke='#14532d' stroke-width='2'/>"
        "<defs><marker id='marr' markerWidth='8' markerHeight='8' refX='7' refY='4' orient='auto'><polygon points='0,0 8,4 0,8' fill='#2563eb'/></marker></defs>"
        "<line x1='420' y1='130' x2='340' y2='200' stroke='#2563eb' stroke-width='3' marker-end='url(#marr)'/>"
        + _label(330, 155, "Light energy", size=11)
    )


def _scene_photosynthesis() -> str:
    return (
        _scene_plant_sun()
        + "<text x='300' y='72' text-anchor='middle' font-size='11' fill='#334155' font-family='sans-serif'>"
        "CO₂ in · H₂O · Glucose &amp; O₂ out (concept)</text>"
    )


def _scene_fruit() -> str:
    return (
        "<path d='M 300 95 Q 240 120 230 200 Q 225 280 300 320 Q 375 280 370 200 Q 360 120 300 95 Z' "
        "fill='#ef4444' stroke='#7f1d1d' stroke-width='3'/>"
        "<path d='M 300 95 Q 290 70 275 65' fill='none' stroke='#166534' stroke-width='4' stroke-linecap='round'/>"
        "<ellipse cx='300' cy='118' rx='14' ry='8' fill='#fca5a5' stroke='#7f1d1d' stroke-width='2'/>"
        + _leader(130, 160, 245, 210)
        + _label(35, 165, "Fruit (seed vessel)", size=11)
        + _leader(470, 200, 355, 230)
        + _label(380, 205, "Flesh / pericarp", anchor="end", size=11)
    )


def _scene_vehicle() -> str:
    return (
        "<rect x='140' y='230' width='320' height='70' rx='14' fill='#3b82f6' stroke='#1e293b' stroke-width='3'/>"
        "<rect x='175' y='195' width='150' height='48' rx='10' fill='#93c5fd' stroke='#1e293b' stroke-width='3'/>"
        "<rect x='340' y='205' width='95' height='38' rx='8' fill='#bfdbfe' stroke='#1e293b' stroke-width='2'/>"
        "<circle cx='200' cy='300' r='28' fill='#1f2937' stroke='#0f172a' stroke-width='3'/>"
        "<circle cx='200' cy='300' r='10' fill='#9ca3af' stroke='#374151' stroke-width='2'/>"
        "<circle cx='400' cy='300' r='28' fill='#1f2937' stroke='#0f172a' stroke-width='3'/>"
        "<circle cx='400' cy='300' r='10' fill='#9ca3af' stroke='#374151' stroke-width='2'/>"
        + _leader(95, 150, 200, 220)
        + _label(30, 155, "Body", size=11)
        + _leader(520, 260, 420, 275)
        + _label(400, 265, "Wheel (rolling)", anchor="end", size=11)
    )


def _scene_disk() -> str:
    return (
        "<circle cx='300' cy='230' r='118' fill='#e2e8f0' stroke='#1e293b' stroke-width='4'/>"
        "<circle cx='300' cy='230' r='28' fill='#f0f4f8' stroke='#1e293b' stroke-width='3'/>"
        "<path d='M 300 112 A 118 118 0 0 1 410 200' fill='none' stroke='#94a3b8' stroke-width='14' opacity='0.6'/>"
        + _leader(120, 120, 210, 165)
        + _label(30, 125, "Reflective surface", size=11)
        + _leader(400, 320, 328, 250)
        + _label(405, 325, "Center hole", anchor="start", size=11)
    )


def _scene_ball(*, physics: bool) -> str:
    base = (
        "<line x1='80' y1='340' x2='520' y2='340' stroke='#78716c' stroke-width='4'/>"
        "<circle cx='300' cy='265' r='68' fill='#f97316' stroke='#1e293b' stroke-width='3'/>"
        "<path d='M 250 240 Q 300 290 350 240' fill='none' stroke='#1e293b' stroke-width='2'/>"
        "<path d='M 245 275 Q 300 255 355 275' fill='none' stroke='#1e293b' stroke-width='2'/>"
    )
    if not physics:
        return base + _leader(440, 160, 360, 220) + _label(400, 165, "Sphere / ball", anchor="end", size=11)
    return (
        base
        + "<defs><marker id='mf' markerWidth='10' markerHeight='8' refX='9' refY='4' orient='auto'>"
        "<polygon points='0,0 10,4 0,8' fill='#dc2626'/></marker>"
        "<marker id='mb' markerWidth='10' markerHeight='8' refX='9' refY='4' orient='auto'>"
        "<polygon points='0,0 10,4 0,8' fill='#2563eb'/></marker></defs>"
        "<line x1='300' y1='265' x2='300' y2='355' stroke='#dc2626' stroke-width='4' marker-end='url(#mf)'/>"
        + _label(312, 320, "Weight (mg)", size=11)
        + "<line x1='300' y1='333' x2='300' y2='250' stroke='#2563eb' stroke-width='4' marker-end='url(#mb)'/>"
        + _label(312, 270, "Normal N", size=11)
    )


def _scene_rocket() -> str:
    return (
        "<rect x='268' y='180' width='64' height='120' rx='12' fill='#e2e8f0' stroke='#1e293b' stroke-width='3'/>"
        "<path d='M 300 180 L 260 130 L 340 130 Z' fill='#ef4444' stroke='#1e293b' stroke-width='3'/>"
        "<polygon points='268,280 248,320 268,300' fill='#f97316' stroke='#1e293b' stroke-width='2'/>"
        "<polygon points='332,280 352,320 332,300' fill='#f97316' stroke='#1e293b' stroke-width='2'/>"
        "<polygon points='290,300 300,360 310,300' fill='#fbbf24' stroke='#b45309' stroke-width='2'/>"
        + _leader(130, 200, 265, 240)
        + _label(35, 205, "Payload / body", size=11)
        + _leader(470, 200, 335, 200)
        + _label(385, 205, "Nose cone", anchor="end", size=11)
        + _leader(300, 400, 300, 360)
        + _label(220, 395, "Exhaust (thrust)", anchor="middle", size=11)
    )


def _scene_human_body() -> str:
    return (
        "<circle cx='300' cy='118' r='36' fill='#fdba74' stroke='#1e293b' stroke-width='3'/>"
        "<rect x='268' y='158' width='64' height='88' rx='16' fill='#3b82f6' stroke='#1e293b' stroke-width='3'/>"
        "<rect x='228' y='168' width='22' height='72' rx='8' fill='#fdba74' stroke='#1e293b' stroke-width='3'/>"
        "<rect x='350' y='168' width='22' height='72' rx='8' fill='#fdba74' stroke='#1e293b' stroke-width='3'/>"
        "<rect x='278' y='242' width='18' height='88' rx='6' fill='#1e3a8a' stroke='#1e293b' stroke-width='3'/>"
        "<rect x='304' y='242' width='18' height='88' rx='6' fill='#1e3a8a' stroke='#1e293b' stroke-width='3'/>"
        + _leader(95, 110, 268, 118)
        + _label(30, 115, "Head", size=11)
        + _leader(505, 200, 332, 205)
        + _label(410, 205, "Torso", anchor="end", size=11)
        + _leader(120, 310, 240, 210)
        + _label(35, 315, "Arm", size=11)
        + _leader(480, 360, 322, 310)
        + _label(400, 365, "Leg", anchor="end", size=11)
    )


def _scene_child_figure() -> str:
    return (
        "<circle cx='300' cy='135' r='32' fill='#fcd34d' stroke='#1e293b' stroke-width='3'/>"
        "<ellipse cx='300' cy='225' rx='42' ry='55' fill='#a78bfa' stroke='#1e293b' stroke-width='3'/>"
        "<line x1='300' y1='175' x2='250' y2='230' stroke='#1e293b' stroke-width='5' stroke-linecap='round'/>"
        "<line x1='300' y1='175' x2='350' y2='230' stroke='#1e293b' stroke-width='5' stroke-linecap='round'/>"
        "<line x1='280' y1='275' x2='265' y2='340' stroke='#1e293b' stroke-width='5' stroke-linecap='round'/>"
        "<line x1='320' y1='275' x2='335' y2='340' stroke='#1e293b' stroke-width='5' stroke-linecap='round'/>"
        + _label(300, 390, "Simple figure (not to scale)", anchor="middle", size=11)
    )


def _scene_atom() -> str:
    return (
        "<circle cx='300' cy='230' r='22' fill='#f87171' stroke='#991b1b' stroke-width='3'/>"
        "<text x='300' y='236' text-anchor='middle' font-size='11' fill='#450a0a' font-family='sans-serif' font-weight='700'>Nucleus</text>"
        "<ellipse cx='300' cy='230' rx='140' ry='70' fill='none' stroke='#64748b' stroke-width='2' stroke-dasharray='6 4'/>"
        "<circle cx='180' cy='230' r='8' fill='#3b82f6' stroke='#1e3a8a' stroke-width='2'/>"
        "<circle cx='420' cy='230' r='8' fill='#3b82f6' stroke='#1e3a8a' stroke-width='2'/>"
        "<circle cx='300' cy='150' r='8' fill='#3b82f6' stroke='#1e3a8a' stroke-width='2'/>"
        + _leader(95, 100, 175, 215)
        + _label(30, 105, "Electron (model)", size=11)
        + _leader(500, 140, 315, 220)
        + _label(410, 145, "Protons / neutrons in nucleus", anchor="end", size=10)
    )


def _scene_cell() -> str:
    return (
        "<rect x='150' y='120' width='300' height='220' rx='70' fill='#dbeafe' stroke='#1e40af' stroke-width='4'/>"
        "<circle cx='300' cy='220' r='48' fill='#fecaca' stroke='#991b1b' stroke-width='3'/>"
        "<text x='300' y='226' text-anchor='middle' font-size='10' fill='#7f1d1d' font-family='sans-serif' font-weight='700'>Nucleus</text>"
        "<ellipse cx='210' cy='170' rx='28' ry='14' fill='#86efac' stroke='#166534' stroke-width='2'/>"
        "<ellipse cx='395' cy='260' rx='32' ry='16' fill='#86efac' stroke='#166534' stroke-width='2'/>"
        "<text x='210' y='155' text-anchor='middle' font-size='9' fill='#14532d' font-family='sans-serif'>Mitochondrion</text>"
        + _leader(85, 200, 155, 210)
        + _label(25, 205, "Cell membrane", size=10)
        + _leader(520, 320, 420, 265)
        + _label(400, 325, "Organelles (simplified)", anchor="end", size=10)
    )


def _scene_car_ball() -> str:
    """Car + ball — collisions / motion problems."""
    return (
        "<rect x='70' y='230' width='220' height='62' rx='12' fill='#3b82f6' stroke='#1e293b' stroke-width='3'/>"
        "<rect x='95' y='198' width='100' height='40' rx='8' fill='#93c5fd' stroke='#1e293b' stroke-width='2'/>"
        "<circle cx='130' cy='292' r='24' fill='#1f2937' stroke='#0f172a' stroke-width='3'/>"
        "<circle cx='260' cy='292' r='24' fill='#1f2937' stroke='#0f172a' stroke-width='3'/>"
        "<circle cx='455' cy='268' r='46' fill='#facc15' stroke='#1e293b' stroke-width='3'/>"
        "<defs><marker id='mp' markerWidth='10' markerHeight='8' refX='9' refY='4' orient='auto'>"
        "<polygon points='0,0 10,4 0,8' fill='#16a34a'/></marker></defs>"
        "<line x1='310' y1='258' x2='395' y2='258' stroke='#16a34a' stroke-width='4' marker-end='url(#mp)'/>"
        + _leader(40, 150, 120, 220)
        + _label(30, 155, "Car (mass)", size=11)
        + _leader(520, 200, 455, 265)
        + _label(400, 205, "Ball / object", anchor="end", size=11)
        + _label(340, 245, "Possible motion →", size=11)
    )


# --- Rule table: (id, positive_keywords, negative_keywords, title, caption, scene_fn) ---

Rule = tuple[str, tuple[str, ...], tuple[str, ...], str, str, Callable[[], str]]

RULES: list[Rule] = [
    (
        "photosynthesis",
        ("photosynthesis", "chlorophyll", "calvin", "chloroplast"),
        (),
        "Photosynthesis (overview)",
        "Sunlight + chloroplasts → sugars & oxygen (simplified).",
        _scene_photosynthesis,
    ),
    (
        "flower",
        ("flower", "petal", "stamen", "pistil", "pollination", "pollen"),
        (),
        "Flower structure",
        "Typical parts for pollination and seed formation.",
        _scene_flower,
    ),
    (
        "fruit",
        ("fruit", "apple", "orange", "berry", "banana", "citrus"),
        ("grapefruit",),
        "Fruit (concept)",
        "Protects seeds and aids dispersal.",
        _scene_fruit,
    ),
    (
        "tree",
        ("tree", "oak", "forest", "wood", "timber"),
        ("family tree", "decision tree", "syntax tree"),
        "Tree (plant)",
        "Shoot system above ground; roots below.",
        _scene_tree,
    ),
    (
        "plant",
        ("seedling", "germination", "sprout"),
        (),
        "Plant & light",
        "Young plant: stem, leaves, soil, and sunlight.",
        _scene_plant_sun,
    ),
    (
        "car_ball",
        ("car", "vehicle", "truck", "bus"),
        (),
        "Vehicle & object",
        "Use for motion, forces, or energy examples.",
        _scene_car_ball,
    ),
    (
        "vehicle",
        ("car", "van", "automobile", "wheel", "tire", "tyre", "engine", "motor"),
        (),
        "Vehicle (side view)",
        "Rigid body on wheels — useful in kinematics.",
        _scene_vehicle,
    ),
    (
        "rocket",
        ("rocket", "spacecraft", "launch", "thrust"),
        (),
        "Rocket (concept)",
        "Body, nose, fins, exhaust — thrust pushes forward on gas.",
        _scene_rocket,
    ),
    (
        "ball_physics",
        (
            "free body",
            "force diagram",
            "normal force",
            "friction on",
            "ball on",
            "sphere on",
            "block on",
            "on a ramp",
        ),
        (),
        "Ball on a surface (forces)",
        "Weight and normal force on a sphere at rest (simplified).",
        lambda: _scene_ball(physics=True),
    ),
    (
        "ball",
        ("ball", "sphere", "soccer", "football", "basketball", "tennis", "cricket ball"),
        ("crystal ball",),
        "Sphere (ball)",
        "Round object — volume and symmetry in math/physics.",
        lambda: _scene_ball(physics=False),
    ),
    (
        "atom",
        ("atom", "electron", "proton", "neutron", "atomic", "bohr", "orbital"),
        ("electronic", "electronics", "electric circuit"),
        "Atom (model)",
        "Nucleus and electrons — not to scale.",
        _scene_atom,
    ),
    (
        "cell",
        (
            "mitochondria",
            "cytoplasm",
            "cell membrane",
            "chloroplast",
            "vacuole",
            "ribosome",
            "organism",
            "plant cell",
            "animal cell",
        ),
        (),
        "Cell (simplified)",
        "Membrane, nucleus, and organelles — diagram not to scale.",
        _scene_cell,
    ),
    (
        "cell2",
        ("cell", "biology", "tissue"),
        ("spreadsheet", "battery", "prison cell", "cell phone", "cellphone", "fuel cell"),
        "Cell (simplified)",
        "Basic parts of a eukaryotic cell (cartoon).",
        _scene_cell,
    ),
    (
        "human_body",
        (
            "human body",
            "body parts",
            "torso",
            "limb",
            "skeleton",
            "anatomy",
            "muscle",
        ),
        (),
        "Human body (simple)",
        "Major regions — not an anatomical plate.",
        _scene_human_body,
    ),
    (
        "child",
        ("child", "boy", "girl", "kid", "pupil", "student figure"),
        (),
        "Child (stick-style)",
        "Very simple figure for scale or story problems.",
        _scene_child_figure,
    ),
]


def _wants_disc_or_cd_visual(lower: str) -> bool:
    if re.search(r"\b(cd|dvd)s?\b", lower):
        return True
    if "compact disc" in lower or "optical disc" in lower or "blu-ray" in lower or "bluray" in lower:
        return True
    if re.search(r"\bdisc\b", lower):
        if any(
            x in lower
            for x in (
                "discover",
                "discard",
                "discord",
                "discrete",
                "disconnect",
                "discipline",
                "disclaim",
            )
        ):
            return False
        return True
    if re.search(r"\bdisk\b", lower):
        if any(x in lower for x in ("hard disk", "disk jockey", "diskette", "floppy")):
            return False
        return True
    return False


def try_parametric_teaching_svg(user_msg: str) -> tuple[str, str] | None:
    """
    If the message clearly matches a template, return (title, full_svg).
    Otherwise None.
    """
    lower = (user_msg or "").lower()
    if len(lower) < 3:
        return None

    if _wants_disc_or_cd_visual(lower):
        return (
            "Disc / CD",
            _wrap(
                "Disc / CD",
                _scene_disk(),
                "Stores data in a spiral track (simplified).",
            ),
        )

    for _rid, pos, neg, title, caption, fn in RULES:
        if any(n in lower for n in neg):
            continue
        if not any(p in lower for p in pos):
            continue
        # car_ball only if both vehicle-ish and ball/motion context
        if _rid == "car_ball":
            if not any(b in lower for b in ("ball", "block", "box", "mass", "hit", "crash", "push", "collision")):
                continue
        body = fn()
        return title, _wrap(title, body, caption)

    return None
