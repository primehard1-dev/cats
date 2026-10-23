"""Builds the hero cat from rounded parts: a stylised, soft-shaped Bengal kitten-cat for phones.

Run:  python tools/blender/make_cat.py [out_dir] [--render preview_dir]

- body, chest, haunches, big round head with cheeks and muzzle, ears, legs, paws and a curled tail are
  made of ellipsoids and sphere chains, fused into one watertight surface (voxel remesh) and smoothed
- eyes stay separate glossy spheres (crisp slit pupils)
- UVs + a painted texture: golden coat, soft rosettes, cream belly/muzzle, pink nose and inner ears,
  green eyes; a second "ginger" skin for the co-op player
- skeleton with the bone names CatAnimator expects: Body, Neck, Head, Leg_FL/FR/BL/BR, Tail1..Tail5
- exports CatHero.fbx (+ T_CatHero_A.png, T_CatHero_Ginger_A.png); faces -Y like the old model, 0.36 m to the ear tips
"""
import math
import os
import sys

import bpy
import bmesh  # noqa: E402  (needs bpy first)
import numpy as np
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(__file__))
from bengal_texture import noise3, rasterise, smooth, worley3d  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "CatsGame", "Assets", "_Project")
TEX = 1024
TARGET_TRIS = 9000

# ---------------------------------------------------------------- proportions (metres, nose towards -Y, Z up)
HEAD_C = Vector((0, -0.175, 0.262))
HEAD_R = 0.066
EYE_R = 0.0165
EYES = [Vector((s * 0.029, -0.229, 0.274)) for s in (1, -1)]
NOSE = Vector((0, -0.258, 0.252))
SHOULDER = [Vector((s * 0.036, -0.085, 0.150)) for s in (1, -1)]
HIP = [Vector((s * 0.040, 0.080, 0.150)) for s in (1, -1)]
TAIL = [Vector(p) for p in ((0, 0.125, 0.170), (0, 0.170, 0.175), (0, 0.205, 0.200), (0, 0.225, 0.240),
                            (0, 0.228, 0.285), (0, 0.215, 0.320))]


def ellipsoid(bm, c, r, rot=(0, 0, 0), seg=24):
    m = Matrix.Translation(c) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((r[0], r[1], r[2], 1.0))
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2 + 2, radius=1.0, matrix=m)


def chain(bm, pts, radii, step=0.005):
    """A soft tube: spheres along a polyline with interpolated radius."""
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        n = max(1, int((b - a).length / step))
        for k in range(n + (i == len(pts) - 2)):
            t = k / n
            r = radii[i] + (radii[i + 1] - radii[i]) * t
            ellipsoid(bm, a.lerp(b, t), (r, r, r), seg=14)


def ear(bm, side):
    """Rounded triangle ear: a flattened cone tilted outwards and slightly back."""
    m = (Matrix.Translation((side * 0.037, -0.168, 0.316)) @
         Euler((math.radians(-12), math.radians(side * 22), 0)).to_matrix().to_4x4() @
         Matrix.Diagonal((1.0, 0.42, 1.0, 1.0)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.026, radius2=0.004, depth=0.05,
                          matrix=m @ Matrix.Translation((0, 0, 0.012)))


def body_parts(bm):
    ellipsoid(bm, (0, -0.075, 0.170), (0.063, 0.078, 0.070))      # chest
    ellipsoid(bm, (0, 0.005, 0.166), (0.060, 0.088, 0.064))       # belly
    ellipsoid(bm, (0, 0.075, 0.168), (0.066, 0.068, 0.070))       # haunches
    ellipsoid(bm, (0, -0.135, 0.212), (0.040, 0.045, 0.048))      # neck
    ellipsoid(bm, HEAD_C, (HEAD_R * 1.08, HEAD_R * 0.95, HEAD_R * 0.92))
    for s in (1, -1):
        ellipsoid(bm, (s * 0.040, -0.205, 0.244), (0.034, 0.030, 0.030))   # cheeks
        ellipsoid(bm, (s * 0.012, -0.240, 0.245), (0.018, 0.017, 0.015))   # whisker pads
        ear(bm, s)
    ellipsoid(bm, (0, -0.236, 0.236), (0.016, 0.015, 0.012))       # chin
    ellipsoid(bm, NOSE, (0.009, 0.006, 0.006))
    for s, sh, hp in ((1, SHOULDER[0], HIP[0]), (-1, SHOULDER[1], HIP[1])):
        # front leg: upper arm, forearm, paw
        chain(bm, [sh, Vector((s * 0.034, -0.092, 0.090)), Vector((s * 0.033, -0.098, 0.030))], [0.030, 0.024, 0.021])
        ellipsoid(bm, (s * 0.034, -0.107, 0.017), (0.023, 0.029, 0.017))
        # hind leg: thigh, hock, paw
        ellipsoid(bm, hp + Vector((0, 0.008, -0.012)), (0.040, 0.054, 0.058))
        chain(bm, [hp + Vector((0, 0.020, -0.050)), Vector((s * 0.038, 0.105, 0.060)), Vector((s * 0.036, 0.085, 0.030))],
              [0.026, 0.021, 0.020])
        ellipsoid(bm, (s * 0.037, 0.073, 0.017), (0.023, 0.030, 0.017))
    chain(bm, TAIL, [0.020, 0.018, 0.016, 0.015, 0.014, 0.013])


def build_fur():
    me = bpy.data.meshes.new("CatHero_Mesh")
    bm = bmesh.new()
    body_parts(bm)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("CatHero_Mesh", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    rm = ob.modifiers.new("Remesh", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = 0.0028
    bpy.ops.object.modifier_apply(modifier=rm.name)
    sm = ob.modifiers.new("Smooth", "SMOOTH")
    sm.factor = 0.6
    sm.iterations = 8
    bpy.ops.object.modifier_apply(modifier=sm.name)
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    dec = ob.modifiers.new("Decimate", "DECIMATE")
    dec.ratio = min(1.0, (TARGET_TRIS - 800) / tris)
    bpy.ops.object.modifier_apply(modifier=dec.name)
    return ob


def build_eyes():
    me = bpy.data.meshes.new("Eyes")
    bm = bmesh.new()
    for c in EYES:
        # look forward and a bit outwards; flattened front so the eye sits in the face
        out = math.copysign(math.radians(18), c.x)
        ellipsoid(bm, c, (EYE_R, EYE_R * 0.72, EYE_R * 1.02), rot=(0, 0, out), seg=20)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("Eyes", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# ---------------------------------------------------------------- texture
def paint(pos, nor, eye, palette):
    x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
    nz = nor[..., 2]
    base = np.array(palette["coat"])
    back = np.array(palette["back"])
    cream = np.array(palette["cream"])
    dark = np.array(palette["dark"])
    mid = np.array(palette["mid"])

    # belly, chest, chin, muzzle and inner legs are cream
    belly = smooth(-0.05, -0.6, nz) * smooth(0.21, 0.15, z)
    muzzle = smooth(-0.226, -0.240, y) * smooth(0.268, 0.258, z)
    chin = smooth(-0.21, -0.23, y) * smooth(0.245, 0.232, z)
    paws = smooth(0.026, 0.012, z)
    cream_k = np.clip(belly + muzzle + chin + paws * 0.8, 0, 1)
    col = base + (back - base) * smooth(0.3, 0.95, nz)[..., None]   # darker along the back
    col = col * (1 - cream_k[..., None]) + cream * cream_k[..., None]

    head = smooth(-0.13, -0.15, y) * smooth(0.2, 0.22, z)
    tail = smooth(0.12, 0.14, y) * smooth(0.15, 0.17, z)
    legs = smooth(0.11, 0.07, z)

    # soft, irregular rosettes on body and haunches, small spots on legs and forehead
    warp = np.stack([noise3(pos, 45, 11 + k) - 0.5 for k in range(3)], -1) * 0.014
    rp = (pos + warp) * np.array([1.0, 0.7, 1.0])
    f1, rid = worley3d(rp, 0.03, 3)
    fr = f1 / (0.8 + 0.4 * rid)
    ring = smooth(0.18, 0.26, fr) * smooth(0.46, 0.34, fr) * (0.45 + 0.55 * smooth(0.35, 0.5, noise3(pos, 120, 21)))
    core = smooth(0.30, 0.14, fr)
    amount = (1 - cream_k * 0.9) * (1 - head) * (1 - tail) * (1 - legs * 0.7)
    col = col * (1 - (core * amount * 0.7)[..., None]) + mid * (core * amount * 0.7)[..., None]
    col = col * (1 - (ring * amount * 0.65)[..., None]) + dark * (ring * amount * 0.65)[..., None]
    spot_f1, _ = worley3d(pos + warp, 0.016, 5)
    spot = smooth(0.36, 0.22, spot_f1) * np.clip(legs * (1 - paws) + head * smooth(0.27, 0.3, z), 0, 1) * (1 - cream_k)
    col = col * (1 - (spot * 0.7)[..., None]) + dark * (spot * 0.7)[..., None]
    # forehead "M" stripes and cheek lines
    fore = head * smooth(0.29, 0.31, z) * smooth(0.006, 0.0, np.abs(np.abs(x) - 0.012 - 0.004 * np.sin((z - 0.29) * 300)))
    lines = np.clip(fore, 0, 1) * 0.7
    col = col * (1 - lines[..., None]) + dark * lines[..., None]
    # tail rings and dark tip
    ty = np.linalg.norm(pos - np.array([0, 0.125, 0.17]), axis=-1) / 0.03
    band = smooth(0.28, 0.12, np.abs(ty - np.round(ty))) * tail * smooth(1.5, 2.0, ty)
    tip = smooth(0.30, 0.315, z) * tail
    k = np.clip(band * 0.8 + tip, 0, 1)[..., None]
    col = col * (1 - k) + dark * k

    # inner ears pink, nose pink
    # inner ear: a smaller rounded triangle inside the front of the ear, the rim keeps the coat colour
    ex = np.abs(x) - 0.038 - (z - 0.32) * 0.35
    ear_in = (smooth(0.318, 0.326, z) * smooth(0.36, 0.35, z) * smooth(-0.35, -0.7, nor[..., 1])
              * smooth(0.012, 0.007, np.abs(ex) + (z - 0.32) * 0.25) * head)
    col = col * (1 - ear_in[..., None] * 0.8) + np.array(palette["pink"]) * ear_in[..., None] * 0.8
    nose = smooth(0.009, 0.006, np.linalg.norm(pos - np.array(NOSE[:]), axis=-1)) * smooth(-0.252, -0.256, y)
    col = col * (1 - nose[..., None]) + np.array(palette["nose"]) * nose[..., None]

    # fur grain: fine streaks along the body
    grain = 1 + (noise3(pos * np.array([1, 0.25, 1]), 900, 31) - 0.5) * 0.12
    col = col * grain[..., None]

    # eyes: iris gradient, vertical slit pupil, dark rim, catch light
    eye_col = np.zeros_like(col)
    for c in EYES:
        d = pos - np.array(c[:])
        fwd = np.array([math.copysign(math.sin(math.radians(18)), c.x), -math.cos(math.radians(18)), 0.0])
        right = np.array([fwd[1], -fwd[0], 0.0]) * -1
        u = (d @ right) / EYE_R
        v = d[..., 2] / EYE_R
        r = np.sqrt(u * u + v * v)
        iris = np.array(palette["iris_in"]) * (1 - r[..., None]) + np.array(palette["iris_out"]) * r[..., None]
        pupil = smooth(0.16, 0.10, np.abs(u) / np.maximum(0.05, 1 - v * v) ** 0.5)
        rim = smooth(0.82, 0.95, r)
        e = iris * (1 - pupil[..., None]) + np.array([0.02, 0.02, 0.025]) * pupil[..., None]
        e = e * (1 - rim[..., None] * 0.85)
        hl = smooth(0.2, 0.12, np.sqrt((u - math.copysign(0.32, -c.x)) ** 2 + (v - 0.38) ** 2))
        e = e * (1 - hl[..., None]) + hl[..., None]
        near = (np.linalg.norm(d, axis=-1) < EYE_R * 1.3)[..., None]
        eye_col = np.where(near, e, eye_col)
    col = col * (1 - eye[..., None]) + eye_col * eye[..., None]
    return np.clip(col, 0, 1)


PALETTES = {
    "T_CatHero_A": {"coat": [0.86, 0.50, 0.15], "back": [0.70, 0.35, 0.09], "cream": [0.96, 0.88, 0.70],
                    "dark": [0.17, 0.09, 0.04], "mid": [0.52, 0.24, 0.06], "pink": [0.93, 0.62, 0.62],
                    "nose": [0.85, 0.47, 0.47], "iris_in": [0.85, 0.82, 0.30], "iris_out": [0.30, 0.62, 0.22]},
    "T_CatHero_Ginger_A": {"coat": [0.93, 0.56, 0.24], "back": [0.85, 0.45, 0.16], "cream": [0.98, 0.93, 0.82],
                           "dark": [0.70, 0.33, 0.10], "mid": [0.80, 0.42, 0.14], "pink": [0.95, 0.66, 0.66],
                           "nose": [0.90, 0.52, 0.52], "iris_in": [0.95, 0.80, 0.30], "iris_out": [0.80, 0.50, 0.15]},
}


def texture(ob, eye_mask, out_dir):
    me = ob.data
    me.calc_loop_triangles()
    co = np.array([v.co[:] for v in me.vertices])
    nrm = np.array([v.normal[:] for v in me.vertices])
    tris = np.array([t.vertices[:] for t in me.loop_triangles])
    loops = np.array([t.loops[:] for t in me.loop_triangles])
    uvs = np.array([d.uv[:] for d in me.uv_layers[0].data])
    pos, nor, mask = rasterise(co, nrm, tris, loops, uvs, TEX, TEX)
    # eye membership per texel: rasterise the vertex mask through the position channel trick
    eyepos, _, _ = rasterise(np.repeat(eye_mask[:, None], 3, 1), nrm, tris, loops, uvs, TEX, TEX)
    eye = eyepos[..., 0]
    os.makedirs(out_dir, exist_ok=True)
    from PIL import Image, ImageFilter
    for name, pal in PALETTES.items():
        col = paint(pos, nor, eye, pal)
        img = Image.fromarray((col * 255 + 0.5).astype(np.uint8))
        # bleed colours past the UV island borders (mip-map seams)
        m = Image.fromarray((mask * 255).astype(np.uint8))
        for _ in range(6):
            grown = img.filter(ImageFilter.MaxFilter(3))
            img = Image.composite(img, grown, m)
            m = m.filter(ImageFilter.MaxFilter(3))
        img.save(os.path.join(out_dir, name + ".png"))
    return os.path.join(out_dir, "T_CatHero_A.png")


# ---------------------------------------------------------------- skeleton + weights
def seg_dist(p, a, b):
    ab = b - a
    t = np.clip(((p - a) @ ab) / max(1e-9, ab @ ab), 0, 1)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1)


def rig(ob, eye_mask):
    arm_data = bpy.data.armatures.new("CatHero_Rig")
    arm = bpy.data.objects.new("CatHero", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones
    bones = {}

    def bone(name, head, tail, parent=None):
        b = eb.new(name)
        b.head, b.tail, b.roll = Vector(head), Vector(tail), 0.0
        if parent:
            b.parent = eb[parent]
        bones[name] = (np.array(head), np.array(tail))

    hip, chest = (0, 0.075, 0.172), (0, -0.075, 0.178)
    bone("Body", hip, chest)
    bone("Neck", chest, (0, -0.140, 0.228), "Body")
    bone("Head", (0, -0.140, 0.228), (0, -0.250, 0.262), "Neck")
    for name, top, paw in (("Leg_FL", SHOULDER[0], (0.033, -0.100, 0.015)), ("Leg_FR", SHOULDER[1], (-0.033, -0.100, 0.015)),
                           ("Leg_BL", HIP[0], (0.036, 0.080, 0.015)), ("Leg_BR", HIP[1], (-0.036, 0.080, 0.015))):
        bone(name, top[:], paw, "Body")
    parent = "Body"
    for i in range(5):
        bone(f"Tail{i + 1}", TAIL[i][:], TAIL[i + 1][:], parent)
        parent = f"Tail{i + 1}"
    bpy.ops.object.mode_set(mode="OBJECT")

    co = np.array([v.co[:] for v in ob.data.vertices])
    names = list(bones)
    D = np.stack([seg_dist(co, *bones[n]) for n in names], 1)
    # legs only own what is below the body; the head owns the face and ears; tail only behind the haunches
    z, y = co[:, 2], co[:, 1]
    for i, n in enumerate(names):
        if n.startswith("Leg"):
            D[:, i] += np.clip(z - 0.125, 0, None) * 2.5
        if n.startswith("Tail"):
            D[:, i] += np.clip(0.125 - y, 0, None) * 4.0
    W = np.exp(-(D / 0.018) ** 2)
    W[eye_mask > 0.5] = 0
    W[eye_mask > 0.5, names.index("Head")] = 1
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    groups = {n: ob.vertex_groups.new(name=n) for n in names}
    for vi in range(len(co)):
        order = np.argsort(-W[vi])[:3]
        tot = W[vi, order].sum()
        for j in order:
            if W[vi, j] > 0.02:
                groups[names[j]].add([vi], float(W[vi, j] / tot), "REPLACE")
    ob.parent = arm
    mod = ob.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    return arm


# ---------------------------------------------------------------- preview render
def render(out_dir, tex_path):
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = 48
    scn.render.resolution_x, scn.render.resolution_y = 900, 700
    scn.view_settings.view_transform = "AgX"
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.25, 0.28, 0.35, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    scn.world = world
    for name, loc, energy in (("Key", (0.6, -0.8, 0.9), 60), ("Fill", (-0.8, -0.4, 0.4), 20), ("Rim", (0, 0.9, 0.7), 40)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy, ld.size = energy, 0.5
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 0.18)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        scn.collection.objects.link(lo)
    floor = bpy.data.meshes.new("Floor")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=2)
    bm.to_mesh(floor)
    bm.free()
    scn.collection.objects.link(bpy.data.objects.new("Floor", floor))
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.lens = 60
    scn.collection.objects.link(cam)
    scn.camera = cam
    for i, (az, el, dist) in enumerate(((-35, 12, 1.15), (-90, 8, 1.2), (-160, 20, 1.2), (0, 6, 0.7))):
        a, e = math.radians(az), math.radians(el)
        target = Vector((0, -0.05, 0.17)) if i < 3 else Vector((0, -0.2, 0.26))
        cam.location = target + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
        cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
        scn.render.filepath = os.path.join(out_dir, f"cat_{i}.png")
        bpy.ops.render.render(write_still=True)


def main(out, preview):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    fur = build_fur()
    eyes = build_eyes()
    eye_n = len(eyes.data.vertices)
    bpy.ops.object.select_all(action="DESELECT")
    fur.select_set(True)
    eyes.select_set(True)
    bpy.context.view_layer.objects.active = fur
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = ob.data.name = "CatHero_Mesh"
    n = len(ob.data.vertices)
    eye_mask = np.zeros(n)
    eye_mask[n - eye_n:] = 1.0          # joined vertices are appended after the fur
    for p in ob.data.polygons:
        p.use_smooth = True

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")
    tex_path = texture(ob, eye_mask, os.path.join(out, "Art", "Textures"))

    mat = bpy.data.materials.new("M_CatHero")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    img = bpy.data.images.load(tex_path)
    tn = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tn.image = img
    mat.node_tree.links.new(tn.outputs[0], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.8
    ob.data.materials.clear()
    ob.data.materials.append(mat)

    arm = rig(ob, eye_mask)
    tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    print(f"cat: {len(ob.data.vertices)} verts, {tris} tris")

    os.makedirs(os.path.join(out, "Art", "Models"), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = arm
    path = os.path.join(out, "Art", "Models", "CatHero.fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"ARMATURE", "MESH"},
                             apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
                             bake_space_transform=False, use_mesh_modifiers=False, add_leaf_bones=False,
                             primary_bone_axis="Y", secondary_bone_axis="X", bake_anim=False,
                             mesh_smooth_type="FACE", path_mode="STRIP")
    print("exported", os.path.abspath(path))
    if preview:
        render(preview, tex_path)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    prev = None
    if "--render" in sys.argv:
        prev = sys.argv[sys.argv.index("--render") + 1]
        args = [a for a in args if a != prev]
    main(args[0] if args else ROOT, prev)
