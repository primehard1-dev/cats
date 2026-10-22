"""Builds Blender node materials from materials.json for preview renders (not used by Unity)."""
import json
import os

import bpy

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "CatsGame", "Assets", "_Project")
TEX = os.path.join(ROOT, "Art", "Textures")
MATS = os.path.join(ROOT, "Data", "materials.json")


def _img(name, non_color=False):
    if not name:
        return None
    path = os.path.join(TEX, name + ".png")
    img = bpy.data.images.get(name) or bpy.data.images.load(path)
    img.name = name
    if non_color:
        img.colorspace_settings.name = "Non-Color"
    return img


def setup_materials():
    with open(MATS) as f:
        defs = {d["name"]: d for d in json.load(f)["materials"]}
    for name, d in defs.items():
        if d["shader"] == "skybox":
            continue
        mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(bsdf.outputs[0], out.inputs[0])
        col = d["color"]
        tint = (col["r"], col["g"], col["b"], 1)
        uv = nt.nodes.new("ShaderNodeTexCoord")
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (d["tiling"]["x"], d["tiling"]["y"], 1)
        nt.links.new(uv.outputs["UV"], mapping.inputs["Vector"])

        def tex(img):
            n = nt.nodes.new("ShaderNodeTexImage")
            n.image = img
            nt.links.new(mapping.outputs[0], n.inputs[0])
            return n

        unlit = d["shader"].startswith("unlit")
        alb = _img(d["albedo"])
        base_socket = None
        if alb:
            t = tex(alb)
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            nt.links.new(t.outputs["Color"], mix.inputs[6])
            mix.inputs[7].default_value = tint
            base_socket = mix.outputs[2]
            if d["shader"] in ("litCutout", "unlitCutout", "unlitTransparent"):
                nt.links.new(t.outputs["Alpha"], bsdf.inputs["Alpha"])
        if unlit:
            em = nt.nodes.new("ShaderNodeEmission")
            if base_socket:
                nt.links.new(base_socket, em.inputs["Color"])
            else:
                em.inputs["Color"].default_value = tint
            mixs = nt.nodes.new("ShaderNodeMixShader")
            trans = nt.nodes.new("ShaderNodeBsdfTransparent")
            if alb:
                nt.links.new(t.outputs["Alpha"], mixs.inputs[0])
            else:
                mixs.inputs[0].default_value = 1
            nt.links.new(trans.outputs[0], mixs.inputs[1])
            nt.links.new(em.outputs[0], mixs.inputs[2])
            nt.links.new(mixs.outputs[0], out.inputs[0])
            continue
        if base_socket:
            nt.links.new(base_socket, bsdf.inputs["Base Color"])
        else:
            bsdf.inputs["Base Color"].default_value = tint
        nrm = _img(d["normal"], True)
        if nrm:
            t = tex(nrm)
            nm = nt.nodes.new("ShaderNodeNormalMap")
            nm.inputs["Strength"].default_value = d["normalScale"]
            nt.links.new(t.outputs["Color"], nm.inputs["Color"])
            nt.links.new(nm.outputs[0], bsdf.inputs["Normal"])
        mask = _img(d["mask"], True)
        if mask:
            t = tex(mask)
            inv = nt.nodes.new("ShaderNodeMath")
            inv.operation = "SUBTRACT"
            inv.inputs[0].default_value = 1.0
            nt.links.new(t.outputs["Alpha"], inv.inputs[1])
            nt.links.new(inv.outputs[0], bsdf.inputs["Roughness"])
        else:
            bsdf.inputs["Roughness"].default_value = 1 - d["smoothness"]
        bsdf.inputs["Metallic"].default_value = d["metallic"]
        e = d["emissionColor"]
        estr = max(e["r"], e["g"], e["b"])
        if estr > 0:
            ecol = (e["r"] / estr, e["g"] / estr, e["b"] / estr, 1)
            emi = _img(d["emission"])
            if emi:
                t = tex(emi)
                nt.links.new(t.outputs["Color"], bsdf.inputs["Emission Color"])
            else:
                bsdf.inputs["Emission Color"].default_value = ecol
            bsdf.inputs["Emission Strength"].default_value = estr
    return defs
