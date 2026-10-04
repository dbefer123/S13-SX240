"""S14 exterior: loft the S14 body and cut it into panels (requires bpy).

One full pass with the zenki front end builds every panel; a second, front-only pass with the
kouki headlamp outline yields the kouki hood, front bumper and headlamps.  Both share the same
fenders (the lamps' outer ends are identical), so zenki <-> kouki swaps work like on the real car.

Tail lamps: the outer units are cut from the quarter panels, the middle/inner units from the
trunk lid; the zenki and kouki lamps share the geometry and differ in their colour zones.
"""
from __future__ import annotations

import math

import bpy
import numpy as np
from mathutils import Vector

from . import bl, panels as P
from . import s13_details as DET
from .prims import MeshBuilder, text_mesh
from .shape import side_x, top_z
from tools.vehicle.s14 import body_spec as B, panel_spec as S

SPEC = B.s14_spec()
PAINT, TRIM, GLASS = "s14_paint", "s14_trim_black", "s14_glass"
SIDES = (("L", (0.35, 1.25)), ("R", (-1.25, -0.35)))
BEZEL = 0.008


def _mat(name):
    from . import materials as MR
    return MR.blender_material(name)


def mirror_plan(pts):
    return [(-x, y) for x, y in pts]


def mirror_front(pts):
    return [(-x, z) for x, z in pts][::-1]


def build_skin():
    ys = SPEC.stations(n_mid=170, n_end=26)
    Y, X, Z, tags = SPEC.grid(ys)
    ob = bl.mesh_from_grid("s14_skin", X, Y, Z, flip=True)
    bl.weld(ob, 1e-5)
    bl.mirror_x(ob)
    bl.weld(ob, 1e-5)
    bl.assign(ob, _mat(PAINT))
    for c in (S.ARCH_F, S.ARCH_R):
        P.cylinder_cut(ob, c, S.ARCH_RADIUS, 0.42, 1.3)
        P.cylinder_cut(ob, c, S.ARCH_RADIUS, -1.3, -0.42)
    return ob


def glass_with_trim(src, name, view, pts, lo, hi, trim_w=0.014, glass_mat=GLASS, trim_mat=TRIM):
    trim = P.extract(src, name + "_trim", view, P.offset_polygon(pts, trim_w), lo, hi, gap=0.0)
    glass = P.extract(trim, name, view, pts, lo, hi, gap=0.0)
    bl.assign(trim, _mat(trim_mat))
    bl.assign(glass, _mat(glass_mat))
    return glass, trim


def _front(skin, kind):
    """Grille, headlamps, hood and front bumper for one facelift (cut in this order)."""
    out = {}
    g = P.extract(skin, f"__grille_{kind}", "front", S.GRILLE, *S.GRILLE_Y)
    bl.assign(g, _mat("s14_grille"))
    out["s14_grille"] = g
    lamps = []
    for s, pts in ((1, S.HEADLIGHTS[kind]), (-1, mirror_front(S.HEADLIGHTS[kind]))):
        lamps.append(P.extract(skin, f"__hl_{kind}_{s}", "front", P.smooth_polygon(pts, 0.02), *S.HEADLIGHT_Y, gap=0.003))
    for lp in lamps:
        bl.assign(lp, _mat("s14_glass_lens"))
    out[f"s14_headlights_{kind}"] = P.join(lamps, f"s14_headlights_{kind}")
    out[f"s14_hood_{kind}"] = P.extract(skin, f"s14_hood_{kind}", "plan", S.HOOD, *S.HOOD_Z)
    out[f"s14_bumper_F_{kind}"] = P.extract(skin, f"s14_bumper_F_{kind}", "side", S.BUMPER_F, *S.BUMPER_X)
    return out


def _tail_pieces(src, rects, kind_zones, name, lamp_keys):
    """Cut lamps (with a black bezel ring) out of `src`; return {facelift: object} with coloured zones."""
    out = {}
    raw = []
    for key, rect in rects:
        for s in (1, -1):
            pts = [(s * x, z) for x, z in rect]
            lamp = P.extract(src, f"__{name}_{key}_{s}", "front", P.offset_polygon(pts, BEZEL), *S.TAIL_Y, gap=0.002)
            raw.append((key, s, pts, lamp))
    for kind, zones in kind_zones.items():
        pieces = []
        for key, s, pts, lamp in raw:
            src_l = P.duplicate(lamp, f"__{name}_{kind}_{key}_{s}")
            xs = sorted(p[0] for p in pts)
            zs = [p[1] for p in pts]
            for i, (zk, x0, x1, z0, z1, mat) in enumerate(zones):
                if zk != key:
                    continue
                mname = {"tail": "s14_taillight" if kind == "zenki" else "s14_taillight_k",
                         "signal": ("s14_signal_L" if s > 0 else "s14_signal_R") + ("" if kind == "zenki" else "_k"),
                         "reverse": "s14_reverselight"}[mat]
                xa, xb = sorted((s * x0, s * x1))
                xa, xb = max(xa, xs[0]), min(xb, xs[-1])
                za, zb = max(z0, min(zs)), min(z1, max(zs))
                if xb - xa < 1e-3 or zb - za < 1e-3:
                    continue
                piece = P.extract(src_l, f"__z_{name}_{kind}_{key}_{s}_{i}", "front",
                                  [(xa, za), (xb, za), (xb, zb), (xa, zb)], *S.TAIL_Y, gap=0.0)
                bl.assign(piece, _mat(mname))
                pieces.append(piece)
            bl.assign(src_l, _mat(TRIM))                 # remaining ring = bezel
            pieces.append(src_l)
        ob = P.join(pieces, f"s14_{name}_{kind}")
        bl.weld(ob, 1e-6)
        out[kind] = ob
    for _, _, _, lamp in raw:
        bpy.data.objects.remove(lamp, do_unlink=True)
    return out


def build_exterior(solid=True):
    out, body_trims = {}, []
    skin = build_skin()
    # --- glass on the body shell ----------------------------------------------------
    out["s14_windshield"], out["s14_windshield_trim"] = glass_with_trim(
        skin, "s14_windshield", "plan", P.smooth_polygon(S.WINDSHIELD, 0.05), *S.WINDSHIELD_Z)
    for side, xr in SIDES:
        g, t = glass_with_trim(skin, f"s14_quarterglass_{side}", "side", P.smooth_polygon(S.QUARTER_GLASS, 0.03), *xr,
                               trim_w=0.012)
        out[g.name] = g
        body_trims.append(t)
        bp = P.extract(skin, f"__bpillar_{side}", "side", S.B_PILLAR, *xr, gap=0.0)
        bl.assign(bp, _mat("s14_trim_gloss"))
        body_trims.append(bp)
    g, t = glass_with_trim(skin, "s14_rearwindow", "plan", P.smooth_polygon(S.REAR_WINDOW, 0.06), *S.REAR_WINDOW_Z,
                           trim_w=0.018)
    out["s14_rearwindow"] = g
    body_trims.append(t)
    # --- frameless doors: the roof / pillar seals stay on the body, the belt strip rides on the door -----
    (by0, bz0), (by1, bz1) = S.DOOR_GLASS[0], S.DOOR_GLASS[-1]
    door_trims = {}
    for side, xr in SIDES:
        g, t = glass_with_trim(skin, f"s14_doorglass_{side}", "side", P.smooth_polygon(S.DOOR_GLASS, 0.03), *xr,
                               trim_w=0.010)
        out[g.name] = g
        door_trims[side] = P.split_faces(
            t, lambda c: c.z < bz0 + (bz1 - bz0) * (c.y - by0) / (by1 - by0) + 0.020, f"__doortrim_{side}")
        body_trims.append(t)
        out[f"s14_door_{side}"] = P.extract(skin, f"s14_door_{side}", "side", P.smooth_polygon(S.DOOR, 0.02), *xr)
    # --- front end (zenki), fenders, rear ----------------------------------------------
    out.update(_front(skin, "zenki"))
    out["s14_fender_L"] = P.extract(skin, "s14_fender_L", "side", S.FENDER, *S.FENDER_X)
    out["s14_fender_R"] = P.extract(skin, "s14_fender_R", "side", S.FENDER, -S.FENDER_X[1], -S.FENDER_X[0])
    out["s14_bumper_R"] = P.extract(skin, "s14_bumper_R", "side", S.BUMPER_R, *S.BUMPER_X)
    trunk = P.extract(skin, "s14_trunk", "front", S.TRUNK, *S.TRUNK_Y)
    outer = _tail_pieces(skin, [("outer", S.TAIL_OUTER)], S.TAIL_ZONES, "taillights", ("outer",))
    inner = _tail_pieces(trunk, [("middle", S.TAIL_MIDDLE), ("inner", S.TAIL_INNER)], S.TAIL_ZONES, "taillights_inner",
                         ("middle", "inner"))
    for kind in ("zenki", "kouki"):
        out[f"s14_taillights_{kind}"] = outer[kind]
        out[f"s14_taillights_inner_{kind}"] = inner[kind]
    out["s14_trunk"] = trunk
    skin.name = skin.data.name = "s14_body_coupe"
    out["s14_body_coupe"] = skin
    for i, t in enumerate(body_trims):
        out[f"__bodytrim_{i}"] = t
    for side, t in door_trims.items():
        out[f"__doortrim_{side}"] = t

    # --- kouki front: second skin, front-only cuts ------------------------------------------
    skin_k = build_skin()
    _ = glass_with_trim(skin_k, "__k_ws", "plan", P.smooth_polygon(S.WINDSHIELD, 0.05), *S.WINDSHIELD_Z)
    kouki = _front(skin_k, "kouki")
    for ob in _:
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.objects.remove(kouki.pop("s14_grille"), do_unlink=True)
    bpy.data.objects.remove(skin_k, do_unlink=True)
    out.update(kouki)

    for name, ob in out.items():
        P.remove_small_islands(ob, 3)
        if solid:
            thick = 0.004 if ("glass" in name or "window" in name or "windshield" == name[4:]) else 0.0022
            if name.startswith("s14_headlights"):
                thick = 0.003
            P.solidify(ob, thick)
        P.shade(ob, 40)
    if solid:
        _details(out)
        rules = {"s14_body_coupe": "s14_interior_trim", "s14_trunk": "s14_interior_trim",
                 "s14_door_L": "s14_interior_trim", "s14_door_R": "s14_interior_trim"}
        DET.interior_faces_for(out, rules, paint_name=PAINT)
        DET.undercoat_faces(out["s14_body_coupe"], paint_name=PAINT)
        _fix_undercoat_name(out["s14_body_coupe"])
    keys = [k for k in out if k.startswith("__bodytrim_")]
    out["s14_body_coupe"] = P.join([out["s14_body_coupe"]] + [out.pop(k) for k in keys], "s14_body_coupe")
    for side in ("L", "R"):
        out[f"s14_door_{side}"] = P.join([out[f"s14_door_{side}"], out.pop(f"__doortrim_{side}")], f"s14_door_{side}")
    return out


def _fix_undercoat_name(ob):
    """DET.undercoat_faces assigns the S13 undercoat; use the S14 copy."""
    me = ob.data
    for i, m in enumerate(me.materials):
        if m and m.name == "s13_undercoat":
            me.materials[i] = _mat("s14_undercoat")


# ---------------------------------------------------------------------------
# details (after solidify)
# ---------------------------------------------------------------------------
def _rect(cx, cz, w, h, r, mirror=False):
    return DET._rect(cx, cz, w, h, r, mirror)


FRONT_OPENINGS = {  # facelift: [(cx, cz, w, h, r, kind)] left side + centre; kind: signal | grille | fog
    "zenki": [(0.52, 0.482, 0.42, 0.064, 0.03, "signal"), (0.53, 0.372, 0.40, 0.072, 0.03, "fog"),
              (0.0, 0.365, 0.46, 0.062, 0.02, "grille")],
    "kouki": [(0.57, 0.487, 0.32, 0.056, 0.026, "signal"), (0.52, 0.365, 0.46, 0.110, 0.035, "grille"),
              (0.0, 0.362, 0.50, 0.100, 0.03, "grille")],
}


def front_bumper_cuts(bf, kind):
    """Cut the openings of a front bumper (on the solidified panel)."""
    for cx, cz, w, h, r, k in FRONT_OPENINGS[kind]:
        for m in ((False, True) if cx else (False,)):
            P.cut_away(bf, "front", _rect(cx, cz, w, h, r, m), -2.45, -2.06)


def _face_y(surf, x, z0, z1):
    """Bumper face depth at x, measured just above and below an opening (the ray through the hole hits nothing)."""
    ys = [surf.y_front(x, z) for z in (z1 + 0.012, z0 - 0.012)]
    ys = [y for y in ys if y is not None]
    return sum(ys) / len(ys) if ys else None


def _opening_grid(surf, x0, x1, z0, z1, nx=14):
    xs = np.linspace(x0, x1, nx)
    ys = [_face_y(surf, float(x), z0, z1) for x in xs]
    good = [(float(x), y) for x, y in zip(xs, ys) if y is not None]
    return good


def _follow_plate(mb, surf, x0, x1, z0, z1, depth, mat, nz=4):
    """Dark back plate following the curved bumper face `depth` behind it (faces forward)."""
    row = _opening_grid(surf, x0 - 0.01, x1 + 0.01, z0, z1)
    if len(row) < 2:
        return
    zs = np.linspace(z0 - 0.01, z1 + 0.01, nz)
    verts = [(x, y + depth, float(z)) for z in zs for x, y in row]
    n = len(row)
    faces = [(i * n + j, i * n + j + 1, (i + 1) * n + j + 1, (i + 1) * n + j) for i in range(nz - 1) for j in range(n - 1)]
    mb.add_faces(verts, faces, mat, smooth=False)


def _follow_slats(mb, surf, x0, x1, z0, z1, pitch, depth, mat):
    row = _opening_grid(surf, x0, x1, z0, z1)
    if len(row) < 2:
        return
    n = len(row)
    z = z0 + pitch / 2
    while z < z1 - 0.003:
        verts = [(x, y + 0.006, z + 0.004) for x, y in row] + [(x, y + depth, z - 0.004) for x, y in row]
        faces = [(j, j + 1, n + j + 1, n + j) for j in range(n - 1)]
        mb.add_faces(verts, faces, mat, smooth=False)
        mb.add_faces(verts, [f[::-1] for f in faces], mat, smooth=False)       # double sided
        z += pitch


def _follow_lens(mb, surf, outline, z0, z1, inset, mat):
    pts = []
    for x, z in outline:
        y = _face_y(surf, x, z0, z1)
        if y is not None:
            pts.append((x, y + inset, z))
    if len(pts) >= 3:
        mb.polygon(pts, mat, outward=(0, -1, 0))


def _front_bumper_inserts(bf, kind):
    surf = DET.Surface(bf)
    mb = MeshBuilder(f"__bfi_{kind}")
    for cx, cz, w, h, r, k in FRONT_OPENINGS[kind]:
        for sgn in ((1, -1) if cx else (1,)):
            x0, x1 = sorted((sgn * (cx - w / 2), sgn * (cx + w / 2)))
            z0, z1 = cz - h / 2, cz + h / 2
            _follow_plate(mb, surf, x0, x1, z0, z1, 0.040, "s1x_dark")
            if k == "signal":
                lens = _rect(sgn * cx, cz, w * 0.62, h * 0.66, r * 0.6)
                _follow_lens(mb, surf, lens, z0, z1, 0.014, "s14_signal_L" if sgn > 0 else "s14_signal_R")
                _follow_slats(mb, surf, x0, x1, z0, z1, h / 2.2, 0.03, "s14_trim_black")
            elif k == "fog":
                _follow_slats(mb, surf, x0, x1, z0, z1, 0.018, 0.03, "s14_trim_black")
                for dx in (-0.08, 0.08):
                    x = sgn * cx + dx
                    y = _face_y(surf, x, z0, z1)
                    if y is not None:
                        mb.cylinder((x, y + 0.035, cz), (x, y + 0.015, cz), 0.027, "s14_headlight_chrome", segs=20)
                        mb.cylinder((x, y + 0.016, cz), (x, y + 0.012, cz), 0.025, "s14_foglight", segs=20)
            else:
                _follow_slats(mb, surf, x0, x1, z0, z1, 0.015, 0.035, "s14_trim_black")
    # side markers on the bumper flanks
    for sgn in (1, -1):
        pts = []
        for y, z in ((-1.98, 0.455), (-1.88, 0.455), (-1.88, 0.485), (-1.98, 0.485)):
            x = surf.x_side(y, z, sgn) or sgn * side_x(SPEC, y, z)
            pts.append((x + sgn * 0.002, y, z))
        mb.polygon(pts, "s14_sidemarker_F", outward=(sgn, 0, 0))
    return mb.to_object()


def _headlamp_internals(kind):
    """Reflector housings behind the clear headlamp lenses (glow key s14_headlight)."""
    mb = MeshBuilder(f"__hli_{kind}")
    for s in (1, -1):
        outline = S.HEADLIGHTS[kind]
        xs = [p[0] for p in outline]
        zs = [p[1] for p in outline]
        x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
        # dark back plate following the lamp outline, 7 cm behind the lens
        yb = -2.04 + 0.08 * ((x0 + x1) / 2 - 0.3)
        pts = [(s * x, yb + 0.07 * (x - x0) / (x1 - x0), z) for x, z in outline]
        mb.polygon(pts, "s14_headlight_housing", outward=(0, -1, 0))
        # low beam (outer) + high beam (inner) reflectors with the glowing bulb faces
        for frac, r in ((0.68, 0.040), (0.38, 0.034)):
            cx = x0 + (x1 - x0) * frac
            cz = z0 + (z1 - z0) * (0.52 if kind == "zenki" else 0.45)
            y = yb + 0.07 * frac - 0.005
            mb.lathe([(0.0, 0.0), (r * 0.5, -0.012), (r, -0.035), (r * 1.02, -0.04)], "s14_headlight_chrome", segs=24,
                     axis="y", center=(s * cx, y, cz))
            mb.cylinder((s * cx, y - 0.012, cz), (s * cx, y - 0.016, cz), r * 0.45, "s14_headlight", segs=16)
        if kind == "kouki":   # kouki: projector-style low beam ring
            cx = x0 + (x1 - x0) * 0.68
            mb.cylinder((s * cx, yb - 0.02, z0 + (z1 - z0) * 0.45), (s * cx, yb - 0.035, z0 + (z1 - z0) * 0.45), 0.030,
                        "s1x_dark", segs=20)
        # amber corner signal at the outer end
        mb.rbox((s * (x1 - 0.035), yb + 0.065, (z0 + z1) / 2), (0.05, 0.02, (z1 - z0) * 0.6), 0.008,
                "s14_signal_L" if s > 0 else "s14_signal_R")
    return mb.to_object()


def _details(out):
    joins = {}

    def add(target, ob):
        joins.setdefault(target, []).append(ob)

    body = out["s14_body_coupe"]
    # front bumpers
    for kind in ("zenki", "kouki"):
        name = f"s14_bumper_F_{kind}"
        front_bumper_cuts(out[name], kind)
        add(name, _front_bumper_inserts(out[name], kind))
        DET._assign_by(out[name], "s14_trim_black", lambda c, n: c.z < 0.235, split_z=0.235)
        _swap_mat(out[name], "s13_trim_black", "s14_trim_black")
        add(f"s14_headlights_{kind}", _headlamp_internals(kind))
    # grille slats + emblem
    gs = DET.Surface(out["s14_grille"])
    mb = MeshBuilder("__grille_slats")
    for z in np.arange(0.598, 0.648, 0.012):
        y = gs.y_front(0.0, float(z))
        if y is not None:
            mb.box((0.0, y - 0.004, float(z)), (0.48, 0.004, 0.004), "s14_trim_gloss")
    y = gs.y_front(0.0, 0.620)
    if y is not None:
        ring = [(0.035 * math.cos(2 * math.pi * k / 32), y - 0.008, 0.620 + 0.022 * math.sin(2 * math.pi * k / 32))
                for k in range(32)]
        mb.polygon(ring, "s14_badge_chrome", outward=(0, -1, 0))
        mb.box((0.0, y - 0.0095, 0.620), (0.062, 0.002, 0.008), "s14_badge_blue")
    add("s14_grille", mb.to_object())
    # rear bumper: plate recess wall, reflectors, side markers
    br = out["s14_bumper_R"]
    rs = DET.Surface(br)
    yw = [rs.y_rear(x, z) for x in (-0.12, 0.0, 0.12) for z in (0.425, 0.625)]
    yw = [y for y in yw if y is not None]
    yw = (sum(yw) / len(yw) if yw else 2.29) - 0.014
    P.cut_away(br, "front", _rect(0.0, 0.525, 0.330, 0.160, 0.012), 2.0, 2.45)
    rs = DET.Surface(br)
    mb = MeshBuilder("__bri")
    mb.box((0.0, yw, 0.525), (0.34, 0.004, 0.17), PAINT)
    for s in (1, -1):
        pts = []
        for x, z in _rect(s * 0.50, 0.585, 0.20, 0.022, 0.008):
            y = rs.y_rear(x, z)
            if y is not None:
                pts.append((x, y + 0.002, z))
        if len(pts) > 3:
            mb.polygon(pts, "s14_lights_red", outward=(0, 1, 0))
        pts = []
        for y, z in ((2.00, 0.50), (1.90, 0.50), (1.90, 0.525), (2.00, 0.525)):
            x = rs.x_side(y, z, s) or s * side_x(SPEC, y, z)
            pts.append((x + s * 0.002, y, z))
        mb.polygon(pts, "s14_sidemarker_R", outward=(s, 0, 0))
    add("s14_bumper_R", mb.to_object())
    DET._assign_by(br, "s14_trim_black", lambda c, n: c.z < 0.30 and n.z < -0.3)
    _swap_mat(br, "s13_trim_black", "s14_trim_black")
    # door handles (body-colour pull in a black recess)
    for s, side in ((1, "L"), (-1, "R")):
        ds = DET.Surface(out[f"s14_door_{side}"])
        y, z = 0.36, 0.742
        x = ds.x_side(y, z, s) or s * side_x(SPEC, y, z)
        mb = MeshBuilder(f"__handle_{side}")
        mb.rbox((x + s * 0.001, y, z), (0.006, 0.15, 0.040), 0.012, "s14_trim_black")
        mb.rbox((x + s * 0.007, y - 0.005, z + 0.004), (0.010, 0.125, 0.020), 0.007, PAINT)
        add(f"s14_door_{side}", mb.to_object())
    # fuel door (right rear quarter)
    s = -1
    qs = DET.Surface(body)
    mb = MeshBuilder("__fueldoor14")
    ring = []
    for k in range(36):
        a = 2 * math.pi * k / 36
        y, z = 1.02 + 0.07 * math.cos(a), 0.76 + 0.058 * math.sin(a)
        x = qs.x_side(y, z, s) or s * side_x(SPEC, y, z)
        ring.append((x + s * 0.0006, y, z))
    for a, b in zip(ring, ring[1:] + ring[:1]):
        mb.add_faces([a, b, (b[0] + s * 0.0004, b[1], b[2] + 0.0022), (a[0] + s * 0.0004, a[1], a[2] + 0.0022)],
                     [(3, 2, 1, 0)], "s1x_dark", smooth=False)
    add("s14_body_coupe", mb.to_object())
    # trunk: emblem + 240SX script on the centre panel
    ts = DET.Surface(out["s14_trunk"])
    y = ts.y_rear(0.0, 0.835)
    if y is not None:
        mb = MeshBuilder("__trunk14")
        ring = [(0.028 * math.cos(2 * math.pi * k / 32), y + 0.004, 0.835 + 0.028 * math.sin(2 * math.pi * k / 32))
                for k in range(32)]
        mb.polygon(ring, "s14_badge_chrome", outward=(0, 1, 0))
        mb.box((0.0, y + 0.0052, 0.835), (0.048, 0.002, 0.007), "s14_badge_blue")
        add("s14_trunk", mb.to_object())
    y = ts.y_rear(0.0, 0.772)
    if y is not None:
        add("s14_trunk", text_mesh("__240sx14", "240SX", 0.028, "s14_badge_chrome", location=(0.0, y + 0.003, 0.772),
                                   rotation=(math.radians(90), 0, math.radians(180)), extrude=0.0012))
    # wipers on the cowl
    mb = MeshBuilder("__wipers14")
    for x0, x1 in ((-0.52, 0.06), (-0.02, 0.56)):
        pts = [(float(x), -0.765, top_z(SPEC, -0.765, abs(float(x))) + 0.012) for x in np.linspace(x0, x1, 10)]
        mb.tube(pts, 0.006, "s1x_dark", segs=6)
        px = x0 + 0.06
        zc = top_z(SPEC, -0.81, abs(px))
        mb.cylinder((px, -0.81, zc - 0.005), (px, -0.81, zc + 0.02), 0.012, "s1x_dark", segs=10)
    add("s14_windshield_trim", mb.to_object())
    for target, obs in joins.items():
        out[target] = P.join([out[target]] + obs, target)


def _swap_mat(ob, old, new):
    me = ob.data
    for i, m in enumerate(me.materials):
        if m and m.name == old:
            me.materials[i] = _mat(new)


# ---------------------------------------------------------------------------
# S14 OEM rear wing (SE / LE / kouki style, three-post with brake light)
# ---------------------------------------------------------------------------
def trunk_spoilers():
    out = []
    mb = MeshBuilder("s14_trunkspoiler_oem")
    span, chord = 0.62, 0.17
    y_le, z0 = 1.975, 0.990
    loop = [(0.0, 0.0), (0.03, 0.014), (0.09, 0.020), (chord, 0.030), (chord, 0.018), (0.08, -0.008)]
    n = len(loop)
    xs = np.linspace(-span, span, 17)
    verts, faces = [], []
    for i, x in enumerate(xs):
        droop = 0.020 * (abs(x) / span) ** 2.5
        verts += [(float(x), y_le + u, z0 + v - droop) for u, v in loop]
        if i:
            a, b = (i - 1) * n, i * n
            faces += [(a + k, b + k, b + (k + 1) % n, a + (k + 1) % n) for k in range(n)]
    mb.add_faces(verts, faces, PAINT, smooth=True)
    for i, x in ((0, -span), (len(xs) - 1, span)):
        mb.polygon(verts[i * n:(i + 1) * n], PAINT, outward=(1 if x > 0 else -1, 0, 0))
    for xp in (-0.46, 0.0, 0.46):
        zd = top_z(SPEC, y_le + 0.08, abs(xp))
        mb.rbox((xp, y_le + 0.08, (zd + z0) / 2), (0.045, 0.11, z0 - zd + 0.012), 0.012, PAINT)
    mb.rbox((0.0, y_le + chord - 0.004, z0 + 0.026), (0.24, 0.010, 0.012), 0.004, "s14_chmsl")
    out.append(mb)
    mb = MeshBuilder("s14_trunkspoiler_lip")
    xs = np.linspace(-0.64, 0.64, 25)
    rows = []
    for y, dz in ((1.98, 0.0), (2.03, 0.018), (2.055, 0.022), (2.05, 0.0)):
        rows.append([(float(x), y, top_z(SPEC, y, abs(float(x))) + dz + 0.0015) for x in xs])
    n = len(xs)
    verts = [v for r in rows for v in r]
    faces = [(i * n + j, i * n + j + 1, (i + 1) * n + j + 1, (i + 1) * n + j) for i in range(len(rows) - 1) for j in range(n - 1)]
    mb.add_faces(verts, faces, PAINT, smooth=True)
    for j in (0, n - 1):
        mb.polygon([rows[i][j] for i in range(len(rows))], PAINT, outward=(1 if xs[j] > 0 else -1, 0, 0))
    out.append(mb)
    return out


# ---------------------------------------------------------------------------
# body kits: lip spoilers and rear valance on copies of the finished bumpers
# ---------------------------------------------------------------------------
LIPS = {"aero": (0.028, 0.040, TRIM), "carbon": (0.042, 0.062, "s1x_carbon")}


def _lip_strip(mb, rows_in, rows_out, drop_z, mat, rear=False):
    """Wedge under a bumper edge: tucked row, outer row and a lowered copy of the outer row, with end caps."""
    n = len(rows_in)
    verts = rows_in + rows_out + [(x, y, z - drop_z) for x, y, z in rows_out]
    faces = [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)]
    faces += [(n + i, n + i + 1, 2 * n + i + 1, 2 * n + i) for i in range(n - 1)]
    faces += [(2 * n + i, 2 * n + i + 1, i + 1, i) for i in range(n - 1)]
    if not rear:
        faces = [f[::-1] for f in faces]                    # outward (front: rows run +x, the wedge points -y)
    mb.add_faces(verts, faces, mat, smooth=False)
    for idx in (0, n - 1):
        mb.polygon([verts[idx], verts[n + idx], verts[2 * n + idx]], mat, outward=(1 if verts[idx][0] > 0 else -1, 0, 0))


def _bottom_z(ob, front=True):
    zs = [v.co.z for v in ob.data.vertices if abs(v.co.x) < 0.45 and ((v.co.y < -2.0) if front else (v.co.y > 2.0))]
    return min(zs)


def front_lip(bf, name, kind):
    drop, reach, mat = LIPS[kind]
    surf = DET.Surface(bf)
    zb = _bottom_z(bf, True)
    mb = MeshBuilder(f"__lip_{name}")
    inner, outer = [], []
    for x in np.linspace(-0.76, 0.76, 45):
        y = surf.y_front(float(x), zb + 0.012)
        if y is None:
            continue
        inner.append((float(x), y + 0.012, zb + 0.004))
        outer.append((float(x), y - reach * (1 - (abs(x) / 0.82) ** 4), zb + 0.004 - drop))
    _lip_strip(mb, inner, outer, 0.008, mat)
    return mb.to_object()


def rear_valance(br, name):
    rs = DET.Surface(br)
    zb = _bottom_z(br, False)
    mb = MeshBuilder(f"__valance_{name}")
    inner, outer = [], []
    for x in np.linspace(-0.70, 0.70, 33):
        y = rs.y_rear(float(x), zb + 0.012)
        if y is None:
            continue
        inner.append((float(x), y - 0.012, zb + 0.004))
        outer.append((float(x), y + 0.030 * (1 - (abs(x) / 0.76) ** 4), zb - 0.030))
    _lip_strip(mb, inner, outer, 0.007, TRIM, rear=True)
    return mb.to_object()


def body_kits(body):
    """s14_bumper_F_<zenki|kouki>_<aero|carbon> and s14_bumper_R_aero from the finished bumpers in `body`."""
    out = {}
    for kind in ("zenki", "kouki"):
        src = body[f"s14_bumper_F_{kind}"]
        for kit in LIPS:
            name = f"s14_bumper_F_{kind}_{kit}"
            cp = P.duplicate(src, f"__{name}")
            out[name] = P.join([cp, front_lip(src, name, kit)], name)
    cp = P.duplicate(body["s14_bumper_R"], "__s14_bumper_R_aero")
    out["s14_bumper_R_aero"] = P.join([cp, rear_valance(body["s14_bumper_R"], "s14_bumper_R_aero")], "s14_bumper_R_aero")
    return out
