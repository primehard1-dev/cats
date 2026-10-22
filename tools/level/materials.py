"""Material library shared by the Unity builder and the Blender preview.

Writes CatsGame/Assets/_Project/Data/materials.json.
UVs of level blocks and hard-surface props are in metres, so `tiling` = 1 / texture size in metres.
Colours are linear; emission values above 1 are HDR (they drive bloom).
"""
import json
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "CatsGame", "Assets", "_Project", "Data", "materials.json")


def m(name, shader="lit", albedo="", normal="", mask="", emission="", color=(1, 1, 1),
      tiling=(1, 1), smoothness=0.3, metallic=0.0, normal_scale=1.0, emission_color=(0, 0, 0),
      cutoff=0.0, double_sided=False, alpha=1.0):
    return {
        "name": name, "shader": shader,
        "albedo": albedo, "normal": normal, "mask": mask, "emission": emission,
        "color": {"r": color[0], "g": color[1], "b": color[2], "a": alpha},
        "tiling": {"x": tiling[0], "y": tiling[1]},
        "smoothness": smoothness, "metallic": metallic, "normalScale": normal_scale,
        "emissionColor": {"r": emission_color[0], "g": emission_color[1], "b": emission_color[2], "a": 1},
        "cutoff": cutoff, "doubleSided": double_sided,
    }


WARM = (1.0, 0.62, 0.3)


def scaled(c, k):
    return tuple(x * k for x in c)


def tex(base):
    return dict(albedo=f"T_{base}_A", normal=f"T_{base}_N", mask=f"T_{base}_M")


MATERIALS = [
    m("M_TerraceTiles", tiling=(0.5, 0.5), **tex("TerraceTiles")),
    m("M_Plaster_Ochre", color=(1.0, 0.72, 0.42), tiling=(0.25, 0.25), **tex("Plaster")),
    m("M_Plaster_Terracotta", color=(0.9, 0.5, 0.36), tiling=(0.25, 0.25), **tex("Plaster")),
    m("M_Plaster_Pink", color=(0.95, 0.66, 0.6), tiling=(0.25, 0.25), **tex("Plaster")),
    m("M_Plaster_Cream", color=(1.0, 0.88, 0.7), tiling=(0.25, 0.25), **tex("Plaster")),
    m("M_Plaster_Yellow", color=(1.0, 0.8, 0.48), tiling=(0.25, 0.25), **tex("Plaster")),
    m("M_Stone", tiling=(0.5, 0.5), **tex("Stone")),
    m("M_Cobble", tiling=(1 / 3, 1 / 3), **tex("Cobble")),
    m("M_RoofTiles", tiling=(0.5, 0.5), **tex("RoofTiles")),
    m("M_PaintedMetal", color=(0.8, 0.8, 0.78), **tex("PaintedMetal")),
    m("M_MetalDark", color=(0.22, 0.22, 0.23), **tex("PaintedMetal")),
    m("M_Iron", color=(0.045, 0.045, 0.05), **tex("PaintedMetal")),
    m("M_Pipe", color=(0.4, 0.38, 0.36), **tex("PaintedMetal")),
    m("M_AwningBlue", albedo="T_AwningBlue_A", normal="T_Fabric_N", smoothness=0.2, double_sided=True),
    m("M_AwningGreen", albedo="T_AwningGreen_A", normal="T_Fabric_N", smoothness=0.2, double_sided=True),
    m("M_Shutter", **tex("Shutter")),
    m("M_WindowLit", albedo="T_WindowLit_A", emission="T_WindowLit_E", smoothness=0.9,
      emission_color=scaled((1.0, 0.8, 0.55), 2.0)),
    m("M_WindowDark", albedo="T_WindowDark_A", smoothness=0.92),
    m("M_Interior", albedo="T_Interior_A", emission="T_Interior_E", smoothness=0.9,
      emission_color=scaled((1.0, 0.82, 0.6), 1.8)),
    m("M_LanternGlass", color=(1.0, 0.85, 0.6), smoothness=0.8, emission_color=scaled(WARM, 7.0)),
    m("M_Bulb", color=(1.0, 0.9, 0.7), smoothness=0.8, emission_color=scaled((1.0, 0.72, 0.4), 9.0)),
    m("M_Terracotta", albedo="T_Terracotta_A", mask="T_Terracotta_M"),
    m("M_Wood", **tex("Wood")),
    m("M_WoodDark", color=(0.35, 0.3, 0.28), **tex("Wood")),
    m("M_Foliage", albedo="T_Foliage_A", shader="litCutout", cutoff=0.45, smoothness=0.25, double_sided=True),
    m("M_PalmFrond", albedo="T_PalmFrond_A", shader="litCutout", cutoff=0.45, smoothness=0.2, double_sided=True),
    m("M_PalmTrunk", albedo="T_Wood_A", normal="T_Wood_N", color=(0.62, 0.52, 0.42), smoothness=0.15),
    m("M_Cypress", albedo="T_Cypress_A", normal="T_Cypress_N", smoothness=0.12),
    m("M_Laundry", albedo="T_Laundry_A", smoothness=0.08, double_sided=True),
    m("M_CatBengal", albedo="T_CatBengal_A", normal="T_CatFur_N", smoothness=0.32, normal_scale=0.6),
    m("M_CatGrey", albedo="T_CatGrey_A", normal="T_CatFur_N", smoothness=0.3, normal_scale=0.6),
    m("M_CatEye", color=(0.32, 0.5, 0.12), smoothness=0.97, emission_color=(0.02, 0.04, 0.01)),
    m("M_CatEyeCopper", color=(0.75, 0.42, 0.08), smoothness=0.97, emission_color=(0.04, 0.02, 0.0)),
    m("M_CatNose", color=(0.42, 0.2, 0.2), smoothness=0.6),
    m("M_PawMarker", shader="unlitTransparent", albedo="T_PawMarker_A", color=(0.25, 1.6, 1.7), alpha=0.9),
    m("M_Sea", normal="T_Sea_N", color=(0.012, 0.03, 0.06), tiling=(0.08, 0.08), smoothness=0.95,
      normal_scale=0.5),
    m("M_FarMatte", shader="unlitCutout", albedo="T_FarMatte_A", color=(1.6, 1.6, 1.6), cutoff=0.5),
    m("M_Moon", shader="unlitCutout", albedo="T_Moon_A", color=(3.2, 3.1, 2.8), cutoff=0.5),
    m("M_FacadeFar", albedo="T_FacadeFar_A", emission="T_FacadeFar_E", tiling=(0.1, 1 / 12),
      smoothness=0.15, emission_color=scaled((1.0, 0.78, 0.5), 2.2)),
    m("M_FacadeFar_Ochre", albedo="T_FacadeFar_A", emission="T_FacadeFar_E", tiling=(0.1, 1 / 12), color=(1.0, 0.76, 0.5),
      smoothness=0.15, emission_color=scaled((1.0, 0.78, 0.5), 2.2)),
    m("M_FacadeFar_Pink", albedo="T_FacadeFar_A", emission="T_FacadeFar_E", tiling=(0.1, 1 / 12), color=(0.96, 0.7, 0.64),
      smoothness=0.15, emission_color=scaled((1.0, 0.78, 0.5), 2.2)),
    m("M_FacadeFar_Terracotta", albedo="T_FacadeFar_A", emission="T_FacadeFar_E", tiling=(0.1, 1 / 12),
      color=(0.88, 0.52, 0.4), smoothness=0.15, emission_color=scaled((1.0, 0.78, 0.5), 2.2)),
    m("M_ShipHull", albedo="T_PaintedMetal_A", color=(0.86, 0.87, 0.9), smoothness=0.5),
    m("M_ShipLights", color=(1.0, 0.9, 0.7), emission_color=scaled((1.0, 0.85, 0.6), 6.0)),
    m("M_TowerLight", color=(1.0, 0.85, 0.6), emission_color=scaled(WARM, 4.0)),
    m("M_Wire", color=(0.03, 0.03, 0.03), smoothness=0.5),
    m("M_Sky", shader="skybox", albedo="T_SkyNight_A"),
    # atmosphere / VFX
    m("M_Glow", shader="particlesAdditive", albedo="T_Glow_A", color=(1.0, 0.62, 0.3), alpha=0.55),
    m("M_Firefly", shader="particlesAdditive", albedo="T_Glow_A", color=(1.6, 2.0, 0.6)),
    m("M_Moth", shader="particlesAdditive", albedo="T_Moth_A", color=(1.0, 0.85, 0.65), alpha=0.8),
    m("M_Drop", shader="particlesAdditive", albedo="T_Drop_A", color=(0.7, 0.75, 0.85), alpha=0.6),
    m("M_Ripple", shader="particlesAdditive", albedo="T_Ripple_A", color=(0.6, 0.6, 0.65), alpha=0.35),
    m("M_Dust", shader="particlesAdditive", albedo="T_Glow_A", color=(1.0, 0.85, 0.7), alpha=0.25),
    m("M_LightCone", shader="unlitAdditive", albedo="T_LightCone_A", color=(0.55, 0.33, 0.14), double_sided=True),
    m("M_MoonHalo", shader="unlitAdditive", albedo="T_Glow_A", color=(0.32, 0.38, 0.55)),
    m("M_MoonPath", shader="unlitAdditive", albedo="T_MoonPath_A", color=(1.4, 1.45, 1.5)),
    m("M_Clouds", shader="unlitTransparent", albedo="T_Clouds_A", color=(1, 1, 1), tiling=(4, 1)),
    m("M_Grime", shader="unlitTransparent", albedo="T_Grime_A", color=(1, 1, 1), alpha=0.75),
    m("M_Streaks", shader="unlitTransparent", albedo="T_Streaks_A", color=(1, 1, 1), alpha=0.6),
    m("M_PawPrint", shader="unlitTransparent", albedo="T_PawPrint_A", color=(1, 1, 1), alpha=0.55),
    m("M_Pigeon", albedo="T_Pigeon_A", smoothness=0.25),
]

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"materials": MATERIALS}, f, indent=1)
    print("wrote", os.path.abspath(OUT), len(MATERIALS), "materials")
