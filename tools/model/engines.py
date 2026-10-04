"""Detailed engine meshes (requires bpy): KA24E/KA24DE, SR20DET and the Honda K20A
(after the reference photo: red crinkle valve cover, silver coil cover with raised
HONDA letters and the i-VTEC plaque, cast silver intake runners).

Engines sit longitudinally: timing end at the front (-y), intake on +x, exhaust on -x.
"""
from __future__ import annotations

import math

from mathutils import Matrix, Vector

from .prims import MeshBuilder, text_mesh, apply_transform, join_into

M_BLACK = "s1x_metal_black"
M_STEEL = "s1x_metal_steel"
M_ALU = "s1x_aluminium"
M_RUBBER = "s1x_rubber"


def _base(mb, D, length, w, block_mat, z0=0.215):
    """Oil pan, block, head and the front accessory drive. Returns (y0, y1, cy)."""
    y0 = D.ENGINE_FRONT_Y + 0.05
    y1 = y0 + length
    cy = (y0 + y1) / 2
    # oil pan with a sump bulge
    mb.rbox((0, cy + 0.03, z0 + 0.045), (w * 0.70, length * 0.85, 0.09), 0.02, M_BLACK)
    mb.rbox((0, cy + 0.10, z0 + 0.01), (w * 0.55, length * 0.40, 0.04), 0.015, M_BLACK)
    # block (slight taper toward the bottom)
    mb.rbox((0, cy, z0 + 0.19), (w * 0.88, length, 0.21), 0.02, block_mat)
    for k in range(4):                                          # ribs on both sides
        yy = y0 + 0.08 + k * (length - 0.12) / 3
        for s in (1, -1):
            mb.box((s * w * 0.445, yy, z0 + 0.18), (0.012, 0.018, 0.17), block_mat)
    # cylinder head
    mb.rbox((0, cy, z0 + 0.345), (w * 0.80, length * 0.98, 0.10), 0.015, block_mat)
    # timing cover + front accessory drive
    mb.rbox((0, y0 - 0.025, z0 + 0.27), (w * 0.78, 0.05, 0.40), 0.03, M_BLACK)
    pulleys = [((0.0, z0 + 0.13), 0.078), ((0.13, z0 + 0.36), 0.050), ((-0.11, z0 + 0.42), 0.055),
               ((0.17, z0 + 0.20), 0.045), ((-0.08, z0 + 0.24), 0.040)]
    for (px, pz), r in pulleys:
        mb.cylinder((px, y0 - 0.075, pz), (px, y0 - 0.045, pz), r, M_STEEL, segs=28)
        mb.cylinder((px, y0 - 0.08, pz), (px, y0 - 0.074, pz), r * 0.35, M_BLACK, segs=14)
    # serpentine belt around the pulleys (approximate polygon path)
    order = [0, 3, 1, 2, 4, 0]
    pts = []
    for i in order:
        (px, pz), r = pulleys[i]
        pts.append((px, y0 - 0.06, pz))
    mb.tube(pts, 0.006, M_RUBBER, segs=6, caps=False)
    # alternator, starter, oil filter
    mb.cylinder((0.21, y0 + 0.02, z0 + 0.26), (0.21, y0 + 0.16, z0 + 0.26), 0.065, M_ALU, segs=24)
    for k in range(8):
        a = 2 * math.pi * k / 8
        mb.box((0.21 + 0.066 * math.cos(a), y0 + 0.09, z0 + 0.26 + 0.066 * math.sin(a)), (0.006, 0.12, 0.006), M_ALU)
    mb.cylinder((-0.17, y1 - 0.03, z0 + 0.10), (-0.17, y1 - 0.20, z0 + 0.10), 0.045, M_BLACK, segs=16)
    mb.cylinder((0.17, cy + 0.05, z0 + 0.08), (0.24, cy + 0.05, z0 + 0.06), 0.040, "s1x_oilfilter", segs=18)
    # engine mounts
    for s in (1, -1):
        mb.rbox((s * w * 0.50, D.ENGINE_FRONT_Y + 0.38, z0 + 0.12), (0.06, 0.08, 0.07), 0.01, M_BLACK)
    return y0, y1, cy


def _letters(text, size, loc, mat, extrude=0.0018, rot=(0.0, 0.0, 0.0)):
    ob = text_mesh("__txt", text, size, mat, location=loc, rotation=rot, extrude=extrude)
    apply_transform(ob)
    return ob


def _attach(mb, extras, col_name):
    ob = mb.to_object()
    if extras:
        join_into(ob, extras)
    ob.name = col_name
    ob.data.name = col_name
    return ob


def engine_k20(D, pfx):
    mb = MeshBuilder(f"{pfx}_engine_k20")
    length, w = 0.50, 0.40
    y0, y1, cy = _base(mb, D, length, w, "s1x_engine_block_alu")
    zt = 0.215 + 0.40                                          # top of head
    # red crinkle valve cover
    mb.rbox((0, cy, zt + 0.035), (w * 0.74, length * 0.92, 0.075), 0.03, "s1x_engine_cover_k20red")
    # ribbed silver panel on the exhaust half (-x)
    mb.rbox((-0.075, cy, zt + 0.074), (0.13, length * 0.80, 0.006), 0.002, "s1x_k20_coilcover")
    for k in range(5):
        mb.box((-0.035 - k * 0.022, cy, zt + 0.078), (0.010, length * 0.78, 0.008), "s1x_k20_coilcover")
    # coil cover (intake half, +x): raised silver plate with HONDA letters + i-VTEC plaque
    cover = Vector((0.075, cy + 0.02, zt + 0.085))
    mb.rbox(tuple(cover), (0.16, length * 0.70, 0.022), 0.008, "s1x_k20_coilcover")
    for k in (-1, 1):                                          # bolt bosses
        mb.cylinder((0.075 + k * 0.05, cy - length * 0.33, zt + 0.07), (0.075 + k * 0.05, cy - length * 0.33, zt + 0.10),
                    0.010, "s1x_k20_coilcover", segs=12)
    # i-VTEC plaque: textured quad on top of the coil cover (texture reads along +y)
    pz = zt + 0.0985
    px0, px1, py0, py1 = 0.050, 0.100, cy + 0.015, cy + 0.125
    fs = mb.add_faces([(px1, py0, pz), (px1, py1, pz), (px0, py1, pz), (px0, py0, pz)], [(0, 1, 2, 3)], "s1x_k20_plaque",
                      smooth=False)
    for f in fs:
        for loop in f.loops:
            co = loop.vert.co
            loop[mb.uv].uv = ((co.y - py0) / (py1 - py0), (co.x - px0) / (px1 - px0))
    # oil filler cap
    mb.cylinder((-0.02, cy - 0.17, zt + 0.07), (-0.02, cy - 0.17, zt + 0.095), 0.026, M_BLACK, segs=20)
    # spark plug / coil connectors poking out under the cover edge
    for k in range(4):
        yy = cy - 0.15 + k * 0.10
        mb.rbox((0.165, yy, zt + 0.075), (0.02, 0.025, 0.02), 0.004, M_BLACK)
    # intake manifold: plenum on +x with four curved cast runners
    pl = Vector((0.27, cy, zt - 0.06))
    mb.rbox(tuple(pl), (0.12, length * 0.88, 0.14), 0.05, "s1x_k20_manifold")
    for k in range(4):
        yy = y0 + 0.08 + k * 0.115
        path = [(0.13, yy, zt - 0.02), (0.18, yy, zt + 0.02), (0.235, yy, zt + 0.01), (0.27, yy, zt - 0.05)]
        mb.tube(path, 0.026, "s1x_k20_manifold", segs=14)
    # throttle body (front of the plenum, RWD swap) + idle air control
    mb.cylinder((0.27, y0 - 0.02, zt - 0.06), (0.27, y0 + 0.05, zt - 0.06), 0.040, M_ALU, segs=22)
    mb.cylinder((0.27, y0 - 0.03, zt - 0.06), (0.27, y0 - 0.02, zt - 0.06), 0.034, M_BLACK, segs=22)
    mb.rbox((0.32, y0 + 0.03, zt - 0.03), (0.04, 0.05, 0.05), 0.008, M_BLACK)
    # fuel rail + injectors
    mb.cylinder((0.155, y0 + 0.04, zt - 0.05), (0.155, y1 - 0.04, zt - 0.05), 0.010, M_STEEL, segs=10)
    for k in range(4):
        yy = y0 + 0.08 + k * 0.115
        mb.cylinder((0.155, yy, zt - 0.05), (0.14, yy, zt - 0.10), 0.008, "s1x_injector_blue", segs=10)
    # coolant: thermostat housing + upper hose toward the radiator
    mb.rbox((-0.05, y0 + 0.02, zt - 0.03), (0.06, 0.06, 0.06), 0.01, M_ALU)
    mb.tube([(-0.05, y0 - 0.01, zt - 0.03), (-0.10, y0 - 0.15, zt - 0.06), (-0.20, -1.85, 0.53)], 0.019, M_RUBBER, segs=12)
    # vacuum / breather hoses (the black hoses in the photo)
    mb.tube([(0.02, cy - 0.20, zt + 0.06), (0.12, cy - 0.24, zt + 0.10), (0.30, cy - 0.20, zt + 0.02)], 0.009, M_RUBBER, segs=8)
    mb.tube([(-0.16, y1 - 0.06, zt - 0.02), (-0.20, y1 - 0.12, zt + 0.02), (-0.22, y1 - 0.30, zt - 0.10)], 0.012, M_RUBBER, segs=8)
    extras = [_letters("HONDA", 0.032, (0.075, cy - 0.04, zt + 0.0965), "s1x_k20_coilcover", rot=(0, 0, math.radians(90)))]
    return [_attach(mb, extras, f"{pfx}_engine_k20")]


def engine_ka24(D, pfx):
    mb = MeshBuilder(f"{pfx}_engine_ka24")
    length, w = 0.58, 0.44
    y0, y1, cy = _base(mb, D, length, w, "s1x_engine_block")
    zt = 0.215 + 0.40
    # black wrinkle cam cover with a silver centre strip
    mb.rbox((0, cy, zt + 0.04), (w * 0.72, length * 0.93, 0.08), 0.03, "s1x_engine_cover_black")
    mb.rbox((0, cy, zt + 0.081), (0.07, length * 0.80, 0.006), 0.003, "s1x_engine_cover_silver")
    mb.cylinder((-0.05, cy - 0.20, zt + 0.08), (-0.05, cy - 0.20, zt + 0.10), 0.025, M_BLACK, segs=18)
    # intake plenum "TWIN CAM 16 VALVE" (+x) with runners
    pl = Vector((0.24, cy, zt - 0.02))
    mb.rbox(tuple(pl), (0.12, length * 0.84, 0.16), 0.04, "s1x_engine_cover_silver")
    for k in range(4):
        yy = y0 + 0.10 + k * 0.13
        mb.tube([(0.15, yy, zt - 0.06), (0.19, yy, zt - 0.05)], 0.022, M_ALU, segs=12)
    mb.cylinder((0.24, y1 - 0.02, zt - 0.02), (0.24, y1 + 0.04, zt - 0.02), 0.035, M_ALU, segs=18)
    mb.tube([(-0.05, y0 - 0.01, zt - 0.03), (-0.12, y0 - 0.15, zt - 0.06), (-0.20, -1.85, 0.53)], 0.019, M_RUBBER, segs=12)
    extras = [_letters("TWIN CAM 16 VALVE", 0.018, (0.302, cy, zt - 0.01), "s1x_metal_black",
                       rot=(math.radians(90), 0, math.radians(90)))]
    return [_attach(mb, extras, f"{pfx}_engine_ka24")]


def engine_sr20(D, pfx):
    mb = MeshBuilder(f"{pfx}_engine_sr20")
    length, w = 0.52, 0.40
    y0, y1, cy = _base(mb, D, length, w, "s1x_engine_block_alu")
    zt = 0.215 + 0.40
    # red top cam cover with the black coil pack strip
    mb.rbox((0, cy, zt + 0.04), (w * 0.72, length * 0.93, 0.08), 0.03, "s1x_engine_cover_red")
    mb.rbox((0, cy, zt + 0.083), (0.06, length * 0.78, 0.012), 0.004, M_BLACK)
    for k in range(4):
        mb.cylinder((0.0, y0 + 0.08 + k * 0.12, zt + 0.08), (0.0, y0 + 0.08 + k * 0.12, zt + 0.095), 0.012, M_BLACK, segs=10)
    mb.cylinder((-0.06, cy + 0.18, zt + 0.08), (-0.06, cy + 0.18, zt + 0.10), 0.024, M_BLACK, segs=18)
    # silver plenum + runners
    mb.rbox((0.23, cy, zt - 0.01), (0.11, length * 0.82, 0.15), 0.04, "s1x_engine_cover_silver")
    for k in range(4):
        yy = y0 + 0.09 + k * 0.12
        mb.tube([(0.14, yy, zt - 0.05), (0.18, yy, zt - 0.04)], 0.021, M_ALU, segs=12)
    mb.tube([(-0.05, y0 - 0.01, zt - 0.03), (-0.12, y0 - 0.15, zt - 0.06), (-0.20, -1.85, 0.53)], 0.019, M_RUBBER, segs=12)
    extras = [_letters("TWIN CAM 16 VALVE", 0.017, (0.286, cy, zt + 0.0), "s1x_metal_black",
                       rot=(math.radians(90), 0, math.radians(90)))]
    return [_attach(mb, extras, f"{pfx}_engine_sr20")]
