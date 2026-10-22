"""Preview render of level01.json in Blender/Cycles from the start camera.

It rebuilds the scene from the same data the Unity builder uses, so the shot shows the
real layout, scale, textures and light placement. Unity's real-time look will differ a bit.

Run:  python tools/blender/render_level.py out.png [width] [samples] [camera: start|garland|street]
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import bpy  # noqa: E402  (must come before bmesh)
import bmesh  # noqa: E402
from mathutils import Euler, Vector  # noqa: E402

import make_models  # noqa: E402
from meshkit import clear_scene  # noqa: E402
from preview_materials import TEX, setup_materials  # noqa: E402

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "CatsGame", "Assets", "_Project", "Data", "level01.json")


def B(v):
    """Unity position -> Blender position."""
    return Vector((-v["x"], -v["z"], v["y"]))


def mat(name):
    return bpy.data.materials.get(name) or bpy.data.materials.new(name)


def box_object(name, size, material, uv_offset=0.0):
    """Box centred on the origin with UVs in metres (same as the Unity builder). size is Unity (x, y, z)."""
    sx, sy, sz = size["x"], size["y"], size["z"]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    # build in Unity-local space, then convert
    faces = [
        ((1, 0, 0), [(hx, -hy, -hz), (hx, -hy, hz), (hx, hy, hz), (hx, hy, -hz)]),
        ((-1, 0, 0), [(-hx, -hy, hz), (-hx, -hy, -hz), (-hx, hy, -hz), (-hx, hy, hz)]),
        ((0, 1, 0), [(-hx, hy, -hz), (hx, hy, -hz), (hx, hy, hz), (-hx, hy, hz)]),
        ((0, -1, 0), [(-hx, -hy, hz), (hx, -hy, hz), (hx, -hy, -hz), (-hx, -hy, -hz)]),
        ((0, 0, 1), [(hx, -hy, hz), (-hx, -hy, hz), (-hx, hy, hz), (hx, hy, hz)]),
        ((0, 0, -1), [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz)]),
    ]
    for n, pts in faces:
        verts = [bm.verts.new((-p[0], -p[2], p[1])) for p in pts]
        f = bm.faces.new(verts)
        for loop, p in zip(f.loops, pts):
            if n[0]:
                u, v = p[2] * -n[0], p[1]
            elif n[1]:
                u, v = p[0], p[2] * n[1]
            else:
                u, v = p[0] * n[2], p[1]
            loop[uv].uv = (u + uv_offset, v)
    me = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    if material:
        me.materials.append(mat(material))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def prism_roof(name, top_center, size, material, flat=False):
    """Gable roof (ridge along Unity z). size: x = span, y = height, z = length."""
    sx, sy, sz = size["x"], size["y"], size["z"]
    c = top_center
    hx, hz = sx / 2, sz / 2
    pts = {
        "a": (c["x"] - hx, c["y"], c["z"] - hz), "b": (c["x"] + hx, c["y"], c["z"] - hz),
        "c": (c["x"] + hx, c["y"], c["z"] + hz), "d": (c["x"] - hx, c["y"], c["z"] + hz),
        "r0": (c["x"], c["y"] + sy, c["z"] - hz), "r1": (c["x"], c["y"] + sy, c["z"] + hz),
    }
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    vs = {k: bm.verts.new((-p[0], -p[2], p[1])) for k, p in pts.items()}
    slope = math.hypot(hx, sy)
    for keys, uvs in ((("b", "c", "r1", "r0"), [(0, 0), (sz, 0), (sz, slope), (0, slope)]),
                      (("d", "a", "r0", "r1"), [(0, 0), (sz, 0), (sz, slope), (0, slope)]),
                      (("a", "b", "r0"), [(0, 0), (sx, 0), (hx, sy)]),
                      (("c", "d", "r1"), [(0, 0), (sx, 0), (hx, sy)])):
        try:
            f = bm.faces.new([vs[k] for k in keys])
        except ValueError:
            continue
        for loop, u in zip(f.loops, uvs):
            loop[uv].uv = u
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat(material))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


_proto = {}


def prop_instance(p):
    name = p["model"]
    if name not in _proto:
        roots = make_models.MODELS[name]()
        coll = bpy.data.collections.new("P_" + name)
        for r in roots:
            for ob in [r] + list(r.children_recursive):
                for c in list(ob.users_collection):
                    c.objects.unlink(ob)
                coll.objects.link(ob)
        _proto[name] = coll
    inst = bpy.data.objects.new(name, None)
    inst.instance_type = "COLLECTION"
    inst.instance_collection = _proto[name]
    bpy.context.scene.collection.objects.link(inst)
    inst.location = B(p["pos"])
    inst.rotation_euler = Euler((0, 0, math.radians(-p["rotY"])))
    s = p["scale"]
    inst.scale = (s["x"], s["z"], s["y"])
    swap = p.get("matSwap", "")
    if swap and "=" in swap:
        a, b = swap.split("=")
        if a != b:
            # material swap needs a real copy of the prototype
            coll = bpy.data.collections.new("P_" + name + "_" + b)
            for ob in _proto[name].objects:
                cp = ob.copy()
                if cp.data:
                    cp.data = ob.data.copy()
                    for i, m in enumerate(cp.data.materials):
                        if m and m.name == a:
                            cp.data.materials[i] = mat(b)
                coll.objects.link(cp)
            inst.instance_collection = coll
    return inst


def point_light(name, pos, color, intensity, rng, offset=None):
    ld = bpy.data.lights.new(name, "POINT")
    ld.color = (color["r"], color["g"], color["b"])
    ld.energy = intensity * 55.0
    ld.shadow_soft_size = 0.08
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = pos if offset is None else pos + offset
    return ob


def light_point_offset(model):
    """Find the LightPoint empty of a prototype in Unity-local coordinates (Blender local)."""
    coll = _proto.get(model)
    if not coll:
        return None
    for ob in coll.objects:
        if ob.name.startswith("LightPoint"):
            return ob.matrix_world.translation.copy()
    return None


def garland(g):
    a, b = B(g["a"]), B(g["b"])
    sag = g["sag"]
    n = 24
    pts = []
    for i in range(n + 1):
        t = i / n
        p = a.lerp(b, t)
        p.z -= sag * 4 * t * (1 - t)
        pts.append(p)
    curve = bpy.data.curves.new("Wire", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.008
    sp = curve.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p.x, p.y, p.z, 1)
    curve.materials.append(mat("M_Wire"))
    ob = bpy.data.objects.new("Wire", curve)
    bpy.context.scene.collection.objects.link(ob)
    length = (b - a).length
    k = max(2, int(length / g["bulbSpacing"]))
    bulb_proto = {"model": "Bulb", "rotY": 0, "scale": {"x": 1, "y": 1, "z": 1}}
    for i in range(1, k):
        t = i / k
        p = a.lerp(b, t)
        p.z -= sag * 4 * t * (1 - t)
        e = dict(bulb_proto)
        e["pos"] = {"x": -p.x, "y": p.z, "z": -p.y}
        prop_instance(e)


def background(bg, eye):
    r, h, y0 = bg["radius"], bg["height"], bg["y"]
    a0, a1 = math.radians(bg["arcStart"]), math.radians(bg["arcEnd"])
    seg = 48
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    for i in range(seg):
        t0, t1 = i / seg, (i + 1) / seg
        ang0, ang1 = a0 + (a1 - a0) * t0, a0 + (a1 - a0) * t1
        # Unity: forward +z, right +x
        p = []
        for ang, yy in ((ang0, y0), (ang1, y0), (ang1, y0 + h), (ang0, y0 + h)):
            ux, uz = eye["x"] + math.sin(ang) * r, eye["z"] + math.cos(ang) * r
            p.append(bm.verts.new((-ux, -uz, yy)))
        f = bm.faces.new(p)
        for loop, u in zip(f.loops, [(t0, 0), (t1, 0), (t1, 1), (t0, 1)]):
            loop[uv].uv = u
    me = bpy.data.meshes.new("FarMatte")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat("M_FarMatte"))
    ob = bpy.data.objects.new("FarMatte", me)
    bpy.context.scene.collection.objects.link(ob)


def main(out, width=1280, samples=64, cam_name="start"):
    with open(DATA) as f:
        L = json.load(f)
    clear_scene()
    setup_materials()
    for blk in L["blocks"]:
        if not blk["visible"]:
            continue
        ob = box_object(blk["name"], blk["size"], blk["mat"])
        ob.location = B(blk["pos"])
        ob.rotation_euler = Euler((0, math.radians(blk["rot"]["z"]), 0))
    for r in L["roofs"]:
        prism_roof("Roof", r["pos"], r["size"], r["mat"])
    for hs in L["houses"]:
        s = hs["size"]
        ob = box_object("House", s, hs["mat"], hs["uvOffset"])
        ob.location = B(hs["pos"]) + Vector((0, 0, s["y"] / 2))
        if hs["gable"]:
            top = dict(hs["pos"])
            top["y"] += s["y"]
            prism_roof("HouseRoof", top, {"x": s["x"] + 0.6, "y": 2.0, "z": s["z"] + 0.6}, hs["roofMat"])
        if hs["foundation"] > 0:
            fs = {"x": s["x"] + 4, "y": hs["foundation"], "z": s["z"] + 4}
            fo = box_object("Foundation", fs, "M_Stone")
            fo.location = B(hs["pos"]) - Vector((0, 0, fs["y"] / 2))
    for p in L["props"]:
        prop_instance(p)
        if p["light"]["intensity"] > 0:
            off = light_point_offset(p["model"])
            if off is not None:
                rot = Euler((0, 0, math.radians(-p["rotY"])))
                s = p["scale"]
                off = Vector((off.x * s["x"], off.y * s["z"], off.z * s["y"]))
                off.rotate(rot)
                point_light("L_" + p["model"], B(p["pos"]), p["light"]["color"], p["light"]["intensity"], 8, off)
    for l in L["lights"]:
        point_light(l["name"], B(l["pos"]), l["color"], l["intensity"], l["range"])
    for g in L["garlands"]:
        garland(g)
    for m in L["markers"]:
        me = bpy.data.meshes.new("Paw")
        s = 0.16
        me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
        me.uv_layers.new()
        for i, uvv in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
            me.uv_layers[0].data[i].uv = uvv
        me.materials.append(mat("M_PawMarker"))
        ob = bpy.data.objects.new("Paw", me)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = B(m["pos"]) + Vector((0, 0, 0.01))
    # hero cat at spawn
    hero = prop_instance({"model": "Cat_Hero", "pos": L["spawn"]["p1"], "rotY": L["spawn"]["rotY"],
                          "scale": {"x": 1, "y": 1, "z": 1}})
    npc = L["npc"]
    prop_instance({"model": npc["model"], "pos": npc["pos"], "rotY": npc["rotY"], "scale": {"x": 1, "y": 1, "z": 1}})
    # sea
    sea = L["sea"]
    me = bpy.data.meshes.new("Sea")
    c, s = sea["center"], sea["size"]
    hx, hz = s["x"] / 2, s["z"] / 2
    corners = [(c["x"] - hx, c["z"] - hz), (c["x"] + hx, c["z"] - hz), (c["x"] + hx, c["z"] + hz), (c["x"] - hx, c["z"] + hz)]
    me.from_pydata([(-x, -z, sea["y"]) for x, z in corners], [], [(0, 3, 2, 1)])
    me.uv_layers.new()
    for i, (x, z) in enumerate([corners[0], corners[3], corners[2], corners[1]]):
        me.uv_layers[0].data[i].uv = (x, z)
    me.materials.append(mat("M_Sea"))
    so = bpy.data.objects.new("Sea", me)
    bpy.context.scene.collection.objects.link(so)
    eye = L["startCamera"]["pos"]
    background(L["background"], eye)
    # moon: sun lamp + emissive disc
    moon = L["moon"]
    az, el = math.radians(moon["azimuth"]), math.radians(moon["elevation"])
    udir = Vector((math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)))
    bdir = Vector((-udir.x, -udir.z, udir.y))
    sun = bpy.data.lights.new("Moon", "SUN")
    sun.color = (moon["color"]["r"], moon["color"]["g"], moon["color"]["b"])
    sun.energy = moon["intensity"] * 2.2
    sun.angle = math.radians(1.0)
    sob = bpy.data.objects.new("Moon", sun)
    sob.rotation_euler = (-bdir).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(sob)
    md = bpy.data.meshes.new("MoonDisc")
    q = moon["quadSize"] / 2
    md.from_pydata([(-q, -q, 0), (q, -q, 0), (q, q, 0), (-q, q, 0)], [], [(0, 1, 2, 3)])
    md.uv_layers.new()
    for i, uvv in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        md.uv_layers[0].data[i].uv = uvv
    md.materials.append(mat("M_Moon"))
    mo = bpy.data.objects.new("MoonDisc", md)
    bpy.context.scene.collection.objects.link(mo)
    mo.location = B(eye) + bdir * moon["quadDistance"]
    mo.rotation_euler = (-bdir).to_track_quat("Z", "Y").to_euler()
    # world: night panorama
    scn = bpy.context.scene
    world = bpy.data.worlds.new("Night")
    world.use_nodes = True
    nt = world.node_tree
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(os.path.join(TEX, "T_SkyNight_A.png"))
    bg = nt.nodes["Background"]
    bg.inputs[1].default_value = 1.0
    nt.links.new(env.outputs[0], bg.inputs[0])
    scn.world = world
    # camera
    cams = {
        "start": (L["startCamera"]["pos"], L["startCamera"]["lookAt"]),
        "garland": ({"x": 4.8, "y": 8.4, "z": 26.5}, {"x": 1.5, "y": 5.0, "z": 33.0}),
        "street": ({"x": 2.6, "y": -2.6, "z": 58.0}, {"x": 2.6, "y": -6.0, "z": 95.0}),
    }
    cpos, clook = cams[cam_name]
    cam = bpy.data.cameras.new("Cam")
    cam.sensor_fit = "VERTICAL"
    cam.angle_y = math.radians(50)
    cam.clip_end = 5000
    co = bpy.data.objects.new("Cam", cam)
    scn.collection.objects.link(co)
    co.location = B(cpos)
    co.rotation_euler = (B(clook) - B(cpos)).to_track_quat("-Z", "Y").to_euler()
    scn.camera = co
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = samples
    scn.cycles.use_denoising = True
    scn.cycles.max_bounces = 4
    scn.cycles.light_sampling_threshold = 0.02
    scn.render.resolution_x = width
    scn.render.resolution_y = int(width * 9 / 20)
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Punchy"
    scn.view_settings.exposure = 0.6
    scn.render.filepath = out
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], int(a[1]) if len(a) > 1 else 1280, int(a[2]) if len(a) > 2 else 64, a[3] if len(a) > 3 else "start")
