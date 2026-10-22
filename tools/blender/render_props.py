"""Renders a contact sheet of every model (Cycles, CPU). For checking the art, not used by Unity.

Run:  python tools/blender/render_props.py out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import make_models  # noqa: E402
from meshkit import clear_scene  # noqa: E402
from preview_materials import setup_materials  # noqa: E402

SKIP = {"Ship", "BellTower", "Lighthouse"}


def main(out):
    clear_scene()
    names = [n for n in make_models.MODELS if n not in SKIP]
    cols = 7
    cell = 2.2
    for i, name in enumerate(names):
        roots = make_models.MODELS[name]()
        r, c = divmod(i, cols)
        for root in roots:
            root.location = Vector((c * cell, r * cell * 1.3, 0)) + root.location
            if name in ("Palm", "Cypress"):
                root.scale = (0.3, 0.3, 0.3)
            if name.startswith("Cat_"):
                root.scale = (3, 3, 3)
            if name == "Awning_3m":
                root.scale = (0.5, 0.5, 0.5)
                root.location.z += 1.0
            if name in ("Lantern_Wall", "Bougainvillea", "AC_Unit"):
                root.location.z += 0.8
    setup_materials()
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = 48
    scn.cycles.use_denoising = True
    scn.render.resolution_x, scn.render.resolution_y = 1600, 1000
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.08, 0.1, 0.16, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    scn.world = world
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 2.5
    so = bpy.data.objects.new("Sun", sun)
    so.rotation_euler = (math.radians(50), 0, math.radians(30))
    scn.collection.objects.link(so)
    rows = math.ceil(len(names) / cols)
    cx, cy = (cols - 1) * cell / 2, (rows - 1) * cell * 1.3 / 2
    cam = bpy.data.cameras.new("Cam")
    cam.type = "ORTHO"
    cam.ortho_scale = cols * cell * 1.05
    co = bpy.data.objects.new("Cam", cam)
    co.location = (cx, cy - 14, 12)
    co.rotation_euler = (math.radians(50), 0, 0)
    scn.collection.objects.link(co)
    scn.camera = co
    ground = bpy.data.meshes.new("G")
    ground.from_pydata([(-5, -5, 0), (40, -5, 0), (40, 30, 0), (-5, 30, 0)], [], [(0, 1, 2, 3)])
    go = bpy.data.objects.new("G", ground)
    gm = bpy.data.materials.new("Ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.25, 0.25, 0.27, 1)
    ground.materials.append(gm)
    scn.collection.objects.link(go)
    scn.render.filepath = out
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main(sys.argv[1])
