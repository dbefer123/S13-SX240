"""Wheels, tires, hubcaps and steering wheels (shared s1x_ meshes, requires bpy).

Wheels/tires are modelled around the origin with the axle along X and the
outer face toward +X (BeamNG vanilla convention for wheel flexbodies).
"""
from __future__ import annotations

import math

from .prims import MeshBuilder

IN = 0.0254
PCD = 0.1143 / 2


WHEEL_STYLE = {
    #            spokes kind       face_depth hub_r  w0     w1     thick  dish   center_mat           lip_mat
    "steel":     (0, "steel", 0.050, 0.075, 0, 0, 0.004, 0.015, "s1x_wheel_steel", "s1x_wheel_steel"),
    "oem15_le":  (7, "spoke", 0.030, 0.072, 0.034, 0.024, 0.022, 0.012, "s1x_wheel_silver", "s1x_wheel_silver"),
    "oem15_se":  (5, "hole", 0.032, 0.075, 0.070, 0.050, 0.026, 0.010, "s1x_wheel_silver", "s1x_wheel_silver"),
    "mesh15":    (20, "mesh", 0.040, 0.070, 0.010, 0.008, 0.012, 0.010, "s1x_wheel_silver", "s1x_wheel_polished"),
    "sixspoke16": (6, "spoke", 0.035, 0.070, 0.040, 0.034, 0.026, 0.022, "s1x_wheel_bronze", "s1x_wheel_bronze"),
    "deepdish17": (6, "spoke", 0.085, 0.070, 0.036, 0.030, 0.024, 0.006, "s1x_wheel_black", "s1x_wheel_polished"),
    "split18":   (10, "spoke", 0.045, 0.070, 0.018, 0.016, 0.024, 0.020, "s1x_wheel_black", "s1x_wheel_black"),
    "race17":    (6, "spoke", 0.040, 0.070, 0.040, 0.032, 0.024, 0.024, "s1x_wheel_white", "s1x_wheel_white"),
    "race18":    (6, "spoke", 0.045, 0.070, 0.042, 0.034, 0.024, 0.026, "s1x_wheel_gunmetal", "s1x_wheel_gunmetal"),
    "beadlock15": (5, "hole", 0.045, 0.070, 0.060, 0.045, 0.020, 0.010, "s1x_wheel_black", "s1x_wheel_polished"),
    "runner15":  (8, "spoke", 0.030, 0.060, 0.016, 0.012, 0.010, 0.006, "s1x_wheel_polished", "s1x_wheel_polished"),
}
STYLE_FOR_KEY = {"steel14": "steel", "oem15_le": "oem15_le", "oem15_se": "oem15_se", "mesh15": "mesh15",
                 "sixspoke16": "sixspoke16", "deepdish17": "deepdish17", "split18": "split18", "race17": "race17",
                 "race18": "race18", "beadlock15": "beadlock15", "runner15": "runner15"}


def _barrel(mb, rb, w, lip_mat, barrel_mat, segs=64, lip=0.016):
    hw = w / 2
    # outer surface profile from outer lip to inner lip (r, x)
    prof = [
        (rb + lip, hw + 0.010), (rb + lip + 0.002, hw + 0.004), (rb + lip - 0.002, hw - 0.002),
        (rb + 0.002, hw - 0.006), (rb, hw - 0.016), (rb - 0.004, hw - 0.028), (rb - 0.022, hw * 0.25),
        (rb - 0.022, -hw * 0.35), (rb - 0.004, -hw + 0.030), (rb, -hw + 0.016), (rb + 0.002, -hw + 0.006),
        (rb + lip - 0.002, -hw + 0.002), (rb + lip, -hw - 0.008),
    ]
    # thickness: inner skin
    inner = [(r - 0.006, x) for r, x in prof[::-1]]
    closed = prof + inner
    mb.lathe(closed, barrel_mat, segs=segs, axis="x", closed=True)
    # polished/painted lip face ring on the outside
    mb.lathe([(rb - 0.006, hw - 0.001), (rb + lip + 0.001, hw + 0.011)], lip_mat, segs=segs, axis="x")


def _spoke(mb, theta, r0, r1, w0, w1, x_face, thick, dish, mat, twist=0.0, nr=6):
    """One spoke from radius r0 (hub) to r1 (rim) in the YZ plane, face at x_face (dish moves the hub outward)."""
    verts, faces = [], []
    across = [-1, 0, 1]
    for i in range(nr + 1):
        t = i / nr
        r = r0 + (r1 - r0) * t
        hw = (w0 + (w1 - w0) * t) / 2
        x = x_face - dish * (1 - t) ** 1.5 * -1  # hub sits further outboard by `dish`
        ang = theta + twist * t
        for front in (0, 1):
            xx = x - (0 if front else thick)
            for a in across:
                # point at radius r, lateral offset a*hw (perpendicular to the spoke direction)
                y = r * math.cos(ang) - a * hw * math.sin(ang)
                z = r * math.sin(ang) + a * hw * math.cos(ang)
                bevel = 0.0 if a == 0 else (0.003 if front else 0.0)
                verts.append((xx - bevel, y, z))
    stride = 6
    for i in range(nr):
        b0, b1 = i * stride, (i + 1) * stride
        # front face (x high): indices 0..2 front, 3..5 back
        faces += [(b0 + 0, b0 + 1, b1 + 1, b1 + 0), (b0 + 1, b0 + 2, b1 + 2, b1 + 1)]
        faces += [(b0 + 4, b0 + 3, b1 + 3, b1 + 4), (b0 + 5, b0 + 4, b1 + 4, b1 + 5)]
        faces += [(b0 + 3, b0 + 0, b1 + 0, b1 + 3), (b0 + 2, b0 + 5, b1 + 5, b1 + 2)]
    mb.add_faces(verts, faces, mat, smooth=True)


def wheel_mesh(key, dia, width, lugs, name=None):
    style = STYLE_FOR_KEY.get(key, "oem15_se")
    n, kind, depth, hub_r, w0, w1, thick, dish, cmat, lmat = WHEEL_STYLE[style]
    mb = MeshBuilder(name or f"s1x_wheel_{key}")
    rb = dia * IN / 2
    w = width * IN
    _barrel(mb, rb, w, lmat, cmat if style not in ("deepdish17", "beadlock15", "mesh15") else "s1x_wheel_barrel")
    x_face = w / 2 - depth
    r_in = rb - 0.012
    if kind == "steel":
        # pressed steel disc with vent holes
        prof = [(0.0, x_face + 0.012), (hub_r, x_face + 0.012), (hub_r + 0.02, x_face + 0.004), (r_in * 0.62, x_face - 0.004),
                (r_in * 0.75, x_face - 0.010), (r_in, x_face - 0.030)]
        mb.lathe(prof, cmat, segs=48, axis="x")
        for k in range(8):
            a = 2 * math.pi * k / 8
            yc, zc = math.cos(a) * r_in * 0.82, math.sin(a) * r_in * 0.82
            mb.cylinder((x_face - 0.012, yc, zc), (x_face - 0.008, yc, zc), 0.016, "s1x_dark", segs=12)
    elif kind in ("spoke", "mesh"):
        mb.lathe([(0.0, x_face + 0.010), (hub_r, x_face + 0.010), (hub_r + 0.004, x_face - thick),
                  (0.0, x_face - thick)], cmat, segs=48, axis="x", closed=True)
        if kind == "mesh":
            for layer, tw in ((0, 0.35), (1, -0.35)):
                for k in range(n):
                    _spoke(mb, 2 * math.pi * k / n, hub_r, r_in, w0, w1, x_face - layer * 0.006, thick, dish, cmat, twist=tw)
        elif style == "split18":
            for k in range(n // 2):
                base = 2 * math.pi * k / (n // 2)
                for off in (-0.09, 0.09):
                    _spoke(mb, base + off, hub_r, r_in, w0, w1, x_face, thick, dish, cmat, twist=off * 0.6)
        else:
            for k in range(n):
                _spoke(mb, 2 * math.pi * k / n, hub_r, r_in, w0, w1, x_face, thick, dish, cmat)
    elif kind == "hole":
        # solid disc with n windows -> approximated by n wide spokes plus a face ring
        mb.lathe([(0.0, x_face + 0.010), (hub_r, x_face + 0.010), (hub_r, x_face - thick), (0.0, x_face - thick)],
                 cmat, segs=48, axis="x", closed=True)
        for k in range(n):
            _spoke(mb, 2 * math.pi * (k + 0.5) / n, hub_r, r_in, w0 * 1.25, w1 * 1.7, x_face, thick, dish, cmat)
        mb.lathe([(r_in * 0.86, x_face + 0.002), (r_in, x_face - 0.004), (r_in, x_face - 0.014), (r_in * 0.86, x_face - 0.012)],
                 cmat, segs=48, axis="x", closed=True)
        if style == "beadlock15":
            mb.lathe([(rb + 0.004, w / 2 + 0.016), (rb + 0.034, w / 2 + 0.016), (rb + 0.034, w / 2 + 0.004), (rb + 0.004, w / 2 + 0.004)],
                     "s1x_wheel_polished", segs=48, axis="x", closed=True)
            for k in range(24):
                a = 2 * math.pi * k / 24
                yc, zc = math.cos(a) * (rb + 0.019), math.sin(a) * (rb + 0.019)
                mb.cylinder((w / 2 + 0.016, yc, zc), (w / 2 + 0.022, yc, zc), 0.004, "s1x_lugnut", segs=6)
    # lug nuts + centre cap
    for k in range(lugs):
        a = 2 * math.pi * k / lugs + math.pi / lugs
        yc, zc = PCD * math.cos(a), PCD * math.sin(a)
        mb.cylinder((x_face + 0.008, yc, zc), (x_face + 0.024, yc, zc), 0.0095, "s1x_lugnut", segs=6)
    mb.lathe([(0.0, x_face + 0.026), (0.028, x_face + 0.024), (0.034, x_face + 0.012), (0.036, x_face + 0.006)],
             "s1x_wheel_cap" if style != "steel" else "s1x_wheel_steel", segs=24, axis="x")
    return mb


def tire_mesh(name, radius, width_mm, aspect, dia, kind, rim_w=None, segs=72):
    """Tire as a lathe of its cross-section (inner bead -> tread -> outer bead)."""
    rb = dia * IN / 2
    R = radius
    sw = width_mm / 1000.0
    H = R - rb
    rw = (rim_w or sw * 0.82) / 2            # bead half-width (rim flanges)
    tw = sw * (0.78 if kind not in ("slick", "dragslick") else 0.90) / 2
    bulge = sw / 2 * (1.0 if kind != "dragslick" else 1.05)
    sh = min(0.022 if kind != "dragslick" else 0.04, H * 0.3)
    half = []
    # sidewall from bead (t=0) to the shoulder start
    for t in [0.0, 0.06, 0.16, 0.30, 0.45, 0.60, 0.72, 0.82]:
        r = rb + (H - sh) * t / 0.82
        k = math.sin(math.pi / 2 * min(t / 0.5, 1.0))
        x = rw + (bulge - rw) * k
        if t > 0.55:
            x -= (bulge - (tw + sh * 0.7)) * ((t - 0.55) / 0.27) ** 2
        half.append((r, x))
    # shoulder (quarter round)
    r0, x0 = half[-1]
    for k in range(1, 6):
        a = (math.pi / 2) * k / 5
        half.append((r0 + (R - r0) * math.sin(a), x0 - (x0 - tw) * (1 - math.cos(a))))
    grooves = {"allseason": 4, "sport": 4, "semislick": 2, "drift": 3, "dragradial": 2, "runner": 2}.get(kind, 0)
    tread = []
    n = 28
    gpos = [(-tw * 0.75 + 1.5 * tw * (g + 0.5) / grooves) for g in range(grooves)] if grooves else []
    for i in range(1, n):
        x = tw - 2 * tw * i / n
        depth = 0.007 if any(abs(x - g) < 0.0055 for g in gpos) else 0.0
        tread.append((R - depth, x))
    prof = [(r, -x) for r, x in half] + tread[::-1] and None
    prof = [(r, -x) for r, x in half] + sorted(tread, key=lambda q: q[1]) + [(r, x) for r, x in half[::-1]]
    mb = MeshBuilder(name)
    mb.lathe(prof, "s1x_tire" if kind not in ("slick", "dragslick") else "s1x_tire_slick", segs=segs, axis="x")
    return mb


def hubcap_mesh(dia, name):
    mb = MeshBuilder(name)
    rb = dia * IN / 2
    x0 = 3.0 * IN - 0.040
    prof = [(0.0, x0 + 0.050), (0.04, x0 + 0.048), (0.09, x0 + 0.040), (0.13, x0 + 0.026), (rb - 0.015, x0 + 0.008),
            (rb - 0.004, x0 - 0.004)]
    mb.lathe(prof, "s1x_hubcap", segs=48, axis="x")
    for k in range(10):
        a = 2 * math.pi * k / 10
        yc, zc = math.cos(a) * 0.115, math.sin(a) * 0.115
        mb.box((x0 + 0.032, yc, zc), (0.004, 0.02, 0.05), "s1x_dark",
               rot=__import__("mathutils").Matrix.Rotation(a, 3, "X"))
    return mb


def steering_wheel_mesh(kind, name):
    """Upright wheel: rim in the local XZ plane, column axis along local +Y (toward the driver), origin at hub."""
    mb = MeshBuilder(name)
    if kind == "stock":
        R, rr, dish, spokes, mat = 0.185, 0.016, 0.03, 3, "s1x_steer_leather"
    elif kind == "deepdish":
        R, rr, dish, spokes, mat = 0.175, 0.016, 0.085, 3, "s1x_steer_suede"
    else:
        R, rr, dish, spokes, mat = 0.160, 0.017, 0.02, 3, "s1x_steer_suede"
    pts = []
    for k in range(48):
        a = 2 * math.pi * k / 48
        z = R * math.sin(a)
        if kind == "race" and z < -R * 0.78:
            z = -R * 0.78
        pts.append((R * math.cos(a), dish, z))
    pts.append(pts[0])
    mb.tube(pts, rr, mat, segs=10, caps=False)
    hub_mat = "s1x_steer_metal" if kind != "stock" else "s13_interior_plastic"
    mb.cylinder((0, -0.03, 0), (0, dish * 0.6 + 0.02, 0), 0.035 if kind != "stock" else 0.055, hub_mat, segs=20)
    for k in range(spokes):
        a = -math.pi / 2 + (2 * math.pi * k / spokes if kind != "stock" else [0, 2.4, -2.4][k] + 0.0)
        if kind == "stock":
            a = [-math.pi / 2, math.pi * 0.1, math.pi * 0.9][k]
        mb.tube([(0, dish * 0.5, 0), (R * 0.92 * math.cos(a), dish, R * 0.92 * math.sin(a))], 0.011,
                hub_mat if kind != "stock" else "s13_interior_plastic", segs=8)
    return mb
