"""Tiny bmesh-based modelling kit used by make_models.py.

Conventions (Blender side): metres, +Z up, the *front* of a prop faces -Y.
Wall-mounted props have their pivot on the wall plane (y = 0).
After FBX export (bake space transform) Blender -Y becomes Unity +Z.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector


def clear_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)


def get_material(name):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    return mat


class MeshBuilder:
    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")
        self.mats = []

    # ---------------------------------------------------------------- utils
    def _mi(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def face(self, pts, uvs, mat, smooth=False):
        verts = [self.bm.verts.new(Vector(p)) for p in pts]
        f = self.bm.faces.new(verts)
        f.material_index = self._mi(mat)
        f.smooth = smooth
        for loop, uv in zip(f.loops, uvs):
            loop[self.uv].uv = uv
        return f

    @staticmethod
    def box_uv(p, n, scale=1.0):
        ax = max(range(3), key=lambda i: abs(n[i]))
        if ax == 0:
            return (p[1] * scale * (1 if n[0] > 0 else -1), p[2] * scale)
        if ax == 1:
            return (p[0] * scale * (1 if n[1] < 0 else -1), p[2] * scale)
        return (p[0] * scale, p[1] * scale * (1 if n[2] > 0 else -1))

    def poly_boxuv(self, pts, mat, scale=1.0, smooth=False):
        a, b, c = Vector(pts[0]), Vector(pts[1]), Vector(pts[2])
        n = (b - a).cross(c - a)
        if n.length < 1e-9:
            n = Vector((0, 0, 1))
        uvs = [self.box_uv(p, n, scale) for p in pts]
        return self.face(pts, uvs, mat, smooth)

    # ---------------------------------------------------------------- primitives
    def box(self, mn, mx, mat, uv_scale=1.0, skip=(), matrix=None):
        x0, y0, z0 = mn
        x1, y1, z1 = mx
        faces = {
            "-z": [(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)],
            "+z": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
            "-y": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
            "+y": [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)],
            "-x": [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)],
            "+x": [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
        }
        for k, pts in faces.items():
            if k in skip:
                continue
            if matrix is not None:
                pts = [tuple(matrix @ Vector(q)) for q in pts]
            self.poly_boxuv(pts, mat, uv_scale)

    def box_c(self, center, size, mat, uv_scale=1.0, skip=(), matrix=None):
        c, s = Vector(center), Vector(size) * 0.5
        self.box(tuple(c - s), tuple(c + s), mat, uv_scale, skip, matrix)

    def tube(self, path, radius, mat, seg=8, closed=False, cap=True, smooth=True, up=Vector((0, 0, 1)),
             radii=None, uv_len_scale=1.0):
        """Sweep a circle along a polyline."""
        path = [Vector(p) for p in path]
        n = len(path)
        rings = []
        for i, p in enumerate(path):
            if closed:
                t = (path[(i + 1) % n] - path[i - 1])
            else:
                t = path[min(i + 1, n - 1)] - path[max(i - 1, 0)]
            t.normalize()
            ref = up if abs(t.dot(up)) < 0.95 else Vector((1, 0, 0))
            side = t.cross(ref).normalized()
            upv = side.cross(t).normalized()
            r = radii[i] if radii else radius
            rr = r if isinstance(r, tuple) else (r, r)
            rings.append([p + side * math.sin(a) * rr[0] + upv * math.cos(a) * rr[1]
                          for a in (2 * math.pi * k / seg for k in range(seg))])
        lengths = [0.0]
        for i in range(1, n):
            lengths.append(lengths[-1] + (path[i] - path[i - 1]).length)
        count = n if closed else n - 1
        for i in range(count):
            j = (i + 1) % n
            for k in range(seg):
                k2 = (k + 1) % seg
                pts = [rings[i][k], rings[i][k2], rings[j][k2], rings[j][k]]
                u0, u1 = k / seg, (k + 1) / seg
                v0 = lengths[i] * uv_len_scale
                v1 = (lengths[j] if j else lengths[-1] + (path[0] - path[-1]).length) * uv_len_scale
                self.face([tuple(q) for q in pts], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], mat, smooth)
        if cap and not closed:
            for ring, rev in ((rings[0], True), (rings[-1], False)):
                pts = list(reversed(ring)) if rev else ring
                c = sum(pts, Vector()) / len(pts)
                for k in range(seg):
                    a, b = pts[k], pts[(k + 1) % seg]
                    self.face([tuple(c), tuple(a), tuple(b)], [(0.5, 0.5), (0.5, 0.5), (0.5, 0.5)], mat, smooth)

    def loft(self, rings, mat, seg=12, up=Vector((0, 0, 1)), v_scale=1.0, cap=True):
        """rings: [(center, rx, rz)]; u = around (0 on top/spine, .5 belly), v along."""
        path = [Vector(c) for c, _, _ in rings]
        n = len(path)
        frames = []
        for i, p in enumerate(path):
            t = path[min(i + 1, n - 1)] - path[max(i - 1, 0)]
            t.normalize()
            ref = up if abs(t.dot(up)) < 0.95 else Vector((0, 1, 0))
            side = t.cross(ref).normalized()
            upv = side.cross(t).normalized()
            if upv.dot(up) < 0:
                upv, side = -upv, -side
            frames.append((side, upv))
        lengths = [0.0]
        for i in range(1, n):
            lengths.append(lengths[-1] + (path[i] - path[i - 1]).length)
        total = lengths[-1] or 1.0
        grid = []
        for i, (c, rx, rz) in enumerate(rings):
            side, upv = frames[i]
            grid.append([Vector(c) + side * math.sin(2 * math.pi * k / seg) * rx + upv * math.cos(2 * math.pi * k / seg) * rz
                         for k in range(seg + 1)])
        for i in range(n - 1):
            for k in range(seg):
                pts = [grid[i][k], grid[i][k + 1], grid[i + 1][k + 1], grid[i + 1][k]]
                v0, v1 = lengths[i] / total * v_scale, lengths[i + 1] / total * v_scale
                self.face([tuple(q) for q in pts], [(k / seg, v0), ((k + 1) / seg, v0), ((k + 1) / seg, v1), (k / seg, v1)],
                          mat, True)
        if cap:
            for idx, rev in ((0, False), (n - 1, True)):
                ring = grid[idx][:seg]
                c = Vector(rings[idx][0])
                for k in range(seg):
                    a, b = ring[k], ring[(k + 1) % seg]
                    tri = [tuple(c), tuple(b), tuple(a)] if not rev else [tuple(c), tuple(a), tuple(b)]
                    vv = 0 if idx == 0 else v_scale
                    self.face(tri, [(0.5, vv), (k / seg, vv), ((k + 1) / seg, vv)], mat, True)

    def cylinder(self, base, height, r0, r1, mat, seg=12, cap_top=True, cap_bottom=True, smooth=True, uv_scale=1.0):
        b = Vector(base)
        circ = 2 * math.pi * max(r0, r1)
        for k in range(seg):
            a0, a1 = 2 * math.pi * k / seg, 2 * math.pi * (k + 1) / seg
            p0 = b + Vector((math.cos(a0) * r0, math.sin(a0) * r0, 0))
            p1 = b + Vector((math.cos(a1) * r0, math.sin(a1) * r0, 0))
            p2 = b + Vector((math.cos(a1) * r1, math.sin(a1) * r1, height))
            p3 = b + Vector((math.cos(a0) * r1, math.sin(a0) * r1, height))
            u0, u1 = k / seg * circ * uv_scale, (k + 1) / seg * circ * uv_scale
            self.face([tuple(p0), tuple(p1), tuple(p2), tuple(p3)],
                      [(u0, 0), (u1, 0), (u1, height * uv_scale), (u0, height * uv_scale)], mat, smooth)
        for z, r, top in ((0, r0, False), (height, r1, True)):
            if (top and not cap_top) or (not top and not cap_bottom) or r <= 0:
                continue
            pts = [tuple(b + Vector((math.cos(2 * math.pi * k / seg) * r, math.sin(2 * math.pi * k / seg) * r, z)))
                   for k in range(seg)]
            if not top:
                pts.reverse()
            self.face(pts, [((q[0] - b.x) * uv_scale, (q[1] - b.y) * uv_scale) for q in pts], mat, False)

    def sphere(self, center, r, mat, seg=12, rings=8, scale=(1, 1, 1)):
        c = Vector(center)
        sx, sy, sz = scale
        pts = []
        for i in range(rings + 1):
            th = math.pi * i / rings
            row = []
            for k in range(seg + 1):
                ph = 2 * math.pi * k / seg
                row.append(c + Vector((math.sin(th) * math.cos(ph) * r * sx, math.sin(th) * math.sin(ph) * r * sy,
                                       math.cos(th) * r * sz)))
            pts.append(row)
        for i in range(rings):
            for k in range(seg):
                quad = [pts[i][k], pts[i + 1][k], pts[i + 1][k + 1], pts[i][k + 1]]
                uvs = [(k / seg, 1 - i / rings), (k / seg, 1 - (i + 1) / rings), ((k + 1) / seg, 1 - (i + 1) / rings),
                       ((k + 1) / seg, 1 - i / rings)]
                if i == 0:
                    self.face([tuple(quad[0]), tuple(quad[1]), tuple(quad[2])], uvs[:3], mat, True)
                elif i == rings - 1:
                    self.face([tuple(quad[0]), tuple(quad[1]), tuple(quad[3])], [uvs[0], uvs[1], uvs[3]], mat, True)
                else:
                    self.face([tuple(q) for q in quad], uvs, mat, True)

    def quad(self, p0, p1, p2, p3, mat, uv=(0, 0, 1, 1)):
        u0, v0, u1, v1 = uv
        self.face([tuple(p0), tuple(p1), tuple(p2), tuple(p3)], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], mat)

    def card(self, center, width, height, yaw, mat, uv, tilt=0.0, bottom=True):
        """Vertical foliage card. `bottom`: center is the bottom middle."""
        c = Vector(center)
        d = Vector((math.cos(yaw), math.sin(yaw), 0)) * (width / 2)
        up = Vector((0, 0, height))
        n = Vector((-math.sin(yaw), math.cos(yaw), 0))
        up = up + n * (math.sin(tilt) * height)
        base = c if bottom else c - up / 2
        self.quad(base - d, base + d, base + d + up, base - d + up, mat, uv)

    # ---------------------------------------------------------------- output
    def build(self, parent=None, location=(0, 0, 0), collection=None):
        me = bpy.data.meshes.new(self.name)
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-5)
        self.bm.normal_update()
        self.bm.to_mesh(me)
        self.bm.free()
        for name in self.mats:
            me.materials.append(get_material(name))
        ob = bpy.data.objects.new(self.name, me)
        (collection or bpy.context.scene.collection).objects.link(ob)
        ob.location = location
        if parent is not None:
            ob.parent = parent
        return ob


def empty(name, location, parent=None):
    ob = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = location
    ob.empty_display_size = 0.1
    if parent is not None:
        ob.parent = parent
    return ob


def shift_mesh(ob, offset):
    """Move mesh data so the object origin ends up at `offset` (world) without moving geometry."""
    off = Vector(offset)
    ob.data.transform(Matrix.Translation(-off))
    ob.location = ob.location + off


def add_subsurf(ob, levels=1):
    mod = ob.modifiers.new("Subsurf", "SUBSURF")
    mod.levels = levels
    mod.render_levels = levels


def export_fbx(path, objects):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={"MESH", "EMPTY"},
        apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y", bake_space_transform=True,
        use_mesh_modifiers=True, mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False,
        path_mode="STRIP", embed_textures=False)
