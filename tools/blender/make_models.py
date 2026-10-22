"""Builds every prop / character model of level 01 and exports FBX files for Unity.

Run:  python tools/blender/make_models.py [out_dir]      (needs the `bpy` module, Blender 4.x/5.x)

Conventions: metres, +Z up, the front of a prop faces -Y (Unity +Z after export),
wall-mounted props have their pivot on the wall plane (y = 0).
Material slot names match CatsGame/Assets/_Project/Data/materials.json; the Unity
builder swaps them for the real URP materials by name.
Empties named `LightPoint` mark where the Unity builder places a light.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from meshkit import MeshBuilder, add_subsurf, clear_scene, empty, export_fbx, shift_mesh  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "CatsGame", "Assets", "_Project", "Art", "Models")

# foliage atlas regions (u0, v0, u1, v1)
IVY = (0.0, 0.5, 0.5, 1.0)
GERANIUM = (0.5, 0.5, 1.0, 1.0)
BOUGAINVILLEA = (0.0, 0.0, 0.5, 0.5)
DAISY = (0.5, 0.0, 1.0, 0.5)
WINDOW_QUADS = [(0.0, 0.5, 0.5, 1.0), (0.5, 0.5, 1.0, 1.0), (0.0, 0.0, 0.5, 0.5), (0.5, 0.0, 1.0, 0.5)]


def circle_path(center, r, axis="y", n=12):
    cx, cy, cz = center
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        if axis == "y":
            pts.append((cx + r * math.cos(a), cy, cz + r * math.sin(a)))
        elif axis == "x":
            pts.append((cx, cy + r * math.cos(a), cz + r * math.sin(a)))
        else:
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a), cz))
    return pts


# ============================================================== hard surface props
def ac_unit():
    mb = MeshBuilder("AC_Unit")
    W, H, D, gap = 0.9, 0.62, 0.33, 0.03
    front = -D - gap
    mb.box((-W / 2, front, 0), (W / 2, -gap, H), "M_PaintedMetal")
    # louvres (right half when seen from the street)
    z = 0.07
    while z < H - 0.08:
        mb.box((0.02, front - 0.014, z), (W / 2 - 0.05, front + 0.002, z + 0.014), "M_MetalDark")
        z += 0.038
    for x0, x1 in ((0.0, 0.02), (W / 2 - 0.05, W / 2 - 0.03)):
        mb.box((x0, front - 0.02, 0.05), (x1, front, H - 0.05), "M_PaintedMetal")
    # fan grille on the left half
    for r in (0.07, 0.12, 0.17):
        mb.tube(circle_path((-0.22, front - 0.012, 0.31), r, "y", 20), 0.006, "M_MetalDark", seg=5, closed=True)
    mb.box((-0.4, front - 0.015, 0.305), (-0.04, front - 0.005, 0.315), "M_MetalDark")
    mb.box((-0.225, front - 0.015, 0.13), (-0.215, front - 0.005, 0.49), "M_MetalDark")
    # wall brackets
    for x in (-0.33, 0.33):
        mb.box((x - 0.02, -0.012, -0.32), (x + 0.02, 0.0, 0.02), "M_MetalDark")
        mb.box((x - 0.02, front - 0.05, -0.04), (x + 0.02, 0.0, 0.0), "M_MetalDark")
        mb.tube([(x, -0.01, -0.3), (x, front + 0.03, -0.035)], 0.012, "M_MetalDark", seg=6)
    # refrigerant pipes going into the wall
    for zz in (0.12, 0.2):
        mb.tube([(W / 2, -0.12, zz), (W / 2 + 0.07, -0.12, zz), (W / 2 + 0.07, -0.02, zz), (W / 2 + 0.07, 0.0, zz)],
                0.012, "M_PaintedMetal", seg=8)
    return [mb.build()]


def railing():
    mb = MeshBuilder("Railing_1m")
    mb.box((-0.5, -0.03, 0.96), (0.5, 0.012, 1.0), "M_Iron")
    mb.box((-0.5, -0.01, 0.78), (0.5, 0.008, 0.8), "M_Iron")
    mb.box((-0.5, -0.012, 0.05), (0.5, 0.01, 0.08), "M_Iron")
    for k in range(10):
        x = -0.45 + 0.1 * k
        mb.box((x - 0.008, -0.008, 0.08), (x + 0.008, 0.008, 0.96), "M_Iron")
        if k < 9:
            mb.tube(circle_path((x + 0.05, 0.0, 0.88), 0.036, "y", 10), 0.006, "M_Iron", seg=4, closed=True)
            mb.tube([(x + 0.012, 0, 0.2), (x + 0.05, 0, 0.14), (x + 0.088, 0, 0.2)], 0.006, "M_Iron", seg=4)
    return [mb.build()]


def railing_post():
    mb = MeshBuilder("Railing_Post")
    mb.box((-0.025, -0.025, 0), (0.025, 0.025, 1.04), "M_Iron")
    mb.sphere((0, 0, 1.08), 0.035, "M_Iron", seg=8, rings=6)
    return [mb.build()]


def _lantern(mb, c):
    cx, cy, cz = c
    mb.cylinder((cx, cy, cz + 0.1), 0.07, 0.11, 0.012, "M_Iron", seg=6)
    mb.cylinder((cx, cy, cz + 0.085), 0.018, 0.1, 0.1, "M_Iron", seg=6)
    mb.cylinder((cx, cy, cz - 0.11), 0.195, 0.065, 0.088, "M_LanternGlass", seg=6, cap_top=False, cap_bottom=False)
    for k in range(6):
        a = 2 * math.pi * k / 6
        mb.tube([(cx + math.cos(a) * 0.066, cy + math.sin(a) * 0.066, cz - 0.11),
                 (cx + math.cos(a) * 0.09, cy + math.sin(a) * 0.09, cz + 0.087)], 0.006, "M_Iron", seg=4)
    mb.cylinder((cx, cy, cz - 0.17), 0.06, 0.02, 0.07, "M_Iron", seg=6)


def lantern_wall():
    mb = MeshBuilder("Lantern_Wall")
    mb.box((-0.06, -0.02, -0.12), (0.06, 0.0, 0.14), "M_Iron")
    mb.tube([(0, -0.01, 0.06), (0, -0.14, 0.13), (0, -0.3, 0.17), (0, -0.42, 0.16)], 0.012, "M_Iron", seg=6)
    mb.tube([(0, -0.01, -0.08), (0, -0.12, -0.02), (0, -0.2, 0.06), (0, -0.26, 0.15)], 0.009, "M_Iron", seg=5)
    mb.tube(circle_path((0, -0.3, 0.07), 0.04, "x", 10), 0.006, "M_Iron", seg=4, closed=True)
    mb.tube([(0, -0.42, 0.16), (0, -0.42, 0.105)], 0.008, "M_Iron", seg=5)
    _lantern(mb, (0, -0.42, -0.02))
    ob = mb.build()
    empty("LightPoint", (0, -0.42, -0.02), ob)
    return [ob]


def street_lamp():
    mb = MeshBuilder("StreetLamp")
    mb.cylinder((0, 0, 0), 0.4, 0.15, 0.09, "M_Iron", seg=10)
    mb.cylinder((0, 0, 0.4), 2.75, 0.06, 0.045, "M_Iron", seg=10)
    for z in (0.42, 1.2, 3.1):
        mb.cylinder((0, 0, z), 0.04, 0.075, 0.075, "M_Iron", seg=10)
    mb.tube([(0, 0, 3.1), (0, -0.2, 3.3), (0, -0.45, 3.32), (0, -0.58, 3.25)], 0.025, "M_Iron", seg=6)
    mb.tube([(0, -0.58, 3.25), (0, -0.58, 3.17)], 0.012, "M_Iron", seg=5)
    _lantern(mb, (0, -0.58, 3.05))
    ob = mb.build()
    empty("LightPoint", (0, -0.58, 3.05), ob)
    return [ob]


def awning():
    """3 m wide, 1.5 m deep striped awning; top edge on the wall at z = 0."""
    mb = MeshBuilder("Awning_3m")
    W, P, D = 3.0, 1.5, 0.55
    nx, ny = 15, 4

    def pt(x, s):
        return (x, -P * s, -D * s - 0.04 * math.sin(math.pi * s))

    for i in range(nx):
        x0, x1 = -W / 2 + W * i / nx, -W / 2 + W * (i + 1) / nx
        for j in range(ny):
            s0, s1 = j / ny, (j + 1) / ny
            u0, u1 = (x0 + W / 2) / 1.6, (x1 + W / 2) / 1.6
            top = [pt(x0, s0), pt(x0, s1), pt(x1, s1), pt(x1, s0)]
            mb.face(top, [(u0, s0), (u0, s1), (u1, s1), (u1, s0)], "M_AwningBlue")
            mb.face(list(reversed(top)), [(u1, s0), (u1, s1), (u0, s1), (u0, s0)], "M_AwningBlue")
        # scalloped valance
        xa, xb = x0, x1
        za = -D
        zb = -D - 0.2
        xm = (xa + xb) / 2
        pts = [(xa, -P, za), (xa, -P, zb + 0.04), (xm, -P, zb), (xb, -P, zb + 0.04), (xb, -P, za)]
        uvs = [((p[0] + W / 2) / 1.6, 1 + (p[2] - za)) for p in pts]
        mb.face(pts, uvs, "M_AwningBlue")
        mb.face(list(reversed(pts)), list(reversed(uvs)), "M_AwningBlue")
    for x in (-W / 2 + 0.02, W / 2 - 0.02):
        mb.tube([(x, -0.02, -0.75), (x, -P + 0.02, -D - 0.01)], 0.012, "M_Iron", seg=6)
    mb.tube([(-W / 2, -P, -D - 0.01), (W / 2, -P, -D - 0.01)], 0.015, "M_Iron", seg=6)
    mb.box((-W / 2, -0.06, -0.02), (W / 2, 0.0, 0.06), "M_MetalDark")
    return [mb.build()]


def _window_frame(mb, w, h):
    j = 0.12
    mb.box((-w / 2 - j, -0.05, -0.02), (-w / 2, 0.0, h), "M_Stone")
    mb.box((w / 2, -0.05, -0.02), (w / 2 + j, 0.0, h), "M_Stone")
    mb.box((-w / 2 - j - 0.03, -0.06, h), (w / 2 + j + 0.03, 0.0, h + 0.18), "M_Stone")
    mb.box((-w / 2 - j - 0.02, -0.14, -0.08), (w / 2 + j + 0.02, 0.0, 0.0), "M_Stone")
    # reveal (inner sides of the opening)
    mb.box((-w / 2, -0.05, 0.0), (w / 2, -0.035, 0.03), "M_Stone")


def _mullions(mb, w, h, y):
    t = 0.035
    mb.box((-w / 2, y - 0.02, 0.0), (-w / 2 + t, y, h), "M_WoodDark")
    mb.box((w / 2 - t, y - 0.02, 0.0), (w / 2, y, h), "M_WoodDark")
    mb.box((-w / 2, y - 0.02, h - t), (w / 2, y, h), "M_WoodDark")
    mb.box((-w / 2, y - 0.02, 0.0), (w / 2, y, t), "M_WoodDark")
    mb.box((-0.018, y - 0.025, 0.0), (0.018, y, h), "M_WoodDark")
    mb.box((-w / 2, y - 0.025, h * 0.64), (w / 2, y, h * 0.64 + 0.03), "M_WoodDark")


def window(name, quad=None, closed=False):
    mb = MeshBuilder(name)
    w, h = 0.9, 1.4
    _window_frame(mb, w, h)
    y = -0.012
    mat = "M_WindowLit" if quad is not None else "M_WindowDark"
    mb.quad((-w / 2, y, 0), (w / 2, y, 0), (w / 2, y, h), (-w / 2, y, h), mat, quad or (0, 0, 1, 1))
    if closed:
        for x0 in (-w / 2, 0.0):
            mb.quad((x0, -0.04, 0.01), (x0 + w / 2, -0.04, 0.01), (x0 + w / 2, -0.04, h - 0.01), (x0, -0.04, h - 0.01),
                    "M_Shutter")
    else:
        _mullions(mb, w, h, -0.015)
        for x0 in (-w / 2 - 0.12 - 0.47, w / 2 + 0.12 + 0.02):
            mb.quad((x0, -0.025, 0.0), (x0 + 0.45, -0.025, 0.0), (x0 + 0.45, -0.025, h), (x0, -0.025, h), "M_Shutter")
            mb.box((x0, -0.025, 0.0), (x0 + 0.45, -0.005, h), "M_Shutter", skip=("-y",))
    return [mb.build()]


def door_balcony():
    mb = MeshBuilder("Door_Balcony")
    w, h = 1.5, 2.4
    j = 0.15
    mb.box((-w / 2 - j, -0.06, 0), (-w / 2, 0.0, h), "M_Stone")
    mb.box((w / 2, -0.06, 0), (w / 2 + j, 0.0, h), "M_Stone")
    mb.box((-w / 2 - j - 0.03, -0.07, h), (w / 2 + j + 0.03, 0.0, h + 0.22), "M_Stone")
    mb.quad((-w / 2, -0.02, 0), (w / 2, -0.02, 0), (w / 2, -0.02, h), (-w / 2, -0.02, h), "M_Interior")
    t, y = 0.06, -0.025
    for x0, x1 in ((-w / 2, -w / 2 + t), (w / 2 - t, w / 2), (-0.03, 0.03)):
        mb.box((x0, y - 0.04, 0), (x1, y, h), "M_WoodDark")
    for z0, z1 in ((h - t, h), (0, 0.12), (1.85, 1.89), (0.9, 0.93)):
        mb.box((-w / 2, y - 0.04, z0), (w / 2, y, z1), "M_WoodDark")
    for xx in (-w / 4, w / 4):
        mb.box((xx - 0.012, y - 0.03, 0.12), (xx + 0.012, y, 1.85), "M_WoodDark")
    mb.box((-0.16, y - 0.07, 1.0), (-0.1, y - 0.04, 1.04), "M_PaintedMetal")
    return [mb.build()]


def door_street():
    mb = MeshBuilder("Door_Street")
    w, h = 1.2, 2.3
    mb.box((-w / 2 - 0.15, -0.06, 0), (-w / 2, 0.0, h), "M_Stone")
    mb.box((w / 2, -0.06, 0), (w / 2 + 0.15, 0.0, h), "M_Stone")
    mb.box((-w / 2 - 0.18, -0.07, h), (w / 2 + 0.18, 0.0, h + 0.25), "M_Stone")
    mb.box((-w / 2, -0.03, 0), (w / 2, 0.0, h), "M_WoodDark")
    for k in range(5):
        x = -w / 2 + 0.12 + k * 0.24
        mb.box((x - 0.005, -0.035, 0.05), (x + 0.005, -0.03, h - 0.05), "M_Iron")
    mb.sphere((0.42, -0.05, 1.05), 0.03, "M_PaintedMetal", seg=8, rings=6)
    return [mb.build()]


def _plants(mb, region, cx, cy, cz, spread_x, spread_y, n, size, rnd, tilt=0.25):
    for i in range(n):
        x = cx + rnd.uniform(-spread_x, spread_x)
        y = cy + rnd.uniform(-spread_y, spread_y)
        s = size * rnd.uniform(0.75, 1.15)
        mb.card((x, y, cz - 0.03), s, s * 0.9, rnd.uniform(0, math.pi), "M_Foliage", region,
                tilt=rnd.uniform(-tilt, tilt))


def flower_box(name, region, seed):
    rnd = random.Random(seed)
    mb = MeshBuilder(name)
    mb.box((-0.4, -0.26, 0), (0.4, -0.01, 0.22), "M_Terracotta")
    mb.box((-0.37, -0.23, 0.2), (0.37, -0.04, 0.21), "M_WoodDark")
    _plants(mb, region, 0, -0.13, 0.22, 0.32, 0.06, 9, 0.38, rnd)
    for x in (-0.25, 0.25):
        mb.box((x - 0.015, -0.03, -0.12), (x + 0.015, 0.0, 0.02), "M_Iron")
    return [mb.build()]


def pot(name, region, seed, scale=1.0):
    rnd = random.Random(seed)
    mb = MeshBuilder(name)
    s = scale
    mb.cylinder((0, 0, 0), 0.42 * s, 0.16 * s, 0.22 * s, "M_Terracotta", seg=14, cap_top=False)
    mb.cylinder((0, 0, 0.4 * s), 0.06 * s, 0.24 * s, 0.24 * s, "M_Terracotta", seg=14)
    _plants(mb, region, 0, 0, 0.44 * s, 0.1 * s, 0.1 * s, 7, 0.55 * s, rnd, tilt=0.4)
    return [mb.build()]


def planter_stone(seed=4):
    rnd = random.Random(seed)
    mb = MeshBuilder("Planter_Stone")
    mb.box((-0.55, -0.22, 0), (0.55, 0.22, 0.48), "M_Stone")
    mb.box((-0.6, -0.27, 0.48), (0.6, 0.27, 0.54), "M_Stone")
    _plants(mb, DAISY, 0, 0, 0.54, 0.45, 0.14, 12, 0.5, rnd, tilt=0.35)
    _plants(mb, GERANIUM, 0, 0, 0.54, 0.4, 0.12, 4, 0.45, rnd, tilt=0.35)
    return [mb.build()]


def ivy_patch(name="Ivy_Patch", seed=7, w=1.6, h=2.2, n=26):
    rnd = random.Random(seed)
    mb = MeshBuilder(name)
    for i in range(n):
        cx, cz = rnd.uniform(-w / 2, w / 2), rnd.uniform(0, h)
        s = rnd.uniform(0.45, 0.8)
        a = rnd.uniform(0, math.pi * 2)
        y = -0.015 - i * 0.003
        corners = []
        for dx, dz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            rx = dx * math.cos(a) - dz * math.sin(a)
            rz = dx * math.sin(a) + dz * math.cos(a)
            corners.append((cx + rx * s / 2, y - rnd.uniform(0, 0.04), cz + rz * s / 2))
        mb.quad(*corners, "M_Foliage", IVY)
    return [mb.build()]


def bougainvillea(seed=9):
    rnd = random.Random(seed)
    mb = MeshBuilder("Bougainvillea")
    for i in range(22):
        x = rnd.uniform(-0.8, 0.8)
        y = rnd.uniform(-0.6, -0.05)
        z = rnd.uniform(-0.9, 0.3) * (1 - abs(x) * 0.4)
        s = rnd.uniform(0.4, 0.75)
        mb.card((x, y, z), s, s, rnd.uniform(0, math.pi), "M_Foliage", BOUGAINVILLEA, tilt=rnd.uniform(-0.6, 0.6),
                bottom=False)
    return [mb.build()]


def chimney():
    mb = MeshBuilder("Chimney")
    mb.box((-0.3, -0.3, 0), (0.3, 0.3, 1.1), "M_Plaster_Cream")
    mb.box((-0.36, -0.36, 1.1), (0.36, 0.36, 1.16), "M_Stone")
    for x in (-0.27, 0.21):
        for y in (-0.27, 0.21):
            mb.box((x, y, 1.16), (x + 0.06, y + 0.06, 1.3), "M_Stone")
    mb.box((-0.36, -0.36, 1.3), (0.36, 0.36, 1.36), "M_RoofTiles")
    return [mb.build()]


def drainpipe():
    mb = MeshBuilder("Drainpipe_1m")
    mb.cylinder((0, -0.08, 0), 1.0, 0.045, 0.045, "M_Pipe", seg=10, cap_top=False, cap_bottom=False)
    mb.box((-0.055, -0.13, 0.47), (0.055, 0.0, 0.52), "M_Pipe")
    return [mb.build()]


def bulb():
    mb = MeshBuilder("Bulb")
    mb.sphere((0, 0, -0.045), 0.032, "M_Bulb", seg=10, rings=7, scale=(1, 1, 1.25))
    mb.cylinder((0, 0, -0.02), 0.02, 0.013, 0.013, "M_MetalDark", seg=8)
    return [mb.build()]


def crate():
    mb = MeshBuilder("Crate")
    s = 0.25
    mb.box((-s + 0.02, -s + 0.02, 0.02), (s - 0.02, s - 0.02, 2 * s - 0.02), "M_Wood")
    for z in (0, 2 * s - 0.04):
        for y in (-s, s - 0.04):
            mb.box((-s, y, z), (s, y + 0.04, z + 0.04), "M_WoodDark")
        for x in (-s, s - 0.04):
            mb.box((x, -s, z), (x + 0.04, s, z + 0.04), "M_WoodDark")
    for x in (-s, s - 0.04):
        for y in (-s, s - 0.04):
            mb.box((x, y, 0), (x + 0.04, y + 0.04, 2 * s), "M_WoodDark")
    return [mb.build()]


def cafe_table():
    mb = MeshBuilder("CafeTable")
    mb.cylinder((0, 0, 0), 0.03, 0.22, 0.2, "M_MetalDark", seg=14)
    mb.cylinder((0, 0, 0.03), 0.69, 0.03, 0.03, "M_MetalDark", seg=8)
    mb.cylinder((0, 0, 0.72), 0.03, 0.35, 0.35, "M_Stone", seg=18)
    return [mb.build()]


def cafe_chair():
    mb = MeshBuilder("CafeChair")
    for x in (-0.18, 0.18):
        for y in (-0.18, 0.18):
            top = 0.88 if y > 0 else 0.45
            mb.tube([(x * 1.05, y * 1.05, 0), (x, y, top)], 0.012, "M_MetalDark", seg=6)
    mb.box((-0.2, -0.2, 0.43), (0.2, 0.2, 0.46), "M_Wood")
    for z in (0.62, 0.74, 0.86):
        mb.box((-0.19, 0.17, z), (0.19, 0.2, z + 0.06), "M_Wood")
    return [mb.build()]


def pergola(seed=11):
    rnd = random.Random(seed)
    mb = MeshBuilder("Pergola")
    for x in (-1.4, 1.4):
        for y in (-1.15, 1.15):
            mb.box((x - 0.06, y - 0.06, 0), (x + 0.06, y + 0.06, 2.6), "M_Wood")
    for y in (-1.15, 1.15):
        mb.box((-1.6, y - 0.07, 2.6), (1.6, y + 0.07, 2.75), "M_Wood")
    for k in range(9):
        x = -1.6 + 0.4 * k
        mb.box((x - 0.03, -1.35, 2.75), (x + 0.03, 1.35, 2.87), "M_Wood")
    for i in range(30):
        x, y = rnd.uniform(-1.5, 1.5), rnd.uniform(-1.3, 1.3)
        s = rnd.uniform(0.6, 1.0)
        a = rnd.uniform(0, 6.28)
        z = 2.9 + rnd.uniform(0, 0.06)
        corners = []
        for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            rx = dx * math.cos(a) - dy * math.sin(a)
            ry = dx * math.sin(a) + dy * math.cos(a)
            corners.append((x + rx * s / 2, y + ry * s / 2, z + rnd.uniform(-0.05, 0.05)))
        mb.quad(*corners, "M_Foliage", IVY)
    for i in range(14):
        side = rnd.choice((-1.36, 1.36))
        x = rnd.uniform(-1.5, 1.5)
        s = rnd.uniform(0.5, 0.9)
        mb.quad((x - s / 2, side, 2.9 - s), (x + s / 2, side, 2.9 - s), (x + s / 2, side, 2.9), (x - s / 2, side, 2.9),
                "M_Foliage", IVY)
    return [mb.build()]


def palm(seed=12):
    rnd = random.Random(seed)
    mb = MeshBuilder("Palm")
    H = 6.0
    rings = []
    for i in range(9):
        t = i / 8
        rings.append(((0.35 * t * t, 0.0, H * t), 0.2 - 0.06 * t, 0.2 - 0.06 * t))
    mb.loft(rings, "M_PalmTrunk", seg=10, v_scale=6.0, cap=False)
    top = Vector((0.35, 0, H))
    for k in range(13):
        yaw = 2 * math.pi * k / 13 + rnd.uniform(-0.15, 0.15)
        d = Vector((math.cos(yaw), math.sin(yaw), 0))
        side = Vector((-math.sin(yaw), math.cos(yaw), 0))
        L = rnd.uniform(2.0, 2.6)
        lift = rnd.uniform(0.3, 0.8)
        segs = 5
        pts = []
        for i in range(segs + 1):
            s = i / segs
            pts.append(top + d * s * L + Vector((0, 0, lift * s - 1.8 * s * s)))
        for i in range(segs):
            w0 = 0.42 * math.sin(math.pi * (0.1 + 0.9 * i / segs)) ** 0.5
            w1 = 0.42 * math.sin(math.pi * (0.1 + 0.9 * (i + 1) / segs)) ** 0.5
            a, b = pts[i], pts[i + 1]
            v0, v1 = 1 - i / segs, 1 - (i + 1) / segs
            mb.face([tuple(a - side * w0), tuple(a + side * w0), tuple(b + side * w1), tuple(b - side * w1)],
                    [(0, v0), (1, v0), (1, v1), (0, v1)], "M_PalmFrond")
    return [mb.build()]


def cypress(seed=13):
    rnd = random.Random(seed)
    mb = MeshBuilder("Cypress")
    H = 7.0
    mb.cylinder((0, 0, 0), 0.6, 0.12, 0.1, "M_PalmTrunk", seg=8)
    rings = []
    n = 16
    for i in range(n + 1):
        t = i / n
        r = 0.8 * (math.sin(math.pi * min(1.0, t ** 0.85)) ** 0.85) + 0.01
        r *= rnd.uniform(0.9, 1.1)
        rings.append(((rnd.uniform(-0.03, 0.03), rnd.uniform(-0.03, 0.03), 0.4 + (H - 0.4) * t), r, r))
    mb.loft(rings, "M_Cypress", seg=12, up=Vector((0, 1, 0)), v_scale=3.0)
    return [mb.build()]


def laundry_line(seed=14):
    rnd = random.Random(seed)
    mb = MeshBuilder("Laundry_Line")
    L, sag = 3.0, 0.15

    def wz(x):
        return -sag * (1 - (2 * x / L) ** 2)

    mb.tube([(x, 0, wz(x)) for x in [(-L / 2 + L * i / 12) for i in range(13)]], 0.005, "M_Wire", seg=4)
    x = -L / 2 + 0.25
    while x < L / 2 - 0.4:
        w, h = rnd.uniform(0.3, 0.6), rnd.uniform(0.35, 0.8)
        cell = rnd.randrange(16)
        u0, v0 = (cell % 4) / 4, 1 - (cell // 4 + 1) / 4
        z0, z1 = wz(x), wz(x + w)
        mb.quad((x, 0, z0 - h), (x + w, 0, z1 - h), (x + w, 0, z1), (x, 0, z0), "M_Laundry",
                (u0 + 0.01, v0 + 0.01, u0 + 0.24, v0 + 0.24))
        x += w + rnd.uniform(0.05, 0.2)
    return [mb.build()]


def ship():
    mb = MeshBuilder("Ship")
    L, W = 180.0, 28.0
    mb.box((-L / 2, -W / 2, 0), (L / 2 - 20, W / 2, 12), "M_ShipHull")
    bow = [(L / 2 - 20, -W / 2, 0), (L / 2, 0, 0), (L / 2 - 20, W / 2, 0)]
    bow_top = [(p[0], p[1], 13) for p in bow]
    mb.poly_boxuv([bow_top[0], bow_top[1], bow_top[2]], "M_ShipHull")
    mb.poly_boxuv([bow[0], bow[1], bow_top[1], bow_top[0]], "M_ShipHull")
    mb.poly_boxuv([bow[1], bow[2], bow_top[2], bow_top[1]], "M_ShipHull")
    decks = [(-80, 70, 12, 18), (-75, 60, 18, 24), (-65, 45, 24, 29), (-50, 25, 29, 33)]
    for x0, x1, z0, z1 in decks:
        w = W / 2 - 1.5
        mb.box((x0, -w, z0), (x1, w, z1), "M_ShipHull")
        for z in (z0 + 1.2, z0 + 3.4):
            if z + 0.9 < z1:
                for side in (-1, 1):
                    y = side * (w + 0.05)
                    mb.box((x0 + 2, min(y, y - side * 0.1), z), (x1 - 2, max(y, y - side * 0.1), z + 0.9), "M_ShipLights")
    for z in (4.0, 7.5):
        for side in (-1, 1):
            y = side * (W / 2 + 0.05)
            mb.box((-L / 2 + 6, min(y, y - side * 0.1), z), (L / 2 - 26, max(y, y - side * 0.1), z + 0.7), "M_ShipLights")
    mb.box((-40, -4, 33), (-28, 4, 41), "M_MetalDark")
    return [mb.build()]


def bell_tower():
    mb = MeshBuilder("BellTower")
    s = 2.0
    mb.box((-s, -s, 0), (s, s, 18), "M_Plaster_Cream", uv_scale=1.0)
    for z in (6, 12, 18):
        mb.box((-s - 0.2, -s - 0.2, z - 0.3), (s + 0.2, s + 0.2, z), "M_Stone")
    for x in (-s, s - 0.7):
        for y in (-s, s - 0.7):
            mb.box((x, y, 18), (x + 0.7, y + 0.7, 22), "M_Plaster_Cream")
    mb.box((-s + 0.5, -s + 0.5, 18), (s - 0.5, s - 0.5, 21.4), "M_TowerLight")
    mb.box((-s - 0.2, -s - 0.2, 22), (s + 0.2, s + 0.2, 22.4), "M_Stone")
    apex = (0, 0, 26)
    c = [(-s - 0.2, -s - 0.2, 22.4), (s + 0.2, -s - 0.2, 22.4), (s + 0.2, s + 0.2, 22.4), (-s - 0.2, s + 0.2, 22.4)]
    for i in range(4):
        mb.poly_boxuv([c[i], c[(i + 1) % 4], apex], "M_RoofTiles")
    mb.tube([(0, 0, 26), (0, 0, 27.5)], 0.06, "M_Iron", seg=6)
    ob = mb.build()
    empty("LightPoint", (0, 0, 19.8), ob)
    return [ob]


def lighthouse():
    mb = MeshBuilder("Lighthouse")
    mb.cylinder((0, 0, 0), 14, 2.0, 1.4, "M_Plaster_Cream", seg=16)
    mb.cylinder((0, 0, 14), 0.3, 2.0, 2.0, "M_Iron", seg=16)
    mb.cylinder((0, 0, 14.3), 1.8, 1.0, 1.0, "M_TowerLight", seg=12)
    mb.cylinder((0, 0, 16.1), 1.0, 1.2, 0.1, "M_MetalDark", seg=12)
    ob = mb.build()
    empty("LightPoint", (0, 0, 15.2), ob)
    return [ob]


# ============================================================== cats
def _part(name, build_fn, origin, parent, root_origin=(0, 0, 0)):
    mb = MeshBuilder(name)
    build_fn(mb)
    ob = mb.build()
    shift_mesh(ob, origin)
    if parent is not None:
        ob.parent = parent
        po = parent.get("_world_origin", root_origin)
        ob.location = Vector(origin) - Vector(po)
    ob["_world_origin"] = tuple(origin)
    add_subsurf(ob)
    return ob


def _cat_leg(mb, rings, mat):
    mb.loft(rings, mat, seg=10, up=Vector((0, -1, 0)), v_scale=3.0)


def cat_hero():
    mat = "M_CatBengal"
    root = empty("Cat_Hero", (0, 0, 0))
    root["_world_origin"] = (0, 0, 0)

    def body(mb):
        mb.loft([((0, 0.252, 0.258), 0.02, 0.02), ((0, 0.238, 0.262), 0.055, 0.06), ((0, 0.2, 0.262), 0.072, 0.08),
                 ((0, 0.12, 0.256), 0.08, 0.085), ((0, 0.04, 0.248), 0.077, 0.079), ((0, -0.05, 0.254), 0.078, 0.085),
                 ((0, -0.13, 0.26), 0.075, 0.088), ((0, -0.18, 0.27), 0.062, 0.075), ((0, -0.205, 0.28), 0.03, 0.04)],
                mat, seg=14, v_scale=1.8)

    b = _part("Body", body, (0, 0, 0.25), root)

    def head(mb):
        mb.loft([((0, -0.17, 0.28), 0.045, 0.05), ((0, -0.215, 0.32), 0.045, 0.048), ((0, -0.24, 0.35), 0.042, 0.045)],
                mat, seg=10, v_scale=0.5)
        mb.loft([((0, -0.226, 0.366), 0.01, 0.01), ((0, -0.236, 0.37), 0.045, 0.045), ((0, -0.26, 0.372), 0.058, 0.052),
                 ((0, -0.29, 0.37), 0.06, 0.05), ((0, -0.32, 0.362), 0.05, 0.042), ((0, -0.345, 0.352), 0.032, 0.03),
                 ((0, -0.36, 0.348), 0.022, 0.022), ((0, -0.367, 0.346), 0.008, 0.008)], mat, seg=12, v_scale=0.85)
        for s in (-1, 1):
            mb.tube([(s * 0.032, -0.272, 0.405), (s * 0.046, -0.268, 0.462)], 0.02, mat, seg=4,
                    radii=[(0.022, 0.01), (0.002, 0.002)], smooth=False)
            mb.sphere((s * 0.027, -0.334, 0.374), 0.012, "M_CatEye", seg=10, rings=6, scale=(1, 0.6, 1))
        mb.sphere((0, -0.368, 0.352), 0.008, "M_CatNose", seg=8, rings=5)

    _part("Head", head, (0, -0.2, 0.3), b)

    for s, tag in ((-1, "L"), (1, "R")):
        x = s * 0.045
        _part(f"Leg_F{tag}", lambda mb, x=x: _cat_leg(mb, [
            ((x, -0.14, 0.25), 0.035, 0.035), ((x, -0.145, 0.16), 0.026, 0.028), ((x, -0.15, 0.07), 0.019, 0.02),
            ((x, -0.152, 0.035), 0.018, 0.018), ((x, -0.165, 0.012), 0.024, 0.014)], mat), (x, -0.14, 0.24), b)
        x = s * 0.05
        _part(f"Leg_B{tag}", lambda mb, x=x: _cat_leg(mb, [
            ((x, 0.15, 0.27), 0.045, 0.05), ((x, 0.185, 0.19), 0.04, 0.045), ((x, 0.2, 0.12), 0.026, 0.028),
            ((x, 0.19, 0.07), 0.02, 0.021), ((x, 0.175, 0.035), 0.018, 0.018), ((x, 0.16, 0.012), 0.024, 0.014)], mat),
            (x, 0.16, 0.25), b)

    # tail: chain of 6 segments
    angles = [-20, -35, -48, -52, -42, -25]
    seg_len = 0.055
    start = Vector((0, 0.245, 0.275))
    parent = b
    r0 = 0.026
    for i, a in enumerate(angles):
        d = Vector((0, math.cos(math.radians(a)), math.sin(math.radians(a))))
        end = start + d * seg_len
        ra, rb = r0 - 0.0016 * i, r0 - 0.0016 * (i + 1)
        if i == len(angles) - 1:
            rb = 0.008

        def tail(mb, s0=start.copy(), e0=end.copy(), ra=ra, rb=rb):
            mb.loft([(tuple(s0 - (e0 - s0) * 0.15), ra * 0.95, ra * 0.95), (tuple(s0), ra, ra),
                     (tuple(e0), rb, rb)], mat, seg=10, v_scale=0.7)

        parent = _part(f"Tail{i + 1}", tail, tuple(start), parent)
        start = end
    return [root]


def cat_baron():
    mat = "M_CatGrey"
    root = empty("Cat_Baron", (0, 0, 0))
    root["_world_origin"] = (0, 0, 0)

    def body(mb):
        mb.loft([((0, 0.07, 0.03), 0.03, 0.03), ((0, 0.06, 0.06), 0.1, 0.09), ((0, 0.03, 0.13), 0.105, 0.095),
                 ((0, -0.01, 0.2), 0.09, 0.085), ((0, -0.04, 0.27), 0.08, 0.08), ((0, -0.06, 0.31), 0.06, 0.06),
                 ((0, -0.065, 0.33), 0.02, 0.02)], mat, seg=14, up=Vector((0, 1, 0)))
        for s in (-1, 1):
            mb.sphere((s * 0.075, 0.04, 0.08), 0.075, mat, seg=12, rings=8, scale=(0.7, 1.2, 0.9))
            mb.loft([((s * 0.04, -0.06, 0.22), 0.032, 0.032), ((s * 0.04, -0.08, 0.1), 0.026, 0.026),
                     ((s * 0.04, -0.09, 0.03), 0.024, 0.024), ((s * 0.04, -0.105, 0.012), 0.027, 0.014)], mat, seg=10)
        mb.tube([(-0.06, 0.12, 0.022), (-0.13, 0.04, 0.022), (-0.13, -0.06, 0.022), (-0.08, -0.13, 0.022),
                 (0.0, -0.15, 0.022)], 0.025, mat, seg=8,
                radii=[0.026, 0.025, 0.023, 0.02, 0.012])

    b = _part("Body", body, (0, 0, 0.15), root)

    def head(mb):
        mb.loft([((0, -0.02, 0.4), 0.01, 0.01), ((0, -0.03, 0.4), 0.06, 0.06), ((0, -0.06, 0.4), 0.08, 0.07),
                 ((0, -0.1, 0.395), 0.075, 0.062), ((0, -0.13, 0.385), 0.05, 0.042), ((0, -0.145, 0.38), 0.03, 0.028),
                 ((0, -0.15, 0.378), 0.01, 0.01)], mat, seg=12)
        for s in (-1, 1):
            mb.tube([(s * 0.05, -0.065, 0.455), (s * 0.068, -0.065, 0.5)], 0.02, mat, seg=4,
                    radii=[(0.024, 0.012), (0.004, 0.004)], smooth=False)
            mb.sphere((s * 0.032, -0.132, 0.405), 0.014, "M_CatEyeCopper", seg=10, rings=6, scale=(1, 0.6, 1))
        mb.sphere((0, -0.152, 0.386), 0.009, "M_CatNose", seg=8, rings=5)

    _part("Head", head, (0, -0.06, 0.33), b)
    return [root]


# ============================================================== registry / export
MODELS = {
    "AC_Unit": ac_unit,
    "Railing_1m": railing,
    "Railing_Post": railing_post,
    "Lantern_Wall": lantern_wall,
    "StreetLamp": street_lamp,
    "Awning_3m": awning,
    "Window_LitA": lambda: window("Window_LitA", WINDOW_QUADS[0]),
    "Window_LitB": lambda: window("Window_LitB", WINDOW_QUADS[1]),
    "Window_LitC": lambda: window("Window_LitC", WINDOW_QUADS[2]),
    "Window_LitD": lambda: window("Window_LitD", WINDOW_QUADS[3]),
    "Window_Dark": lambda: window("Window_Dark"),
    "Window_Closed": lambda: window("Window_Closed", None, closed=True),
    "Door_Balcony": door_balcony,
    "Door_Street": door_street,
    "FlowerBox_Red": lambda: flower_box("FlowerBox_Red", GERANIUM, 1),
    "FlowerBox_White": lambda: flower_box("FlowerBox_White", DAISY, 2),
    "FlowerBox_Magenta": lambda: flower_box("FlowerBox_Magenta", BOUGAINVILLEA, 3),
    "Pot_Geranium": lambda: pot("Pot_Geranium", GERANIUM, 5),
    "Pot_Daisy": lambda: pot("Pot_Daisy", DAISY, 6),
    "Pot_Small": lambda: pot("Pot_Small", GERANIUM, 7, 0.6),
    "Planter_Stone": planter_stone,
    "Ivy_Patch": ivy_patch,
    "Ivy_Tall": lambda: ivy_patch("Ivy_Tall", 21, 1.0, 4.5, 34),
    "Bougainvillea": bougainvillea,
    "Chimney": chimney,
    "Drainpipe_1m": drainpipe,
    "Bulb": bulb,
    "Crate": crate,
    "CafeTable": cafe_table,
    "CafeChair": cafe_chair,
    "Pergola": pergola,
    "Palm": palm,
    "Cypress": cypress,
    "Laundry_Line": laundry_line,
    "Ship": ship,
    "BellTower": bell_tower,
    "Lighthouse": lighthouse,
    "Cat_Hero": cat_hero,
    "Cat_Baron": cat_baron,
}


def all_objects(roots):
    out = []
    for r in roots:
        out.append(r)
        out.extend(r.children_recursive)
    return out


def export_all(out_dir, only=None):
    os.makedirs(out_dir, exist_ok=True)
    for name, fn in MODELS.items():
        if only and name not in only:
            continue
        clear_scene()
        roots = fn()
        for ob in all_objects(roots):
            if "_world_origin" in ob.keys():
                del ob["_world_origin"]
        path = os.path.join(out_dir, name + ".fbx")
        export_fbx(path, all_objects(roots))
        tris = sum(len(o.data.polygons) for o in all_objects(roots) if o.type == "MESH")
        print(f"{name:20s} faces={tris:6d} -> {os.path.relpath(path)}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    out = args[0] if args else OUT
    export_all(out, set(args[1:]) or None)
