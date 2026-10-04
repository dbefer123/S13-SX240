"""S13 notchback coupe and convertible rear bodies (requires bpy).

Both bodies share every panel ahead of the B-pillar with the hatch (the lofts are identical
there), so the coupe skin is cut with the same outlines to get matching openings and only the
body-specific pieces are kept:

    coupe        s13_body_coupe, coupe quarter glass, rear window, trunk lid, coupe tail lamps,
                 parcel shelf, coupe headliner
    convertible  s13_body_convertible (with the hard tonneau over the top well), trunk lid, tail
                 lamps, soft top (fabric + rear window + quarter windows)

The trunk lid, tail lamps and trunk spoilers are shared by both.
"""
from __future__ import annotations

import math

import bpy
import numpy as np
from mathutils import Matrix, Vector

from . import bl, panels as P
from . import s13_exterior as EXT
from . import s13_details as DET
from .prims import MeshBuilder, text_mesh
from .shape import side_x, top_z
from tools.vehicle.s13 import body_spec as B, panel_spec as S

SPEC = B.coupe_spec()
FABRIC = "s13_softtop_fabric"
SIDES = (("L", (0.35, 1.25)), ("R", (-1.25, -0.35)))


def _glass_with_trim(src, name, view, pts, lo, hi, trim_w=0.014, glass_mat="s13_glass"):
    from . import materials as MR
    trim = P.extract(src, name + "_trim", view, P.offset_polygon(pts, trim_w), lo, hi, gap=0.0)
    glass = P.extract(trim, name, view, pts, lo, hi, gap=0.0)
    bl.assign(trim, MR.blender_material(EXT.TRIM))
    bl.assign(glass, MR.blender_material(glass_mat))
    return glass, trim


def _tail_lamps(skin):
    """Coupe tail lamps: red lower half, amber outer / clear inner upper half, wrapped around the corners."""
    from . import materials as MR
    pieces = []
    bezel = 0.008
    for s in (1, -1):
        rect = [(s * x, z) for x, z in S.COUPE_TAIL]
        lamp = P.extract(skin, f"__ctail{s}", "front", P.offset_polygon(rect, bezel), *S.COUPE_TAIL_Y, gap=0.002)
        xs = sorted(s * x for x, _ in S.COUPE_TAIL)
        zs = [z for _, z in S.COUPE_TAIL]
        for i, (x0, x1, z0, z1, mat) in enumerate(S.COUPE_TAIL_ZONES):
            if mat == "signal":
                mat = "s13_signal_L" if s > 0 else "s13_signal_R"
            xa, xb = sorted((s * x0, s * x1))
            xa, xb = max(xa, xs[0]), min(xb, xs[-1])
            za, zb = max(z0, min(zs)), min(z1, max(zs))
            piece = P.extract(lamp, f"__ctz{s}{i}", "front", [(xa, za), (xb, za), (xb, zb), (xa, zb)],
                              *S.COUPE_TAIL_Y, gap=0.0)
            bl.assign(piece, MR.blender_material(mat))
            pieces.append(piece)
        bl.assign(lamp, MR.blender_material(EXT.TRIM))        # what is left is the black bezel ring
        pieces.append(lamp)
    ob = P.join(pieces, "s13_taillights_coupe")
    bl.weld(ob, 1e-6)
    return ob


def _cut_shared(skin):
    """Cut every opening the shared (hatch) panels need; the extracted pieces are thrown away."""
    scrap = list(_glass_with_trim(skin, "__ws", "plan", P.smooth_polygon(S.WINDSHIELD, 0.05), *S.WINDSHIELD_Z))
    return scrap


def _cut_front(skin):
    scrap = []
    for side, xr in SIDES:
        scrap += _glass_with_trim(skin, f"__dg{side}", "side", P.smooth_polygon(S.DOOR_GLASS, 0.035), *xr)
        scrap.append(P.extract(skin, f"__door{side}", "side", P.smooth_polygon(S.DOOR, 0.02), *xr))
    scrap.append(P.extract(skin, "__puL", "plan", S.POPUP, *S.POPUP_Z))
    scrap.append(P.extract(skin, "__puR", "plan", EXT.mirror_plan(S.POPUP), *S.POPUP_Z))
    scrap.append(P.extract(skin, "__hood", "plan", S.HOOD, *S.HOOD_Z))
    scrap.append(P.extract(skin, "__bf", "side", S.BUMPER_F, *S.BUMPER_X))
    scrap.append(P.extract(skin, "__br", "side", S.BUMPER_R, *S.BUMPER_X))
    scrap.append(P.extract(skin, "__fl", "side", S.FENDER, *S.FENDER_X))
    scrap.append(P.extract(skin, "__fr", "side", S.FENDER, -S.FENDER_X[1], -S.FENDER_X[0]))
    return scrap


def build_rear_exterior(kind="coupe", solid=True):
    """Return {mesh name: object} for the coupe or convertible specific exterior meshes."""
    from . import materials as MR
    M = EXT.mats()
    skin = EXT.build_skin(SPEC)
    bl.assign(skin, M[EXT.PAINT])
    out, scrap, trims = {}, [], {}
    for c in (S.ARCH_F, S.ARCH_R):
        P.cylinder_cut(skin, c, S.ARCH_RADIUS, 0.42, 1.3)
        P.cylinder_cut(skin, c, S.ARCH_RADIUS, -1.3, -0.42)
    scrap += _cut_shared(skin)
    body_name = f"s13_body_{kind}"

    if kind == "coupe":
        for side, xr in SIDES:
            g, t = _glass_with_trim(skin, f"s13_quarterglass_coupe_{side}", "side",
                                    P.smooth_polygon(S.COUPE_QUARTER_GLASS, 0.03), *xr)
            out[g.name] = g
            trims.setdefault(body_name, []).append(t)
        g, t = _glass_with_trim(skin, "s13_rearwindow", "plan", P.smooth_polygon(S.REAR_WINDOW, 0.05), *S.REAR_WINDOW_Z,
                                trim_w=0.018)
        out["s13_rearwindow"] = g
        trims[body_name].append(t)

    scrap += _cut_front(skin)
    out["s13_trunk"] = P.extract(skin, "s13_trunk", "front", S.TRUNK, *S.TRUNK_Y)
    out["s13_taillights_coupe"] = _tail_lamps(skin)

    if kind == "convertible":
        y0, y1 = S.CONV_TOP_Y
        lower = [(float(y), float(SPEC.g("z_belt", float(y))) + 0.004) for y in np.linspace(y0, y1, 40)]
        top = P.extract(skin, "s13_softtop", "side", lower + [(y1, 1.60), (y0, 1.60)], -1.3, 1.3)
        bl.assign(top, MR.blender_material(FABRIC))
        g, t = _glass_with_trim(top, "s13_softtop_glass", "plan", P.smooth_polygon(S.CONV_REAR_WINDOW, 0.05), 0.9, 1.4,
                                trim_w=0.022)
        out["s13_softtop_glass"] = g
        trims.setdefault("s13_softtop", []).append(t)
        for side, xr in SIDES:
            g, t = _glass_with_trim(top, f"s13_quarterglass_conv_{side}", "side",
                                    P.smooth_polygon(S.CONV_QUARTER_GLASS, 0.03), *xr, trim_w=0.010)
            out[g.name] = g
            trims["s13_softtop"].append(t)
        out["s13_softtop"] = top

    for ob in scrap:
        bpy.data.objects.remove(ob, do_unlink=True)
    skin.name = body_name
    skin.data.name = body_name
    out[body_name] = skin
    for target, ts in trims.items():
        for i, t in enumerate(ts):
            out[f"__trim_{target}_{i}"] = t

    for name, ob in out.items():
        P.remove_small_islands(ob, 3)
        if solid:
            thick = 0.004 if "glass" in name or "window" in name else 0.0022
            if name == "s13_softtop":
                thick = 0.006
            P.solidify(ob, thick)
        P.shade(ob, 40)
    if solid:
        _details(out, kind, body_name)
        rules = {body_name: "s13_interior_trim", "s13_trunk": "s13_interior_trim"}
        DET.interior_faces_for(out, rules)
        DET.undercoat_faces(out[body_name])
        if kind == "convertible":
            DET.interior_faces_for(out, {"s13_softtop": "s13_softtop_lining"}, paint_name=FABRIC, ylim=(-0.3, 1.8))
    # trims become part of their owner mesh
    for target, ts in trims.items():
        keys = [f"__trim_{target}_{i}" for i in range(len(ts))]
        out[target] = P.join([out[target]] + [out.pop(k) for k in keys], target)
    return out


# ---------------------------------------------------------------------------
# details (after solidify)
# ---------------------------------------------------------------------------
def _details(out, kind, body_name):
    body = out[body_name]
    joins = {}

    def add(target, ob):
        joins.setdefault(target, []).append(ob)

    # side rub strips on the rear quarters
    for s, side in ((1, "L"), (-1, "R")):
        mb = MeshBuilder(f"__strip_{body_name}_{side}")
        DET._band(mb, np.linspace(0.61, 1.72, 26), *DET.STRIP_Z, s, "s13_trim_black", surf=DET.Surface(body))
        if mb.bm.faces:
            add(body_name, mb.to_object())
        else:
            mb.bm.free()
    # fuel door (right rear quarter)
    s = -1
    qs = DET.Surface(body)
    mb = MeshBuilder("__fueldoor_c")
    yc, zc = 1.00, 0.72
    ring = []
    for k in range(36):
        a = 2 * math.pi * k / 36
        y = yc + 0.065 * math.cos(a)
        z = zc + 0.055 * math.sin(a)
        x = qs.x_side(y, z, s) or s * side_x(SPEC, y, z)
        ring.append((x + s * 0.0006, y, z))
    for (a, b) in zip(ring, ring[1:] + ring[:1]):
        mb.add_faces([a, b, (b[0] + s * 0.0004, b[1], b[2] + 0.0022), (a[0] + s * 0.0004, a[1], a[2] + 0.0022)],
                     [(3, 2, 1, 0)], "s1x_dark", smooth=False)
    add(body_name, mb.to_object())

    # NISSAN letters on the rear panel under the left lamp
    rp = DET.Surface(body)
    y = rp.y_rear(0.50, 0.598)
    if y is not None:
        add(body_name, text_mesh("__nissan_c", "N I S S A N", 0.026, "s13_badge_chrome", location=(0.50, y + 0.002, 0.598),
                                 rotation=(math.radians(90), 0, math.radians(180)), extrude=0.0012))
    # trunk: 240SX script right of centre, round emblem above, key lock below
    ts = DET.Surface(out["s13_trunk"])
    y = ts.y_rear(-0.15, 0.700)
    if y is not None:
        add("s13_trunk", text_mesh("__240sx_c", "240SX", 0.034, "s13_badge_chrome", location=(-0.15, y + 0.003, 0.700),
                                   rotation=(math.radians(90), 0, math.radians(180)), extrude=0.0014))
    y = ts.y_rear(0.0, 0.838)
    if y is not None:
        mb = MeshBuilder("__trunk_emblem")
        c = Vector((0.0, y + 0.004, 0.838))
        ring = [(c.x + 0.030 * math.cos(2 * math.pi * k / 32), c.y, c.z + 0.030 * math.sin(2 * math.pi * k / 32))
                for k in range(32)]
        mb.polygon(ring, "s13_badge_chrome", outward=(0, 1, 0))
        mb.box((0.0, c.y + 0.0012, c.z), (0.052, 0.002, 0.008), "s13_badge_blue")
        yk = ts.y_rear(0.0, 0.672)
        if yk is not None:
            mb.cylinder((0.0, yk - 0.002, 0.672), (0.0, yk + 0.004, 0.672), 0.011, "s1x_chrome", segs=16)
        add("s13_trunk", mb.to_object())
    if kind == "convertible":
        add(body_name, tonneau().to_object())

    for target, obs in joins.items():
        out[target] = P.join([out[target]] + obs, target)


def tonneau():
    """Hard body-colour cover over the folded-top well, between the rear seat back and the deck."""
    mb = MeshBuilder("__tonneau")
    y0, y1 = S.CONV_TONNEAU_Y
    ys = list(np.linspace(y0 + 0.04, y1, 12))
    xs = np.linspace(-1, 1, 25)
    rows = []
    for y in ys:
        w = min(SPEC.g("w_belt", 1.55), 0.745) - 0.004
        rows.append([(float(u * w), float(y), top_z(SPEC, 1.603, abs(float(u * w))) - 0.004) for u in xs])
    # rounded front nose dropping toward the seat back
    nose = []
    for k, a in enumerate(np.linspace(0, math.pi / 2, 5)[1:]):
        r = 0.04
        nose.append([(x, y0 + 0.04 - r * math.sin(a), z - r * (1 - math.cos(a))) for x, _, z in rows[0]])
    rows = nose[::-1] + rows
    n = len(xs)
    verts = [v for r in rows for v in r]
    faces = [(i * n + j, i * n + j + 1, (i + 1) * n + j + 1, (i + 1) * n + j) for i in range(len(rows) - 1)
             for j in range(n - 1)]
    mb.add_faces(verts, faces, "s13_paint", smooth=True)
    # underside skin so the edge reads as a thick panel
    verts2 = [(x, y, z - 0.012) for x, y, z in verts]
    faces2 = [f[::-1] for f in faces]
    mb.add_faces(verts2, faces2, "s13_interior_trim", smooth=True)
    return mb


# ---------------------------------------------------------------------------
# coupe interior pieces and trunk spoilers
# ---------------------------------------------------------------------------
def parcel_shelf():
    """Package tray from the rear seat back to the rear window base (coupe)."""
    mb = MeshBuilder("s13_parcelshelf")
    ys = np.linspace(1.16, 1.60, 10)
    xs = np.linspace(-1, 1, 21)
    verts = []
    for y in ys:
        w = side_x(SPEC, float(y), 0.88) - 0.07
        for u in xs:
            verts.append((float(u * w), float(y), 0.885 + 0.012 * (1 - u * u) - 0.01 * (y - 1.16)))
    n = len(xs)
    faces = [(i * n + j, i * n + j + 1, (i + 1) * n + j + 1, (i + 1) * n + j) for i in range(len(ys) - 1) for j in range(n - 1)]
    mb.add_faces(verts, faces, "s13_carpet", smooth=True)
    for s in (1, -1):                                   # speaker grilles
        mb.rbox((s * 0.40, 1.42, 0.886), (0.20, 0.13, 0.012), 0.02, "s1x_dark")
    return mb


def headliner_coupe():
    mb = MeshBuilder("s13_headliner_coupe")
    ys = np.linspace(-0.12, 0.92, 18)
    xs = np.linspace(-0.52, 0.52, 17)
    verts = [(float(x), float(y), top_z(SPEC, float(y), abs(float(x))) - 0.035) for y in ys for x in xs]
    n = len(xs)
    faces = [(i * n + j, (i + 1) * n + j, (i + 1) * n + j + 1, i * n + j + 1) for i in range(len(ys) - 1) for j in range(n - 1)]
    mb.add_faces(verts, faces, "s13_headliner", smooth=True)
    return mb


def trunk_spoilers():
    out = []
    # OEM wing on two pedestals with the high-mount stop lamp in the centre (LE / SE)
    mb = MeshBuilder("s13_trunkspoiler_oem")
    span, chord = 0.64, 0.150
    y_le, z0 = 1.975, 0.990
    loop = [(0.0, 0.0), (0.03, 0.013), (0.085, 0.018), (chord, 0.014), (chord, 0.002), (0.07, -0.007)]
    n = len(loop)
    xs = np.linspace(-span, span, 17)
    verts, faces = [], []
    for i, x in enumerate(xs):
        droop = 0.012 * (abs(x) / span) ** 3                  # tips curve down slightly
        verts += [(float(x), y_le + u, z0 + v - droop) for u, v in loop]
        if i:
            a, b = (i - 1) * n, i * n
            faces += [(a + k, b + k, b + (k + 1) % n, a + (k + 1) % n) for k in range(n)]
    mb.add_faces(verts, faces, "s13_paint", smooth=True)
    for i, x in ((0, -span), (len(xs) - 1, span)):
        mb.polygon(verts[i * n:(i + 1) * n], "s13_paint", outward=(1 if x > 0 else -1, 0, 0))
    for s in (1, -1):
        zd = top_z(SPEC, y_le + 0.07, 0.50)
        mb.rbox((s * 0.50, y_le + 0.07, (zd + z0) / 2 - 0.003), (0.05, 0.10, z0 - zd + 0.012), 0.012, "s13_paint")
    mb.rbox((0.0, y_le + chord - 0.004, z0 + 0.010), (0.26, 0.010, 0.012), 0.004, "s13_chmsl")
    out.append(mb)
    # small rear-edge lip (ducktail)
    mb = MeshBuilder("s13_trunkspoiler_lip")
    xs = np.linspace(-0.66, 0.66, 25)
    rows = []
    for y, dz in ((2.075, 0.0), (2.140, 0.022), (2.165, 0.026), (2.160, 0.0)):
        rows.append([(float(x), y, top_z(SPEC, y, abs(float(x))) + dz + 0.0015) for x in xs])
    n = len(xs)
    verts = [v for r in rows for v in r]
    faces = [(i * n + j, i * n + j + 1, (i + 1) * n + j + 1, (i + 1) * n + j) for i in range(len(rows) - 1) for j in range(n - 1)]
    mb.add_faces(verts, faces, "s13_paint", smooth=True)
    for j in (0, n - 1):
        mb.polygon([rows[i][j] for i in range(len(rows))], "s13_paint", outward=(1 if xs[j] > 0 else -1, 0, 0))
    out.append(mb)
    return out
