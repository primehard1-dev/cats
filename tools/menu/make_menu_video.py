"""Main-menu background: the reference picture turned into a seamless living-photo loop (cinemagraph).

Usage:  python tools/menu/make_menu_video.py [out_dir] [--preview]
Writes  menu_loop.mp4 (1280x720, H.264, 24 fps, seamless loop) and menu_poster.jpg (first frame).

Everything moves with a period that divides the loop length, so the loop has no seam:
flickering lanterns and garland bulbs, glowing paw marker, twinkling stars, breathing clouds,
moon glow, sea sparkles and moon path, wet tiles shimmer, cat tail sway, swaying plants,
floating dust and fireflies, slow camera drift.
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
SRC = os.path.join(ROOT, "docs", "reference", "level-01-concept.jpg")
OUT = os.path.join(ROOT, "CatsGame", "Assets", "_Project", "Art", "Menu")

W, H = 1280, 720
FPS = 24
T = 8.0                      # loop length, seconds
N = int(T * FPS)
S = W / 1080.0               # reference (1080x606) -> video scale
rng = np.random.default_rng(11)


def P(x, y):
    """Reference pixel coordinates -> video coordinates."""
    return x * S, y * (H / 606.0)


def periodic(t, k, phase=0.0):
    """Sine with k whole cycles per loop."""
    return math.sin(2 * math.pi * (k * t / T) + phase)


def flicker(t, seed, amount):
    s = sum(periodic(t, k, seed * (k + 1.7)) / k for k in (3, 5, 7, 11))
    return 1.0 + amount * s / 1.7


# ------------------------------------------------------------------ base image
def load_base():
    im = Image.open(SRC).convert("RGB").resize((W, H), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=60, threshold=2))
    a = np.asarray(im).astype(np.float32) / 255.0
    # remove the on-screen joystick and jump button of the concept screenshot
    for (cx, cy, r, sx, sy) in ((93, 519, 62, 0, -118), (990, 509, 52, -4, -112)):
        a = patch(a, *P(cx, cy), r * S, sx * S, sy * S)
    return a


def patch(a, cx, cy, r, dx, dy):
    """Copy a nearby region over a circle with a feathered edge (simple exemplar inpainting)."""
    ys, xs = np.mgrid[0:H, 0:W]
    d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    m = np.clip((r * 1.25 - d) / (r * 0.3), 0, 1)[..., None]
    src = np.roll(np.roll(a, -int(dy), axis=0), -int(dx), axis=1)
    src = np.asarray(Image.fromarray((src * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))) / 255.0
    return a * (1 - m) + src * m


def gauss_sprite(radius):
    r = int(radius * 3)
    ys, xs = np.mgrid[-r:r + 1, -r:r + 1]
    return np.exp(-(xs ** 2 + ys ** 2) / (2 * radius ** 2)).astype(np.float32)


def add_sprite(img, x, y, sprite, color, k):
    r = sprite.shape[0] // 2
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(0, x - r), max(0, y - r), min(W, x + r + 1), min(H, y + r + 1)
    if x0 >= x1 or y0 >= y1:
        return
    sp = sprite[y0 - (y - r):y1 - (y - r), x0 - (x - r):x1 - (x - r)]
    img[y0:y1, x0:x1] += sp[..., None] * np.asarray(color, np.float32) * k


# ------------------------------------------------------------------ masks
def masks(base):
    ys, xs = np.mgrid[0:H, 0:W] / np.array([H, W])[:, None, None] if False else np.mgrid[0:H, 0:W]
    r, g, b = base[..., 0], base[..., 1], base[..., 2]
    lum = base.max(axis=2)
    sky = ((b > r + 0.06) & (lum < 0.5) & (ys < P(0, 118)[1]) & (xs > P(585, 0)[0])).astype(np.float32)
    sky = blur(sky, 3)
    sx0, sy0 = P(760, 118)
    sx1, sy1 = P(965, 212)
    sea = ((b > r) & (xs > sx0) & (xs < sx1) & (ys > sy0) & (ys < sy1) & (lum < 0.6)).astype(np.float32)
    sea = blur(sea, 2)
    tx0, ty0 = P(225, 355)
    tx1, ty1 = P(700, 606)
    wet = ((lum > 0.5) & (r > b + 0.1) & (xs > tx0) & (xs < tx1) & (ys > ty0)).astype(np.float32)
    wet = blur(wet, 1.5)
    green = ((g > r * 0.95) & (g > b) & (lum < 0.7)).astype(np.float32)
    return sky, sea, wet, green


def blur(m, radius):
    return np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius))) / 255.0


def wrap_noise(w, h, cells, seed):
    """Tileable smooth noise in [0,1]."""
    r = np.random.default_rng(seed)
    total = np.zeros((h, w), np.float32)
    amp = 1.0
    for o in range(5):
        c = cells * 2 ** o
        grid = r.random((max(2, int(c * h / w)), c)).astype(np.float32)
        layer = np.asarray(Image.fromarray((grid * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)) / 255.0
        total += layer * amp
        amp *= 0.5
    total -= total.min()
    return total / total.max()


# ------------------------------------------------------------------ warps (tail, plants)
def warp_x(img, dx):
    """Horizontal displacement field (pixels) with bilinear sampling."""
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    sx = np.clip(xs - dx, 0, W - 1.001)
    x0 = np.floor(sx).astype(int)
    f = (sx - x0)[..., None]
    yi = ys.astype(int)
    return img[yi, x0] * (1 - f) + img[yi, x0 + 1] * f


# ------------------------------------------------------------------ main
def main(out_dir, preview=False):
    os.makedirs(out_dir, exist_ok=True)
    base = load_base()
    sky, sea, wet, green = masks(base)
    clouds_a = wrap_noise(W, H, 6, 3)
    clouds_b = wrap_noise(W, H, 6, 4)
    sea_noise = wrap_noise(W, H, 40, 5)
    tile_noise = wrap_noise(W, H, 30, 6)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)

    warm = (1.0, 0.62, 0.3)
    glows = [  # (x, y, radius px, intensity, colour)  in reference coordinates
        (238, 58, 30, 0.55, warm), (238, 58, 9, 0.6, (1.0, 0.85, 0.6)), (392, 92, 18, 0.35, warm),
        (614, 113, 12, 0.3, warm), (757, 350, 14, 0.3, warm), (838, 382, 14, 0.3, warm),
        (873, 466, 16, 0.35, warm), (48, 100, 40, 0.18, warm), (1068, 300, 22, 0.2, warm),
    ]
    paw = (515, 243)
    moon = (826, 25)
    ship = (850, 128)
    # garland bulbs: parabola between the two ends of the string lights
    gx0, gy0, gx1, gy1 = 703, 162, 952, 112
    bulbs = []
    for i in range(22):
        tt = i / 21
        bulbs.append((gx0 + (gx1 - gx0) * tt, gy0 + (gy1 - gy0) * tt + 9 * 4 * tt * (1 - tt), rng.random() * 6))
    sky_idx = np.argwhere(sky > 0.8)
    stars = sky_idx[rng.choice(len(sky_idx), 45, replace=False)] if len(sky_idx) > 50 else []
    star_phase = rng.random(len(stars)) * 6.28
    star_k = rng.integers(2, 7, len(stars))
    # dust motes near the lanterns and fireflies in the plants
    dust = [(rng.uniform(150, 520), rng.uniform(20, 330), rng.uniform(0, 6.28), rng.integers(1, 3)) for _ in range(26)]
    flies = [(rng.uniform(20, 300), rng.uniform(380, 590), rng.uniform(0, 6.28), rng.integers(1, 3)) for _ in range(10)]

    spr_big = {}
    tail_box = P(325, 415) + P(400, 540)
    plant_mask = green * np.clip((P(300, 0)[0] - xs) / 80, 0, 1) * np.clip((ys - P(0, 380)[1]) / 40, 0, 1)
    flower_mask = green * ((xs > P(150, 0)[0]) & (xs < P(330, 0)[0]) & (ys > P(0, 95)[1]) & (ys < P(0, 215)[1]))

    exe = None
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        exe = "ffmpeg"
    mp4 = os.path.join(out_dir, "menu_loop.mp4")
    proc = None
    if not preview:
        proc = subprocess.Popen([exe, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                 "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-profile:v", "main",
                                 "-preset", "slow", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4],
                                stdin=subprocess.PIPE)
    frames = [0, N // 4, N // 2] if preview else range(N)
    for fi in frames:
        t = fi / FPS
        img = base.copy()

        # cat tail sways, plants breathe in the breeze
        tx0, ty0, tx1, ty1 = tail_box
        wy = np.clip((ys - ty0) / (ty1 - ty0), 0, 1) ** 1.6
        wx = np.clip(1 - np.abs(xs - (tx0 + tx1) / 2) / ((tx1 - tx0) / 2 + 1e-3), 0, 1) ** 0.7
        inside = (ys > ty0) & (ys < ty1 + 10)
        dx = 7.0 * S * (0.7 * periodic(t, 2) + 0.3 * periodic(t, 5, 1.0)) * wy * wx * inside
        dx += 2.2 * S * np.sin(ys * 0.035 + 2 * math.pi * 3 * t / T) * plant_mask
        dx += 1.4 * S * np.sin(ys * 0.05 + 2 * math.pi * 2 * t / T + 1.3) * flower_mask
        img = warp_x(img, dx)

        # clouds breathe and drift a little (periodic), only over the sky
        drift = 18 * S * periodic(t, 1)
        ca = np.roll(clouds_a, int(drift), axis=1)
        cb = np.roll(clouds_b, int(-drift), axis=1)
        mixk = 0.5 + 0.5 * periodic(t, 1, 0.7)
        cl = np.clip((ca * mixk + cb * (1 - mixk) - 0.55) * 2.2, 0, 1) * sky
        img = img * (1 - cl[..., None] * 0.25) + np.array([0.33, 0.38, 0.5], np.float32) * cl[..., None] * 0.25

        # sea sparkle and moon path
        sh = np.roll(sea_noise, int(26 * S * t / T) * 1, axis=1)
        sparkle = np.clip((sh - 0.72) * 6, 0, 1) * sea
        path = np.exp(-((xs - P(moon[0] + 4, 0)[0]) / (14 * S)) ** 2) * sea
        img += (sparkle * 0.35 + path * 0.12 * (0.7 + 0.3 * np.roll(sea_noise, int(-40 * S * t / T), axis=0)))[..., None] * \
            np.array([0.8, 0.85, 1.0], np.float32)

        # wet tiles shimmer
        tn = np.roll(np.roll(tile_noise, int(30 * S * t / T), axis=1), int(15 * S * t / T), axis=0)
        img *= (1 + wet * (tn - 0.5) * 0.35)[..., None]

        # lights
        for i, (x, y, r, k, c) in enumerate(glows):
            key = int(r * S)
            if key not in spr_big:
                spr_big[key] = gauss_sprite(r * S)
            add_sprite(img, *P(x, y), spr_big[key], c, k * flicker(t, i + 1, 0.12))
        if 4 not in spr_big:
            spr_big[4] = gauss_sprite(4 * S)
            spr_big[60] = gauss_sprite(60 * S)
            spr_big[2] = gauss_sprite(0.9 * S)
            spr_big[18] = gauss_sprite(18 * S)
        for i, (x, y, ph) in enumerate(bulbs):
            add_sprite(img, *P(x, y), spr_big[4], (1.0, 0.8, 0.5), 0.35 * (0.75 + 0.25 * periodic(t, 3 + i % 4, ph)))
        add_sprite(img, *P(*paw), spr_big[18], (0.2, 0.9, 1.0), 0.28 * (0.6 + 0.4 * periodic(t, 2)))
        add_sprite(img, *P(*moon), spr_big[60], (0.55, 0.62, 0.85), 0.12 * (0.9 + 0.1 * periodic(t, 1)))
        add_sprite(img, *P(*ship), spr_big[4], (1.0, 0.9, 0.7), 0.25 * (0.8 + 0.2 * periodic(t, 4)))
        for (yy, xx), ph, k in zip(stars, star_phase, star_k):
            add_sprite(img, xx, yy, spr_big[2], (0.9, 0.95, 1.0), 0.8 * max(0.0, periodic(t, int(k), ph)) ** 2)

        # floating dust and fireflies (closed periodic paths)
        for (x, y, ph, k) in dust:
            px = x + 14 * periodic(t, int(k), ph)
            py = y + 10 * periodic(t, int(k), ph + 1.3) - 4 * periodic(t, 1, ph)
            add_sprite(img, *P(px, py), spr_big[2], (1.0, 0.85, 0.6), 0.5 * (0.5 + 0.5 * periodic(t, 2, ph)))
        for (x, y, ph, k) in flies:
            px = x + 22 * periodic(t, int(k), ph)
            py = y + 12 * periodic(t, int(k) + 1, ph * 1.7)
            add_sprite(img, *P(px, py), spr_big[4], (0.75, 1.0, 0.35), 0.45 * max(0.0, periodic(t, 3, ph)) ** 3)

        # slow camera drift (Ken Burns, periodic) + vignette
        z = 1.035 + 0.012 * periodic(t, 1)
        ox = 6 * periodic(t, 1, 0.5)
        oy = 3 * periodic(t, 1, 2.0)
        out = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
        cw, ch = W / z, H / z
        left = (W - cw) / 2 + ox
        top = (H - ch) / 2 + oy
        out = out.transform((W, H), Image.EXTENT, (left, top, left + cw, top + ch), Image.BICUBIC)
        arr = np.asarray(out).astype(np.float32) / 255.0
        v = 1 - 0.35 * (((xs / W - 0.5) * 1.6) ** 2 + ((ys / H - 0.5) * 1.9) ** 2)
        arr *= np.clip(v, 0.55, 1)[..., None]
        frame = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
        if fi == 0:
            Image.fromarray(frame).save(os.path.join(out_dir, "menu_poster.jpg"), quality=90)
        if preview:
            Image.fromarray(frame).save(os.path.join(out_dir, f"preview_{fi:03d}.jpg"), quality=90)
        else:
            proc.stdin.write(frame.tobytes())
        if fi % 24 == 0:
            print(f"frame {fi}/{N}", flush=True)
    if proc:
        proc.stdin.close()
        proc.wait()
        print("wrote", os.path.abspath(mp4), os.path.getsize(mp4) // 1024, "KB")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    main(a[0] if a and a[0] else OUT, "--preview" in sys.argv)
