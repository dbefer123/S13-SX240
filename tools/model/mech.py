"""Suspension, brakes, engines, drivetrain and exhaust meshes positioned at a
vehicle's hard points (requires bpy).  `D` is the vehicle dims module and
`pfx` the mesh prefix (s13 / s14)."""
from __future__ import annotations

import math

from mathutils import Matrix, Vector

from .prims import MeshBuilder, rot_to, text_mesh

M_ARM = "s1x_metal_black"
M_STEEL = "s1x_metal_steel"
M_ALU = "s1x_aluminium"
M_RUBBER = "s1x_rubber"
M_SPRING = "s1x_spring_red"


def both(p):
    x, y, z = p
    return (x, y, z), (-x, y, z)


# ---------------------------------------------------------------------------
# front suspension
# ---------------------------------------------------------------------------
def front_suspension(D, pfx):
    out = []
    # lower arms (transverse link + tension rod), both sides in one mesh
    mb = MeshBuilder(f"{pfx}_lowerarm_F")
    for s in (1, -1):
        fh1 = (s * D.FH1[0], D.FH1[1], D.FH1[2])
        fx1 = (s * D.FX1[0], D.FX1[1], D.FX1[2])
        fx2 = (s * D.FX2[0], D.FX2[1], D.FX2[2])
        mb.tube([fx1, fh1], 0.018, M_ARM, segs=10)
        mb.tube([fx2, (s * (D.FH1[0] - 0.05), D.FH1[1] - 0.02, D.FH1[2] + 0.005), fh1], 0.012, M_ARM, segs=8)
        mb.cylinder((fx1[0], fx1[1] - 0.03, fx1[2]), (fx1[0], fx1[1] + 0.03, fx1[2]), 0.026, M_RUBBER, segs=12)
        mb.cylinder((fx2[0], fx2[1] - 0.025, fx2[2]), (fx2[0], fx2[1] + 0.025, fx2[2]), 0.030, M_RUBBER, segs=12)
        mb.lathe([(0.0, 0.025), (0.022, 0.02), (0.022, -0.01), (0.0, -0.015)], M_STEEL, segs=12, axis="z", center=fh1, closed=True)
    out.append(mb)
    # knuckles
    mb = MeshBuilder(f"{pfx}_knuckle_F")
    for s in (1, -1):
        fh1 = Vector((s * D.FH1[0], D.FH1[1], D.FH1[2]))
        fh2 = Vector((s * D.FH2[0], D.FH2[1], D.FH2[2]))
        fh3 = Vector((s * D.FH3[0], D.FH3[1], D.FH3[2]))
        fh5 = Vector((s * D.FH5[0], D.FH5[1], D.FH5[2]))
        c = Vector((s * (D.TRACK_F / 2 - 0.10), D.AXLE_F_Y, D.AXLE_Z))
        mb.tube([tuple(fh1), tuple(c), tuple(fh2)], 0.030, M_STEEL, segs=10)
        mb.tube([tuple(c), tuple((c + fh3) / 2), tuple(fh3)], 0.016, M_STEEL, segs=8)
        mb.tube([tuple(c), tuple(fh5)], 0.020, M_STEEL, segs=8)
        mb.cylinder(tuple(c - Vector((s * 0.02, 0, 0))), tuple(c + Vector((s * 0.035, 0, 0))), 0.062, M_STEEL, segs=20)
    out.append(mb)
    # crossmember / subframe
    mb = MeshBuilder(f"{pfx}_fsubframe")
    y0 = D.FX1[1]
    mb.tube([(-D.FX1[0], y0, D.FX1[2] + 0.02), (-0.15, y0, 0.16), (0.15, y0, 0.16), (D.FX1[0], y0, D.FX1[2] + 0.02)], 0.035, M_ARM, segs=12)
    for s in (1, -1):
        mb.tube([(s * D.FX1[0], y0, D.FX1[2] + 0.02), (s * 0.42, y0 - 0.02, 0.24)], 0.03, M_ARM, segs=10)
        mb.tube([(s * D.FX2[0], D.FX2[1], D.FX2[2]), (s * 0.42, D.FX2[1] + 0.02, 0.26)], 0.022, M_ARM, segs=10)
    out.append(mb)
    # steering rack + tie rods
    mb = MeshBuilder(f"{pfx}_steering_rack")
    mb.cylinder((-D.RACK_X + 0.03, D.RACK_Y, D.RACK_Z), (D.RACK_X - 0.03, D.RACK_Y, D.RACK_Z), 0.024, M_ALU, segs=14)
    for s in (1, -1):
        mb.cylinder((s * (D.RACK_X - 0.06), D.RACK_Y, D.RACK_Z), (s * (D.RACK_X + 0.01), D.RACK_Y, D.RACK_Z), 0.030, M_RUBBER, segs=14)
    mb.cylinder((0.18, D.RACK_Y, D.RACK_Z), (0.22, D.RACK_Y + 0.12, D.RACK_Z + 0.25), 0.02, M_ALU, segs=10)
    out.append(mb)
    mb = MeshBuilder(f"{pfx}_tierod_F")
    for s in (1, -1):
        mb.tube([(s * D.RACK_X, D.RACK_Y, D.RACK_Z), (s * D.FH3[0], D.FH3[1], D.FH3[2])], 0.009, M_STEEL, segs=8)
    out.append(mb)
    # sway bar
    mb = MeshBuilder(f"{pfx}_swaybar_F")
    yb = D.FX1[1] - 0.20
    mb.tube([(0.55, D.FH1[1], 0.19), (0.45, yb, 0.22), (-0.45, yb, 0.22), (-0.55, D.FH1[1], 0.19)], 0.011, M_ARM, segs=8)
    out.append(mb)
    # struts (one mesh per spring variant)
    for key, col in (("", "s1x_spring_black"), ("_sport", "s1x_spring_blue"), ("_street", "s1x_spring_red"),
                     ("_track", "s1x_spring_yellow"), ("_drift", "s1x_spring_purple"), ("_drag", "s1x_spring_black"),
                     ("_rally", "s1x_spring_blue")):
        mb = MeshBuilder(f"{pfx}_strut_F{key}")
        coil = key not in ("",)
        for s in (1, -1):
            bot = Vector((s * D.FH2[0], D.FH2[1], D.FH2[2]))
            top = Vector((s * D.FS1[0], D.FS1[1], D.FS1[2]))
            d = (top - bot)
            mb.cylinder(tuple(bot - d * 0.05), tuple(bot + d * 0.55), 0.026, M_ARM, segs=14)
            mb.cylinder(tuple(bot + d * 0.5), tuple(top), 0.011, "s1x_chrome", segs=10)
            seat_lo = bot + d * (0.42 if coil else 0.35)
            mb.cylinder(tuple(seat_lo), tuple(seat_lo + d * 0.02), 0.06, M_ARM, segs=16)
            mb.cylinder(tuple(top - d * 0.05), tuple(top), 0.065, M_ARM, segs=16)
            r = 0.045 if coil else 0.062
            mb.helix(tuple(seat_lo + d * 0.02), tuple(top - d * 0.05), r, 0.0065 if coil else 0.0075, 6 if coil else 5, col)
        out.append(mb)
    return out


# ---------------------------------------------------------------------------
# rear suspension
# ---------------------------------------------------------------------------
def rear_suspension(D, pfx):
    out = []
    mb = MeshBuilder(f"{pfx}_rsubframe")
    xs = D.RX1[0]
    yA, yB = D.RX1[1] - 0.05, D.RX4[1] + 0.03
    for s in (1, -1):
        mb.tube([(s * xs, yA, 0.21), (s * xs, yB, 0.23), (s * 0.42, yB + 0.05, 0.32)], 0.032, M_ARM, segs=10)
        mb.tube([(s * xs, yA, 0.21), (s * 0.42, yA - 0.10, 0.27)], 0.03, M_ARM, segs=10)
        mb.tube([(s * D.RX3[0], D.RX3[1], D.RX3[2]), (s * xs, D.RX3[1], 0.22)], 0.025, M_ARM, segs=10)
    mb.tube([(xs, yA + 0.02, 0.22), (-xs, yA + 0.02, 0.22)], 0.03, M_ARM, segs=10)
    mb.tube([(xs, yB - 0.02, 0.23), (-xs, yB - 0.02, 0.23)], 0.03, M_ARM, segs=10)
    out.append(mb)
    mb = MeshBuilder(f"{pfx}_rearlinks")
    for s in (1, -1):
        def P(p):
            return (s * p[0], p[1], p[2])
        mb.tube([P(D.RX1), P(D.RH1)], 0.016, M_ARM, segs=8)
        mb.tube([P(D.RX2), P(D.RH1)], 0.016, M_ARM, segs=8)
        mb.tube([P(D.RX3), P(D.RH2)], 0.014, M_ARM, segs=8)
        mb.tube([P(D.RX4), P(D.RH3)], 0.010, M_STEEL, segs=8)
        mb.tube([P(D.RX5), P(D.RH5)], 0.012, M_ARM, segs=8)
    out.append(mb)
    mb = MeshBuilder(f"{pfx}_knuckle_R")
    for s in (1, -1):
        c = (s * (D.TRACK_R / 2 - 0.10), D.AXLE_R_Y, D.AXLE_Z)
        for p in (D.RH1, D.RH2, D.RH3, D.RH5):
            mb.tube([c, (s * p[0], p[1], p[2])], 0.022, M_STEEL, segs=8)
        mb.cylinder((c[0] - s * 0.02, c[1], c[2]), (c[0] + s * 0.035, c[1], c[2]), 0.060, M_STEEL, segs=20)
    out.append(mb)
    mb = MeshBuilder(f"{pfx}_swaybar_R")
    yb = D.AXLE_R_Y + 0.17
    mb.tube([(0.56, D.RH1[1] + 0.05, 0.20), (0.42, yb, 0.25), (-0.42, yb, 0.25), (-0.56, D.RH1[1] + 0.05, 0.20)], 0.009, M_ARM, segs=8)
    out.append(mb)
    for key, col in (("", "s1x_spring_black"), ("_sport", "s1x_spring_blue"), ("_street", "s1x_spring_red"),
                     ("_track", "s1x_spring_yellow"), ("_drift", "s1x_spring_purple"), ("_drag", "s1x_spring_red"),
                     ("_rally", "s1x_spring_blue")):
        mb = MeshBuilder(f"{pfx}_shock_R{key}")
        for s in (1, -1):
            bot = Vector((s * D.RH4[0], D.RH4[1], D.RH4[2]))
            top = Vector((s * D.RS1[0], D.RS1[1], D.RS1[2]))
            d = top - bot
            mb.cylinder(tuple(bot), tuple(bot + d * 0.55), 0.024, M_ARM, segs=12)
            mb.cylinder(tuple(bot + d * 0.5), tuple(top), 0.010, "s1x_chrome", segs=10)
            mb.helix(tuple(bot + d * 0.3), tuple(top - d * 0.06), 0.045, 0.0065, 6, col)
            mb.cylinder(tuple(top - d * 0.06), tuple(top), 0.055, M_ARM, segs=14)
        out.append(mb)
    return out


# ---------------------------------------------------------------------------
# brakes
# ---------------------------------------------------------------------------
BRAKE_SPEC = {  # key: (disc_F, disc_R, caliper_color, vented_R, drilled)
    "stock": (0.257, 0.258, "s1x_caliper_raw", False, False),
    "z32": (0.296, 0.297, "s1x_caliper_black", True, False),
    "bbk": (0.330, 0.310, "s1x_caliper_red", True, True),
    "drag": (0.280, 0.280, "s1x_caliper_gold", False, True),
}


def brakes(D, pfx):
    out = []
    for key, (dF, dR, cmat, ventR, drilled) in BRAKE_SPEC.items():
        for axle in ("F", "R"):
            dia = dF if axle == "F" else dR
            vented = axle == "F" or ventR
            y = D.AXLE_F_Y if axle == "F" else D.AXLE_R_Y
            track = D.TRACK_F if axle == "F" else D.TRACK_R
            xr = track / 2 - 0.020           # rotor centre plane (wheel hub face is at track/2 + 0.045)
            face = 0.045 + 0.020 - 0.002      # hat reaches the hub face
            for side, s in (("L", 1), ("R", -1)):
                mb = MeshBuilder(f"{pfx}_brake_{key}_{axle}_{side}")
                c = (s * xr, y, D.AXLE_Z)
                R = dia / 2
                th = 0.026 if vented else 0.010
                if vented:
                    mb.lathe([(R * 0.62, -th / 2), (R, -th / 2), (R, -th / 2 + 0.008), (R * 0.62, -th / 2 + 0.008)],
                             "s1x_rotor", segs=48, axis="x", center=c, closed=True)
                    mb.lathe([(R * 0.62, th / 2 - 0.008), (R, th / 2 - 0.008), (R, th / 2), (R * 0.62, th / 2)],
                             "s1x_rotor", segs=48, axis="x", center=c, closed=True)
                    mb.lathe([(R * 0.64, -th / 2 + 0.008), (R * 0.98, -th / 2 + 0.008), (R * 0.98, th / 2 - 0.008),
                              (R * 0.64, th / 2 - 0.008)], "s1x_dark", segs=24, axis="x", center=c, closed=True)
                else:
                    mb.lathe([(R * 0.62, -th / 2), (R, -th / 2), (R, th / 2), (R * 0.62, th / 2)], "s1x_rotor", segs=48,
                             axis="x", center=c, closed=True)
                # hat toward the hub face (outboard)
                mb.lathe([(R * 0.62, s * th / 2), (R * 0.60, s * (face - 0.012)), (0.085, s * (face - 0.004)),
                          (0.075, s * face), (0.0, s * face)], "s1x_rotor_hat", segs=32, axis="x", center=c)
                out.append(mb)
            # caliper (both sides in one mesh, mapped to the hub group)
            mb = MeshBuilder(f"{pfx}_caliper_{key}_{axle}")
            for s in (1, -1):
                ang = math.radians(15)  # behind the axle, slightly up
                cy = y + (dia / 2 - 0.018) * math.cos(ang) * (1 if axle == "F" else -1)
                cz = D.AXLE_Z + (dia / 2 - 0.018) * math.sin(ang)
                big = key in ("bbk", "z32")
                size = (0.075 if big else 0.06, 0.05, 0.15 if big else 0.11)
                rot = Matrix.Rotation(-ang if axle == "F" else ang, 3, "X")
                mb.rbox((s * (track / 2 - 0.020), cy, cz), size, 0.012, cmat, rot=rot)
            out.append(mb)
    return out


# ---------------------------------------------------------------------------
# engines
# ---------------------------------------------------------------------------
def _engine_block(mb, D, length, w_bot, w_top, z_bot, z_top, cover_mat, block_mat, cover_style="ka"):
    y0, y1 = D.ENGINE_FRONT_Y + 0.05, D.ENGINE_FRONT_Y + 0.05 + length
    cy = (y0 + y1) / 2
    # oil pan
    mb.rbox((0, cy, z_bot + 0.05), (w_bot, length * 0.92, 0.10), 0.02, "s1x_metal_black")
    # block
    mb.rbox((0, cy, z_bot + 0.20), (w_top * 0.95, length, 0.22), 0.025, block_mat)
    # head
    mb.rbox((0, cy, z_bot + 0.36), (w_top * 0.85, length * 0.96, 0.11), 0.02, block_mat)
    # cam / valve cover
    mb.rbox((0, cy, z_bot + 0.45), (w_top * 0.70, length * 0.90, 0.075), 0.025, cover_mat)
    # timing cover + pulleys at the front
    mb.rbox((0, y0 - 0.025, z_bot + 0.26), (w_top * 0.8, 0.05, 0.38), 0.02, "s1x_metal_black")
    mb.cylinder((0.0, y0 - 0.06, z_bot + 0.14), (0.0, y0 - 0.03, z_bot + 0.14), 0.075, "s1x_metal_steel", segs=24)
    mb.cylinder((0.12, y0 - 0.06, z_bot + 0.36), (0.12, y0 - 0.03, z_bot + 0.36), 0.05, "s1x_metal_steel", segs=20)
    mb.cylinder((-0.14, y0 - 0.06, z_bot + 0.30), (-0.14, y0 - 0.03, z_bot + 0.30), 0.055, "s1x_metal_steel", segs=20)
    # alternator, starter
    mb.cylinder((0.20, y0 + 0.05, z_bot + 0.28), (0.20, y0 + 0.17, z_bot + 0.28), 0.06, M_ALU, segs=20)
    mb.cylinder((-0.17, y1 - 0.04, z_bot + 0.10), (-0.17, y1 - 0.20, z_bot + 0.10), 0.045, "s1x_metal_black", segs=16)
    return y0, y1, cy


def engine_ka24(D, pfx):
    mb = MeshBuilder(f"{pfx}_engine_ka24")
    y0, y1, cy = _engine_block(mb, D, 0.60, 0.30, 0.42, 0.215, 0.735, "s1x_engine_cover_silver", "s1x_engine_block")
    # intake plenum (left side) + runners
    mb.rbox((0.17, cy, 0.62), (0.10, 0.48, 0.12), 0.03, M_ALU)
    for k in range(4):
        yy = y0 + 0.10 + k * 0.14
        mb.tube([(0.14, yy, 0.62), (0.10, yy, 0.58)], 0.022, M_ALU, segs=10)
    # throttle body + intake tube to the air box
    mb.cylinder((0.17, y1 - 0.02, 0.62), (0.17, y1 + 0.05, 0.62), 0.035, M_ALU, segs=14)
    return [mb]


def engine_sr20(D, pfx):
    mb = MeshBuilder(f"{pfx}_engine_sr20")
    y0, y1, cy = _engine_block(mb, D, 0.56, 0.28, 0.40, 0.215, 0.73, "s1x_engine_cover_red", "s1x_engine_block_alu")
    mb.rbox((0.16, cy, 0.64), (0.10, 0.44, 0.11), 0.03, M_ALU)
    for k in range(4):
        yy = y0 + 0.10 + k * 0.13
        mb.tube([(0.13, yy, 0.64), (0.10, yy, 0.58)], 0.02, M_ALU, segs=10)
    # coil pack cover strip
    mb.rbox((0.0, cy, 0.71), (0.06, 0.40, 0.02), 0.008, "s1x_metal_black")
    return [mb]


def engine_k20(D, pfx):
    """K20A: red crinkle valve cover, coil packs, silver intake manifold with plaque (reference photo)."""
    mb = MeshBuilder(f"{pfx}_engine_k20")
    y0, y1, cy = _engine_block(mb, D, 0.52, 0.27, 0.38, 0.215, 0.72, "s1x_engine_cover_k20red", "s1x_engine_block_alu")
    # intake manifold: plenum cover across the front of the head (RWD swap: rotated, runners on the left)
    mb.rbox((0.16, cy, 0.64), (0.13, 0.46, 0.15), 0.035, "s1x_k20_manifold")
    for k in range(4):
        yy = y0 + 0.08 + k * 0.12
        mb.tube([(0.10, yy, 0.62), (0.16, yy, 0.66), (0.20, yy, 0.62)], 0.026, "s1x_k20_manifold", segs=12)
    # coil packs on the valve cover
    for k in range(4):
        yy = y0 + 0.09 + k * 0.115
        mb.rbox((0.0, yy, 0.715), (0.045, 0.035, 0.035), 0.006, "s1x_metal_black")
    return [mb]


def intakes(D, pfx, engine, kinds):
    out = []
    for kind in kinds:
        mb = MeshBuilder(f"{pfx}_intake_{engine}_{kind}")
        y1 = D.ENGINE_REAR_Y - 0.02
        if kind == "stock":
            mb.rbox((0.42, -1.72, 0.60), (0.22, 0.26, 0.16), 0.03, "s1x_plastic_black")
            mb.tube([(0.42, -1.58, 0.60), (0.30, -1.20, 0.62), (0.20, y1 + 0.05, 0.62)], 0.04, "s1x_rubber", segs=12)
        elif kind == "cai":
            mb.tube([(0.50, -1.92, 0.42), (0.40, -1.55, 0.58), (0.22, y1 + 0.05, 0.62)], 0.038, "s1x_aluminium_polished", segs=12)
            mb.lathe([(0.0, 0.0), (0.06, 0.0), (0.07, 0.08), (0.06, 0.16), (0.0, 0.16)], "s1x_filter_red", segs=20,
                     axis="y", center=(0.50, -2.06, 0.40))
        elif kind == "itb":
            for k in range(4):
                yy = D.ENGINE_FRONT_Y + 0.13 + k * 0.12
                mb.cylinder((0.20, yy, 0.62), (0.30, yy, 0.62), 0.03, M_ALU, segs=14)
                mb.lathe([(0.03, 0.0), (0.045, 0.02), (0.05, 0.06), (0.0, 0.06)], "s1x_chrome", segs=16, axis="x",
                         center=(0.30, yy, 0.62))
        out.append(mb)
    return out


def manifolds(D, pfx, engine, kinds):
    out = []
    y0 = D.ENGINE_FRONT_Y + 0.12
    for kind in kinds:
        mb = MeshBuilder(f"{pfx}_manifold_{engine}_{kind}")
        mat = "s1x_exhaust_hot" if kind != "header" else "s1x_header"
        col = []
        for k in range(4):
            yy = y0 + k * 0.13
            if kind == "turbo":
                mb.tube([(-0.17, yy, 0.52), (-0.24, yy, 0.50), (-0.28, (yy + y0 + 0.2) / 2, 0.47)], 0.022, mat, segs=10)
            else:
                mb.tube([(-0.17, yy, 0.52), (-0.26, yy, 0.48), (-0.26, D.ENGINE_REAR_Y + 0.05, 0.32)], 0.021, mat, segs=10)
        if kind != "turbo":
            mb.tube([(-0.26, D.ENGINE_REAR_Y + 0.05, 0.32), (-0.24, D.ENGINE_REAR_Y - 0.10, 0.30)], 0.03, mat, segs=12)
        else:
            mb.tube([(-0.28, y0 + 0.2, 0.47), (-0.30, y0 + 0.2, 0.42), (-0.25, D.ENGINE_REAR_Y - 0.1, 0.30)], 0.032, mat, segs=12)
        out.append(mb)
    return out


def turbos(D, pfx):
    out = []
    y0 = D.ENGINE_FRONT_Y + 0.32
    for kind, r in (("small", 0.055), ("medium", 0.068), ("large", 0.085)):
        mb = MeshBuilder(f"{pfx}_turbo_{kind}")
        c = (-0.33, y0, 0.50)
        mb.lathe([(0.0, -0.05), (r, -0.04), (r * 1.1, 0.0), (r, 0.04), (0.0, 0.05)], "s1x_turbo_hot", segs=24, axis="y", center=c)
        mb.lathe([(0.0, 0.05), (r * 0.9, 0.06), (r * 0.95, 0.10), (r * 0.6, 0.13), (0.0, 0.13)], M_ALU, segs=24, axis="y", center=c)
        # charge pipe to a front-mount intercooler
        mb.tube([(-0.33, y0 + 0.13, 0.50), (-0.40, -1.95, 0.45), (-0.30, -2.05, 0.33)], 0.03, "s1x_aluminium_polished", segs=12)
        mb.rbox((0.0, -2.08, 0.33), (0.62 if kind != "small" else 0.40, 0.06, 0.16), 0.01, "s1x_intercooler")
        mb.tube([(0.30, -2.05, 0.33), (0.40, -1.95, 0.45), (0.25, D.ENGINE_FRONT_Y + 0.2, 0.66)], 0.03, "s1x_aluminium_polished", segs=12)
        out.append(mb)
    return out


# ---------------------------------------------------------------------------
# drivetrain
# ---------------------------------------------------------------------------
def gearboxes(D, pfx):
    out = []
    fy, ry = D.ENGINE_REAR_Y, D.TRANS_REAR_Y
    for kind in ("manual", "sequential", "automatic"):
        mb = MeshBuilder(f"{pfx}_gearbox_{kind}")
        mb.lathe([(0.20, 0.0), (0.21, 0.04), (0.16, 0.20), (0.12, 0.30), (0.10, 0.45), (0.07, 0.62), (0.0, 0.64)],
                 M_ALU if kind != "automatic" else "s1x_metal_black", segs=24, axis="y", center=(0, fy, 0.34))
        if kind == "sequential":
            mb.rbox((0.0, fy + 0.30, 0.47), (0.09, 0.14, 0.06), 0.01, "s1x_metal_black")
        out.append(mb)
    mb = MeshBuilder(f"{pfx}_driveshaft")
    mb.cylinder((0, ry, 0.30), (0, 0.38, 0.30), 0.034, "s1x_metal_black", segs=14)
    mb.cylinder((0, 0.38, 0.30), (0, D.DIFF_Y - 0.24, 0.31), 0.034, "s1x_metal_black", segs=14)
    out.append(mb)
    mb = MeshBuilder(f"{pfx}_diff_R")
    mb.lathe([(0.0, -0.10), (0.11, -0.08), (0.14, 0.0), (0.11, 0.08), (0.0, 0.10)], "s1x_metal_black", segs=24, axis="x",
             center=(0, D.DIFF_Y, D.DIFF_Z))
    mb.cylinder((0, D.DIFF_Y - 0.08, D.DIFF_Z), (0, D.DIFF_Y - 0.24, D.DIFF_Z), 0.05, "s1x_metal_black", segs=16)
    mb.lathe([(0.0, 0.10), (0.10, 0.10), (0.12, 0.12), (0.0, 0.13)], M_ALU, segs=24, axis="x", center=(0, D.DIFF_Y, D.DIFF_Z))
    out.append(mb)
    for side, s in (("RL", 1), ("RR", -1)):
        mb = MeshBuilder(f"{pfx}_halfshaft_{side}")
        mb.cylinder((s * 0.16, D.DIFF_Y, D.DIFF_Z), (s * (D.TRACK_R / 2 - 0.07), D.AXLE_R_Y, D.AXLE_Z), 0.016, M_STEEL, segs=10)
        out.append(mb)
    return out


def exhaust_stock(D, pfx, name=None, tips=1, tip_r=0.032, pipe_r=0.026):
    mb = MeshBuilder(name or f"{pfx}_exhaust_stock")
    path = [(-0.24, -1.05, 0.30), (-0.14, -0.55, 0.205), (-0.14, 0.40, 0.205), (-0.30, 1.00, 0.23), (-0.42, 1.55, 0.26)]
    mb.tube(path, pipe_r, "s1x_exhaust", segs=12)
    mb.rbox((-0.14, -0.15, 0.20), (0.14, 0.32, 0.09), 0.04, "s1x_exhaust")         # catalytic converter
    mb.rbox((-0.45, 1.85, 0.27), (0.30, 0.42, 0.18), 0.06, "s1x_exhaust")          # muffler
    for k in range(tips):
        dx = (k - (tips - 1) / 2) * 0.075
        mb.tube([(-0.50 + dx, 2.05, 0.255), (-0.50 + dx, 2.29, 0.25)], tip_r, "s1x_chrome", segs=16, caps=False)
    return mb
