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
    mb.add_faces(verts, grid_faces(len(ys), len(xs), flip=False), M_UNDER, smooth=True)
    return mb


def wheelwells():
    mb = MeshBuilder("s13_wheelwells")
    for (cy, cz), track in ((B.AXLE_F_Y and (D.AXLE_F_Y, D.AXLE_Z), D.TRACK_F), ((D.AXLE_R_Y, D.AXLE_Z), D.TRACK_R)):
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
            mb.add_faces(verts, faces, M_UNDER, smooth=True)
            # inner wall disc
            prof = [(0.0, 0.0), (r, 0.0)]
            mb.lathe(prof, M_UNDER, segs=24, axis="x", center=(s * x_in, cy, cz), angle=(0, math.pi))
    return mb


def enginebay():
    mb = MeshBuilder("s13_enginebay")
    for s in (1, -1):
        # inner fender apron wall
        verts = []
        ys = np.linspace(-2.02, -0.88, 12)
        for y in ys:
            for z in (0.30, 0.50, 0.66):
                x = 0.66 if z < 0.6 else 0.71
                if -1.62 < y < -0.86 and z < 0.66:
                    x = 0.60                                  # strut tower bulge
                verts.append((s * x, float(y), z))
        mb.add_faces(verts, grid_faces(len(ys), 3, flip=s < 0), "s13_enginebay_paint", smooth=False)
        # strut tower top
        mb.cylinder((s * D.FS1[0], D.FS1[1], D.FS1[2] - 0.02), (s * D.FS1[0], D.FS1[1], D.FS1[2] + 0.01), 0.09,
                    "s13_enginebay_paint", segs=20)
    # firewall
    verts = []
    xs = np.linspace(-0.72, 0.72, 13)
    for z in (0.22, 0.45, 0.68, 0.84):
        for x in xs:
            verts.append((float(x), -0.885 + (0.02 if z > 0.8 else 0.0), z))
    mb.add_faces(verts, grid_faces(4, len(xs)), "s13_enginebay_paint", smooth=False)
    # radiator core support (upper bar)
    mb.rbox((0.0, -2.06, 0.555), (0.95, 0.05, 0.04), 0.008, "s13_enginebay_paint")
    return mb


def popup_lamps():
    out = []
    for side, s in (("L", 1), ("R", -1)):
        mb = MeshBuilder(f"s13_popup_lamp_{side}")
        x0, x1 = 0.40, 0.665
        # lamp box modelled in the raised orientation (lens facing forward), then rotated closed about the hinge
        hy, hz = -1.875, top_z(SPEC, -1.875, 0.53) - 0.006
        box_c = Vector((s * (x0 + x1) / 2, -2.02, hz + 0.075))
        sizex, sizey, sizez = (x1 - x0), 0.15, 0.115
        mb.rbox(tuple(box_c), (sizex, sizey, sizez), 0.01, "s13_popup_housing")
        # lens (glowing material)
        lens_c = box_c + Vector((0, -sizey / 2 - 0.004, 0))
        mb.rbox(tuple(lens_c), (sizex - 0.02, 0.008, sizez - 0.02), 0.004, "s13_headlight")
        # reflector rings
        for k in (-1, 1):
            c = lens_c + Vector((s * k * 0.06, 0.004, 0))
            mb.cylinder(tuple(c + Vector((0, -0.006, 0))), tuple(c + Vector((0, 0.01, 0))), 0.035, "s13_headlight_chrome", segs=16)
        ob_rot = Matrix.Rotation(math.radians(-PJ.POPUP_ANGLE), 4, Vector((1, 0, 0)))
        piv = Vector((0, hy, hz))
        bm = mb.bm
        for v in bm.verts:
            v.co = (ob_rot @ (v.co - piv)) + piv
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


def dash():
    mb = MeshBuilder("s13_dash")
    cx = D.STEER_CENTER[0]

    def prof(x):
        hood = math.exp(-((x - cx) / 0.19) ** 4)          # cluster hood bump on the driver side
        top = 0.905 + 0.075 * hood
        front_y = -0.47 + 0.03 * hood
        wall = 0.73 - 0.04 * math.cos(x * 2.0)
        return [(-0.80, 0.86), (-0.66, top - 0.01), (-0.55, top), (front_y, top - 0.01), (front_y + 0.025, top - 0.05),
                (front_y + 0.02, wall), (front_y - 0.04, wall - 0.12), (-0.62, 0.56), (-0.80, 0.55)]
    xs = np.linspace(-0.74, 0.74, 37)
    _loft_x(mb, xs, prof, M_INT, flip=True)
    # end caps
    # centre stack
    mb.rbox((0.0, -0.50, 0.66), (0.28, 0.10, 0.20), 0.02, M_INT)
    mb.rbox((0.0, -0.455, 0.70), (0.22, 0.01, 0.07), 0.004, "s13_radio")
    mb.rbox((0.0, -0.455, 0.615), (0.22, 0.01, 0.06), 0.004, "s13_hvac")
    # vents
    for x in (-0.55, -0.12, 0.12, 0.62):
        mb.rbox((x, -0.445, 0.84 if abs(x) > 0.3 else 0.79), (0.10, 0.012, 0.045), 0.006, "s1x_dark")
    # steering column shroud
    sc = Vector(D.STEER_CENTER)
    a = math.radians(23)
    d = Vector((0, -math.cos(a), -math.sin(a)))
    mb.tube([tuple(sc + d * 0.06), tuple(sc + d * 0.30)], 0.05, M_INT, segs=14)
    return mb


def gauges():
    """Instrument cluster face (textured) recessed in the hood, facing the driver (+y)."""
    mb = MeshBuilder("s13_gauges")
    cx = D.STEER_CENTER[0]
    gy = D.STEER_CENTER[1] - 0.21
    gz = 0.955
    w, h = 0.36, 0.13
    verts = [(cx + w / 2, gy, gz - h / 2), (cx - w / 2, gy, gz - h / 2), (cx - w / 2, gy, gz + h / 2), (cx + w / 2, gy, gz + h / 2)]
    faces = [(0, 1, 2, 3)]
    fs = mb.add_faces(verts, faces, "s13_gauges", smooth=False)
    # proper 0..1 UVs for the gauge texture (u from left to right as seen by the driver)
    for f in fs:
        for loop in f.loops:
            x, z = loop.vert.co.x, loop.vert.co.z
            loop[mb.uv].uv = ((cx + w / 2 - x) / w, (z - (gz - h / 2)) / h)
    # surround / bezel
    mb.rbox((cx, gy - 0.005, gz), (w + 0.03, 0.01, h + 0.03), 0.006, "s1x_dark")
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


def rearseat():
    mb = MeshBuilder("s13_rearseat")
    mb.rbox((0.0, 0.86, 0.36), (1.10, 0.38, 0.12), 0.04, M_CLOTH)
    rot = Matrix.Rotation(math.radians(-30), 3, "X")
    mb.rbox((0.0, 1.05, 0.62), (1.10, 0.10, 0.48), 0.04, M_CLOTH, rot=rot)
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
        mb.add_faces(verts, grid_faces(len(ys), len(zs), flip=s < 0), "s13_doorcard", smooth=True)
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


def interior_all():
    return [dash(), gauges(), console(), carpet(), headliner(), seats(), rearseat(), *doorcards(), *needles(), *pedals(),
            *shifters()]
