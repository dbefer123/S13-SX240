"""Build the S13 exterior panels from the lofted skin (requires bpy)."""
from __future__ import annotations

import numpy as np
import bpy

from . import bl, panels as P
from tools.vehicle.s13 import body_spec as B, panel_spec as S

PAINT = "s13_paint"
TRIM = "s13_trim_black"
GLASS = "s13_glass"
RUBBER = "s13_rubber"


def mats():
    from . import materials as MR
    return {n: MR.blender_material(n) for n in (PAINT, TRIM, GLASS, RUBBER)}


# taillight band zones (US fastback): outer tail/brake, turn signal, reverse, centre reflector garnish
TAIL_ZONES = [  # (x_from, x_to, material)
    (0.56, 0.80, "s13_taillight"), (0.45, 0.56, "s13_signal_L"), (0.33, 0.45, "s13_reverselight"),
    (-0.33, 0.33, "s13_tail_garnish"),
    (-0.45, -0.33, "s13_reverselight"), (-0.56, -0.45, "s13_signal_R"), (-0.80, -0.56, "s13_taillight"),
]


def taillight_zones(tail):
    """Split the extracted taillight band into lamp zones with clean vertical boundaries."""
    from . import materials as MR
    pieces = []
    for i, (x0, x1, mat) in enumerate(TAIL_ZONES):
        rect = [(x0, 0.55), (x1, 0.55), (x1, 0.95), (x0, 0.95)]
        piece = P.extract(tail, f"__tail{i}", "front", rect, *S.TAIL_Y, gap=0.0)
        bl.assign(piece, MR.blender_material(mat))
        pieces.append(piece)
    bpy.data.objects.remove(tail, do_unlink=True)
    ob = P.join(pieces, "s13_taillights")
    bl.weld(ob, 1e-6)
    return ob


def mirror_side(pts):
    return pts


def mirror_plan(pts):
    return [(-x, y) for x, y in pts]


def build_skin(spec, n_mid=170):
    ys = spec.stations(n_mid=n_mid, n_end=26)
    Y, X, Z, tags = spec.grid(ys)
    ob = bl.mesh_from_grid("s13_skin", X, Y, Z, flip=True)
    bl.weld(ob, 1e-5)
    bl.mirror_x(ob)
    bl.weld(ob, 1e-5)
    return ob


def build_hatch_exterior(solid=True):
    M = mats()
    spec = B.hatch_spec()
    skin = build_skin(spec)
    bl.assign(skin, M[PAINT])
    out = {}

    # wheel arches
    for c in (S.ARCH_F, S.ARCH_R):
        P.cylinder_cut(skin, c, S.ARCH_RADIUS, 0.42, 1.3)
        P.cylinder_cut(skin, c, S.ARCH_RADIUS, -1.3, -0.42)

    def glass_with_trim(name, view, pts, lo, hi, trim_w=0.014, glass_mat=GLASS):
        trim = P.extract(skin, name + "_trim", view, P.offset_polygon(pts, trim_w), lo, hi, gap=0.0)
        glass = P.extract(trim, name, view, pts, lo, hi, gap=0.0)
        bl.assign(trim, M[TRIM]); bl.assign(glass, M[glass_mat])
        return glass, trim

    # --- glass that belongs to the body shell -------------------------------
    out["s13_windshield"], out["s13_windshield_trim"] = glass_with_trim(
        "s13_windshield", "plan", P.smooth_polygon(S.WINDSHIELD, 0.05), *S.WINDSHIELD_Z)
    for side, xr in (("L", S.SIDE_X), ("R", (-S.SIDE_X[1], -S.SIDE_X[0]))):
        out[f"s13_quarterglass_{side}"], out[f"s13_quarterglass_trim_{side}"] = glass_with_trim(
            f"s13_quarterglass_{side}", "side", P.smooth_polygon(S.QUARTER_GLASS, 0.035), *xr)

    # --- hatch (with its glass) ----------------------------------------------
    hatch = P.extract(skin, "s13_hatch", "plan", P.smooth_polygon(S.HATCH, 0.04), *S.HATCH_Z)
    hg_trim = P.extract(hatch, "s13_hatchglass_trim", "plan", P.offset_polygon(P.smooth_polygon(S.HATCH_GLASS, 0.06), 0.016), *S.HATCH_GLASS_Z, gap=0.0)
    hg = P.extract(hg_trim, "s13_hatchglass", "plan", P.smooth_polygon(S.HATCH_GLASS, 0.06), *S.HATCH_GLASS_Z, gap=0.0)
    bl.assign(hg_trim, M[TRIM]); bl.assign(hg, M[GLASS])
    out["s13_hatch"] = P.join([hatch, hg_trim], "s13_hatch")
    out["s13_hatchglass"] = hg

    # --- doors ------------------------------------------------------------------
    for side, xr in (("L", S.SIDE_X), ("R", (-S.SIDE_X[1], -S.SIDE_X[0]))):
        glass, trim = glass_with_trim(f"s13_doorglass_{side}", "side", P.smooth_polygon(S.DOOR_GLASS, 0.035), *xr)
        door = P.extract(skin, f"s13_door_{side}", "side", P.smooth_polygon(S.DOOR, 0.02), *xr)
        out[f"s13_door_{side}"] = P.join([door, trim], f"s13_door_{side}")
        out[f"s13_doorglass_{side}"] = glass

    # --- front: pop-ups, hood, bumper, fenders --------------------------------
    out["s13_popup_lid_L"] = P.extract(skin, "s13_popup_lid_L", "plan", S.POPUP, *S.POPUP_Z)
    out["s13_popup_lid_R"] = P.extract(skin, "s13_popup_lid_R", "plan", mirror_plan(S.POPUP), *S.POPUP_Z)
    out["s13_hood"] = P.extract(skin, "s13_hood", "plan", S.HOOD, *S.HOOD_Z)
    out["s13_bumper_F"] = P.extract(skin, "s13_bumper_F", "side", S.BUMPER_F, *S.BUMPER_X)
    out["s13_bumper_R"] = P.extract(skin, "s13_bumper_R", "side", S.BUMPER_R, *S.BUMPER_X)
    out["s13_fender_L"] = P.extract(skin, "s13_fender_L", "side", S.FENDER, *S.FENDER_X)
    out["s13_fender_R"] = P.extract(skin, "s13_fender_R", "side", S.FENDER, -S.FENDER_X[1], -S.FENDER_X[0])

    # tail light bar
    out["s13_taillights"] = taillight_zones(P.extract(skin, "s13_taillights", "front", S.TAILLIGHT, *S.TAIL_Y, gap=0.002))

    skin.name = "s13_body_hatch"
    skin.data.name = "s13_body_hatch"
    out["s13_body_hatch"] = skin

    for name, ob in out.items():
        P.remove_small_islands(ob, 3)
        if solid:
            thick = 0.004 if "glass" in name or "windshield" in name else 0.0022
            P.solidify(ob, thick)
        P.shade(ob, 40)
    return out
