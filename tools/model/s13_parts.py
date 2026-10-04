"""S13-specific meshes: underbody, wheel wells, engine bay, pop-up lamps,
radiator, fuel tank and the interior (requires bpy)."""
from __future__ import annotations

import math

import numpy as np
from mathutils import Matrix, Vector

from .prims import MeshBuilder, rounded_rect
from .shape import top_z, side_x
from tools.vehicle.s13 import body_spec as B
from tools.vehicle.s13 import dims as D
from tools.vehicle.s13 import panels_jb as PJ

SPEC = B.hatch_spec()
M_UNDER = "s13_undercoat"
M_INT = "s13_interior_plastic"
M_INT2 = "s13_interior_plastic_light"
M_CARPET = "s13_carpet"
M_CLOTH = "s13_seat_cloth"


def grid_faces(nu, nv, flip=False):
    f = []
    for i in range(nu - 1):
        for j in range(nv - 1):
            a, b, c, d = i * nv + j, (i + 1) * nv + j, (i + 1) * nv + j + 1, i * nv + j + 1
            f.append((a, d, c, b) if flip else (a, b, c, d))
    return f


def underbody():
    mb = MeshBuilder("s13_underbody")
    ys = np.linspace(-2.05, 2.15, 60)
    xs = np.linspace(-0.80, 0.80, 25)
    verts = []
    for y in ys:
        k = SPEC.keypoints(float(y))
        for x in xs:
            w = k["w_sill"] - 0.03
            xx = float(np.clip(x, -w, w))
            z = k["z_bot"] + 0.004
            if abs(xx) < 0.15 and -0.90 < y < 0.75:      # transmission tunnel
                z += 0.10 * (1 - (abs(xx) / 0.15) ** 2)
            verts.append((xx, float(y), z))
    mb.add_faces(verts, grid_faces(len(ys), len(xs), flip=False), M_UNDER, smooth=True)       # faces the road
    # upper side (seen from the cabin, the cargo area and the open engine bay): own vertices, 1.5 mm up
    mb.add_faces([(x, y, z + 0.0015) for x, y, z in verts], grid_faces(len(ys), len(xs), flip=True), M_UNDER, smooth=True)
    return mb


def wheelwells():
    mb = MeshBuilder("s13_wheelwells")
    for (cy, cz), track in (((D.AXLE_F_Y, D.AXLE_Z), D.TRACK_F), ((D.AXLE_R_Y, D.AXLE_Z), D.TRACK_R)):
        for s in (1, -1):
            r = 0.372
            x_in, x_out = 0.50, 0.83
            verts = []
            n = 28
            for i in range(n + 1):
                a = math.pi * (-0.05 + 1.10 * i / n)
                y = cy - r * math.cos(a)
                z = cz + r * math.sin(a)
                verts.append((s * x_in, y, z))
                verts.append((s * x_out, y, z))
            faces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) if s < 0 else (2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1) for i in range(n)]
            mb.add_faces(verts, faces, M_UNDER, smooth=True)                 # faces the wheel
            # back of the arch (seen from the engine bay and the cabin): own vertices, 2 mm further out
            k = (r + 0.002) / r
            back = [(x, cy + (y - cy) * k, cz + (z - cz) * k) for x, y, z in verts]
            mb.add_faces(back, [f[::-1] for f in faces], M_UNDER, smooth=True)
            # inner wall disc, both sides
            prof = [(0.0, 0.0), (r, 0.0)]
            mb.lathe(prof, M_UNDER, segs=24, axis="x", center=(s * x_in, cy, cz),
                     angle=(math.pi, 0) if s > 0 else (0, math.pi))          # faces the wheel
            mb.lathe(prof, M_UNDER, segs=24, axis="x", center=(s * (x_in - 0.002), cy, cz),
                     angle=(0, math.pi) if s > 0 else (math.pi, 0))          # faces the cabin / engine bay
    return mb


def enginebay():
    mb = MeshBuilder("s13_enginebay")
    for s in (1, -1):
        # inner fender apron wall, its top following the underside of the hood/nose
        verts = []
        ys = np.linspace(-2.02, -0.90, 15)
        for y in ys:
            ztop = min(0.66, top_z(SPEC, float(y), 0.74) - 0.045)
            for z in (0.30, 0.50, ztop):
                x = 0.66 if z < ztop - 0.01 else 0.69
                if -1.62 < y < -0.92 and z < ztop - 0.01:
                    x = 0.60                                  # strut tower bulge
                verts.append((s * x, float(y), z))
        mb.add_faces(verts, grid_faces(len(ys), 3, flip=s > 0), "s13_enginebay_paint", smooth=False)   # faces the bay
        # strut tower top
        mb.cylinder((s * D.FS1[0], D.FS1[1], D.FS1[2] - 0.025), (s * D.FS1[0], D.FS1[1], D.FS1[2] - 0.005), 0.09,
                    "s13_enginebay_paint", segs=20)
    # firewall (top follows the cowl)
    verts = []
    xs = np.linspace(-0.72, 0.72, 13)
    for k, z in enumerate((0.22, 0.45, 0.68, None)):
        for x in xs:
            zz = z if z is not None else min(0.84, top_z(SPEC, -0.90, abs(float(x))) - 0.03)
            verts.append((float(x), -0.885 + (0.02 if z is None else 0.0), zz))
    mb.add_faces(verts, grid_faces(4, len(xs), flip=True), "s13_enginebay_paint", smooth=False)   # faces forward
    # cabin side (seen under race / stripped dashes): own vertices, 2 mm rearward, sound-deadening black
    mb.add_faces([(x, y + 0.002, z) for x, y, z in verts], grid_faces(4, len(xs), flip=False), M_UNDER, smooth=False)
    # radiator core support (upper bar)
    mb.rbox((0.0, -2.06, min(0.555, top_z(SPEC, -2.06, 0.0) - 0.05)), (0.95, 0.05, 0.04), 0.008, "s13_enginebay_paint")
    return mb


def popup_lamps():
    """Pop-up headlamp pods (geometry from tools/vehicle/s13/popup_geom.py), modelled raised and rotated closed."""
    from tools.vehicle.s13 import popup_geom as PG
    out = []
    th = math.radians(PG.POPUP_ANGLE)
    x0, x1 = PG.X0, PG.X1
    xm = (x0 + x1) / 2
    prof = PG.raised_profile()
    Fy, Fz = prof[0]
    closed = PG.closed
    lens_n = (0, -math.cos(th), -math.sin(th))
    for side, s in (("L", 1), ("R", -1)):
        mb = MeshBuilder(f"s13_popup_lamp_{side}")
        xa, xb = s * x0, s * x1
        P = [closed(y, z) for y, z in prof]
        verts = [(xa, y, z) for y, z in P] + [(xb, y, z) for y, z in P]
        n = len(P)
        faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        faces += [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
        if s < 0:
            faces = [f[::-1] for f in faces]
        mb.add_faces(verts, faces, "s13_popup_housing", smooth=False)
        inset = 0.010
        lz0, lz1 = Fz - PG.LENS_H + inset, Fz - inset
        lens = [(xa + s * inset, Fy - 0.004, lz0), (xb - s * inset, Fy - 0.004, lz0), (xb - s * inset, Fy - 0.004, lz1),
                (xa + s * inset, Fy - 0.004, lz1)]
        mb.polygon([(x, *closed(y, z)) for x, y, z in lens], "s13_headlight", outward=lens_n)
        for k in (-1, 1):
            cx_ = s * (xm + k * 0.065)
            for r_, mat, dy in ((0.045, "s13_headlight_chrome", 0.0055), (0.012, "s1x_dark", 0.006)):
                ring = [(cx_ + r_ * math.cos(2 * math.pi * j / 20),
                         *closed(Fy - dy, (lz0 + lz1) / 2 + r_ * math.sin(2 * math.pi * j / 20))) for j in range(20)]
                mb.polygon(ring, mat, outward=lens_n)
        out.append(mb)
    return out


def led_projectors():
    """Small LED projector headlamps in the bumper corners (pop-up delete)."""
    out = []
    for side, s in (("L", 1), ("R", -1)):
        mb = MeshBuilder(f"s13_led_projector_{side}")
        c = Vector((s * 0.52, -2.205, 0.395))
        mb.cylinder(tuple(c + Vector((0, 0.06, 0))), tuple(c), 0.042, "s1x_metal_black", segs=24)
        mb.cylinder(tuple(c), tuple(c + Vector((0, -0.006, 0))), 0.036, "s13_headlight", segs=24)
        mb.cylinder(tuple(c + Vector((0, -0.006, 0))), tuple(c + Vector((0, -0.010, 0))), 0.012, "s1x_dark", segs=12)
        out.append(mb)
    return out


def radiator():
    mb = MeshBuilder("s13_radiator")
    mb.rbox((0.0, -1.96, 0.42), (0.66, 0.035, 0.25), 0.006, "s1x_radiator_core")
    for s in (1, -1):
        mb.rbox((s * 0.35, -1.96, 0.42), (0.05, 0.05, 0.27), 0.01, "s1x_plastic_black")
    mb.cylinder((0.0, -1.93, 0.42), (0.0, -1.88, 0.42), 0.16, "s1x_plastic_black", segs=24)  # fan shroud
    return mb


def fueltank():
    mb = MeshBuilder("s13_fueltank")
    mb.rbox((0.0, 0.89, 0.235), (0.80, 0.28, 0.13), 0.04, "s1x_metal_black")
    return mb


# ---------------------------------------------------------------------------
# interior
# ---------------------------------------------------------------------------
def _loft_x(name_mb, xs, profile_fn, mat, closed=False, flip=False):
    rows = [profile_fn(float(x)) for x in xs]
    n = len(rows[0])
    verts = [(float(x), y, z) for x, row in zip(xs, rows) for (y, z) in row]
    faces = grid_faces(len(xs), n, flip=flip)
    if closed:
        for i in range(len(xs) - 1):
            a, b = i * n + n - 1, (i + 1) * n + n - 1
            faces.append((a, b, (i + 1) * n, i * n) if not flip else (a, i * n, (i + 1) * n, b))
    return name_mb.add_faces(verts, faces, mat, smooth=True)


def _plateau(x, c, half, ramp):
    """1 inside |x-c| < half, 0 beyond half+ramp, smooth in between."""
    d = abs(x - c)
    if d <= half:
        return 1.0
    if d >= half + ramp:
        return 0.0
    t = (d - half) / ramp
    return 1.0 - t * t * (3 - 2 * t)


GLASS_CLEAR = 0.014        # dash / binnacle clearance under the windshield's outer surface
DASH_UNDER_COWL = 0.10     # how far the dash top continues forward under the cowl (past the glass base)


def _cowl_top_s13(x, y):
    return top_z(SPEC, y, min(abs(x), 0.66))


# top of the windshield / cowl skin at (x, y) in these (S13) coordinates; build_s14 swaps in the S14 skin seen
# through the S13 -> S14 warp while it generates the (warped) S14 dash and race dash
COWL_TOP = _cowl_top_s13


def under_glass(x, y, z, clear=GLASS_CLEAR):
    """Clamp a dash point below the windshield / cowl (top surface) ahead of the A-pillar base."""
    if y < -0.40:
        z = min(z, COWL_TOP(x, y) - clear)
    return z


def dash_loft(mb, normal, cluster, mat=None, x_lo=-0.74, x_hi=0.74, ramp=0.035):
    """Loft the dash along x: the `normal` profile blends into the `cluster` (binnacle) profile around the
    column.  Both are [(y, z)] lists of equal length running from the windshield base, over the top, down the
    face and back along the underside; every point is kept under the glass."""
    cx = D.STEER_CENTER[0]

    def prof(x):
        k = _plateau(x, cx, D.GAUGE_W / 2 + 0.025, ramp)
        pts = [(a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k) for a, b in zip(normal(x), cluster(x))]
        # front lip carried on under the cowl: the driver's sight line over the dash top must end on the dash,
        # not pass under the windshield's lower edge into the engine bay
        out = [(pts[0][0] - DASH_UNDER_COWL, COWL_TOP(x, pts[0][0] - DASH_UNDER_COWL) - 0.012)]
        return out + [(y, under_glass(x, y, z)) for y, z in pts]

    xs = np.concatenate([np.linspace(x_lo, cx - 0.32, 26), np.linspace(cx - 0.31, min(cx + 0.31, x_hi), 40)])
    xs = np.unique(np.round(xs, 4))
    _loft_x(mb, xs, prof, mat or M_INT)          # faces up / toward the cabin
    # side caps of the dash ends
    for x in (xs[0], xs[-1]):
        pts = prof(float(x))
        mb.polygon([(float(x), y, z) for y, z in pts], mat or M_INT, (1 if x > 0 else -1, 0, 0))
    return prof


def column_shroud(mb, r=0.05, mat=None):
    """Steering column shroud from the wheel into the lower cluster bezel, with the combination switch stalks."""
    sc = Vector(D.STEER_CENTER)
    a = math.radians(23)
    d = Vector((0, -math.cos(a), -math.sin(a)))
    # ends at the lower cluster bezel: further in it would show inside the gauge recess
    mb.tube([tuple(sc + d * 0.05), tuple(sc + d * 0.078)], r, mat or M_INT, segs=14)
    for s_ in (1, -1):
        b = sc + d * 0.075
        mb.tube([tuple(b), tuple(b + Vector((s_ * 0.13, 0.02, 0.01)))], 0.006, "s1x_dark", segs=8)


def dash():
    """Dash top/face loft with the S13's raised cluster binnacle and gauge recess on the driver side."""
    mb = MeshBuilder("s13_dash")
    gy, gz, gh = D.GAUGE_Y, D.GAUGE_Z, D.GAUGE_H

    def normal(x):
        wall = 0.73 - 0.04 * math.cos(x * 2.0)
        return [(-0.80, 0.86), (-0.72, 0.880), (-0.64, 0.898), (-0.57, 0.906), (-0.51, 0.905), (-0.488, 0.899),
                (-0.474, 0.889), (-0.465, 0.874), (-0.457, 0.856), (-0.450, 0.835), (-0.444, 0.810), (-0.440, 0.780),
                (-0.44, wall), (-0.48, 0.61), (-0.62, 0.56), (-0.80, 0.55)]

    def cluster(x):
        wall = 0.73 - 0.04 * math.cos(x * 2.0)
        return [(-0.80, 0.86), (-0.72, 0.888), (-0.64, 0.925), (-0.57, 0.958), (-0.51, 0.990), (-0.468, 1.006),
                (-0.446, 1.008), (-0.436, 1.002), (-0.442, 0.995), (gy - 0.002, gz + gh / 2 + 0.008),
                (gy - 0.002, gz - gh / 2 - 0.008), (-0.452, 0.842), (-0.44, wall), (-0.48, 0.61), (-0.62, 0.56),
                (-0.80, 0.55)]

    dash_loft(mb, normal, cluster)
    # centre stack
    mb.rbox((0.0, -0.50, 0.66), (0.28, 0.10, 0.20), 0.02, M_INT)
    textured_quad(mb, (0.0, -0.449, 0.70), 0.21, 0.065, "s13_radio")
    textured_quad(mb, (0.0, -0.449, 0.612), 0.21, 0.060, "s13_hvac")
    # vents
    for x in (-0.55, -0.12, 0.12, 0.62):
        z = 0.80 if abs(x) > 0.3 else 0.79
        mb.rbox((x, -0.45, z), (0.10, 0.012, 0.045), 0.006, "s1x_dark")
        for k in range(4):
            mb.box((x, -0.443, z - 0.015 + k * 0.01), (0.092, 0.004, 0.003), "s13_interior_plastic_light")
    # glovebox outline
    mb.rbox((-0.42, -0.432, 0.70), (0.34, 0.006, 0.13), 0.01, M_INT2)
    column_shroud(mb)
    return mb


def textured_quad(mb, center, w, h, mat, normal="+y"):
    """Quad facing the driver (+y) with 0..1 UVs (u = driver's left -> right)."""
    cx, cy, cz = center
    verts = [(cx + w / 2, cy, cz - h / 2), (cx - w / 2, cy, cz - h / 2), (cx - w / 2, cy, cz + h / 2), (cx + w / 2, cy, cz + h / 2)]
    fs = mb.add_faces(verts, [(0, 1, 2, 3)], mat, smooth=False)
    for f in fs:
        for loop in f.loops:
            x, z = loop.vert.co.x, loop.vert.co.z
            loop[mb.uv].uv = ((cx + w / 2 - x) / w, (z - (cz - h / 2)) / h)
    return fs


def gauges():
    """Instrument cluster face (textured, glow-mapped) recessed in the hood, facing the driver (+y)."""
    mb = MeshBuilder("s13_gauges")
    cx = D.STEER_CENTER[0]
    gy, gz, w, h = D.GAUGE_Y, D.GAUGE_Z, D.GAUGE_W, D.GAUGE_H
    verts = [(cx + w / 2, gy, gz - h / 2), (cx - w / 2, gy, gz - h / 2), (cx - w / 2, gy, gz + h / 2), (cx + w / 2, gy, gz + h / 2)]
    fs = mb.add_faces(verts, [(0, 1, 2, 3)], "s13_gaugeface", smooth=False)
    # 0..1 UVs for the gauge texture (u from the driver's left to right, v up)
    for f in fs:
        for loop in f.loops:
            x, z = loop.vert.co.x, loop.vert.co.z
            loop[mb.uv].uv = ((cx + w / 2 - x) / w, (z - (gz - h / 2)) / h)
    # surround / bezel (the binnacle hood is part of the dash)
    mb.rbox((cx, gy - 0.006, gz), (w + 0.03, 0.01, h + 0.016), 0.006, "s1x_dark")
    # clear lens (slightly tinted) in front of the face
    lv = [(cx + w / 2, gy + 0.012, gz - h / 2), (cx - w / 2, gy + 0.012, gz - h / 2), (cx - w / 2, gy + 0.016, gz + h / 2),
          (cx + w / 2, gy + 0.016, gz + h / 2)]
    mb.add_faces(lv, [(0, 1, 2, 3)], "s13_gauge_glass", smooth=False)
    return mb


def needles():
    out = []
    for name, L in (("s13_needle_tach", 0.052), ("s13_needle_speedo", 0.052), ("s13_needle_small", 0.026)):
        mb = MeshBuilder(name)
        # pointing up (+z), in the x-z plane, slightly in front of the face (+y)
        verts = [(-0.0025, 0.002, -0.008), (0.0025, 0.002, -0.008), (0.0008, 0.002, L), (-0.0008, 0.002, L)]
        mb.add_faces(verts, [(0, 1, 2, 3), (3, 2, 1, 0)], "s13_needle", smooth=False)
        mb.cylinder((0, 0.0, 0), (0, 0.006, 0), 0.006, "s1x_dark", segs=10)
        out.append(mb)
    return out


def pedals():
    out = []
    for name, w in (("s13_pedal_gas", 0.04), ("s13_pedal_brake", 0.075), ("s13_pedal_clutch", 0.065)):
        mb = MeshBuilder(name)
        mb.tube([(0, 0, 0), (0, 0.015, -0.12), (0, 0.04, -0.20)], 0.006, "s1x_metal_black", segs=8)
        mb.rbox((0, 0.045, -0.22), (w, 0.012, 0.06 if "gas" not in name else 0.09), 0.006, "s1x_rubber")
        out.append(mb)
    mb = MeshBuilder("s13_pedals_static")
    mb.rbox((D.STEER_CENTER[0], -0.88, 0.50), (0.25, 0.04, 0.14), 0.01, "s1x_metal_black")
    out.append(mb)
    return out


def console():
    mb = MeshBuilder("s13_console")
    mb.rbox((0.0, -0.10, 0.37), (0.22, 0.70, 0.16), 0.04, M_INT)
    mb.rbox((0.0, 0.30, 0.42), (0.24, 0.24, 0.10), 0.03, M_INT2)          # armrest
    mb.rbox((0.0, -0.20, 0.457), (0.12, 0.16, 0.01), 0.004, "s1x_rubber")  # shifter boot base
    mb.rbox((0.10, 0.08, 0.46), (0.03, 0.22, 0.02), 0.008, M_INT)          # handbrake lever
    return mb


def carpet():
    mb = MeshBuilder("s13_carpet")
    ys = np.linspace(-0.86, 1.05, 30)
    xs = np.linspace(-0.76, 0.76, 25)
    verts = []
    for y in ys:
        k = SPEC.keypoints(float(y))
        for x in xs:
            z = 0.175 + 0.012
            if abs(x) < 0.16 and y < 0.70:
                z += 0.13 * (1 - (abs(x) / 0.16) ** 2)
            if y > 0.62:
                z = max(z, 0.20 + (y - 0.62) * 0.25)
            if y < -0.62:                                   # toe board rising to the firewall
                z += (-0.62 - y) * 1.2
            verts.append((float(x), float(y), z))
    mb.add_faces(verts, grid_faces(len(ys), len(xs), flip=True), M_CARPET, smooth=True)
    return mb


def headliner():
    mb = MeshBuilder("s13_headliner")
    ys = np.linspace(-0.12, 0.84, 16)
    xs = np.linspace(-0.52, 0.52, 17)
    verts = []
    for y in ys:
        for x in xs:
            verts.append((float(x), float(y), top_z(SPEC, float(y), float(x)) - 0.035))
    mb.add_faces(verts, grid_faces(len(ys), len(xs), flip=False), "s13_headliner", smooth=True)
    return mb


def seat(mb, x, cloth, bolster=0.055, front=True):
    y_h, z_h = D.SEAT_H_POINT[1], D.SEAT_H_POINT[2]
    # cushion
    mb.rbox((x, y_h - 0.10, z_h - 0.04), (0.46, 0.46, 0.10), 0.04, cloth)
    for s in (1, -1):
        mb.rbox((x + s * 0.21, y_h - 0.10, z_h + 0.005), (0.07, 0.44, 0.08), 0.03, cloth)
    # backrest (reclined 18 deg)
    rot = Matrix.Rotation(math.radians(-18), 3, "X")
    c = Vector((x, y_h + 0.14, z_h + 0.30))
    mb.rbox(tuple(c), (0.46, 0.10, 0.58), 0.04, cloth, rot=rot)
    for s in (1, -1):
        mb.rbox(tuple(c + rot @ Vector((s * 0.21, -0.03, -0.05))), (0.07, 0.12, 0.46), 0.03, cloth, rot=rot)
    # headrest
    mb.rbox(tuple(c + rot @ Vector((0, 0.0, 0.36))), (0.24, 0.09, 0.17), 0.04, cloth, rot=rot)
    # frame / rails
    mb.rbox((x, y_h - 0.10, 0.21), (0.40, 0.42, 0.05), 0.01, "s1x_metal_black")


def seats(name="s13_seats_cloth", cloth=M_CLOTH):
    mb = MeshBuilder(name)
    for x in (D.DRIVER_X, -D.DRIVER_X):
        seat(mb, x, cloth)
    return mb


def rearseat(name="s13_rearseat", cloth=M_CLOTH):
    mb = MeshBuilder(name)
    mb.rbox((0.0, 0.86, 0.36), (1.10, 0.38, 0.12), 0.04, cloth)
    rot = Matrix.Rotation(math.radians(-30), 3, "X")
    mb.rbox((0.0, 1.05, 0.62), (1.10, 0.10, 0.48), 0.04, cloth, rot=rot)
    for s in (1, -1):                                   # seat bolsters
        mb.rbox((s * 0.40, 0.86, 0.40), (0.22, 0.36, 0.10), 0.04, cloth)
    return mb


def doorcards():
    out = []
    for side, s in (("L", 1), ("R", -1)):
        mb = MeshBuilder(f"s13_doorcard_{side}")
        verts = []
        ys = np.linspace(-0.60, 0.52, 10)
        zs = np.linspace(0.24, 0.87, 8)
        for y in ys:
            for z in zs:
                x = side_x(SPEC, float(y), float(z)) - 0.075
                verts.append((s * x, float(y), float(z)))
        mb.add_faces(verts, grid_faces(len(ys), len(zs), flip=s > 0), "s13_doorcard", smooth=True)   # faces the cabin
        mb.rbox((s * (side_x(SPEC, 0.0, 0.6) - 0.11), 0.05, 0.60), (0.07, 0.40, 0.05), 0.02, M_INT)  # armrest
        mb.rbox((s * (side_x(SPEC, -0.3, 0.75) - 0.09), -0.30, 0.75), (0.02, 0.05, 0.03), 0.008, "s1x_chrome")  # handle
        out.append(mb)
    return out


def shifters():
    out = []
    for name, knob in (("s13_shifter_stock", "s13_interior_plastic"), ("s1x_shifter_short", "s1x_aluminium_polished"),
                       ("s1x_shifter_seq", "s1x_metal_black"), ("s13_shifter_auto", "s13_interior_plastic")):
        mb = MeshBuilder(name)
        base = Vector((0.0, -0.20, 0.46))
        h = 0.22 if "short" not in name else 0.15
        if "seq" in name:
            mb.tube([tuple(base), tuple(base + Vector((0, 0.06, h)))], 0.008, "s1x_metal_black", segs=8)
            mb.rbox(tuple(base + Vector((0, 0.06, h + 0.03))), (0.03, 0.03, 0.08), 0.01, "s1x_steer_suede")
        elif "auto" in name:
            mb.rbox(tuple(base + Vector((0, 0.0, 0.01))), (0.08, 0.16, 0.02), 0.005, M_INT)
            mb.tube([tuple(base), tuple(base + Vector((0, 0.0, 0.14)))], 0.01, "s1x_chrome", segs=8)
            mb.rbox(tuple(base + Vector((0, 0.0, 0.17))), (0.04, 0.06, 0.07), 0.015, M_INT)
        else:
            mb.lathe([(0.0, 0.0), (0.05, 0.0), (0.035, 0.05), (0.012, 0.12), (0.0, 0.12)], "s1x_rubber", segs=12, axis="z",
                     center=tuple(base))
            mb.tube([tuple(base), tuple(base + Vector((0, 0.0, h)))], 0.007, "s1x_chrome", segs=8)
            mb.lathe([(0.0, -0.02), (0.022, -0.012), (0.025, 0.01), (0.0, 0.03)], knob, segs=16, axis="z",
                     center=tuple(base + Vector((0, 0, h))))
        out.append(mb)
    return out


def handbrakes():
    out = []
    mb = MeshBuilder("s13_handbrake_hydro")
    base = Vector((0.115, 0.02, 0.45))
    mb.rbox(tuple(base), (0.05, 0.08, 0.06), 0.01, "s1x_aluminium")
    mb.tube([tuple(base + Vector((0, 0, 0.02))), tuple(base + Vector((0, -0.06, 0.28)))], 0.010, "s1x_aluminium_polished", segs=10)
    mb.rbox(tuple(base + Vector((0, -0.065, 0.30))), (0.035, 0.035, 0.07), 0.012, "s1x_fire_red")
    mb.cylinder(tuple(base + Vector((-0.03, 0.03, 0.0))), tuple(base + Vector((-0.03, 0.03, 0.05))), 0.012, "s1x_metal_black", segs=10)
    out.append(mb)
    return out


def interior_all():
    return [dash(), gauges(), console(), carpet(), headliner(), seats(), seats("s13_seats_leather", "s13_seat_leather"),
            rearseat(), rearseat("s13_rearseat_leather", "s13_seat_leather"), *doorcards(), *needles(), *pedals(),
            *shifters(), *handbrakes()]
