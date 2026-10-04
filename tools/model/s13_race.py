"""S13 race hardware meshes (requires bpy).  Geometry is driven by the same
data as the JBeam in tools/vehicle/s13/race.py so tubes sit on their nodes."""
from __future__ import annotations

import math

import bpy
import numpy as np
from mathutils import Matrix, Vector

from . import bl, panels as P
from .prims import MeshBuilder, rounded_rect
from .s13_parts import SPEC, grid_faces
from .shape import top_z, side_x
from tools.vehicle.s13 import dims as D, race as R, panels_jb as PJ, panel_spec as S

M_CAGE = "s1x_cage_grey"
M_ALU = "s1x_aluminium_sheet"
M_CARBON = "s1x_carbon"


# ---------------------------------------------------------------------------
# tubes
# ---------------------------------------------------------------------------
def _inset(name, p):
    """Pull frame tube end points slightly inside the shell (body nodes sit on the skin)."""
    p = np.array(p, float)
    if name.startswith("cg"):
        return p
    p[0] *= 0.955
    if p[2] < 0.26:
        p[2] += 0.025
    return p


def tube_set(mb, pairs, pos, radius, mat, segs=12, joints=True):
    used = {}
    for a, b in pairs:
        pa, pb = _inset(a, pos[a]), _inset(b, pos[b])
        if np.linalg.norm(pb - pa) < 0.02:
            continue
        mb.tube([tuple(pa), tuple(pb)], radius, mat, segs=segs, caps=False)
        used[a] = pa
        used[b] = pb
    if joints:
        for n, p in used.items():
            prof = [(radius * 1.25 * math.sin(math.pi * k / 8), radius * 1.25 * -math.cos(math.pi * k / 8)) for k in range(9)]
            mb.lathe(prof, mat, segs=12, axis="z", center=tuple(p))


def rollcages():
    pos = R.node_positions()
    out = []
    for key, (title, value, levels) in R.CAGE_TITLES.items():
        mb = MeshBuilder(f"s13_rollcage_{key}")
        tube_set(mb, R.cage_tubes(levels), pos, R.TUBE_R["cage"], M_CAGE)
        # base plates at the floor feet
        for nm, x, y, z, w, att in R.cage_nodes(levels):
            if z < 0.3:
                mb.box((x, y, z - 0.02), (0.10, 0.10, 0.006), M_CAGE)
        out.append(mb)
    return out


def tubeframe():
    pos = R.node_positions()
    mb = MeshBuilder("s13_tubeframe")
    tube_set(mb, R.cage_tubes(R.LEVEL_ORDER), pos, R.TUBE_R["cage"], M_CAGE)
    tube_set(mb, R.frame_tubes(), pos, R.TUBE_R["frame"], M_CAGE)
    # gussets / strut tower plates
    for s in (1, -1):
        mb.cylinder((s * D.FS1[0], D.FS1[1], D.FS1[2] - 0.03), (s * D.FS1[0], D.FS1[1], D.FS1[2] - 0.01), 0.075, M_ALU, segs=20)
        mb.cylinder((s * D.RS1[0], D.RS1[1], D.RS1[2] - 0.03), (s * D.RS1[0], D.RS1[1], D.RS1[2] - 0.01), 0.07, M_ALU, segs=20)
    # aluminium firewall (the tube car keeps a bulkhead)
    xs = np.linspace(-0.70, 0.70, 11)
    verts = []
    for z in (0.24, 0.50, 0.74):
        for x in xs:
            verts.append((float(x), -0.885, z))
    mb.add_faces(verts, grid_faces(3, len(xs)), M_ALU, smooth=False)
    return mb


def tube_floor():
    """Flat aluminium floor + transmission tunnel + rear wheel tubs for the spaceframe."""
    mb = MeshBuilder("s13_tube_floor")
    ys = np.linspace(-0.88, 2.05, 36)
    xs = np.linspace(-0.76, 0.76, 21)
    verts = []
    for y in ys:
        k = SPEC.keypoints(float(y))
        for x in xs:
            w = k["w_sill"] - 0.04
            xx = float(np.clip(x, -w, w))
            z = 0.185
            if abs(xx) < 0.14 and y < 0.75:
                z += 0.11 * (1 - (abs(xx) / 0.14) ** 4)
            if y > 1.0:
                z = 0.30
            verts.append((xx, float(y), z))
    mb.add_faces(verts, grid_faces(len(ys), len(xs), flip=True), M_ALU, smooth=False)
    # rear tubs
    cy, cz = D.AXLE_R_Y, D.AXLE_Z
    for s in (1, -1):
        r = 0.39
        verts = []
        n = 24
        for i in range(n + 1):
            a = math.pi * (0.05 + 0.9 * i / n)
            y = cy - r * math.cos(a)
            z = cz + r * math.sin(a)
            verts += [(s * 0.46, y, z), (s * 0.80, y, z)]
        faces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) if s < 0 else (2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1) for i in range(n)]
        mb.add_faces(verts, faces, M_ALU, smooth=True)
        mb.lathe([(0.0, 0.0), (r, 0.0)], M_ALU, segs=20, axis="x", center=(s * 0.46, cy, cz), angle=(0.15, math.pi - 0.15))
    return mb


# ---------------------------------------------------------------------------
# aero
# ---------------------------------------------------------------------------
def _slab(mb, outline_xy, z_of, thickness, mat):
    """Extruded plate from a plan outline [(x, y)] with per-point height z_of(x, y)."""
    n = len(outline_xy)
    top = [(x, y, z_of(x, y)) for x, y in outline_xy]
    bot = [(x, y, z_of(x, y) - thickness) for x, y in outline_xy]
    verts = top + bot
    faces = [tuple(range(n)), tuple(range(n, 2 * n))[::-1]]
    faces += [(i, n + i, n + (i + 1) % n, (i + 1) % n) for i in range(n)]
    return mb.add_faces(verts, faces, mat, smooth=False)


def splitter():
    mb = MeshBuilder("s13_splitter_race")
    # plan outline follows the bumper nose, 9 cm proud of it
    pts = []
    for t in np.linspace(-1, 1, 25):
        x = 0.78 * t
        y = -2.34 + 0.20 * abs(t) ** 3.2
        pts.append((x, y))
    pts += [(0.78, -1.96), (-0.78, -1.96)]          # rear edge (closes the loop counter-clockwise from above)

    def z_of(x, y):
        return 0.150 + (y + 2.34) / 0.38 * 0.018          # front edge lower than rear edge

    _slab(mb, pts, z_of, 0.008, M_CARBON)
    # end plates + support rods
    for s in (1, -1):
        mb.box((s * 0.775, -2.10, 0.195), (0.006, 0.20, 0.07), M_CARBON)
        mb.tube([(s * 0.42, -2.28, 0.152), (s * 0.40, -2.18, 0.30)], 0.006, "s1x_aluminium_polished", segs=8)
    mb.tube([(0.0, -2.30, 0.152), (0.0, -2.20, 0.29)], 0.006, "s1x_aluminium_polished", segs=8)
    return mb


def canards():
    mb = MeshBuilder("s13_canards_race")
    for s in (1, -1):
        for k, (z, dz) in {1: (0.330, 0.0), 2: (0.450, 0.010)}.items():
            a = (s * 0.770, -2.080 + dz, z)
            b = (s * 0.800, -1.960 + dz, z + 0.030)
            c = (s * 0.865, -2.000 + dz, z + 0.016)
            top = [a, b, c] if s > 0 else [a, c, b]
            bot = [(p[0], p[1], p[2] - 0.004) for p in top]
            mb.add_faces(top + bot, [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)], M_CARBON, smooth=False)
    return mb


def _airfoil(chord, thick=0.11, camber=0.06, n=18):
    """Inverted cambered airfoil (suction side down) as a closed loop of (u, v) with u along chord (0=LE)."""
    us = (1 - np.cos(np.linspace(0, math.pi, n))) / 2
    yt = 5 * thick * (0.2969 * np.sqrt(us) - 0.1260 * us - 0.3516 * us ** 2 + 0.2843 * us ** 3 - 0.1015 * us ** 4)
    yc = camber * 4 * us * (1 - us)
    upper = [(u * chord, -(c - t) * chord) for u, c, t in zip(us, yc, yt)]     # inverted: camber points down
    lower = [(u * chord, -(c + t) * chord) for u, c, t in zip(us, yc, yt)]
    return upper + lower[::-1][1:-1]


def wing_gt():
    """Main plane + gurney + endplates at the default angle (mapped to the wing nodes)."""
    mb = MeshBuilder("s13_wing_gt")
    (yl, zl), (yt, zt) = R.wing_points(R.WING["default_angle"])
    ang = math.atan2(zt - zl, yt - yl)
    chord = R.WING["chord"]
    span = R.WING["span"] + 0.02
    loop = _airfoil(chord)
    ca, sa = math.cos(ang), math.sin(ang)

    def to3(u, v, x):
        # chord direction along +y rotated up by ang; v perpendicular (up)
        return (x, yl + u * ca - v * sa, zl + u * sa + v * ca)
    n = len(loop)
    verts = [to3(u, v, -span) for u, v in loop] + [to3(u, v, span) for u, v in loop]
    faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    mb.add_faces(verts, faces, M_CARBON, smooth=True)
    # gurney flap
    mb.box(to3(chord - 0.004, 0.012, 0.0), (2 * span, 0.004, 0.026), M_CARBON, rot=Matrix.Rotation(ang, 3, "X"))
    # end plates: trapezoids extending mostly below the main plane
    for s in (1, -1):
        x = s * (span + 0.003)
        le = Vector(to3(-0.03, 0.0, x))
        te = Vector(to3(chord + 0.04, 0.0, x))
        plate = [(le.y, le.z - 0.13), (te.y, te.z - 0.10), (te.y + 0.01, te.z + 0.07), (le.y + 0.06, le.z + 0.05)]
        for dx, outward in ((0.0, (s, 0, 0)), (s * -0.004, (-s, 0, 0))):
            mb.polygon([(x + dx, y, z) for y, z in plate], M_CARBON, outward=outward)
    return mb


def wing_gt_mounts():
    """Swan-neck uprights: deck foot -> knee -> over the top of the main plane."""
    mb = MeshBuilder("s13_wing_gt_mounts")
    k, up = R._angle_link_factor()
    (yl, zl), (yt, zt) = R.wing_points(R.WING["default_angle"])
    xm = R.WING["x_mount"]
    for s in (1, -1):
        path = [(2.185, 0.905), (2.17, 1.00), (up[0], up[1] + 0.06), (yl + 0.05, zl + 0.075), (yl + 0.10, zl + 0.045)]
        # flat plate upright: offset the path +-6 mm in x, extrude a 70 mm wide band
        verts, faces = [], []
        prof = []
        for i, (y, z) in enumerate(path):
            prof.append((y, z))
        m = len(prof)
        for dx in (-0.006, 0.006):
            for y, z in prof:
                verts.append((s * xm + dx, y - 0.035, z))
            for y, z in prof:
                verts.append((s * xm + dx, y + 0.035, z))
        for side in range(2):
            o = side * 2 * m
            for i in range(m - 1):
                f = (o + i, o + i + 1, o + m + i + 1, o + m + i)
                faces.append(f if (side == 0) ^ (s < 0) else f[::-1])
        mb.add_faces(verts, faces, "s1x_aluminium", smooth=False)
        mb.cylinder((s * xm, 2.185, 0.895), (s * xm, 2.185, 0.912), 0.035, "s1x_aluminium", segs=16)
    return mb


def wicker():
    mb = MeshBuilder("s13_wing_wicker")
    pts = [(-0.64, 2.190, 0.900), (0.64, 2.190, 0.900), (0.62, 2.222, 0.962), (-0.62, 2.222, 0.962)]
    mb.polygon(pts, "s1x_aluminium", outward=(0, 1, 0.4))
    mb.polygon([(x, y - 0.003, z) for x, y, z in pts], "s1x_aluminium", outward=(0, -1, -0.4))
    return mb


def diffuser():
    mb = MeshBuilder("s13_diffuser_race")
    xs = np.linspace(-0.62, 0.62, 13)
    verts = []
    for y, z in ((1.90, 0.205), (2.30, 0.330)):
        for x in xs:
            verts.append((float(x), y, z))
    mb.add_faces(verts, grid_faces(2, len(xs), flip=True), M_CARBON, smooth=False)
    for x in (-0.62, -0.30, 0.0, 0.30, 0.62):
        mb.polygon([(x, 1.90, 0.205), (x, 2.30, 0.330), (x, 2.30, 0.235), (x, 2.0, 0.19)], M_CARBON, outward=(1, 0, 0))
        mb.polygon([(x + 0.004, 1.90, 0.205), (x + 0.004, 2.30, 0.330), (x + 0.004, 2.30, 0.235), (x + 0.004, 2.0, 0.19)],
                   M_CARBON, outward=(-1, 0, 0))
    return mb


def overfenders_R():
    """Bolt-on rear over-fenders: a flared band around each rear arch."""
    mb = MeshBuilder("s13_overfenders_R")
    cy, cz = S.ARCH_R
    r0 = S.ARCH_RADIUS
    for s in (1, -1):
        rows = []
        n = 36
        for i in range(n + 1):
            a = math.pi * (-0.06 + 1.12 * i / n)
            row = []
            for t, (dr, dx) in enumerate(((-0.004, 0.0), (0.02, 0.040), (0.050, 0.052), (0.085, 0.030), (0.115, 0.0))):
                r = r0 + dr
                y = cy - r * math.cos(a)
                z = cz + r * math.sin(a)
                x = side_x(SPEC, y, max(z, 0.2)) + 0.002 + dx
                row.append((s * x, y, z))
            rows.append(row)
        nv = len(rows[0])
        verts = [v for row in rows for v in row]
        mb.add_faces(verts, grid_faces(len(rows), nv, flip=s < 0), "s13_paint", smooth=True)
        # rivets
        for i in range(2, n - 1, 4):
            a = math.pi * (-0.06 + 1.12 * i / n)
            r = r0 + 0.10
            y, z = cy - r * math.cos(a), cz + r * math.sin(a)
            x = side_x(SPEC, y, max(z, 0.2)) + 0.012
            mb.cylinder((s * x, y, z), (s * (x + 0.004), y, z), 0.005, "s1x_aluminium_polished", segs=8)
    return mb


def widen_fender(src, name, side_sign, amount):
    ob = src.copy()
    ob.data = src.data.copy()
    ob.name = name
    ob.data.name = name
    for c in src.users_collection:
        c.objects.link(ob)
    for v in ob.data.vertices:
        x, y, z = v.co
        v.co.x = x + side_sign * amount * PJ.flare_weight(y, z, "F")
    return ob


def recolor_copy(src, name, mat_map):
    """Copy an object and swap materials: mat_map {old: new} or a single material name for all."""
    from . import materials as MR
    ob = src.copy()
    ob.data = src.data.copy()
    ob.name = name
    ob.data.name = name
    for c in src.users_collection:
        c.objects.link(ob)
    for i, m in enumerate(ob.data.materials):
        new = mat_map if isinstance(mat_map, str) else mat_map.get(m.name if m else "", None)
        if new:
            ob.data.materials[i] = MR.blender_material(new)
    return ob


def vented_hood(src):
    """FRP race hood: copy of the stock hood with two louvre fields cut out and louvre slats below."""
    ob = recolor_copy(src, "s13_hood_vented", {})
    for s in (1, -1):
        for i in range(6):
            y0 = -1.62 + i * 0.075
            rect = [(s * 0.14, y0), (s * 0.40, y0), (s * 0.40, y0 + 0.035), (s * 0.14, y0 + 0.035)]
            P.cut_away(ob, "plan", rect, 0.4, 1.2)
    mb = MeshBuilder("__louvres")
    for s in (1, -1):
        for i in range(6):
            y0 = -1.62 + i * 0.075
            yy = y0 + 0.0175
            z = top_z(SPEC, yy, 0.27) - 0.022
            mb.box((s * 0.27, yy + 0.01, z), (0.27, 0.05, 0.003), "s1x_dark", rot=Matrix.Rotation(math.radians(-28), 3, "X"))
    lv = mb.to_object()
    return P.join([ob, lv], "s13_hood_vented")


def wheelie_bar():
    pos = {}
    x, ye, za = R.WHEELIE["x"], R.WHEELIE["y_end"], R.WHEELIE["z_axle"]
    for s, sx in (("l", 1), ("r", -1)):
        pos["wb0" + s] = (sx * x, 2.10, 0.250)
        pos["wb1" + s] = (sx * x, 2.10, 0.420)
        pos["wb2" + s] = (sx * x, 2.85, 0.205)
        pos["wb3" + s] = (sx * x, ye, za)
        pos["wb4" + s] = (sx * (x + 0.04), ye, za)
    pos["wb2"] = (0.0, 2.85, 0.205)
    mb = MeshBuilder("s13_wheeliebar")
    pairs = []
    for s in ("l", "r"):
        pairs += [("wb0" + s, "wb2" + s), ("wb1" + s, "wb2" + s), ("wb2" + s, "wb3" + s), ("wb1" + s, "wb3" + s)]
    pairs += [("wb2l", "wb2"), ("wb2r", "wb2"), ("wb3l", "wb3r"), ("wb2l", "wb3r"), ("wb2r", "wb3l")]
    for a, b in pairs:
        mb.tube([pos[a], pos[b]], 0.016, "s1x_aluminium_polished", segs=10, caps=True)
    for s in ("l", "r"):
        mb.rbox(pos["wb0" + s], (0.05, 0.06, 0.06), 0.01, "s1x_metal_black")
        mb.rbox(pos["wb1" + s], (0.05, 0.06, 0.06), 0.01, "s1x_metal_black")
    return mb


def wheelie_wheel():
    mb = MeshBuilder("s13_wheeliebar_wheel")
    r = R.WHEELIE["hub_r"]
    mb.lathe([(r * 0.55, -0.018), (r, -0.016), (r, 0.016), (r * 0.55, 0.018)], "s1x_polyurethane", segs=32, axis="x", closed=True)
    mb.lathe([(0.0, -0.02), (r * 0.56, -0.02), (r * 0.56, 0.02), (0.0, 0.02)], "s1x_aluminium", segs=24, axis="x", closed=True)
    return mb


def parachute():
    mb = MeshBuilder("s13_parachute")
    c = Vector((0.0, 2.33, 0.47))
    mb.cylinder(tuple(c + Vector((0, -0.04, 0))), tuple(c + Vector((0, 0.30, 0))), 0.095, "s1x_chute_red", segs=24)
    mb.lathe([(0.095, 0.30), (0.07, 0.34), (0.0, 0.35)], "s1x_chute_red", segs=24, axis="y", center=tuple(c))
    for t in (0.06, 0.20):
        mb.cylinder(tuple(c + Vector((0, t, 0))), tuple(c + Vector((0, t + 0.025, 0))), 0.098, "s1x_strap_black", segs=24)
    mb.rbox(tuple(c + Vector((0, -0.06, -0.09))), (0.12, 0.04, 0.05), 0.008, "s1x_metal_black")
    mb.tube([tuple(c + Vector((0.05, 0.30, 0.05))), tuple(c + Vector((0.05, -0.05, 0.12))), (0.05, 2.10, 0.70)],
            0.003, "s1x_strap_black", segs=6)
    return mb


def fuelcells():
    out = []
    for name, cap in (("s13_fuelcell", 40), ("s13_fuelcell_drag", 10)):
        mb = MeshBuilder(name)
        hw = 0.26 if cap > 20 else 0.16
        mb.rbox((0.0, 1.80, 0.40), (2 * hw + 0.05, 0.36, 0.20 if cap > 20 else 0.14), 0.02, "s1x_aluminium_sheet")
        mb.cylinder((0.0, 1.80, 0.50 if cap > 20 else 0.47), (0.0, 1.80, 0.53 if cap > 20 else 0.50), 0.045,
                    "s1x_aluminium_polished", segs=20)
        for s in (1, -1):
            mb.box((s * (hw + 0.03), 1.80, 0.34), (0.03, 0.42, 0.012), "s1x_metal_black")
        out.append(mb)
    return out


def exhaust_race():
    from . import mech
    return mech.exhaust_stock(D, "s13", name="s13_exhaust_race", tips=1, tip_r=0.052, pipe_r=0.038)


# ---------------------------------------------------------------------------
# race interior
# ---------------------------------------------------------------------------
def dash_race():
    mb = MeshBuilder("s13_dash_race")
    # flat carbon dash panel spanning the cowl, with a lower bolster
    xs = np.linspace(-0.72, 0.72, 25)
    verts = []
    for x in xs:
        for y, z in ((-0.80, 0.86), (-0.64, 0.905), (-0.50, 0.90), (-0.47, 0.86), (-0.47, 0.70)):
            verts.append((float(x), y, z))
    mb.add_faces(verts, grid_faces(len(xs), 5, flip=True), M_CARBON, smooth=False)
    # column shroud + pod stalk
    sc = Vector(D.STEER_CENTER)
    a = math.radians(23)
    d = Vector((0, -math.cos(a), -math.sin(a)))
    mb.tube([tuple(sc + d * 0.06), tuple(sc + d * 0.30)], 0.045, "s1x_dark", segs=14)
    return mb


def race_tach():
    from tools.vehicle.s13.vehicle import RACE_TACH
    mb = MeshBuilder("s13_race_tach")
    tx, ty, tz = RACE_TACH
    R0 = 0.066
    # cup (opens toward +y, the driver)
    mb.lathe([(0.0, -0.06), (R0 + 0.006, -0.055), (R0 + 0.010, 0.0), (R0 + 0.010, 0.012), (R0 - 0.002, 0.012)],
             "s1x_metal_black", segs=40, axis="y", center=(tx, ty, tz))
    # face (textured disc, 0..1 UVs)
    n = 40
    verts = [(tx, ty + 0.001, tz)] + [(tx - R0 * math.cos(2 * math.pi * k / n), ty + 0.001, tz + R0 * math.sin(2 * math.pi * k / n))
                                      for k in range(n)]
    faces = [(0, 1 + k, 1 + (k + 1) % n) for k in range(n)]
    fs = mb.add_faces(verts, faces, "s13_racetach_face", smooth=False)
    for f in fs:
        for loop in f.loops:
            co = loop.vert.co
            loop[mb.uv].uv = (0.5 + (tx - co.x) / (2 * R0), 0.5 + (co.z - tz) / (2 * R0))
    # shift light strip above the pod
    for i in range(5):
        x = tx + 0.048 - i * 0.024
        mb.cylinder((x, ty - 0.004, tz + R0 + 0.022), (x, ty + 0.006, tz + R0 + 0.022), 0.007, f"s13_shiftled_{i}", segs=12)
    mb.rbox((tx, ty - 0.01, tz + R0 + 0.022), (0.14, 0.02, 0.022), 0.006, "s1x_metal_black")
    # stalk to the dash
    mb.tube([(tx, ty - 0.05, tz - 0.02), (tx, ty - 0.11, tz - 0.12)], 0.012, "s1x_metal_black", segs=10)
    return mb


def needle_race():
    mb = MeshBuilder("s13_needle_race")
    L = 0.058
    verts = [(-0.003, 0.002, -0.012), (0.003, 0.002, -0.012), (0.0009, 0.002, L), (-0.0009, 0.002, L)]
    mb.add_faces(verts, [(0, 1, 2, 3), (3, 2, 1, 0)], "s13_needle", smooth=False)
    mb.cylinder((0, 0.0, 0), (0, 0.007, 0), 0.008, "s1x_dark", segs=12)
    return mb


def _bucket(mb, x, shell=M_CARBON, pad="s1x_seat_fabric", harness=True):
    """FIA-style bucket: shell from a lofted U-section, pads and an optional 6-point harness."""
    y_h, z_h = D.SEAT_H_POINT[1], D.SEAT_H_POINT[2]
    rot = Matrix.Rotation(math.radians(-16), 3, "X")
    base = Vector((x, y_h + 0.12, z_h - 0.12))
    rows = []
    for t in np.linspace(0, 1, 14):
        # path: seat pan forward edge (t=0) -> hip -> back -> head (t=1)
        if t < 0.35:
            u = t / 0.35
            c = Vector((0, -0.42 + 0.42 * u, 0.02 * u))
            w, h = 0.25, 0.10
        else:
            u = (t - 0.35) / 0.65
            c = rot @ Vector((0, 0.02, 0.02 + 0.78 * u))
            w, h = 0.26 - 0.06 * u ** 2, 0.16 - 0.04 * u
        row = []
        for k in range(13):
            a = math.pi * k / 12
            px, pz = -w * math.cos(a), -h * math.sin(a) * (1 if t < 0.35 else 0) + (0 if t < 0.35 else 0)
            if t < 0.35:
                pt = Vector((px, c.y, c.z + h * (1 - math.sin(a))))
            else:
                n_ = rot @ Vector((0, 1, 0))
                pt = c + Vector((px, 0, 0)) - n_ * (h * math.sin(a) - h)
            row.append(tuple(base + pt))
        rows.append(row)
    verts = [v for r in rows for v in r]
    mb.add_faces(verts, grid_faces(len(rows), 13, flip=True), shell, smooth=True)
    mb.add_faces(verts, grid_faces(len(rows), 13, flip=False), pad, smooth=True)
    # side mounts / rails
    mb.rbox((x, y_h - 0.08, 0.21), (0.40, 0.42, 0.04), 0.008, "s1x_metal_black")
    if harness:
        top = base + rot @ Vector((0, 0.02, 0.70))
        for s in (1, -1):
            mb.tube([tuple(top + Vector((s * 0.06, 0.0, 0.0))), tuple(base + Vector((s * 0.07, -0.20, 0.40))),
                     tuple(base + Vector((s * 0.10, -0.24, 0.18)))], 0.012, "s1x_harness_red", segs=4)
            mb.tube([tuple(base + Vector((s * 0.23, -0.05, 0.06))), tuple(base + Vector((s * 0.06, -0.28, 0.16)))],
                    0.012, "s1x_harness_red", segs=4)
        mb.rbox(tuple(base + Vector((0, -0.27, 0.17))), (0.07, 0.02, 0.07), 0.01, "s1x_aluminium_polished")
        mb.tube([tuple(top + Vector((0.06, 0.0, 0.0))), (x + 0.10, 0.62, 0.72)], 0.012, "s1x_harness_red", segs=4)
        mb.tube([tuple(top + Vector((-0.06, 0.0, 0.0))), (x - 0.10, 0.62, 0.72)], 0.012, "s1x_harness_red", segs=4)


def seat_race():
    mb = MeshBuilder("s13_seat_race")
    _bucket(mb, D.DRIVER_X)
    return mb


def seats_bucket():
    mb = MeshBuilder("s13_seats_bucket")
    for x in (D.DRIVER_X, -D.DRIVER_X):
        _bucket(mb, x, shell="s1x_frp_black", pad="s13_seat_cloth", harness=False)
    return mb


def extinguisher():
    mb = MeshBuilder("s13_extinguisher")
    c = Vector((-0.22, -0.30, 0.25))
    mb.cylinder(tuple(c), tuple(c + Vector((0, 0.30, 0))), 0.045, "s1x_fire_red", segs=20)
    mb.lathe([(0.045, 0.30), (0.03, 0.33), (0.012, 0.35), (0.0, 0.35)], "s1x_fire_red", segs=20, axis="y", center=tuple(c))
    mb.rbox(tuple(c + Vector((0, 0.37, 0))), (0.03, 0.04, 0.05), 0.006, "s1x_chrome")
    for t in (0.06, 0.24):
        mb.cylinder(tuple(c + Vector((0, t, 0))), tuple(c + Vector((0, t + 0.02, 0))), 0.048, "s1x_metal_black", segs=20)
    return mb


def switch_panel():
    mb = MeshBuilder("s13_race_switchpanel")
    c = Vector((0.0, -0.47, 0.78))
    mb.box(tuple(c), (0.26, 0.006, 0.12), "s1x_aluminium_sheet")
    for i in range(6):
        x = -0.10 + i * 0.04
        mb.cylinder((x, -0.467, 0.80), (x, -0.45, 0.81), 0.004, "s1x_chrome", segs=8)
        mb.box((x, -0.466, 0.765), (0.022, 0.004, 0.008), "s1x_fire_red" if i == 0 else "s1x_dark")
    mb.cylinder((0.10, -0.467, 0.75), (0.10, -0.455, 0.75), 0.016, "s1x_fire_red", segs=16)
    return mb


def race_all():
    return ([*rollcages(), tubeframe(), tube_floor(), splitter(), canards(), wing_gt(), wing_gt_mounts(), wicker(),
             diffuser(), overfenders_R(), wheelie_bar(), wheelie_wheel(), parachute(), *fuelcells(), exhaust_race(),
             dash_race(), race_tach(), needle_race(), seat_race(), seats_bucket(), extinguisher(), switch_panel()])
