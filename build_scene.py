import bpy, math

# ---------- CLEAR SCENE ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
    for b in list(coll):
        coll.remove(b)

# ---------- MATERIALS ----------
def emission_mat(name, color, strength=25):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em  = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*color, 1)
    em.inputs['Strength'].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m

def diffuse_mat(name, color, roughness=0.9):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    return m

mat_figure   = diffuse_mat('Figure',  (0.015, 0.015, 0.02))
mat_hair     = diffuse_mat('Hair',    (0.40, 0.32, 0.22), 0.85)
mat_stone    = diffuse_mat('Stone',   (0.32, 0.29, 0.25), 0.95)
mat_ground   = diffuse_mat('Ground',  (0.30, 0.30, 0.26), 1.0)
mat_smoke_d  = diffuse_mat('SmokeD',  (0.38, 0.35, 0.30), 1.0)   # darker lower smoke
mat_smoke_l  = diffuse_mat('SmokeL',  (0.78, 0.72, 0.60), 1.0)   # lighter upper smoke
mat_rocket   = diffuse_mat('Rocket',  (0.88, 0.88, 0.90), 0.35)
mat_flame    = emission_mat('Flame',  (1.0, 0.45, 0.08), 35)
mat_flame_y  = emission_mat('FlameY', (1.0, 0.75, 0.25), 45)
mat_flame_r  = emission_mat('FlameR', (1.0, 0.22, 0.05), 20)

# ---------- GROUND ----------
bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 10, 0))
bpy.context.object.data.materials.append(mat_ground)

# ---------- PEDESTAL ----------
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
p = bpy.context.object; p.scale = (0.9, 0.85, 1.0)
p.data.materials.append(mat_stone)
bpy.ops.mesh.primitive_cube_add(size=2, location=(0.55, 0.5, 0.45))
p2 = bpy.context.object; p2.scale = (0.45, 0.45, 0.45)
p2.data.materials.append(mat_stone)
bpy.ops.mesh.primitive_cube_add(size=2, location=(-0.65, 0.35, 0.3))
p3 = bpy.context.object; p3.scale = (0.35, 0.35, 0.3)
p3.data.materials.append(mat_stone)

# ---------- FIGURE ----------
base_z = 2.0  # top of pedestal
FIG_Y  = 0.0   # figure Y

# Legs (close together, slightly narrow stance)
for x in (-0.10, 0.10):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, FIG_Y, base_z + 0.5))
    l = bpy.context.object; l.scale = (0.10, 0.13, 0.55)
    l.data.materials.append(mat_figure)

# Hip band
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, FIG_Y, base_z + 1.02))
hp = bpy.context.object; hp.scale = (0.26, 0.17, 0.16)
hp.data.materials.append(mat_figure)

# Torso — tapered (wider at shoulders) via two stacked cubes + uv sphere blend
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, FIG_Y, base_z + 1.55))
tl = bpy.context.object; tl.scale = (0.28, 0.18, 0.45)     # lower torso
tl.data.materials.append(mat_figure)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, FIG_Y, base_z + 2.05))
tu = bpy.context.object; tu.scale = (0.38, 0.20, 0.25)     # upper torso / shoulders
tu.data.materials.append(mat_figure)

# Shoulder caps (spheres to smooth join)
for sx in (-0.36, 0.36):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.17, location=(sx, FIG_Y, base_z + 2.15))
    sh = bpy.context.object
    sh.data.materials.append(mat_figure)

# Neck
bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.18, location=(0, FIG_Y, base_z + 2.38))
nk = bpy.context.object
nk.data.materials.append(mat_figure)

# Head
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(0, FIG_Y, base_z + 2.62))
hd = bpy.context.object
hd.data.materials.append(mat_figure)

# Hair — short, slightly lighter, crown
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.235, location=(0, FIG_Y - 0.02, base_z + 2.68))
hr = bpy.context.object; hr.scale = (1, 1, 0.75)
hr.data.materials.append(mat_hair)

# ARMS — outstretched, slight upward tilt, connected at shoulder
arm_tilt = math.radians(14)
for side in (-1, 1):
    # Arm cylinder oriented along X
    length = 1.15
    bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=length,
                                         location=(side * (0.36 + length/2 * math.cos(arm_tilt)),
                                                   FIG_Y,
                                                   base_z + 2.15 + length/2 * math.sin(arm_tilt)))
    a = bpy.context.object
    a.rotation_euler = (0, math.radians(90) + -side * arm_tilt, 0)
    a.data.materials.append(mat_figure)

    # Elbow/end cap sphere
    ex = side * (0.36 + length * math.cos(arm_tilt))
    ez = base_z + 2.15 + length * math.sin(arm_tilt)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.10, location=(ex, FIG_Y, ez))
    bpy.context.object.data.materials.append(mat_figure)

    # Splayed hand: a flat flattened sphere with small "fingers"
    hx = side * (0.36 + (length + 0.18) * math.cos(arm_tilt))
    hz = base_z + 2.15 + (length + 0.18) * math.sin(arm_tilt)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.13, location=(hx, FIG_Y, hz))
    hand = bpy.context.object; hand.scale = (1.3, 0.45, 1.0)
    hand.data.materials.append(mat_figure)
    # a couple of finger nubs
    for fz_off, fx_off in [(0.10, 0.05), (0.16, 0.0), (0.10, -0.05), (-0.05, 0.07)]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03,
                                              location=(hx + side*fx_off*2, FIG_Y, hz + fz_off))
        bpy.context.object.data.materials.append(mat_figure)

# ---------- ROCKET / SMOKE COLUMNS ----------
# closer to figure, framing it left & right
columns = [
    (-9.5, 9.0, 1.05),
    (-6.0, 8.0, 0.95),
    (-3.0, 9.5, 1.00),
    ( 2.8, 8.5, 0.98),
    ( 5.8, 9.2, 1.05),
    ( 9.0, 9.8, 0.90),
    (-11.5,11.0, 0.85),
]

for idx, (cx, cy, s) in enumerate(columns):
    # Column body: use stacked spheres to look puffy, plus a tapered cone core
    h = 10 * s

    # Core tapered cone (darker lower smoke)
    bpy.ops.mesh.primitive_cone_add(radius1=1.3*s, radius2=0.35*s, depth=h,
                                     location=(cx, cy, h/2 - 0.2))
    core = bpy.context.object
    core.data.materials.append(mat_smoke_d)

    # Puffy smoke balls along the column (lighter)
    for k in range(6):
        frac = k / 5
        zk = 0.6 + frac * (h - 1.2)
        rk = (1.5 - frac * 0.9) * s
        jitter_x = ((idx * 37 + k * 13) % 11 - 5) * 0.08 * s
        jitter_y = ((idx * 19 + k * 7) % 9 - 4) * 0.08 * s
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=rk,
            location=(cx + jitter_x, cy + jitter_y, zk))
        pf = bpy.context.object
        pf.scale = (1.0, 1.0, 0.85)
        pf.data.materials.append(mat_smoke_l if k >= 2 else mat_smoke_d)

    # Flame cluster at top of trail (below rocket)
    fz = h + 0.1
    # outer red glow
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.9*s, location=(cx, cy, fz))
    f1 = bpy.context.object; f1.scale = (1.0, 1.0, 1.8)
    f1.data.materials.append(mat_flame_r)
    # mid orange
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.55*s, location=(cx, cy, fz + 0.3*s))
    f2 = bpy.context.object; f2.scale = (1.0, 1.0, 1.6)
    f2.data.materials.append(mat_flame)
    # inner yellow hot core
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.28*s, location=(cx, cy, fz + 0.5*s))
    f3 = bpy.context.object; f3.scale = (1.0, 1.0, 1.4)
    f3.data.materials.append(mat_flame_y)

    # Rocket body
    rz = fz + 1.3*s
    bpy.ops.mesh.primitive_cylinder_add(radius=0.22*s, depth=1.2*s, location=(cx, cy, rz))
    r = bpy.context.object
    r.data.materials.append(mat_rocket)
    # Nose cone
    bpy.ops.mesh.primitive_cone_add(radius1=0.22*s, depth=0.55*s,
                                     location=(cx, cy, rz + 0.87*s))
    nc = bpy.context.object
    nc.data.materials.append(mat_rocket)
    # Tail fins (4, crosswise)
    for ang in (0, 90, 180, 270):
        bpy.ops.mesh.primitive_cube_add(size=1,
                                         location=(cx + 0.25*s*math.cos(math.radians(ang)),
                                                   cy + 0.25*s*math.sin(math.radians(ang)),
                                                   rz - 0.45*s))
        fn = bpy.context.object
        fn.scale = (0.20*s, 0.03*s, 0.28*s)
        fn.rotation_euler = (0, 0, math.radians(ang))
        fn.data.materials.append(mat_rocket)

# ---------- LIGHTS ----------
# Bright backlight sun (hazy, slightly warm)
bpy.ops.object.light_add(type='SUN', location=(0, 30, 22))
sun = bpy.context.object
sun.data.energy = 6
sun.data.color = (1.0, 0.88, 0.72)
sun.rotation_euler = (math.radians(55), 0, math.radians(180))

# Cool ambient fill from camera side
bpy.ops.object.light_add(type='AREA', location=(0, -7, 5))
fill = bpy.context.object
fill.data.energy = 150
fill.data.size = 10
fill.data.color = (0.60, 0.72, 1.0)

# Warm flame glow point lights at each column
for cx, cy, s in columns:
    bpy.ops.object.light_add(type='POINT', location=(cx, cy, 10*s))
    pl = bpy.context.object
    pl.data.energy = 1500 * s
    pl.data.color = (1.0, 0.45, 0.12)
    pl.data.shadow_soft_size = 1.5

# Rim light from upper-right to define silhouette shoulders/hair
bpy.ops.object.light_add(type='SPOT', location=(4, -2, 9))
rim = bpy.context.object
rim.data.energy = 800
rim.data.color = (1.0, 0.80, 0.55)
rim.data.spot_size = math.radians(60)
rim.rotation_euler = (math.radians(110), 0, math.radians(25))

# ---------- WORLD ----------
world = bpy.context.scene.world
world.use_nodes = True
wnt = world.node_tree
wnt.nodes.clear()
out  = wnt.nodes.new('ShaderNodeOutputWorld')
bg   = wnt.nodes.new('ShaderNodeBackground')
ramp = wnt.nodes.new('ShaderNodeValToRGB')
tex  = wnt.nodes.new('ShaderNodeTexGradient')
mapn = wnt.nodes.new('ShaderNodeMapping')
crd  = wnt.nodes.new('ShaderNodeTexCoord')

tex.gradient_type = 'LINEAR'
mapn.inputs['Rotation'].default_value[1] = math.radians(90)
# low horizon dusty, upper sky bright and slightly golden
ramp.color_ramp.elements[0].color = (0.55, 0.55, 0.48, 1)
e_mid = ramp.color_ramp.elements.new(0.45)
e_mid.color = (0.80, 0.78, 0.68, 1)
ramp.color_ramp.elements[-1].color = (0.95, 0.95, 0.88, 1)
bg.inputs['Strength'].default_value = 1.3

wnt.links.new(crd.outputs['Generated'], mapn.inputs['Vector'])
wnt.links.new(mapn.outputs['Vector'], tex.inputs['Vector'])
wnt.links.new(tex.outputs['Color'], ramp.inputs['Fac'])
wnt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
wnt.links.new(bg.outputs[0], out.inputs[0])

# ---------- CAMERA ----------
bpy.ops.object.camera_add(location=(0, -5.5, base_z + 0.9))
cam = bpy.context.object
cam.rotation_euler = (math.radians(102), 0, 0)
cam.data.lens = 32
bpy.context.scene.camera = cam

# ---------- RENDER / VIEWPORT ----------
scn = bpy.context.scene
try:
    scn.render.engine = 'BLENDER_EEVEE_NEXT'
except Exception:
    scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x = 1920
scn.render.resolution_y = 1080
scn.render.film_transparent = False

# Bloom where available
try:
    scn.eevee.use_bloom = True
    scn.eevee.bloom_intensity = 0.2
    scn.eevee.bloom_threshold = 1.0
    scn.eevee.bloom_radius = 6.0
except Exception:
    pass

# Color management punch
try:
    scn.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    try:
        scn.view_settings.look = 'Medium High Contrast'
    except Exception:
        pass

# Switch viewport to camera + rendered shading
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for sp in area.spaces:
            if sp.type == 'VIEW_3D':
                sp.shading.type = 'RENDERED'
                sp.region_3d.view_perspective = 'CAMERA'

print("Scene rebuilt.")
