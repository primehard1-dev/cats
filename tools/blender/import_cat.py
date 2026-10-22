"""Turns a downloaded cat model (glTF/GLB) into the game's rigged hero cat.

Run:  python tools/blender/import_cat.py <cat.glb> [out_dir]

- bakes transforms, scales the cat to 0.36 m (ear tips), feet on the ground, facing -Y (Unity +Z)
- decimates to ~14k triangles for phones
- builds a skeleton whose bone names match CatAnimator: Body, Neck, Head, Leg_FL/FR/BL/BR, Tail1..Tail5
- skins the mesh with region-aware distance weights (robust on scanned/game meshes where heat weighting fails)
- exports CatHero.fbx and the albedo texture T_CatHero_A.png

Model used by default: "Cat 3D Model (FREE)" by Empire, CC-BY-4.0
https://sketchfab.com/3d-models/cat-3d-model-free-0db8c53b5b3d474b8a7c90e2350994f6
"""
import os
import sys

import bpy
import bmesh  # noqa: F401
import numpy as np
from mathutils import Matrix, Vector

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "CatsGame", "Assets", "_Project")
HEIGHT = 0.36
TARGET_TRIS = 14000


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def main(src, out_models, out_textures):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    # join, bake world transform into the mesh, drop the Sketchfab empties
    for o in meshes:
        o.data.transform(o.matrix_world)
        o.parent = None
        o.matrix_world = Matrix.Identity(4)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    cat = bpy.context.view_layer.objects.active
    cat.name = "CatHero_Mesh"
    for o in list(bpy.data.objects):
        if o.type == "EMPTY":
            bpy.data.objects.remove(o, do_unlink=True)

    co = np.array([v.co[:] for v in cat.data.vertices])
    mn, mx = co.min(0), co.max(0)
    k = HEIGHT / (mx[2] - mn[2])
    offset = Vector(((mn[0] + mx[0]) / 2, 0.0, mn[2]))
    cat.data.transform(Matrix.Scale(k, 4) @ Matrix.Translation(-offset))
    # centre the body (between front and hind paws) on the origin along Y
    co = np.array([v.co[:] for v in cat.data.vertices])
    feet = co[co[:, 2] < 0.03]
    cy = (feet[:, 1].min() + feet[:, 1].max()) / 2
    cat.data.transform(Matrix.Translation((0, -cy, 0)))

    # decimate for phones
    tris = sum(len(p.vertices) - 2 for p in cat.data.polygons)
    if tris > TARGET_TRIS:
        dec = cat.modifiers.new("Decimate", "DECIMATE")
        dec.ratio = TARGET_TRIS / tris
        dec.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=dec.name)
    for p in cat.data.polygons:
        p.use_smooth = True
    tris = sum(len(p.vertices) - 2 for p in cat.data.polygons)

    # material + texture
    img = next((i for i in bpy.data.images if i.size[0] > 0), None)
    os.makedirs(out_textures, exist_ok=True)
    if img is not None:
        img.filepath_raw = os.path.join(out_textures, "T_CatHero_A.png")
        img.file_format = "PNG"
        img.save()
    mat = bpy.data.materials.new("M_CatHero")
    cat.data.materials.clear()
    cat.data.materials.append(mat)
    # keep only the first UV map
    while len(cat.data.uv_layers) > 1:
        cat.data.uv_layers.remove(cat.data.uv_layers[-1])

    # ------------------------------------------------------------------ landmarks
    co = np.array([v.co[:] for v in cat.data.vertices])
    y0, y1 = co[:, 1].min(), co[:, 1].max()      # nose (-Y) .. tail tip (+Y)
    low = co[co[:, 2] < 0.05]
    front_feet = low[low[:, 1] < 0]
    back_feet = low[low[:, 1] >= 0]

    def foot(arr, side):
        s = arr[(arr[:, 0] * side) > 0]
        return s.mean(0) if len(s) else np.array([0.035 * side, 0, 0.02])

    fl, fr = foot(front_feet, 1), foot(front_feet, -1)
    bl, br = foot(back_feet, 1), foot(back_feet, -1)
    fy, by = front_feet[:, 1].mean(), back_feet[:, 1].mean()
    body = co[(co[:, 1] > fy + 0.03) & (co[:, 1] < by - 0.03)]
    torso_top = body[:, 2].max()
    # tail starts where the cross-section becomes thin behind the hind legs
    tail_start = None
    for y in np.arange(back_feet[:, 1].max(), y1, 0.005):
        s = co[(co[:, 1] >= y) & (co[:, 1] < y + 0.01)]
        if len(s) and (s[:, 0].max() - s[:, 0].min()) < 0.04:
            tail_start = y
            break
    tail_start = tail_start or (back_feet[:, 1].max() + 0.01)
    tail = co[co[:, 1] > tail_start]
    tail_z = np.median(tail[:, 2]) if len(tail) else 0.2
    head_back = front_feet[:, 1].min() - 0.01
    print(f"tris={tris} nose={y0:.3f} tail={tail_start:.3f}..{y1:.3f} front feet y={front_feet[:,1].mean():.3f} "
          f"back feet y={back_feet[:,1].mean():.3f} torso_top={torso_top:.3f}")

    shoulder_z = torso_top - 0.06
    hip_z = torso_top - 0.06
    chest_y = (fl[1] + fr[1]) / 2
    hip_y = (bl[1] + br[1]) / 2

    # ------------------------------------------------------------------ armature
    arm_data = bpy.data.armatures.new("CatHero_Rig")
    arm = bpy.data.objects.new("CatHero", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones

    def bone(name, head, tail_, parent=None):
        b = eb.new(name)
        b.head = Vector(head)
        b.tail = Vector(tail_)
        b.roll = 0.0
        if parent:
            b.parent = eb[parent]
            b.use_connect = False
        return b

    body_head = (0, hip_y, hip_z)
    body_tail = (0, chest_y, shoulder_z)
    bone("Body", body_head, body_tail)
    neck_top = (0, head_back, torso_top + 0.01)
    bone("Neck", body_tail, neck_top, "Body")
    bone("Head", neck_top, (0, y0 + 0.01, torso_top + 0.02), "Neck")
    for name, f, top_y in (("Leg_FL", fl, chest_y), ("Leg_FR", fr, chest_y), ("Leg_BL", bl, hip_y), ("Leg_BR", br, hip_y)):
        bone(name, (f[0], top_y, shoulder_z - 0.04), (f[0], f[1], 0.015), "Body")
    n_tail = 5
    pts = [Vector((0, tail_start + (y1 - tail_start) * i / n_tail, tail_z)) for i in range(n_tail + 1)]
    parent = "Body"
    for i in range(n_tail):
        bone(f"Tail{i + 1}", pts[i], pts[i + 1], parent)
        parent = f"Tail{i + 1}"
    bpy.ops.object.mode_set(mode="OBJECT")

    # ------------------------------------------------------------------ skin weights (region aware)
    names = ["Body", "Neck", "Head", "Leg_FL", "Leg_FR", "Leg_BL", "Leg_BR"] + [f"Tail{i + 1}" for i in range(n_tail)]
    W = np.zeros((len(co), len(names)))
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    leg_zone = smooth(shoulder_z - 0.06, shoulder_z - 0.12, z)
    front_band = smooth(head_back - 0.02, head_back + 0.01, y) * smooth(chest_y + 0.06, chest_y + 0.03, y)
    back_band = smooth(hip_y - 0.06, hip_y - 0.03, y) * smooth(tail_start + 0.01, tail_start - 0.01, y)
    for i, (fy, side) in enumerate(((front_band, 1), (front_band, -1), (back_band, 1), (back_band, -1))):
        W[:, 3 + i] = leg_zone * fy * smooth(-0.004, 0.004, x * side)
    tail_w = smooth(tail_start - 0.01, tail_start + 0.02, y)
    t = np.clip((y - tail_start) / max(1e-4, (y1 - tail_start)) * n_tail - 0.5, 0, n_tail - 1)
    for i in range(n_tail):
        W[:, 7 + i] = tail_w * np.clip(1 - np.abs(t - i), 0, 1)
    head_w = smooth(head_back + 0.03, head_back - 0.01, y) * smooth(shoulder_z - 0.07, shoulder_z - 0.01, z)
    W[:, 2] = head_w * smooth(head_back, head_back - 0.03, y)
    W[:, 1] = head_w - W[:, 2]
    used = W[:, 1:].sum(1)
    W[:, 0] = np.clip(1 - used, 0, 1)
    W /= np.maximum(W.sum(1, keepdims=True), 1e-6)
    groups = {n: cat.vertex_groups.new(name=n) for n in names}
    for vi in range(len(co)):
        order = np.argsort(-W[vi])[:4]
        tot = W[vi, order].sum()
        for j in order:
            if W[vi, j] > 0.01:
                groups[names[j]].add([vi], float(W[vi, j] / tot), "REPLACE")
    cat.parent = arm
    mod = cat.modifiers.new("Armature", "ARMATURE")
    mod.object = arm

    # ------------------------------------------------------------------ export
    os.makedirs(out_models, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    cat.select_set(True)
    bpy.context.view_layer.objects.active = arm
    path = os.path.join(out_models, "CatHero.fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"ARMATURE", "MESH"},
                             apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
                             bake_space_transform=False, use_mesh_modifiers=False, add_leaf_bones=False,
                             primary_bone_axis="Y", secondary_bone_axis="X", bake_anim=False,
                             mesh_smooth_type="FACE", path_mode="STRIP")
    print("exported", os.path.abspath(path))
    return arm, cat


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    src = args[0]
    out = args[1] if len(args) > 1 else ROOT
    main(src, os.path.join(out, "Art", "Models"), os.path.join(out, "Art", "Textures"))
