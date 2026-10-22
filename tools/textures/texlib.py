"""Small numpy toolkit for procedural, tileable PBR textures."""
import numpy as np
from PIL import Image


def rng(seed):
    return np.random.default_rng(seed)


def _smooth(t):
    return t * t * (3.0 - 2.0 * t)


def value_noise(w, h, fx, fy, r):
    """Tileable value noise with fx x fy lattice cells over the image."""
    grid = r.random((fy, fx))
    xs = np.arange(w) * fx / w
    ys = np.arange(h) * fy / h
    x0 = np.floor(xs).astype(int)
    y0 = np.floor(ys).astype(int)
    tx = _smooth(xs - x0)[None, :]
    ty = _smooth(ys - y0)[:, None]
    x1 = (x0 + 1) % fx
    y1 = (y0 + 1) % fy
    x0 %= fx
    y0 %= fy
    a = grid[np.ix_(y0, x0)]
    b = grid[np.ix_(y0, x1)]
    c = grid[np.ix_(y1, x0)]
    d = grid[np.ix_(y1, x1)]
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


def fbm(w, h, base, octaves, r, gain=0.5, aspect=1.0):
    total = np.zeros((h, w))
    amp, norm = 1.0, 0.0
    f = base
    for _ in range(octaves):
        fx = max(1, int(round(f)))
        fy = max(1, int(round(f * aspect)))
        total += amp * value_noise(w, h, fx, fy, r)
        norm += amp
        amp *= gain
        f *= 2
    return total / norm


def worley(w, h, cells_x, cells_y, r, jitter=0.9):
    """Tileable Worley noise. Returns (F1, F2, cell id) in cell-size units."""
    pts = r.random((cells_y, cells_x, 2)) * jitter + (1 - jitter) / 2
    ids = r.random((cells_y, cells_x))
    xs = np.arange(w) * cells_x / w
    ys = np.arange(h) * cells_y / h
    X, Y = np.meshgrid(xs, ys)
    cx = np.floor(X).astype(int)
    cy = np.floor(Y).astype(int)
    f1 = np.full((h, w), 9.0)
    f2 = np.full((h, w), 9.0)
    cid = np.zeros((h, w))
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            nx = cx + dx
            ny = cy + dy
            p = pts[ny % cells_y, nx % cells_x]
            px = nx + p[..., 0]
            py = ny + p[..., 1]
            d = np.sqrt((X - px) ** 2 + (Y - py) ** 2)
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))
            cid = np.where(closer, ids[ny % cells_y, nx % cells_x], cid)
            f1 = np.where(closer, d, f1)
    return f1, f2, cid


def normal_from_height(hgt, strength):
    dx = (np.roll(hgt, -1, axis=1) - np.roll(hgt, 1, axis=1)) * 0.5
    dy = (np.roll(hgt, -1, axis=0) - np.roll(hgt, 1, axis=0)) * 0.5
    nx = -dx * strength
    ny = dy * strength  # OpenGL / Unity convention (green up)
    nz = np.ones_like(hgt)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([nx / l, ny / l, nz / l], axis=-1)
    return n * 0.5 + 0.5


def lerp(a, b, t):
    t = np.asarray(t)
    if np.ndim(a) and np.ndim(t) == 2 and np.ndim(a) != 2:
        t = t[..., None]
    return a + (b - a) * t


def colorize(t, c0, c1):
    c0 = np.array(c0, dtype=float)
    c1 = np.array(c1, dtype=float)
    return c0 + (c1 - c0) * t[..., None]


def blur(arr, radius):
    """Separable Gaussian blur with wrap-around (keeps textures tileable)."""
    k = int(radius * 3) + 1
    xs = np.arange(-k, k + 1)
    w = np.exp(-(xs ** 2) / (2 * radius * radius))
    w /= w.sum()
    out = np.zeros_like(arr, dtype=float)
    for o, wt in zip(xs, w):
        out += wt * np.roll(arr, o, axis=1)
    res = np.zeros_like(out)
    for o, wt in zip(xs, w):
        res += wt * np.roll(out, o, axis=0)
    return res


def save_rgb(path, rgb):
    img = np.clip(rgb, 0, 1)
    Image.fromarray((img * 255 + 0.5).astype(np.uint8), "RGB").save(path, optimize=True)


def save_rgba(path, rgba):
    img = np.clip(rgba, 0, 1)
    Image.fromarray((img * 255 + 0.5).astype(np.uint8), "RGBA").save(path, optimize=True)


def save_mask(path, metal, ao, smooth):
    """Unity URP mask: R metallic, G occlusion, B unused, A smoothness."""
    h, w = smooth.shape
    m = np.zeros((h, w, 4))
    m[..., 0] = metal
    m[..., 1] = ao
    m[..., 3] = smooth
    save_rgba(path, m)


def save_gray(path, g):
    Image.fromarray((np.clip(g, 0, 1) * 255 + 0.5).astype(np.uint8), "L").save(path, optimize=True)
