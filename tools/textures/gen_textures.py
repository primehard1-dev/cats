"""Generates every texture for level 01 "Moon Street".

Usage:  python3 tools/textures/gen_textures.py [output_dir]

Naming (picked up by the Unity texture postprocessor):
  *_A  albedo (sRGB)          *_N  normal map (OpenGL / Unity)
  *_M  mask (linear): R metallic, G occlusion, A smoothness
  *_E  emission (sRGB)        UI_* sprites
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from texlib import (blur, colorize, fbm, normal_from_height, rng, save_mask,
                    save_rgb, save_rgba, value_noise, worley)

OUT = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else os.path.join(
    os.path.dirname(__file__), "..", "..", "CatsGame", "Assets", "_Project", "Art", "Textures")
os.makedirs(OUT, exist_ok=True)

# Must match tools/level/level01_layout.py (moon position in the sky).
MOON_AZIMUTH_DEG = 24.0    # to the right of +Z (down the street)
MOON_ELEVATION_DEG = 11.0


def p(name):
    return os.path.join(OUT, name)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- terrace tiles
def terrace_tiles(size=2048, tiles=5, seed=1):
    """2 m x 2 m of 0.4 m terracotta tiles, wet after rain, with puddles."""
    r = rng(seed)
    ys, xs = np.mgrid[0:size, 0:size] / size * tiles
    ix, iy = np.floor(xs).astype(int), np.floor(ys).astype(int)
    fx, fy = xs - ix, ys - iy
    edge = np.minimum(np.minimum(fx, 1 - fx), np.minimum(fy, 1 - fy))
    grout = edge < 0.018
    tile_rand = r.random((tiles, tiles, 3))
    tr = tile_rand[iy % tiles, ix % tiles]

    base0 = np.array([0.50, 0.22, 0.13])
    base1 = np.array([0.66, 0.35, 0.21])
    alb = base0 + (base1 - base0) * tr[..., 0:1]
    alb *= (0.85 + 0.25 * tr[..., 1:2])
    wear = fbm(size, size, 6, 6, r)
    alb *= (0.8 + 0.4 * wear)[..., None]
    alb = np.where(grout[..., None], np.array([0.22, 0.19, 0.17]), alb)
    stains = smoothstep(0.55, 0.75, fbm(size, size, 3, 5, r))
    alb *= (1 - 0.25 * stains)[..., None]

    bevel = smoothstep(0.018, 0.06, edge)
    hgt = bevel * 0.8 + 0.08 * fbm(size, size, 40, 4, r) + 0.03 * value_noise(size, size, 300, 300, r)
    chips = (fbm(size, size, 20, 3, r) > 0.68) & (edge < 0.08)
    hgt = np.where(chips, hgt * 0.5, hgt)

    puddle_n = fbm(size, size, 3, 5, r)
    puddle = smoothstep(0.56, 0.6, puddle_n)
    damp = smoothstep(0.42, 0.56, puddle_n)
    water_level = 0.62
    hgt = np.where(hgt < water_level, hgt * (1 - puddle) + water_level * puddle, hgt)

    wet = np.clip(0.55 + 0.45 * damp + grout * 0.3, 0, 1)
    alb *= (1 - 0.3 * wet)[..., None]
    smooth = 0.32 + 0.3 * wet + 0.3 * puddle
    smooth = np.where(grout, 0.85, smooth) - 0.08 * wear
    ao = np.where(grout, 0.55, 1.0) * (0.85 + 0.15 * bevel)

    save_rgb(p("T_TerraceTiles_A.png"), alb)
    save_rgb(p("T_TerraceTiles_N.png"), normal_from_height(hgt, 6))
    save_mask(p("T_TerraceTiles_M.png"), 0, ao, np.clip(smooth, 0, 0.96))


# ---------------------------------------------------------------- plaster
def plaster(size=1024, seed=2):
    """4 m x 4 m of old lime plaster. Neutral, tinted per material."""
    r = rng(seed)
    big = fbm(size, size, 3, 6, r)
    mid = fbm(size, size, 12, 5, r)
    fine = value_noise(size, size, 256, 256, r)
    alb = colorize(big, [0.72, 0.68, 0.62], [0.92, 0.89, 0.83])
    stains = smoothstep(0.58, 0.8, fbm(size, size, 5, 6, r, aspect=0.4))
    alb *= (1 - 0.14 * stains)[..., None]
    patches = smoothstep(0.72, 0.75, fbm(size, size, 4, 6, r))
    alb = alb * (1 - patches[..., None]) + np.array([0.74, 0.7, 0.64]) * patches[..., None] * (0.85 + 0.2 * mid[..., None])
    alb *= (0.95 + 0.08 * fine)[..., None]
    hgt = 0.6 * mid + 0.25 * fine + 0.5 * patches
    smooth = 0.14 + 0.12 * stains + 0.05 * fine
    save_rgb(p("T_Plaster_A.png"), alb)
    save_rgb(p("T_Plaster_N.png"), normal_from_height(hgt, 3))
    save_mask(p("T_Plaster_M.png"), 0, 1 - 0.3 * patches, smooth)


# ---------------------------------------------------------------- stone
def stone(size=1024, seed=3):
    """2 m x 2 m limestone blocks (ledges, parapets, sills, stairs)."""
    r = rng(seed)
    ys, xs = np.mgrid[0:size, 0:size] / size
    rows = 4
    row = np.floor(ys * rows).astype(int)
    off = (row % 2) * 0.25
    bx = (xs + off) * 3
    fx = bx - np.floor(bx)
    fy = ys * rows - row
    joint = (np.minimum(fx, 1 - fx) < 0.012 * 3) | (np.minimum(fy, 1 - fy) < 0.012 * rows)
    block_id = (np.floor(bx).astype(int) % 3) + row * 3
    block_rand = r.random(64)[block_id % 64]
    base = colorize(fbm(size, size, 6, 6, r), [0.55, 0.5, 0.43], [0.78, 0.72, 0.62])
    base *= (0.88 + 0.2 * block_rand)[..., None]
    f1, _, _ = worley(size, size, 60, 60, r)
    pits = smoothstep(0.12, 0.0, f1)
    grime = smoothstep(0.5, 0.85, fbm(size, size, 4, 6, r, aspect=0.5))
    alb = base * (1 - 0.35 * grime)[..., None] * (1 - 0.3 * pits)[..., None]
    alb = np.where(joint[..., None], alb * 0.55, alb)
    hgt = 0.7 - 0.6 * joint - 0.3 * pits + 0.2 * fbm(size, size, 30, 3, r)
    smooth = 0.38 + 0.2 * grime + 0.25 * joint
    save_rgb(p("T_Stone_A.png"), alb)
    save_rgb(p("T_Stone_N.png"), normal_from_height(blur(hgt, 1.0), 5))
    save_mask(p("T_Stone_M.png"), 0, 1 - 0.4 * joint, smooth)


# ---------------------------------------------------------------- cobbles
def cobbles(size=1024, seed=4):
    """3 m x 3 m wet cobblestone street."""
    r = rng(seed)
    f1, f2, cid = worley(size, size, 14, 14, r, jitter=0.7)
    edge = f2 - f1
    gap = smoothstep(0.1, 0.03, edge)
    dome = np.clip(1 - (f1 * 1.4) ** 2, 0, 1)
    hgt = dome * (1 - gap) * 0.9 + 0.1 * fbm(size, size, 30, 3, r)
    col = colorize(cid, [0.28, 0.27, 0.27], [0.5, 0.45, 0.4])
    col *= (0.8 + 0.35 * fbm(size, size, 20, 4, r))[..., None]
    alb = col * (1 - 0.7 * gap)[..., None] * 0.8
    puddle = smoothstep(0.58, 0.62, fbm(size, size, 2, 5, r))
    smooth = 0.52 + 0.35 * gap + 0.35 * puddle
    hgt = hgt * (1 - 0.8 * puddle)
    save_rgb(p("T_Cobble_A.png"), alb * (1 - 0.15 * puddle)[..., None])
    save_rgb(p("T_Cobble_N.png"), normal_from_height(hgt, 7))
    save_mask(p("T_Cobble_M.png"), 0, 1 - 0.5 * gap, np.clip(smooth, 0, 0.95))


# ---------------------------------------------------------------- roof tiles
def roof_tiles(size=1024, seed=5):
    """2 m x 2 m Mediterranean canal tiles. U across slope, V down slope."""
    r = rng(seed)
    ys, xs = np.mgrid[0:size, 0:size] / size
    cols, rows = 10, 5
    cx = xs * cols
    col = np.floor(cx).astype(int)
    fu = cx - col
    ry = ys * rows + (col % 2) * 0.5
    row = np.floor(ry).astype(int)
    fv = ry - row
    profile = np.sin(np.pi * fu) ** 0.7
    hgt = profile * (0.6 + 0.4 * fv)
    lip_shadow = smoothstep(0.08, 0.0, fv)
    tid = (row * 31 + col * 7) % 97
    trand = r.random(97)[tid]
    base = colorize(trand, [0.50, 0.21, 0.12], [0.72, 0.38, 0.22])
    dirt = smoothstep(0.45, 0.8, fbm(size, size, 5, 6, r))
    moss = smoothstep(0.7, 0.85, fbm(size, size, 8, 5, r)) * (1 - profile)
    alb = base * (0.7 + 0.35 * profile)[..., None]
    alb = alb * (1 - 0.4 * dirt)[..., None]
    alb = alb * (1 - moss[..., None]) + np.array([0.16, 0.18, 0.1]) * moss[..., None]
    alb *= (1 - 0.6 * lip_shadow)[..., None]
    gap = (fu < 0.04) | (fu > 0.96)
    alb = np.where(gap[..., None], alb * 0.3, alb)
    smooth = 0.42 + 0.15 * profile - 0.2 * moss
    save_rgb(p("T_RoofTiles_A.png"), alb)
    save_rgb(p("T_RoofTiles_N.png"), normal_from_height(hgt - 0.6 * lip_shadow, 10))
    save_mask(p("T_RoofTiles_M.png"), 0, 1 - 0.5 * lip_shadow - 0.4 * gap, smooth)


# ---------------------------------------------------------------- painted metal
def painted_metal(size=512, seed=6):
    """1 m x 1 m painted metal with grime and rust (AC units, pipes, iron)."""
    r = rng(seed)
    streaks = fbm(size, size, 8, 5, r, aspect=0.15)
    rust = smoothstep(0.68, 0.78, fbm(size, size, 6, 6, r))
    base = np.full((size, size, 3), 0.86) * (0.9 + 0.1 * streaks[..., None])
    grime = smoothstep(0.4, 0.9, streaks)
    alb = base * (1 - 0.35 * grime)[..., None]
    alb = alb * (1 - rust[..., None]) + np.array([0.42, 0.2, 0.09]) * rust[..., None]
    hgt = 0.2 * fbm(size, size, 50, 3, r) + 0.4 * rust
    smooth = 0.5 - 0.3 * rust - 0.15 * grime
    save_rgb(p("T_PaintedMetal_A.png"), alb)
    save_rgb(p("T_PaintedMetal_N.png"), normal_from_height(hgt, 3))
    save_mask(p("T_PaintedMetal_M.png"), 0.15 * (1 - rust), 1, smooth)


# ---------------------------------------------------------------- awning
def awning(size=512, seed=7):
    """Striped canvas. U across width (8 stripes per tile), V along projection."""
    r = rng(seed)
    ys, xs = np.mgrid[0:size, 0:size] / size
    stripe = (np.floor(xs * 8) % 2) == 0
    weave = 0.5 + 0.25 * np.sin(xs * size * np.pi * 0.9) + 0.25 * np.sin(ys * size * np.pi * 0.9)
    dirt = smoothstep(0.5, 0.9, fbm(size, size, 4, 5, r)) * 0.12 + ys * 0.1
    for name, color in (("Blue", [0.1, 0.22, 0.46]), ("Green", [0.1, 0.32, 0.2])):
        alb = np.where(stripe[..., None], np.array(color), np.array([0.88, 0.87, 0.82]))
        alb = alb * (0.92 + 0.08 * weave[..., None]) * (1 - dirt[..., None])
        save_rgb(p(f"T_Awning{name}_A.png"), alb)
    save_rgb(p("T_Fabric_N.png"), normal_from_height(weave, 1.5))


# ---------------------------------------------------------------- shutter
def shutter(w=512, h=1024, seed=8):
    """One louvred shutter leaf (UV 0..1 over the leaf)."""
    r = rng(seed)
    ys, xs = np.mgrid[0:h, 0:w]
    u, v = xs / w, ys / h
    frame = (u < 0.1) | (u > 0.9) | (v < 0.05) | (v > 0.95) | (np.abs(v - 0.5) < 0.02)
    slat = (v * 26) % 1.0
    hgt = np.where(frame, 1.0, 0.3 + 0.6 * slat)
    green = np.array([0.15, 0.3, 0.2])
    alb = np.ones((h, w, 3)) * green * (0.85 + 0.3 * fbm(w, h, 4, 5, r, aspect=2)[..., None])
    worn = smoothstep(0.72, 0.8, fbm(w, h, 6, 6, r, aspect=2))
    alb = alb * (1 - worn[..., None]) + np.array([0.45, 0.33, 0.2]) * worn[..., None]
    alb = np.where(~frame[..., None], alb * (0.55 + 0.45 * slat[..., None]), alb)
    save_rgb(p("T_Shutter_A.png"), alb)
    save_rgb(p("T_Shutter_N.png"), normal_from_height(hgt, 6))
    save_mask(p("T_Shutter_M.png"), 0, np.where(frame, 1, 0.6 + 0.4 * slat), 0.35 - 0.2 * worn)


# ---------------------------------------------------------------- windows
def _room_image(w, h, seed, warmth=1.0, kind=0):
    """Warm interior seen through a window: wall, lamp glow, curtain, furniture."""
    r = rng(seed)
    ys, xs = np.mgrid[0:h, 0:w]
    u, v = xs / w, ys / h
    wall = np.array([0.95, 0.62, 0.3]) * warmth
    lx, ly = 0.3 + 0.4 * r.random(), 0.25
    glow = np.exp(-(((u - lx) * 1.6) ** 2 + ((v - ly) * 1.2) ** 2) * 3.5)
    img = wall * (0.35 + 0.8 * glow[..., None])
    floor = v > 0.78
    img = np.where(floor[..., None], np.array([0.45, 0.2, 0.12]) * (0.5 + 0.5 * glow[..., None]), img)
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    dark = (40, 22, 14)
    if kind == 0:  # chair + picture
        d.rectangle([w * 0.55, h * 0.3, w * 0.75, h * 0.45], outline=(90, 55, 30), width=6)
        d.rectangle([w * 0.2, h * 0.6, w * 0.38, h * 0.66], fill=dark)
        d.rectangle([w * 0.2, h * 0.45, w * 0.24, h * 0.9], fill=dark)
        d.rectangle([w * 0.34, h * 0.62, w * 0.38, h * 0.9], fill=dark)
    elif kind == 1:  # plant + shelf
        d.rectangle([w * 0.6, h * 0.35, w * 0.95, h * 0.38], fill=dark)
        for i in range(5):
            d.rectangle([w * (0.62 + i * 0.06), h * 0.25, w * (0.65 + i * 0.06), h * 0.35], fill=(70 + i * 20, 40, 30))
        d.ellipse([w * 0.12, h * 0.45, w * 0.42, h * 0.8], fill=(30, 45, 20))
        d.rectangle([w * 0.2, h * 0.75, w * 0.34, h * 0.92], fill=(110, 50, 30))
    elif kind == 2:  # hanging lamp + table
        d.line([w * 0.5, 0, w * 0.5, h * 0.2], fill=dark, width=4)
        d.pieslice([w * 0.38, h * 0.15, w * 0.62, h * 0.32], 180, 360, fill=(255, 210, 140))
        d.rectangle([w * 0.25, h * 0.65, w * 0.75, h * 0.7], fill=dark)
        d.rectangle([w * 0.3, h * 0.7, w * 0.34, h * 0.92], fill=dark)
        d.rectangle([w * 0.66, h * 0.7, w * 0.7, h * 0.92], fill=dark)
    else:  # silhouette of a person behind curtain
        d.ellipse([w * 0.55, h * 0.28, w * 0.68, h * 0.42], fill=(70, 38, 22))
        d.rounded_rectangle([w * 0.5, h * 0.4, w * 0.73, h * 0.95], 30, fill=(70, 38, 22))
    im = im.filter(ImageFilter.GaussianBlur(2))
    img = np.asarray(im) / 255.0
    # curtains at both sides
    folds = 0.75 + 0.25 * np.sin(u * 60)
    curtain = (u < 0.18) | (u > 0.82)
    ccol = np.array([0.98, 0.85, 0.62]) * folds[..., None] * (0.6 + 0.6 * glow[..., None])
    img = np.where(curtain[..., None], ccol, img)
    return np.clip(img, 0, 1)


def windows(size=1024):
    q = size // 2
    atlas = np.zeros((size, size, 3))
    for i in range(4):
        y, x = divmod(i, 2)
        atlas[y * q:(y + 1) * q, x * q:(x + 1) * q] = _room_image(q, q, 100 + i, 1.0, i)
    save_rgb(p("T_WindowLit_E.png"), atlas)
    save_rgb(p("T_WindowLit_A.png"), atlas * 0.25)
    r = rng(9)
    dark = colorize(fbm(512, 512, 3, 4, r), [0.03, 0.04, 0.07], [0.09, 0.11, 0.16])
    ys, xs = np.mgrid[0:512, 0:512] / 512
    dark += (0.06 * np.clip(1 - np.abs(xs - ys - 0.2) * 6, 0, 1))[..., None]
    save_rgb(p("T_WindowDark_A.png"), dark)
    interior = _room_image(1024, 1024, 77, 1.05, 0)
    save_rgb(p("T_Interior_E.png"), interior)
    save_rgb(p("T_Interior_A.png"), interior * 0.3)


# ---------------------------------------------------------------- small surfaces
def terracotta(size=512, seed=10):
    r = rng(seed)
    alb = colorize(fbm(size, size, 6, 6, r), [0.48, 0.22, 0.13], [0.68, 0.36, 0.22])
    salt = smoothstep(0.7, 0.8, fbm(size, size, 5, 6, r))
    alb = alb * (1 - salt[..., None]) + np.array([0.75, 0.7, 0.62]) * salt[..., None]
    save_rgb(p("T_Terracotta_A.png"), alb)
    save_mask(p("T_Terracotta_M.png"), 0, 1, 0.3 + 0.1 * salt)


def wood(size=512, seed=11):
    r = rng(seed)
    ys, xs = np.mgrid[0:size, 0:size] / size
    plank = np.floor(xs * 5).astype(int)
    grain = fbm(size, size, 6, 6, r, aspect=0.08)
    prand = r.random(5)[plank % 5]
    alb = colorize(grain, [0.25, 0.16, 0.09], [0.48, 0.33, 0.2]) * (0.8 + 0.3 * prand[..., None])
    gap = ((xs * 5) % 1.0) < 0.03
    alb = np.where(gap[..., None], alb * 0.3, alb)
    save_rgb(p("T_Wood_A.png"), alb)
    save_rgb(p("T_Wood_N.png"), normal_from_height(grain * 0.5 - gap * 0.6, 4))
    save_mask(p("T_Wood_M.png"), 0, np.where(gap, 0.5, 1.0), 0.3 + 0.0 * grain)


def sea_normal(size=512, seed=12):
    r = rng(seed)
    hgt = fbm(size, size, 8, 5, r, gain=0.55) + 0.5 * fbm(size, size, 16, 3, r, aspect=0.5)
    save_rgb(p("T_Sea_N.png"), normal_from_height(hgt, 8))


def laundry(size=256):
    """4x4 atlas of cloth colours."""
    cols = [(0.92, 0.92, 0.9), (0.55, 0.7, 0.88), (0.9, 0.6, 0.65), (0.95, 0.85, 0.45),
            (0.35, 0.45, 0.6), (0.85, 0.85, 0.95), (0.7, 0.3, 0.3), (0.9, 0.75, 0.6),
            (0.6, 0.75, 0.6), (0.3, 0.3, 0.35), (0.95, 0.95, 0.95), (0.75, 0.55, 0.8),
            (0.5, 0.6, 0.75), (0.95, 0.7, 0.4), (0.85, 0.9, 0.95), (0.6, 0.4, 0.3)]
    img = np.zeros((size, size, 3))
    q = size // 4
    ys, xs = np.mgrid[0:q, 0:q]
    for i, c in enumerate(cols):
        y, x = divmod(i, 4)
        tile = np.ones((q, q, 3)) * np.array(c)
        if i % 5 == 3:
            tile *= (0.75 + 0.25 * ((xs // 8) % 2))[..., None]
        img[y * q:(y + 1) * q, x * q:(x + 1) * q] = tile
    save_rgb(p("T_Laundry_A.png"), img)


# ---------------------------------------------------------------- facade for distant houses
def facade_far(size=1024, seed=13):
    """10 m wide x 12 m high facade: 4 floors x 4 windows, some lit."""
    r = rng(seed)
    base = colorize(fbm(size, size, 4, 5, r), [0.75, 0.72, 0.66], [0.92, 0.9, 0.84])
    alb = base.copy()
    emis = np.zeros_like(base)
    px_m = size / 10.0
    py_m = size / 12.0
    room = _room_image(64, 96, 5, 1.0, 1)
    for fl in range(4):
        for wi in range(4):
            cx = (wi + 0.5) * 2.5 * px_m
            top = size - (fl * 3.0 + 2.4) * py_m
            ww, wh = 0.9 * px_m, 1.4 * py_m
            x0, x1 = int(cx - ww / 2), int(cx + ww / 2)
            y0, y1 = int(top), int(top + wh)
            lit = r.random() < 0.38
            if lit:
                rm = np.asarray(Image.fromarray((room * 255).astype(np.uint8)).resize((x1 - x0, y1 - y0))) / 255.0
                alb[y0:y1, x0:x1] = rm * 0.3
                emis[y0:y1, x0:x1] = rm * (0.7 + 0.5 * r.random())
            else:
                alb[y0:y1, x0:x1] = [0.15, 0.27, 0.19] if r.random() < 0.7 else [0.06, 0.07, 0.09]
            sill = int(0.12 * py_m)
            alb[y1:y1 + sill, x0 - 4:x1 + 4] = [0.82, 0.78, 0.7]
        cy = size - int(fl * 3.0 * py_m) - 2
        alb[max(cy - 6, 0):cy, :] *= 0.8
    save_rgb(p("T_FacadeFar_A.png"), alb)
    save_rgb(p("T_FacadeFar_E.png"), emis)


# ---------------------------------------------------------------- cats
def cat_bengal(w=1024, h=512, seed=14):
    """U around the body (0 = spine, 0.5 = belly), V along the part."""
    r = rng(seed)
    ys, xs = np.mgrid[0:h, 0:w]
    u, v = xs / w, ys / h
    belly = 0.5 - 0.5 * np.cos(2 * np.pi * u)  # 0 spine .. 1 belly
    back = np.array([0.72, 0.43, 0.16])
    side = np.array([0.86, 0.58, 0.27])
    cream = np.array([0.95, 0.86, 0.68])
    col = colorize(np.clip(belly * 1.6, 0, 1), back, side)
    col = col * (1 - smoothstep(0.65, 0.95, belly)[..., None]) + cream * smoothstep(0.65, 0.95, belly)[..., None]
    f1, f2, cid = worley(w, h, 26, 10, r, jitter=0.85)
    ring = smoothstep(0.13, 0.18, f1) * smoothstep(0.38, 0.3, f1) * (0.6 + 0.4 * (fbm(w, h, 40, 3, r) > 0.45))
    inner = smoothstep(0.18, 0.1, f1)
    spot_mask = (1 - smoothstep(0.55, 0.85, belly)) * (cid > 0.15)
    col = col * (1 - (ring * spot_mask * 0.8)[..., None]) + np.array([0.12, 0.07, 0.04]) * (ring * spot_mask * 0.8)[..., None]
    col = col * (1 - (inner * spot_mask * 0.35)[..., None]) + np.array([0.5, 0.26, 0.09]) * (inner * spot_mask * 0.35)[..., None]
    spine = smoothstep(0.06, 0.0, np.minimum(u, 1 - u))
    col *= (1 - 0.35 * spine)[..., None]
    fur = fbm(w, h, 64, 3, r, aspect=0.12)
    col *= (0.85 + 0.25 * fur)[..., None]
    save_rgb(p("T_CatBengal_A.png"), col)
    save_rgb(p("T_CatFur_N.png"), normal_from_height(fur, 2))

    r2 = rng(seed + 1)
    g = colorize(np.clip(belly * 1.3, 0, 1), [0.36, 0.38, 0.42], [0.55, 0.57, 0.6])
    g2 = np.asarray(Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)).resize((w // 2, h // 2))) / 255.0
    g2 = g2 * (0.88 + 0.2 * fbm(w // 2, h // 2, 48, 3, r2, aspect=0.15)[..., None])
    save_rgb(p("T_CatGrey_A.png"), g2)


# ---------------------------------------------------------------- foliage (alpha)
def _leaf(d, cx, cy, length, width, ang, color):
    pts = []
    for t in np.linspace(0, 1, 14):
        wv = math.sin(math.pi * t) ** 0.8 * width
        pts.append((t * length, wv))
    for t in np.linspace(1, 0, 14):
        wv = math.sin(math.pi * t) ** 0.8 * width
        pts.append((t * length, -wv))
    ca, sa = math.cos(ang), math.sin(ang)
    d.polygon([(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts], fill=color)


def foliage(size=1024, seed=15):
    """2x2 atlas: ivy | geraniums / bougainvillea | white daisies."""
    r = rng(seed)
    S = size * 2
    q = S // 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def greens(k=1.0):
        g = r.uniform(0.6, 1.1) * k
        return (int(30 * g), int(70 * g + r.uniform(0, 30)), int(25 * g), 255)

    # ivy: dense heart leaves
    for _ in range(900):
        x, y = r.uniform(30, q - 30), r.uniform(30, q - 30)
        _leaf(d, x, y, r.uniform(40, 80), r.uniform(18, 32), r.uniform(0, 6.28), greens(0.9))
    # geraniums
    ox = q
    for _ in range(260):
        x, y = ox + r.uniform(30, q - 30), r.uniform(q * 0.45, q - 20)
        d.ellipse([x - 40, y - 30, x + 40, y + 30], fill=greens(1.1))
    for _ in range(26):
        cx, cy = ox + r.uniform(80, q - 80), r.uniform(60, q * 0.6)
        base = (220, 40, 50) if r.random() < 0.6 else (235, 90, 140)
        for _ in range(40):
            a, rr = r.uniform(0, 6.28), r.uniform(0, 55)
            x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
            s = r.uniform(10, 18)
            k = r.uniform(0.75, 1.1)
            d.ellipse([x - s, y - s, x + s, y + s], fill=(int(base[0] * k), int(base[1] * k), int(base[2] * k), 255))
    # bougainvillea
    oy = q
    for _ in range(300):
        x, y = r.uniform(30, q - 30), oy + r.uniform(30, q - 30)
        _leaf(d, x, y, r.uniform(30, 55), r.uniform(14, 22), r.uniform(0, 6.28), greens(0.8))
    for _ in range(700):
        x, y = r.uniform(30, q - 30), oy + r.uniform(30, q - 30)
        k = r.uniform(0.7, 1.1)
        _leaf(d, x, y, r.uniform(22, 36), r.uniform(14, 20), r.uniform(0, 6.28), (int(200 * k), int(30 * k), int(130 * k), 255))
    # white daisies
    for _ in range(260):
        x, y = q + r.uniform(30, q - 30), oy + r.uniform(q * 0.4, q - 20)
        _leaf(d, x, y, r.uniform(40, 70), r.uniform(12, 20), r.uniform(0, 6.28), greens(1.0))
    for _ in range(90):
        cx, cy = q + r.uniform(50, q - 50), oy + r.uniform(40, q * 0.75)
        for k in range(12):
            a = k / 12 * 6.28
            _leaf(d, cx, cy, 28, 7, a, (245, 245, 238, 255))
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(240, 190, 40, 255))
    im = im.resize((size, size), Image.LANCZOS)
    arr = np.asarray(im).astype(float) / 255.0
    save_rgba(p("T_Foliage_A.png"), arr)

    # palm frond
    W, H = 512, 1024
    pf = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(pf)
    d.line([W, 0, W, H * 2], fill=(60, 70, 30, 255), width=10)
    for i in range(60):
        y = 40 + i * (H * 2 - 80) / 60
        L = (W - 30) * math.sin(math.pi * (0.15 + 0.85 * y / (H * 2))) ** 0.6
        for s in (-1, 1):
            ang = -0.5 if s > 0 else math.pi + 0.5
            _leaf(d, W, y, L, 12, ang, greens(0.95))
    pf = pf.resize((W, H), Image.LANCZOS)
    save_rgba(p("T_PalmFrond_A.png"), np.asarray(pf) / 255.0)

    # cypress: dense dark foliage, opaque, tileable
    c = rng(seed + 3)
    f1, f2, cid = worley(512, 512, 24, 24, c)
    leaf = np.clip(1 - f1 * 1.5, 0, 1)
    cyp = colorize(leaf * (0.6 + 0.4 * cid), [0.02, 0.06, 0.03], [0.13, 0.25, 0.1])
    save_rgb(p("T_Cypress_A.png"), cyp)
    save_rgb(p("T_Cypress_N.png"), normal_from_height(leaf, 4))


# ---------------------------------------------------------------- sky and background
def _moon_dir():
    az, el = math.radians(MOON_AZIMUTH_DEG), math.radians(MOON_ELEVATION_DEG)
    return np.array([math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)])


def sky(w=4096, h=2048, seed=16):
    """Equirect panorama for Unity's Skybox/Panoramic (+Z = down the street)."""
    r = rng(seed)
    ys, xs = np.mgrid[0:h, 0:w]
    u = (xs + 0.5) / w
    v = 1 - (ys + 0.5) / h
    lon = (0.5 - u) * 2 * np.pi
    theta = (1 - v) * np.pi
    dy = np.cos(theta)
    dx = np.sin(theta) * np.cos(lon)
    dz = np.sin(theta) * np.sin(lon)
    el = np.arcsin(np.clip(dy, -1, 1))
    m = _moon_dir()
    cosang = np.clip(dx * m[0] + dy * m[1] + dz * m[2], -1, 1)
    ang = np.arccos(cosang)

    t = np.clip(el / (np.pi / 2), 0, 1) ** 0.45
    zen = np.array([0.012, 0.025, 0.07])
    hor = np.array([0.15, 0.21, 0.36])
    col = hor + (zen - hor) * t[..., None]
    col += np.array([0.25, 0.3, 0.42]) * (np.exp(-(ang / 0.35) ** 2) * 0.5 + np.exp(-(ang / 0.9) ** 2) * 0.18)[..., None]

    # clouds (tileable along u)
    cl = fbm(w, h, 6, 7, r, aspect=0.5)
    band = smoothstep(0.02, 0.12, el) * smoothstep(0.75, 0.35, el)
    dens = smoothstep(0.5, 0.72, cl) * band
    lit = np.exp(-(ang / 0.6) ** 2)
    ccol = np.array([0.05, 0.07, 0.13]) + np.array([0.45, 0.48, 0.55]) * (lit * smoothstep(0.5, 0.62, cl))[..., None]
    col = col * (1 - dens[..., None] * 0.85) + ccol * dens[..., None] * 0.85

    # stars
    stars = r.random((h, w)) > 0.9993
    starv = stars * r.uniform(0.3, 1.0, (h, w)) * smoothstep(0.08, 0.3, el) * (1 - dens) * smoothstep(0.25, 0.6, ang)
    col += starv[..., None] * np.array([0.85, 0.9, 1.0])

    # moon disc (the real bloomy moon is a separate HDR quad in the scene)
    col = np.where((ang < 0.018)[..., None], np.array([0.95, 0.95, 0.9]), col)

    below = el < 0
    col = np.where(below[..., None], np.array([0.02, 0.035, 0.07]), col)
    save_rgb(p("T_SkyNight_A.png"), col)


def far_matte(w=4096, h=1024, seed=17):
    """Mountains and lit coastal towns around the bay. Alpha = silhouette.
    U spans the 200 deg arc in front of the player (left -> right)."""
    r = rng(seed)
    xs = np.arange(w) / w
    ridge = np.zeros(w)
    prof = fbm(w, 1, 6, 6, r)[0]
    # high mountains on the left, low coast on the right, bay in the middle-right
    shape = 0.72 - 0.55 * xs + 0.25 * np.exp(-((xs - 0.12) / 0.1) ** 2)
    shape -= 0.35 * np.exp(-((xs - 0.62) / 0.08) ** 2)
    ridge = np.clip(shape + 0.18 * (prof - 0.5), 0.04, 0.95)
    ys = np.arange(h)[:, None] / h
    height_from_bottom = 1 - ys
    inside = height_from_bottom < ridge[None, :]
    depth = np.clip((ridge[None, :] - height_from_bottom) / np.maximum(ridge[None, :], 1e-3), 0, 1)
    col = np.zeros((h, w, 3))
    col[:] = np.array([0.05, 0.065, 0.11])
    col += np.array([0.07, 0.08, 0.13]) * (1 - depth)[..., None] ** 3
    alpha = inside.astype(float)
    # town lights: dense along the shore, sparse on slopes
    n = 9000
    lx = r.random(n)
    lyf = r.random(n) ** 2.2
    ly = (1 - lyf * ridge[(lx * (w - 1)).astype(int)] * 0.9)
    img = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(img)
    for x, y in zip(lx, ly):
        if r.random() < 0.15:
            continue
        px, py = x * w, y * h - 2
        s = r.uniform(0.8, 2.0)
        k = r.uniform(0.6, 1.0)
        d.ellipse([px - s, py - s, px + s, py + s], fill=(int(255 * k), int(190 * k), int(110 * k)))
    lights = np.asarray(img.filter(ImageFilter.GaussianBlur(0.8))) / 255.0
    lights *= inside[..., None]
    col = col + lights * 1.6
    rgba = np.concatenate([col, alpha[..., None]], axis=-1)
    save_rgba(p("T_FarMatte_A.png"), rgba)


def moon(size=256, seed=18):
    r = rng(seed)
    ys, xs = np.mgrid[0:size, 0:size] / size * 2 - 1
    d = np.sqrt(xs ** 2 + ys ** 2)
    disc = smoothstep(0.92, 0.86, d)
    maria = smoothstep(0.55, 0.7, fbm(size, size, 4, 5, r))
    col = np.ones((size, size, 3)) * (1 - 0.18 * maria)[..., None] * np.array([1.0, 0.98, 0.92])
    save_rgba(p("T_Moon_A.png"), np.concatenate([col, disc[..., None]], axis=-1))


# ---------------------------------------------------------------- gameplay + UI
def paw(size=256):
    S = size * 4
    im = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(im)
    c = S / 2
    d.ellipse([c - 0.26 * S, c - 0.02 * S, c + 0.26 * S, c + 0.36 * S], fill=255)
    for ox, oy in ((-0.3, -0.12), (-0.11, -0.3), (0.11, -0.3), (0.3, -0.12)):
        d.ellipse([c + (ox - 0.09) * S, c + (oy - 0.11) * S, c + (ox + 0.09) * S, c + (oy + 0.11) * S], fill=255)
    core = np.asarray(im.resize((size, size), Image.LANCZOS)) / 255.0
    glow = np.asarray(im.resize((size, size), Image.LANCZOS).filter(ImageFilter.GaussianBlur(10))) / 255.0
    a = np.clip(core + glow * 0.8, 0, 1)
    save_rgba(p("T_PawMarker_A.png"), np.concatenate([np.ones((size, size, 3)), a[..., None]], axis=-1))


def _cat_silhouette(d, cx, cy, s, fill):
    # leaping cat, facing right
    d.ellipse([cx - 0.45 * s, cy - 0.16 * s, cx + 0.25 * s, cy + 0.1 * s], fill=fill)
    d.ellipse([cx + 0.15 * s, cy - 0.3 * s, cx + 0.42 * s, cy - 0.05 * s], fill=fill)
    d.polygon([(cx + 0.2 * s, cy - 0.24 * s), (cx + 0.24 * s, cy - 0.42 * s), (cx + 0.3 * s, cy - 0.27 * s)], fill=fill)
    d.polygon([(cx + 0.31 * s, cy - 0.27 * s), (cx + 0.38 * s, cy - 0.42 * s), (cx + 0.41 * s, cy - 0.22 * s)], fill=fill)
    w = int(0.07 * s)
    d.line([cx + 0.15 * s, cy, cx + 0.48 * s, cy + 0.12 * s], fill=fill, width=w)
    d.line([cx + 0.05 * s, cy + 0.02 * s, cx + 0.35 * s, cy + 0.2 * s], fill=fill, width=w)
    d.line([cx - 0.35 * s, cy + 0.02 * s, cx - 0.62 * s, cy + 0.25 * s], fill=fill, width=w)
    d.line([cx - 0.3 * s, cy + 0.04 * s, cx - 0.5 * s, cy + 0.32 * s], fill=fill, width=w)
    d.arc([cx - 0.95 * s, cy - 0.5 * s, cx - 0.35 * s, cy + 0.1 * s], 300, 40, fill=fill, width=int(0.06 * s))


def ui(size=256):
    S = size * 4

    def finish(im, name):
        a = np.asarray(im.resize((size, size), Image.LANCZOS)) / 255.0
        save_rgba(p(name), np.concatenate([np.ones((size, size, 3)), a[..., None]], axis=-1))

    im = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(im)
    d.ellipse([8, 8, S - 8, S - 8], fill=40, outline=200, width=22)
    finish(im, "UI_JoystickBase.png")

    im = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(im)
    d.ellipse([8, 8, S - 8, S - 8], fill=190)
    finish(im.filter(ImageFilter.GaussianBlur(6)), "UI_JoystickKnob.png")

    im = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(im)
    d.ellipse([8, 8, S - 8, S - 8], fill=40, outline=200, width=22)
    _cat_silhouette(d, S * 0.55, S * 0.55, S * 0.55, 230)
    finish(im, "UI_JumpButton.png")

    im = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=S // 6, fill=255)
    finish(im, "UI_Panel.png")


ALL = [terrace_tiles, plaster, stone, cobbles, roof_tiles, painted_metal, awning, shutter,
       windows, terracotta, wood, sea_normal, laundry, facade_far, cat_bengal, foliage,
       sky, far_matte, moon, paw, ui]

if __name__ == "__main__":
    only = set(sys.argv[2:])
    for fn in ALL:
        if only and fn.__name__ not in only:
            continue
        print("->", fn.__name__, flush=True)
        fn()
    print("textures written to", os.path.abspath(OUT))
