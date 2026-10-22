"""Repaints the hero cat's texture as a Bengal: golden coat, cream belly, dark rosettes with rufous centres.

Run:  python tools/blender/bengal_texture.py <cat.glb> [textures_dir]

Every texel is mapped back to its 3D point on the cat (UV rasterisation), so rosettes are placed on the
body surface (3D Worley noise) and do not stretch across UV seams. The fine fur detail of the original
texture is kept (high-pass of its luminance); its broad tabby stripes are removed. The face keeps the
original detail with only a hue shift, so eyes, nose and whiskers stay intact.
Writes T_CatHero_A.png (Bengal) and keeps the original as T_CatHero_Ginger_A.png (second skin for co-op).
"""
import os
import sys

import bpy
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "CatsGame", "Assets", "_Project", "Art", "Textures")


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def load(src):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    bpy.context.view_layer.update()
    ob = [o for o in bpy.data.objects if o.type == "MESH"][0]
    me = ob.data
    me.calc_loop_triangles()
    mw = ob.matrix_world
    co = np.array([(mw @ v.co)[:] for v in me.vertices])
    mn, mx = co.min(0), co.max(0)
    k = 0.36 / (mx[2] - mn[2])
    co = (co - np.array([(mn[0] + mx[0]) / 2, 0, mn[2]])) * k
    feet = co[co[:, 2] < 0.03]
    co[:, 1] -= (feet[:, 1].min() + feet[:, 1].max()) / 2
    uv_layer = me.uv_layers[0].data
    tris = np.array([t.vertices[:] for t in me.loop_triangles])
    loops = np.array([t.loops[:] for t in me.loop_triangles])
    uvs = np.array([d.uv[:] for d in uv_layer])
    nrm = np.array([(mw.to_3x3() @ v.normal).normalized()[:] for v in me.vertices])
    img = next(i for i in bpy.data.images if i.size[0] > 0)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1, :, :3]  # top row first
    return co, nrm, tris, loops, uvs, px


def rasterise(co, nrm, tris, loops, uvs, w, h):
    """Position / normal map in texture space."""
    pos = np.zeros((h, w, 3), np.float32)
    nor = np.zeros((h, w, 3), np.float32)
    mask = np.zeros((h, w), bool)
    for tri, lp in zip(tris, loops):
        uv = uvs[lp] * np.array([w, h])
        uv[:, 1] = h - uv[:, 1]
        x0, y0 = np.floor(uv.min(0)).astype(int)
        x1, y1 = np.ceil(uv.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1 + 1, w), min(y1 + 1, h)
        if x1 <= x0 or y1 <= y0:
            continue
        ys, xs = np.mgrid[y0:y1, x0:x1] + 0.5
        (ax, ay), (bx, by), (cx, cy) = uv
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9:
            continue
        l1 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
        l2 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den
        l3 = 1 - l1 - l2
        inside = (l1 >= -0.02) & (l2 >= -0.02) & (l3 >= -0.02)
        if not inside.any():
            continue
        L = np.stack([l1, l2, l3], -1)[inside]
        yy, xx = (ys[inside] - 0.5).astype(int), (xs[inside] - 0.5).astype(int)
        pos[yy, xx] = L @ co[tri]
        nor[yy, xx] = L @ nrm[tri]
        mask[yy, xx] = True
    return pos, nor, mask


def worley3d(p, cell, seed):
    """F1 distance (in cell units) of 3D jittered-grid Worley noise, plus a random value per cell."""
    rng = np.random.default_rng(seed)
    table = rng.random((64, 64, 64, 4)).astype(np.float32)
    q = p / cell
    base = np.floor(q).astype(int)
    f1 = np.full(q.shape[:-1], 9.0, np.float32)
    rid = np.zeros(q.shape[:-1], np.float32)
    for dz in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                c = base + np.array([dx, dy, dz])
                r = table[c[..., 0] % 64, c[..., 1] % 64, c[..., 2] % 64]
                fp = c + 0.15 + r[..., :3] * 0.7
                d = np.linalg.norm(q - fp, axis=-1)
                closer = d < f1
                rid = np.where(closer, r[..., 3], rid)
                f1 = np.minimum(f1, d)
    return f1, rid


def noise3(p, freq, seed):
    """Smooth 3D value noise in [0, 1] (trilinear lattice)."""
    rng = np.random.default_rng(seed)
    table = rng.random((32, 32, 32)).astype(np.float32)
    q = p * freq
    i = np.floor(q).astype(int)
    f = q - i
    f = f * f * (3 - 2 * f)
    out = 0.0
    for dz in (0, 1):
        for dy in (0, 1):
            for dx in (0, 1):
                wgt = (f[..., 0] if dx else 1 - f[..., 0]) * (f[..., 1] if dy else 1 - f[..., 1]) * (f[..., 2] if dz else 1 - f[..., 2])
                out = out + wgt * table[(i[..., 0] + dx) % 32, (i[..., 1] + dy) % 32, (i[..., 2] + dz) % 32]
    return out


def main(src, out_dir):
    co, nrm, tris, loops, uvs, px = load(src)
    h, w = px.shape[:2]
    os.makedirs(out_dir, exist_ok=True)
    # Blender keeps byte images in their own (sRGB) encoding, so the pixels are already sRGB
    Image.fromarray((np.clip(px, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(out_dir, "T_CatHero_Ginger_A.png"))
    print("rasterising", len(tris), "triangles into", w, "x", h)
    pos, nor, mask = rasterise(co, nrm, tris, loops, uvs, w, h)

    srgb = np.clip(px, 0, 1)
    lum = srgb.mean(-1)
    blur = np.asarray(Image.fromarray((lum * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5))) / 255.0
    detail = np.clip(lum / np.maximum(blur, 0.05), 0.6, 1.5)

    x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
    nz = nor[..., 2]
    belly = smooth(0.0, -0.75, nz) * smooth(0.2, 0.1, z)
    inner_leg = smooth(0.05, 0.14, z) * 0 + smooth(0.14, 0.04, z) * smooth(0.3, 0.9, np.abs(nor[..., 0])) * 0.5
    back = smooth(0.2, 0.9, nz)
    gold = np.array([0.66, 0.42, 0.17])
    rufous = np.array([0.56, 0.30, 0.10])
    cream = np.array([0.86, 0.76, 0.58])
    base = gold + (rufous - gold) * back[..., None] * 0.6
    cream_k = np.clip(belly + inner_leg, 0, 1)[..., None]
    base = base * (1 - cream_k) + cream * cream_k

    # rosettes (body/legs) and small spots (legs/head); tail gets bands
    head = smooth(-0.13, -0.16, y)
    tail = smooth(0.14, 0.17, y)
    legs = smooth(0.12, 0.06, z) * (1 - tail)
    # irregular, horizontally elongated, partly broken rosettes of varying size
    warp = np.stack([noise3(pos, 55, 11 + k) - 0.5 for k in range(3)], -1) * 0.012
    rp = (pos + warp) * np.array([1.0, 0.62, 1.0])
    f1, rid = worley3d(rp, 0.022, 3)
    size = 0.8 + 0.45 * rid
    fr = f1 / size
    ring = smooth(0.2, 0.27, fr) * smooth(0.46, 0.36, fr)
    core = smooth(0.3, 0.16, fr)
    gaps = smooth(0.38, 0.52, noise3(pos, 140, 21))
    ring *= 0.35 + 0.65 * gaps
    solid = (rid < 0.18).astype(np.float32)            # a few plain spots between rosettes
    spot_f1, _ = worley3d(pos + warp, 0.014, 5)
    spot = smooth(0.38, 0.25, spot_f1)
    amount = (1 - belly * 0.85) * (1 - head) * (1 - tail) * (1 - legs * 0.6)
    dark = np.array([0.16, 0.09, 0.045])
    mid = np.array([0.45, 0.22, 0.07])
    col = base.copy()
    ck = (core * amount * (0.6 + 0.4 * solid))[..., None]
    col = col * (1 - ck * 0.75) + (mid * (1 - solid[..., None]) + dark * solid[..., None]) * (ck * 0.75)
    rk = (ring * amount * (1 - solid) * 0.85)[..., None]
    col = col * (1 - rk) + dark * rk
    sk = (spot * np.clip(legs + head * 0.7, 0, 1) * (1 - belly * 0.6) * 0.75)[..., None]
    col = col * (1 - sk) + dark * sk
    ty = (y - 0.16) / 0.035
    band = smooth(0.25, 0.1, np.abs(ty - np.round(ty))) * tail * smooth(-0.6, 0.6, nz + 0.3)
    col = col * (1 - (band * 0.85)[..., None]) + dark * (band * 0.85)[..., None]
    tip = smooth(0.32, 0.345, y) * tail
    col = col * (1 - tip[..., None]) + dark * tip[..., None]
    col = col * detail[..., None]

    # face: keep the original, only shift ginger towards Bengal gold
    face = head * smooth(0.0, -0.4, nor[..., 1]) * smooth(0.24, 0.29, z) * 0 + head * smooth(0.2, 0.26, z)
    hue_shift = srgb * np.array([0.98, 0.9, 0.78])
    out = col * (1 - face[..., None] * 0.65) + hue_shift * (face[..., None] * 0.65)

    # keep texels outside the UV islands untouched (they are never seen, but avoid seams on mips)
    m = mask.astype(np.float32)
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) / 255.0
    out = out * m[..., None] + srgb * (1 - m[..., None])
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(os.path.join(out_dir, "T_CatHero_A.png"))
    print("wrote", os.path.abspath(os.path.join(out_dir, "T_CatHero_A.png")))


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("-")]
    main(a[0], a[1] if len(a) > 1 else ROOT)
