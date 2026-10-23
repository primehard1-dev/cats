"""Level 01 "Moon Street" layout -> CatsGame/Assets/_Project/Data/level01.json

All numbers follow docs/level-01/README.md. The design doc uses
    X  = along the street (downhill, towards the sea),
    Y  = up,
    Zd = across the street (left facade at Zd = 0, right facade at Zd = 5.2).
Unity coordinates are (x, y, z) = (Zd, Y, X): the cat walks towards +z with the
left facade on its left (x = 0) and the street on its right (x > 0).
"""
import json
import math
import os
import random

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "CatsGame", "Assets", "_Project", "Data", "level01.json")

MOON_AZIMUTH_DEG = 24.0   # keep in sync with tools/textures/gen_textures.py
MOON_ELEVATION_DEG = 11.0
STREET_W = 5.2

rnd = random.Random(2026)
L = {k: [] for k in ("blocks", "roofs", "props", "lights", "markers", "checkpoints", "killZones", "cameraZones",
                      "ropes", "ledgeZones", "reflectionProbes", "houses", "garlands", "lightProbes",
                      "decals", "pigeons", "fireflies", "drips", "ripples", "tvLights", "sounds")}


def V(X, Y, Zd):
    return {"x": round(Zd, 4), "y": round(Y, 4), "z": round(X, 4)}


def S(sx, sy, szd):
    return {"x": round(szd, 4), "y": round(sy, 4), "z": round(sx, 4)}


def C(r, g, b):
    return {"r": r, "g": g, "b": b, "a": 1.0}


def street_y(X):
    return -0.08 * (X - 6.0) if X < 70 else -5.12 - (X - 70) * (3.0 / 8.0) if X < 78 else -8.1 - 0.2 * min(1, (X - 78) / 12)


# ------------------------------------------------------------------ helpers
def block(name, mat, X0, X1, Y0, Y1, Z0, Z1, visible=True, collide=True, surface="", tilt=0.0, static=True):
    """Axis-aligned box in doc coordinates; `tilt` rotates around the street axis (degrees)."""
    L["blocks"].append({
        "name": name, "mat": mat if visible else "",
        "pos": V((X0 + X1) / 2, (Y0 + Y1) / 2, (Z0 + Z1) / 2),
        "size": S(X1 - X0, Y1 - Y0, Z1 - Z0),
        "rot": {"x": 0, "y": 0, "z": tilt},
        "visible": visible, "collide": collide, "isStatic": static, "surface": surface,
    })


def prop(model, X, Y, Zd, rot_y=0.0, scale=1.0, collider="none", mat_swap="", light=None, static=True):
    sc = scale if isinstance(scale, (tuple, list)) else (scale, scale, scale)
    entry = {"model": model, "pos": V(X, Y, Zd), "rotY": rot_y, "scale": {"x": sc[0], "y": sc[1], "z": sc[2]},
             "collider": collider, "matSwap": mat_swap, "isStatic": static,
             "light": light or {"color": C(0, 0, 0), "intensity": 0, "range": 0, "mode": "baked", "shadows": False}}
    L["props"].append(entry)


def lamp_light(intensity=2.6, rng=7.0, mode="baked", shadows=False, color=(1.0, 0.6, 0.28)):
    return {"color": C(*color), "intensity": intensity, "range": rng, "mode": mode, "shadows": shadows}


def light(name, X, Y, Zd, color, intensity, rng, mode="baked", shadows=False):
    L["lights"].append({"name": name, "type": "point", "pos": V(X, Y, Zd), "color": C(*color),
                        "intensity": intensity, "range": rng, "mode": mode, "shadows": shadows})


LEFT = 90.0     # prop on the left facade, facing the street
RIGHT = -90.0   # prop on the right facade, facing the street


def facade_windows(X0, X1, floors, side="left", skip=(), spacing=2.6, lit_ratio=0.45, closed_ratio=0.2):
    zd = 0.0 if side == "left" else STREET_W
    rot = LEFT if side == "left" else RIGHT
    n = int((X1 - X0) // spacing)
    if n <= 0:
        return
    start = X0 + ((X1 - X0) - (n - 1) * spacing) / 2
    for fy in floors:
        for i in range(n):
            X = start + i * spacing
            if any(a <= X <= b and ya <= fy <= yb for a, b, ya, yb in skip):
                continue
            r = rnd.random()
            if r < lit_ratio:
                model = rnd.choice(["Window_LitA", "Window_LitB", "Window_LitC", "Window_LitD"])
            elif r < lit_ratio + closed_ratio:
                model = "Window_Closed"
            else:
                model = "Window_Dark"
            prop(model, X, fy, zd, rot)
            if rnd.random() < 0.3:
                fb = rnd.choice(["FlowerBox_Red", "FlowerBox_White", "FlowerBox_Magenta"])
                prop(fb, X, fy, zd, rot)


# ================================================================== LEFT BUILDING (Zd < 0)
# House segments: (X0, X1, roof Y, material)
left_houses = [(-12, 8.0, 12.5, "M_Plaster_Ochre"), (8.0, 23.0, 11.8, "M_Plaster_Terracotta"),
               (23.0, 33.0, 10.2, "M_Plaster_Yellow"), (33.0, 46.0, 9.0, "M_Plaster_Pink"),
               (46.0, 58.0, 6.5, "M_Plaster_Cream"), (58.0, 70.0, 2.5, "M_Plaster_Ochre")]
for i, (x0, x1, top, mat) in enumerate(left_houses):
    base = min(street_y(x0), street_y(x1)) - 1.0
    block(f"LeftHouse{i}", mat, x0, x1, base, top, -10.0, 0.0)
    block(f"LeftHouse{i}_Cornice", "M_Stone", x0, x1, top - 0.25, top, -10.0, 0.25)
    L["roofs"].append({"pos": V((x0 + x1) / 2, top, -5.0), "size": S(x1 - x0, 2.2, 10.6), "rotY": 0.0, "mat": "M_RoofTiles",
                       "gable": "street"})
    # drainpipe at the segment border
    for k in range(int(top - base)):
        prop("Drainpipe_1m", x0 + 0.15, base + k, 0.0, LEFT)

# ------------------------------------------------------------------ Z0 apartment + Z1 terrace (Y = 6.0)
TY = 6.0
block("Apartment_Floor", "M_WoodDark", -5.0, 0.0, TY - 0.2, TY, -5.0, 0.0)
block("Terrace_Slab", "M_Stone", 0.0, 6.0, TY - 0.4, TY - 0.05, 0.0, 2.5)
block("Terrace_Tiles", "M_TerraceTiles", 0.0, 6.0, TY - 0.05, TY, 0.0, 2.5)
block("Terrace_ParapetSide", "M_Stone", 4.0, 6.0, TY, TY + 0.45, 2.1, 2.5)
block("Terrace_Curb", "M_Stone", 0.0, 4.0, TY, TY + 0.08, 2.3, 2.5)
block("Terrace_ParapetEnd", "M_Stone", 5.6, 6.0, TY, TY + 0.45, 0.0, 2.1)
block("Terrace_ParapetBack", "M_Stone", -0.4, 0.0, TY, TY + 0.45, 0.0, 2.5)
for X in (0.6, 2.4, 4.2, 5.8):
    block(f"Terrace_Corbel{X}", "M_Stone", X - 0.18, X + 0.18, TY - 1.2, TY - 0.4, 0.0, 2.1)
# railing on the parapet for the first 4 m (no accidental falls at the start)
for X in (0.5, 1.5, 2.5, 3.5):
    prop("Railing_1m", X, TY + 0.08, 2.4, 90.0)
block("Terrace_RailGuard", "", 0.0, 4.0, TY + 0.08, TY + 2.2, 2.3, 2.5, visible=False)
block("Terrace_BackGuard", "", -0.4, 0.0, TY + 0.45, TY + 2.2, 0.0, 2.5, visible=False)
prop("Railing_Post", 4.0, TY + 0.08, 2.4)
prop("Door_Balcony", 0.9, TY, 0.0, LEFT)
prop("Lantern_Wall", 3.1, TY + 2.25, 0.0, LEFT,
     light=lamp_light(3.2, 8.0, "mixed", shadows=True))
prop("Planter_Stone", -0.1, TY, 0.45, 90.0, collider="box")
prop("Pot_Daisy", 4.6, TY, 0.35, 0.0, collider="box")
prop("Pot_Geranium", 5.2, TY + 0.45, 2.3, 0.0, scale=0.8)
prop("Ivy_Tall", 4.8, TY - 0.2, 0.0, LEFT, scale=(1.0, 1.0, 1.0))
prop("Bougainvillea", 5.2, TY + 3.6, 0.0, LEFT)
prop("Window_LitB", 4.2, TY + 3.2, 0.0, LEFT)
light("Apartment_Spill", 0.9, TY + 1.6, 0.7, (1.0, 0.7, 0.42), 1.6, 5.0, "mixed")
light("Apartment_Room", 0.9, TY + 1.8, -2.5, (1.0, 0.68, 0.4), 2.0, 6.0, "baked")

# ------------------------------------------------------------------ Z2 AC unit #1 (top 6.7)
prop("AC_Unit", 7.05, 6.08, 0.0, LEFT)
block("AC1_Collider", "", 6.6, 7.5, 6.08, 6.7, 0.0, 0.62, visible=False)
L["markers"].append({"pos": V(7.05, 6.71, 0.32)})

# ------------------------------------------------------------------ Z3 balcony with Baron (floor 7.3)
B1 = 7.3
block("B1_Slab", "M_Stone", 8.0, 11.0, B1 - 0.2, B1, 0.0, 1.1)
for X in (8.3, 9.4, 10.5):
    block(f"B1_Corbel{X}", "M_Stone", X - 0.1, X + 0.1, B1 - 0.6, B1 - 0.2, 0.0, 0.9)
for X in (8.5, 9.5, 10.5):
    prop("Railing_1m", X, B1, 1.05, 90.0)
prop("Railing_1m", 11.0, B1, 0.55, 0.0, scale=(1.1, 1, 1))
block("B1_RailGuard", "", 8.0, 11.0, B1, B1 + 1.8, 1.0, 1.1, visible=False)
block("B1_EndGuard", "", 10.95, 11.05, B1, B1 + 1.8, 0.35, 1.1, visible=False)
prop("Door_Balcony", 9.5, B1, 0.0, LEFT)
prop("FlowerBox_Red", 8.6, B1 + 1.0, 1.1, 0.0)
prop("FlowerBox_Magenta", 10.4, B1 + 1.0, 1.1, 0.0)
prop("Pot_Geranium", 8.3, B1, 0.3, 0.0, collider="box")
prop("Lantern_Wall", 11.4, B1 + 2.2, 0.0, LEFT, light=lamp_light(2.6, 7.0, "mixed"))
L["markers"].append({"pos": V(8.6, B1 + 0.01, 0.5)})
L["checkpoints"].append({"id": "B1", "pos": V(9.0, B1 + 0.5, 0.6), "size": S(2.0, 1.2, 1.1), "spawnRotY": 0.0})
npc_pos = V(10.3, B1, 0.6)

# ------------------------------------------------------------------ Z4 ledge (0.35 m) with sills and AC #2
block("Ledge", "M_Stone", 11.0, 23.0, B1 - 0.2, B1, 0.0, 0.35, surface="Ledge")
L["ledgeZones"].append({"pos": V(17.0, B1 + 0.4, 0.2), "size": S(12.0, 0.8, 0.5)})
for X in (13.5, 19.0, 22.0):
    block(f"Sill{X}", "M_Stone", X - 0.55, X + 0.55, B1 - 0.15, B1, 0.0, 0.55)
    prop(rnd.choice(["Window_LitA", "Window_LitC", "Window_Dark"]), X, B1 + 0.05, 0.0, LEFT)
prop("AC_Unit", 15.95, B1 - 0.02, 0.0, LEFT)
block("AC2_Collider", "", 15.5, 16.4, B1, B1 + 0.6, 0.0, 0.62, visible=False)
L["markers"].append({"pos": V(15.95, B1 + 0.61, 0.3)})
L["markers"].append({"pos": V(17.0, B1 + 0.01, 0.18)})
prop("Pot_Small", 12.5, B1, 0.18, 0.0, collider="box", static=False)
prop("Pot_Small", 20.6, B1, 0.18, 0.0, collider="box", static=False)
prop("Lantern_Wall", 17.6, B1 + 1.9, 0.0, LEFT, light=lamp_light(2.4, 6.5))
prop("Ivy_Patch", 12.0, B1 - 3.2, 0.0, LEFT)
prop("Ivy_Tall", 21.0, B1 - 4.6, 0.0, LEFT)
L["checkpoints"].append({"id": "LedgeEnd", "pos": V(22.0, B1 + 0.5, 0.3), "size": S(1.2, 1.2, 0.8), "spawnRotY": 0.0})
L["cameraZones"].append({"pos": V(17.0, B1 + 0.8, 0.6), "size": S(12.5, 2.5, 2.0), "distance": 2.0, "height": 1.2,
                         "pitch": 18.0, "side": 0.45})

# ------------------------------------------------------------------ Z5 awning slide -> balcony B2 (5.4)
prop("Awning_3m", 25.0, 6.9, 0.0, LEFT, mat_swap="M_AwningBlue=M_AwningBlue")
block("Awning_Slide", "", 23.5, 26.5, 6.58, 6.63, 0.0, 1.6, visible=False, surface="Slide", tilt=-20.0)
block("Awning_Guard", "", 23.5, 26.5, 6.3, 7.4, 1.5, 1.62, visible=False)
L["markers"].append({"pos": V(24.6, 6.8, 0.5)})
B2 = 5.4
block("B2_Slab", "M_Stone", 26.5, 29.5, B2 - 0.2, B2, 0.0, 1.2)
for X in (27.0, 28.0):
    prop("Railing_1m", X, B2, 1.15, 90.0)
block("B2_RailGuard", "", 26.5, 28.6, B2, B2 + 1.8, 1.1, 1.2, visible=False)
prop("Window_LitD", 28.0, B2 + 0.05, 0.0, LEFT)
prop("FlowerBox_White", 27.0, B2 + 1.0, 1.2, 0.0)
prop("Lantern_Wall", 29.2, B2 + 2.0, 0.0, LEFT, light=lamp_light(2.4, 6.0))
L["markers"].append({"pos": V(27.6, B2 + 0.01, 0.6)})
L["checkpoints"].append({"id": "B2", "pos": V(27.6, B2 + 0.5, 0.6), "size": S(2.0, 1.2, 1.2), "spawnRotY": 0.0})

# ------------------------------------------------------------------ Z6 garland across the street (balance rope)
rope_a = (29.4, 5.62, 1.15)
rope_b = (33.6, 5.28, 4.15)
L["ropes"].append({"points": [V(*rope_a), V(*rope_b)], "sag": 0.55, "width": 0.08})
L["garlands"].append({"a": V(*rope_a), "b": V(*rope_b), "sag": 0.55, "bulbSpacing": 0.45, "gameplay": True})
L["markers"].append({"pos": V(rope_a[0] - 0.2, B2 + 0.01, rope_a[2] - 0.2)})
# on the garland the camera looks along the cable, so "stick up" walks the cat along it
rope_yaw = math.degrees(math.atan2(rope_b[2] - rope_a[2], rope_b[0] - rope_a[0]))
L["cameraZones"].append({"pos": V(31.5, 5.6, 2.6), "size": S(5.5, 3.0, 4.5), "distance": 3.2, "height": 1.6, "pitch": 26.0,
                         "side": -0.8, "fixYaw": True, "yaw": round(rope_yaw, 1)})
# decorative garlands further down the street (like the reference)
L["garlands"].append({"a": V(44.0, 8.6, 0.0), "b": V(52.0, 8.0, STREET_W), "sag": 0.9, "bulbSpacing": 0.6,
                      "gameplay": False})
L["garlands"].append({"a": V(62.0, 3.6, 0.0), "b": V(66.0, 3.2, STREET_W), "sag": 0.6, "bulbSpacing": 0.6,
                      "gameplay": False})

# ================================================================== RIGHT BUILDINGS (Zd > 5.2)
right_houses = [(-12, 4.0, 10.5, "M_Plaster_Pink"), (4.0, 14.0, 2.6, "M_Plaster_Cream"),
                (14.0, 24.0, 1.8, "M_Plaster_Yellow"), (24.0, 36.0, 4.4, "M_Plaster_Cream"),
                (36.0, 42.0, 4.6, "M_Plaster_Terracotta"), (42.0, 49.5, 3.0, "M_Plaster_Ochre"),
                (49.5, 55.0, 1.6, "M_Plaster_Yellow"), (60.0, 70.0, 0.5, "M_Plaster_Pink")]
for i, (x0, x1, top, mat) in enumerate(right_houses):
    base = min(street_y(x0), street_y(x1)) - 1.0
    block(f"RightHouse{i}", mat, x0, x1, base, top, STREET_W, STREET_W + 10.0)
    block(f"RightHouse{i}_Cornice", "M_Stone", x0, x1, top - 0.25, top, STREET_W - 0.25, STREET_W + 10.0)
    if i in (1, 2, 3, 7):
        L["roofs"].append({"pos": V((x0 + x1) / 2, top, STREET_W + 5.0), "size": S(x1 - x0, 1.5, 10.6), "rotY": 0.0,
                           "mat": "M_RoofTiles", "gable": "street"})

# B3 balcony on the right house, end of the garland (5.2)
B3 = 5.2
block("B3_Slab", "M_Stone", 33.0, 36.0, B3 - 0.2, B3, 4.0, STREET_W)
for X in (33.5, 34.5, 35.5):
    prop("Railing_1m", X, B3, 4.05, -90.0)
block("B3_RailGuard", "", 34.1, 36.0, B3, B3 + 1.8, 4.0, 4.1, visible=False)
prop("Window_LitA", 34.5, B3 + 0.05, STREET_W, RIGHT)
prop("Lantern_Wall", 33.2, B3 + 2.1, STREET_W, RIGHT, light=lamp_light(2.6, 7.0, "mixed"))
prop("Pot_Geranium", 35.6, B3, 4.9, 0.0, collider="box")
L["checkpoints"].append({"id": "B3", "pos": V(34.4, B3 + 0.5, 4.6), "size": S(2.4, 1.2, 1.1), "spawnRotY": 0.0})

# R1 roof terrace (4.6) with laundry, R2 tiles (3.2 -> tilted), R3 (1.8)
R1 = 4.6
block("R1_Floor", "M_TerraceTiles", 36.0, 42.0, R1 - 0.2, R1, 4.0, STREET_W + 6.0)
block("R1_Parapet", "M_Stone", 36.0, 42.0, R1, R1 + 0.5, 4.0, 4.3)
block("R1_Guard", "", 36.0, 42.0, R1 + 0.5, R1 + 2.0, 4.0, 4.3, visible=False)
prop("Laundry_Line", 39.0, R1 + 1.8, 7.0, 0.0)
prop("Laundry_Line", 39.0, R1 + 1.8, 9.0, 0.0)
prop("Chimney", 41.0, R1, 10.0, 0.0, collider="box")
prop("Pot_Daisy", 36.6, R1, 5.0, 0.0, collider="box")
prop("Pot_Geranium", 37.4, R1, 4.7, 0.0, collider="box")
prop("Cypress", 37.0, R1, 10.2, 0.0, scale=0.65)
prop("Cypress", 38.2, R1, 10.4, 0.0, scale=0.55)
prop("Lantern_Wall", 41.8, R1 + 2.0, 8.0, 180.0, light=lamp_light(2.4, 7.0))
L["checkpoints"].append({"id": "R1", "pos": V(37.0, R1 + 0.5, 6.0), "size": S(2.0, 1.2, 2.0), "spawnRotY": 0.0})

block("R2_Roof", "M_RoofTiles", 42.0, 49.5, 2.95, 3.25, 4.6, STREET_W + 8.0, tilt=-8.0)
prop("Chimney", 44.5, 3.2, 8.5, 0.0, collider="box")
prop("Chimney", 47.8, 3.2, 10.5, 0.0, collider="box")
block("R3_Roof", "M_RoofTiles", 49.5, 55.0, 1.55, 1.85, 4.6, STREET_W + 8.0, tilt=-8.0)
prop("Laundry_Line", 52.0, 3.2, 9.5, 90.0)
L["markers"].append({"pos": V(43.6, 3.25, 7.5)})
L["markers"].append({"pos": V(50.6, 1.85, 7.5)})

# ------------------------------------------------------------------ Z8 descent: pergola -> crates -> cafe -> street
CAFE = -3.0
block("Cafe_Platform", "M_Stone", 54.0, 60.0, street_y(60) - 1.0, CAFE, STREET_W, STREET_W + 6.0)
block("Cafe_Floor", "M_TerraceTiles", 54.0, 60.0, CAFE, CAFE + 0.02, STREET_W, STREET_W + 6.0)
prop("Pergola", 56.5, CAFE, 7.6, 0.0)
block("Pergola_Top", "", 55.0, 58.0, CAFE + 2.75, CAFE + 2.9, 6.3, 8.9, visible=False)
for (X, Zd, h) in ((58.6, 6.0, 0), (58.6, 6.0, 1), (58.6, 6.0, 2), (59.2, 6.4, 0), (58.0, 5.6, 0)):
    prop("Crate", X, CAFE + 0.02 + 0.5 * h, Zd, rnd.uniform(-10, 10), collider="box")
for X, Zd in ((55.2, 9.8), (57.8, 9.8), (59.0, 9.0)):
    prop("CafeTable", X, CAFE, Zd, 0.0, collider="box")
    prop("CafeChair", X - 0.5, CAFE, Zd, 90.0, collider="box")
    prop("CafeChair", X + 0.5, CAFE, Zd, -90.0, collider="box")
block("Cafe_House", "M_Plaster_Ochre", 53.5, 60.5, street_y(60) - 1.0, 1.4, STREET_W + 6.0, STREET_W + 16.0)
prop("Window_LitC", 55.0, CAFE + 0.9, STREET_W + 6.0, RIGHT)
prop("Window_LitA", 59.2, CAFE + 0.9, STREET_W + 6.0, RIGHT)
prop("Awning_3m", 57.0, CAFE + 2.6, STREET_W + 6.0, RIGHT, mat_swap="M_AwningBlue=M_AwningGreen")
light("Cafe_Light", 57.0, CAFE + 2.3, 9.0, (1.0, 0.62, 0.32), 3.0, 9.0, "baked")
prop("Palm", 54.6, CAFE, 10.5, 30.0, scale=0.8)
L["markers"].append({"pos": V(56.6, CAFE + 2.9, 7.4)})
L["markers"].append({"pos": V(58.6, CAFE + 1.52, 6.0)})
L["checkpoints"].append({"id": "Cafe", "pos": V(57.0, CAFE + 0.5, 8.0), "size": S(4.0, 1.2, 3.0), "spawnRotY": 0.0})

# ================================================================== STREET (cobbles, stairs, embankment)
seg = 2.0
X = -12.0
while X < 70.0:
    y0, y1 = street_y(X), street_y(X + seg)
    block(f"Street{X:.0f}", "M_Cobble", X, X + seg, min(y0, y1) - 1.0, (y0 + y1) / 2, 0.0, STREET_W)
    X += seg
for i in range(16):
    X0 = 70.0 + i * 0.5
    top = -5.12 - (i + 1) * (3.0 / 16)
    block(f"Stair{i}", "M_Stone", X0, X0 + 0.5, -10.0, top, 0.0, STREET_W)
block("Embankment", "M_Cobble", 78.0, 92.0, -10.0, -8.3, -30.0, 40.0)
block("Embankment_Edge", "M_Stone", 91.4, 92.0, -8.3, -7.9, -30.0, 40.0)
block("Embankment_Guard", "", 91.4, 92.0, -7.9, -6.0, -30.0, 40.0, visible=False)
block("Quay_Wall", "M_Stone", 91.4, 92.4, -12.0, -8.3, -30.0, 40.0)
for X in range(-8, 70, 9):
    prop("StreetLamp", X + 1.0, street_y(X + 1.0), STREET_W - 0.35, RIGHT, collider="box", light=lamp_light(3.0, 9.0))
for Zd in (-20.0, -8.0, 4.0, 16.0, 28.0):
    prop("StreetLamp", 91.0, -8.3, Zd, 180.0, collider="box", light=lamp_light(3.0, 10.0))
for X, Zd in ((62.0, 4.4), (75.0, 4.6), (84.0, -12.0), (86.0, 14.0), (83.0, 24.0), (88.0, -24.0)):
    prop("Palm", X, street_y(X) if X < 78 else -8.3, Zd, rnd.uniform(0, 360), scale=rnd.uniform(0.8, 1.15))
for X in (66.0, 68.0):
    prop("Planter_Stone", X, street_y(X), 0.5, 90.0, collider="box")
L["checkpoints"].append({"id": "Stairs", "pos": V(79.0, -7.8, 2.6), "size": S(2.0, 1.4, 5.0), "spawnRotY": 0.0})
for X0 in range(-12, 54, 6):
    X1 = min(X0 + 6, 54)
    ym = street_y((X0 + X1) / 2)
    L["killZones"].append({"pos": V((X0 + X1) / 2, ym + 0.3, STREET_W / 2), "size": S(X1 - X0, 1.6, STREET_W + 0.2)})

# facade dressing along the route
facade_windows(-10.0, 8.0, [2.8, 9.6], "left")
facade_windows(11.5, 23.0, [3.6, 10.2], "left", skip=[(13.0, 14.0, 0, 20)])
facade_windows(23.0, 33.0, [2.0, 8.2], "left", skip=[(26.0, 30.0, 7.0, 9.0)])
facade_windows(33.0, 46.0, [1.2, 4.2, 6.9], "left")
facade_windows(46.0, 58.0, [-1.4, 1.6, 4.4], "left")
facade_windows(58.0, 70.0, [-2.7], "left")
facade_windows(-10.0, 4.0, [1.3, 4.5, 7.7], "right")
facade_windows(4.0, 14.0, [-0.3], "right")
facade_windows(14.0, 24.0, [-1.2], "right")
facade_windows(24.0, 33.0, [-1.8, 1.4], "right")
facade_windows(36.0, 42.0, [0.4], "right")
facade_windows(42.0, 49.5, [-1.0], "right")
facade_windows(60.0, 70.0, [-2.6], "right")
for X in (6.5, 20.0, 37.0, 50.0, 63.0):
    prop("Door_Street", X, street_y(X), 0.0, LEFT)
for X in (9.0, 24.0, 44.0, 64.0):
    prop("Door_Street", X, street_y(X), STREET_W, RIGHT)
for X, Y, side in ((31.0, 7.6, 0.0), (40.0, 6.0, 0.0), (52.0, 3.0, 0.0), (20.0, 0.6, STREET_W), (2.0, 6.2, STREET_W)):
    rot = LEFT if side == 0.0 else RIGHT
    prop("Lantern_Wall", X, Y, side, rot, light=lamp_light(2.2, 6.0))
for X, Y, side in ((26.0, 3.0, 0.0), (41.0, 2.0, 0.0), (18.0, -0.8, STREET_W), (30.0, -1.6, STREET_W)):
    prop("Ivy_Tall", X, Y, side, LEFT if side == 0.0 else RIGHT)
for X, Y, side in ((36.0, 6.8, 0.0), (16.0, 0.6, STREET_W), (46.5, 2.0, 0.0)):
    prop("Bougainvillea", X, Y, side, LEFT if side == 0.0 else RIGHT)
prop("Awning_3m", 47.0, 1.4, 0.0, LEFT, mat_swap="M_AwningBlue=M_AwningGreen")
prop("Awning_3m", 64.0, -1.4, STREET_W, RIGHT)
prop("Laundry_Line", 22.0, 9.2, STREET_W / 2, 0.0, scale=(1.75, 1, 1))
# roof terrace on the first right house (top right of the reference shot)
RT = 10.5
block("RT_Parapet", "M_Stone", -12.0, 4.0, RT, RT + 0.4, STREET_W, STREET_W + 0.3)
for X in range(-6, 4):
    prop("Railing_1m", X + 0.5, RT + 0.4, STREET_W + 0.15, -90.0)
prop("Cypress", 1.6, RT, STREET_W + 2.5, 0.0, scale=0.85)
prop("Cypress", 3.0, RT, STREET_W + 3.4, 0.0, scale=0.7)
prop("Pergola", -2.0, RT, STREET_W + 3.2, 0.0)
prop("Pot_Geranium", 0.0, RT, STREET_W + 0.7, 0.0)
light("RoofTerrace_Light", -2.0, RT + 2.4, STREET_W + 3.2, (1.0, 0.65, 0.35), 2.4, 8.0)
# the long right house is low (tile roof), so the view down to the sea opens over it
prop("Chimney", 10.0, 3.3, STREET_W + 7.0, 0.0)
prop("Chimney", 19.0, 2.5, STREET_W + 6.5, 0.0)
prop("Chimney", 30.0, 5.1, STREET_W + 8.0, 0.0)

# ================================================================== distant town, landmarks, sea
facade_mats = ["M_FacadeFar", "M_FacadeFar_Ochre", "M_FacadeFar_Pink", "M_FacadeFar_Terracotta"]


def house(X, Zd, w, d, h, ground):
    L["houses"].append({"pos": V(X, ground, Zd), "size": S(w, h, d), "mat": rnd.choice(facade_mats),
                        "roofMat": "M_RoofTiles", "gable": rnd.random() < 0.6, "uvOffset": rnd.random() * 10,
                        "foundation": max(0.0, ground + 12.0)})


# second row of houses behind the right side of the street (lit windows in the middle of the shot)
for X in range(4, 64, 8):
    house(X + rnd.uniform(-1, 1), STREET_W + 18.0 + rnd.uniform(-2, 3), 7.0, 9.0, rnd.uniform(7.5, 10.5), street_y(X) - 0.5)
    house(X + 4, STREET_W + 30.0 + rnd.uniform(-2, 3), 7.0, 9.0, rnd.uniform(7.5, 11.0), street_y(X) - 1.5)
# both sides of the lower street and stairs
for X in range(72, 92, 7):
    house(X, -8.0, 6.5, 10.0, rnd.uniform(6, 10), street_y(X) - 1)
    house(X, STREET_W + 6.0, 6.5, 10.0, rnd.uniform(6, 10), street_y(X) - 1)
# the town around the bay (left and right shores)
for i in range(46):
    X = 100 + i * 7.5 + rnd.uniform(-2, 2)
    Zd = -40 - (X - 100) * 0.35 + rnd.uniform(-6, 6)
    house(X, Zd, rnd.uniform(6, 11), rnd.uniform(7, 12), rnd.uniform(6, 16), -8.5 + max(0, (X - 100) * 0.04))
    if i % 2 == 0:
        house(X + 3, Zd - 14, rnd.uniform(6, 11), rnd.uniform(7, 12), rnd.uniform(8, 18), -8.5 + (X - 100) * 0.08 + 4)
for i in range(40):
    X = 100 + i * 8 + rnd.uniform(-2, 2)
    Zd = 55 + (X - 100) * 0.5 + rnd.uniform(-6, 6)
    house(X, Zd, rnd.uniform(6, 11), rnd.uniform(7, 12), rnd.uniform(6, 14), -8.5 + max(0, (X - 100) * 0.03))
    if i % 2 == 1:
        house(X + 2, Zd + 14, rnd.uniform(6, 11), rnd.uniform(7, 12), rnd.uniform(8, 16), -8.5 + (X - 100) * 0.06 + 3)
for X, Zd in ((96, -30), (110, -46), (125, -50), (98, 48), (112, 60), (140, 75)):
    prop("Palm", X, -8.3, Zd, rnd.uniform(0, 360), scale=rnd.uniform(0.9, 1.2), static=True)
prop("BellTower", 265.0, 2.0, -95.0, 30.0, light=lamp_light(6.0, 30.0))
prop("Lighthouse", 330.0, -8.6, 165.0, 0.0, light=lamp_light(8.0, 40.0))
prop("Ship", 1300.0, -9.3, 400.0, 75.0, scale=0.6, static=False)

# ================================================================== atmosphere & life
def decal(mat, corners, uv):
    """corners in doc coordinates (X, Y, Zd), counter-clockwise seen from the front."""
    L["decals"].append({"mat": mat, "a": V(*corners[0]), "b": V(*corners[1]), "c": V(*corners[2]), "d": V(*corners[3]),
                        "uv": {"x": uv[0], "y": uv[1]}})


# dirt at the bottom of the walls (follows the slope of the street) and streaks under ledges/balconies
for x0, x1, _top, _mat in left_houses:
    X = x0
    while X < x1:
        Xn = min(x1, X + 4.0)
        ya, yb = street_y(X), street_y(Xn)
        decal("M_Grime", [(X, ya - 0.05, 0.015), (Xn, yb - 0.05, 0.015), (Xn, yb + 1.6, 0.015), (X, ya + 1.6, 0.015)],
              ((Xn - X) / 2.0, 1.0))
        X = Xn
for x0, x1, _top, _mat in right_houses:
    X = x0
    while X < x1:
        Xn = min(x1, X + 4.0)
        ya, yb = street_y(X), street_y(Xn)
        z = STREET_W - 0.015
        decal("M_Grime", [(Xn, yb - 0.05, z), (X, ya - 0.05, z), (X, ya + 1.6, z), (Xn, yb + 1.6, z)], ((Xn - X) / 2.0, 1.0))
        X = Xn
for X0, X1, Ytop in ((11.0, 23.0, B1 - 0.2), (8.0, 11.0, B1 - 0.6), (26.5, 29.5, B2 - 0.2), (0.0, 6.0, TY - 1.2),
                     (-12.0, 70.0, 12.3), (23.0, 33.0, 10.0), (33.0, 46.0, 8.8)):
    X = X0
    while X < X1:
        Xn = min(X1, X + 4.0)
        decal("M_Streaks", [(X, Ytop - 1.4, 0.02), (Xn, Ytop - 1.4, 0.02), (Xn, Ytop, 0.02), (X, Ytop, 0.02)], ((Xn - X) / 2.0, 1.0))
        X = Xn

# a warm, glowing lane: lanterns low on both facades along the street (the reference street glows)
for X in range(8, 68, 10):
    prop("Lantern_Wall", X + 0.5, street_y(X + 0.5) + 3.1, 0.0, LEFT, light=lamp_light(2.8, 8.5))
    prop("Lantern_Wall", X + 5.5, street_y(X + 5.5) + 3.1, STREET_W, RIGHT, light=lamp_light(2.6, 8.0))

# more greenery around the start (the reference is full of plants)
prop("Ivy_Tall", 2.3, TY - 0.3, 0.0, LEFT)
prop("Ivy_Patch", 6.4, TY + 0.9, 0.0, LEFT, scale=0.8)
prop("Bougainvillea", 2.4, TY + 3.5, 0.0, LEFT, scale=0.7)
prop("FlowerBox_Red", 4.2, TY + 3.2, 0.0, LEFT)
prop("Pot_Small", 4.5, TY + 0.45, 2.3, 0.0)
prop("Bougainvillea", 9.4, B1 + 2.9, 0.0, LEFT)
prop("Ivy_Tall", 14.6, B1 - 0.1, 0.0, LEFT, scale=(1.0, 0.7, 1.0))
prop("FlowerBox_White", 13.5, B1 + 1.0, 0.0, LEFT)

# pigeons: one waits on the terrace parapet so the world reacts right at the start
for X, Y, Zd, r in ((5.8, TY + 0.45, 0.9, 200.0), (10.8, B1 + 1.0, 1.05, 160.0), (37.4, R1 + 0.5, 4.15, 110.0),
                    (38.3, R1 + 0.5, 4.15, 70.0), (44.5, 4.56, 8.5, 20.0), (56.0, CAFE + 2.9, 8.6, 300.0)):
    L["pigeons"].append({"pos": V(X, Y, Zd), "rotY": r})

# fireflies in the gardens, drips from awnings and balconies, ripples in puddles
for X, Y, Zd, rad in ((56.5, CAFE + 1.6, 7.6, 2.5), (37.5, R1 + 1.0, 9.5, 2.0), (-2.0, 11.8, STREET_W + 3.2, 2.5),
                      (85.0, -7.2, 14.0, 4.0), (84.0, -7.2, -12.0, 4.0)):
    L["fireflies"].append({"pos": V(X, Y, Zd), "size": S(rad * 2, 1.6, rad * 2)})
for X, Y, Zd, w in ((25.0, 6.32, 1.55, 3.0), (9.5, B1 - 0.2, 1.1, 3.0), (28.0, B2 - 0.2, 1.2, 3.0),
                    (57.0, CAFE + 2.0, STREET_W + 4.5, 3.0), (47.0, 0.85, 1.5, 3.0)):
    L["drips"].append({"pos": V(X, Y, Zd), "size": S(w, 0.02, 0.1)})
for X, Y, Zd, w, d in ((2.5, TY + 0.01, 1.2, 4.0, 1.8), (28.0, B2 + 0.01, 0.6, 2.6, 1.0), (40.0, R1 + 0.01, 7.5, 5.0, 5.0),
                       (57.0, CAFE + 0.03, 8.0, 5.0, 4.0), (64.0, street_y(64) + 0.03, 2.6, 8.0, 4.0)):
    L["ripples"].append({"pos": V(X, Y, Zd), "size": S(w, 0.01, d)})

# someone watching TV across the street
L["tvLights"].append({"pos": V(2.2, 5.3, STREET_W - 0.6)})

# positional sounds
L["sounds"].append({"clip": "mus_cafe_waltz", "pos": V(57.5, CAFE + 1.5, 10.5), "volume": 0.55, "minDistance": 3.0, "maxDistance": 75.0})
L["sounds"].append({"clip": "amb_lantern_hum", "pos": V(3.1, TY + 2.2, 0.3), "volume": 0.12, "minDistance": 0.4, "maxDistance": 4.0})
L["sounds"].append({"clip": "amb_lantern_hum", "pos": V(33.2, B3 + 2.1, STREET_W - 0.4), "volume": 0.1, "minDistance": 0.4, "maxDistance": 4.0})

# ================================================================== probes, spawn, camera, exit
for (X0, X1, Y0, Y1, Z0, Z1, imp) in ((-0.5, 6.5, 5.6, 9.5, 0.0, 2.6, 2), (6.0, 11.5, 6.0, 10.0, 0.0, 2.0, 2),
                                       (11.0, 23.5, 6.8, 10.0, 0.0, 2.0, 1), (23.0, 30.0, 4.8, 9.0, 0.0, 2.5, 1),
                                       (28.0, 36.5, 3.5, 8.0, 0.0, STREET_W, 1), (35.5, 55.5, 1.0, 8.0, 4.0, 13.0, 1),
                                       (53.5, 60.5, -3.2, 1.0, STREET_W, 11.5, 1), (-12.0, 70.0, -6.0, 6.0, 0.0, STREET_W, 0),
                                       (70.0, 92.0, -8.5, -2.0, -30.0, 40.0, 1)):
    L["reflectionProbes"].append({"pos": V((X0 + X1) / 2, (Y0 + Y1) / 2, (Z0 + Z1) / 2), "size": S(X1 - X0, Y1 - Y0, Z1 - Z0),
                                  "importance": imp})
route = [(-1.0, 6.0, 1.2), (3.0, 6.0, 1.2), (5.8, 6.0, 1.0), (7.0, 6.7, 0.3), (9.5, 7.3, 0.6), (13.0, 7.3, 0.2),
         (16.0, 7.9, 0.3), (19.0, 7.3, 0.2), (23.0, 7.3, 0.2), (25.0, 6.6, 0.8), (28.0, 5.4, 0.6), (31.5, 4.9, 2.6),
         (34.5, 5.2, 4.6), (38.0, 4.6, 6.0), (41.0, 4.6, 8.0), (45.0, 3.1, 7.5), (48.0, 3.1, 8.0), (52.0, 1.7, 7.5),
         (56.5, -0.1, 7.6), (58.6, -1.5, 6.0), (57.0, -3.0, 8.0), (59.0, -4.2, 2.6), (64.0, -4.6, 2.6), (70.0, -5.1, 2.6),
         (74.0, -6.6, 2.6), (80.0, -8.3, 2.6), (86.0, -8.3, 2.6), (90.0, -8.3, 2.6)]
for i in range(len(route) - 1):
    a, b = route[i], route[i + 1]
    n = max(1, int(math.dist(a, b) / 2.0))
    for k in range(n):
        t = k / n
        X, Y, Zd = (a[j] + (b[j] - a[j]) * t for j in range(3))
        for dy in (0.3, 1.6):
            L["lightProbes"].append(V(X, Y + dy, Zd))
for X in range(-8, 92, 4):
    for Zd in (0.8, 2.6, 4.4):
        L["lightProbes"].append(V(X, street_y(X) + 0.5, Zd))

level = {
    "name": "Level01_MoonStreet",
    "moon": {"azimuth": MOON_AZIMUTH_DEG, "elevation": MOON_ELEVATION_DEG, "color": C(0.62, 0.72, 1.0), "intensity": 0.8,
             "quadDistance": 250.0, "quadSize": 9.0},
    "environment": {"ambientSky": C(0.22, 0.29, 0.50), "ambientEquator": C(0.15, 0.16, 0.25),
                    "ambientGround": C(0.10, 0.08, 0.07), "fogColor": C(0.09, 0.12, 0.21), "fogStart": 80.0,
                    "fogEnd": 3500.0},
    "spawn": {"p1": V(1.6, TY + 0.05, 1.2), "p2": V(1.6, TY + 0.05, 0.5), "rotY": 0.0},
    "startCamera": {"pos": V(-1.8, 8.1, 1.7), "lookAt": V(8.2, 5.79, 2.0)},
    "npc": {"model": "Cat_Baron", "pos": npc_pos, "rotY": 180.0, "radius": 2.6},
    "exit": {"pos": V(89.5, -7.6, 2.6), "size": S(3.0, 2.0, 12.0)},
    "sea": {"y": -9.3, "center": V(1100.0, -9.3, 60.0), "size": S(2100.0, 0.0, 2600.0)},
    "background": {"radius": 1450.0, "height": 340.0, "y": -40.0, "arcStart": -100.0, "arcEnd": 100.0},
    **L,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    json.dump(level, f, indent=0, separators=(",", ":"))
print("wrote", os.path.abspath(OUT), {k: len(v) for k, v in L.items()})
