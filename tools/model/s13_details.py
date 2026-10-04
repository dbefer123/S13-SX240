"""S13 exterior detailing (requires bpy): bumper openings, grilles, lamps, rub strips,
handles, markers, badges, fuel door, wipers, licence plate recess.

`pre_solidify(out)` cuts openings into the open panel surfaces; `post_solidify(out)`
adds inserts (grilles, lenses, strips, badges) and joins them into the panel objects so
they deform with the panel's flexbody.
"""
from __future__ import annotations

import math

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from . import bl, panels as P
from .prims import MeshBuilder, rounded_rect, text_mesh
from .shape import side_x, top_z
from tools.vehicle.s13 import body_spec as B, panel_spec as S

SPEC = B.hatch_spec()

# front bumper features in front view (x, z), left side; mirrored
F_LAMP = dict(cx=0.505, cz=0.418, w=0.205, h=0.044, r=0.019)
F_SIDE_GRILLE = dict(cx=0.505, cz=0.336, w=0.190, h=0.050, r=0.010)
F_CENTER_GRILLE = dict(cx=0.0, cz=0.336, w=0.600, h=0.056, r=0.012)
F_LIP_Z = 0.238
R_PLATE = dict(cx=0.0, cz=0.405, w=0.330, h=0.175, r=0.012, wall_y=2.226)   # licence plate sits at wall_y + 0.006
STRIP_Z = (0.332, 0.354)
PLATE_F = dict(x=0.0, z=0.415)


def _rect(cx, cz, w, h, r, mirror=False):
    pts = [(cx + px, cz + pz) for px, pz in rounded_rect(w, h, r, 5)]
    if mirror:
        pts = [(-x, z) for x, z in pts][::-1]
    return pts


class Surface:
    """Ray-cast helper against an object (front: rays toward +y; rear: toward -y; side: toward -x/+x)."""

    def __init__(self, ob):
        dg = bpy.context.evaluated_depsgraph_get()
        self.bvh = BVHTree.FromObject(ob, dg)

    def y_front(self, x, z):
        hit = self.bvh.ray_cast(Vector((x, -3.5, z)), Vector((0, 1, 0)))
        return hit[0].y if hit[0] is not None else None

    def y_rear(self, x, z):
        hit = self.bvh.ray_cast(Vector((x, 3.5, z)), Vector((0, -1, 0)))
        return hit[0].y if hit[0] is not None else None

    def x_side(self, y, z, s=1):
        hit = self.bvh.ray_cast(Vector((s * 2.0, y, z)), Vector((-s, 0, 0)))
        return hit[0].x if hit[0] is not None else None


# ---------------------------------------------------------------------------
# cuts on the open surfaces (before solidify)
# ---------------------------------------------------------------------------
FRONT_VARIANTS = {
    # name: (openings [(cx, cz, w, h, r)] mirrored when cx != 0, keep stock signal lamps, lip)
    "aero": ([(F_SIDE_GRILLE["cx"], F_SIDE_GRILLE["cz"], F_SIDE_GRILLE["w"], F_SIDE_GRILLE["h"], F_SIDE_GRILLE["r"]),
              (0.0, F_CENTER_GRILLE["cz"], F_CENTER_GRILLE["w"], F_CENTER_GRILLE["h"], F_CENTER_GRILLE["r"])], True, "lip"),
    "drift": ([(0.0, 0.322, 0.700, 0.118, 0.030), (0.590, 0.330, 0.085, 0.130, 0.020)], True, "deep"),
    "race": ([(0.0, 0.330, 0.940, 0.150, 0.035)], True, None),
    "drag": ([(0.0, 0.330, 0.460, 0.050, 0.020)], True, "flat"),
}
REAR_VARIANTS = {"aero": "valance", "race": "cutout"}


def _openings(spec_list):
    out = []
    for cx, cz, w, h, r in spec_list:
        out.append(_rect(cx, cz, w, h, r))
        if cx != 0:
            out.append(_rect(cx, cz, w, h, r, True))
    return out


def pre_solidify(out):
    # body-kit variants are cut from raw copies of the stock bumpers
    for key, (opens, lamps, lip) in FRONT_VARIANTS.items():
        v = P.duplicate(out["s13_bumper_F"], f"s13_bumper_F_{key}")
        for o in _openings(opens):
            P.cut_away(v, "front", o, -2.45, -1.95)
        if lamps:
            for m in (False, True):
                P.cut_away(v, "front", _rect(F_LAMP["cx"], F_LAMP["cz"], F_LAMP["w"], F_LAMP["h"], F_LAMP["r"], m),
                           -2.45, -1.95)
        out[f"s13_bumper_F_{key}"] = v
    for key, kind in REAR_VARIANTS.items():
        v = P.duplicate(out["s13_bumper_R"], f"s13_bumper_R_{key}")
        P.cut_away(v, "front", _rect(R_PLATE["cx"], R_PLATE["cz"], R_PLATE["w"], R_PLATE["h"], R_PLATE["r"]), 2.0, 2.45)
        if kind == "cutout":
            P.cut_away(v, "front", [(-0.64, 0.10), (0.64, 0.10), (0.64, 0.30), (-0.64, 0.30)], 2.0, 2.45)
        out[f"s13_bumper_R_{key}"] = v
    bf = out["s13_bumper_F"]
    for spec in (F_LAMP, F_SIDE_GRILLE):
        for m in (False, True):
            P.cut_away(bf, "front", _rect(spec["cx"] if not m else spec["cx"], spec["cz"], spec["w"], spec["h"], spec["r"], m),
                       -2.45, -1.95)
    P.cut_away(bf, "front", _rect(**{k: F_CENTER_GRILLE[k] for k in ("cx", "cz", "w", "h", "r")}), -2.45, -2.0)
    br = out["s13_bumper_R"]
    P.cut_away(br, "front", _rect(R_PLATE["cx"], R_PLATE["cz"], R_PLATE["w"], R_PLATE["h"], R_PLATE["r"]), 2.0, 2.45)


# ---------------------------------------------------------------------------
# inserts (after solidify)
# ---------------------------------------------------------------------------
def _assign_by(ob, mat_name, pred):
    from . import materials as MR
    me = ob.data
    mat = MR.blender_material(mat_name)
    if mat.name not in [m.name for m in me.materials if m]:
        me.materials.append(mat)
    idx = [m.name for m in me.materials].index(mat.name)
    for poly in me.polygons:
        if pred(poly.center, poly.normal):
            poly.material_index = idx


def _recess_grille(mb, surf, outline, depth=0.030, slat_pitch=0.012, mirror_x=False, rear=False):
    """Black back plate + horizontal slats behind a front-view opening."""
    xs = [p[0] for p in outline]
    zs = [p[1] for p in outline]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    ys = [surf.y_front(x, z) for x, z in outline]
    ys = [y for y in ys if y is not None]
    yb = (max(ys) if ys else -2.2) + depth
    mb.box(((x0 + x1) / 2, yb, (z0 + z1) / 2), (x1 - x0 + 0.02, 0.004, z1 - z0 + 0.02), "s1x_dark")
    # surround walls
    for xa, xb, za, zb in ((x0, x1, z0, z0), (x0, x1, z1, z1)):
        pass
    z = z0 + slat_pitch / 2
    while z < z1 - 0.004:
        ym = min((surf.y_front(x, z) or yb) for x in np.linspace(x0 + 0.01, x1 - 0.01, 5)) + 0.008
        mb.box(((x0 + x1) / 2, (ym + yb) / 2, z), (x1 - x0, yb - ym, 0.004), "s13_trim_black",
               rot=Matrix.Rotation(math.radians(-25), 3, "X"))
        z += slat_pitch


def _lens(mb, surf, outline, mat, inset=0.004):
    pts = []
    for x, z in outline:
        y = surf.y_front(x, z)
        if y is None:
            continue
        pts.append((x, y + inset, z))
    if len(pts) >= 3:
        mb.polygon(pts, mat, outward=(0, -1, 0))
        # rim (black bezel) behind the lens edges
        for (a, b) in zip(pts, pts[1:] + pts[:1]):
            pass


def _band(mb, ys, z0, z1, s, mat, avoid_arches=True, thick=0.004, surf=None):
    """Thin raised strip along the body side between z0..z1 for the given y samples."""
    rows = []
    for y in ys:
        if avoid_arches:
            skip = False
            for cy, cz in (S.ARCH_F, S.ARCH_R):
                if math.hypot(y - cy, (z0 + z1) / 2 - cz) < S.ARCH_RADIUS + 0.012:
                    skip = True
            if skip:
                if rows:
                    _emit_band(mb, rows, s, mat)
                rows = []
                continue
        xa = (surf.x_side(y, z0, s) if surf else None) or s * side_x(SPEC, y, z0)
        xb = (surf.x_side(y, z1, s) if surf else None) or s * side_x(SPEC, y, z1)
        rows.append((y, xa, xb))
    if rows:
        _emit_band(mb, rows, s, mat, thick)


def _emit_band(mb, rows, s, mat, thick=0.004):
    if len(rows) < 2:
        return
    z0, z1 = STRIP_Z
    verts = []
    for y, xa, xb in rows:
        verts += [(xa + s * 0.0008, y, z0), (xa + s * thick, y, z0 + 0.002), (xb + s * thick, y, z1 - 0.002),
                  (xb + s * 0.0008, y, z1)]
    faces = []
    for i in range(len(rows) - 1):
        for k in range(3):
            a, b = i * 4 + k, i * 4 + k + 1
            f = (a, a + 4, b + 4, b)
            faces.append(f if s > 0 else f[::-1])
    mb.add_faces(verts, faces, mat, smooth=True)


def _badge_text(name, text, size, loc, rot, mat, extrude=0.0015):
    ob = text_mesh(name, text, size, mat, location=loc, rotation=rot, extrude=extrude)
    return ob


def _front_inserts(name, bf, openings, lamps=True, lip=None, intercooler=False):
    surf = Surface(bf)
    mb = MeshBuilder(f"__inserts_{name}")
    if lamps:
        for m in (False, True):
            _lens(mb, surf, _rect(F_LAMP["cx"], F_LAMP["cz"], F_LAMP["w"], F_LAMP["h"], F_LAMP["r"], m),
                  "s13_signal_R" if m else "s13_signal_L")
    for o in openings:
        _recess_grille(mb, surf, o, depth=0.05 if intercooler else 0.030, slat_pitch=0.014)
    for s_ in (1, -1):
        y0, y1, zc = -1.86, -1.76, 0.420
        pts = []
        for y, z in ((y0, zc - 0.014), (y1, zc - 0.014), (y1, zc + 0.014), (y0, zc + 0.014)):
            x = surf.x_side(y, z, s_) or s_ * side_x(SPEC, y, z)
            pts.append((x + s_ * 0.002, y, z))
        mb.polygon(pts, "s13_sidemarker_F", outward=(s_, 0, 0))
    ye = surf.y_front(0.0, 0.468)
    if ye is not None:
        c = Vector((0.0, ye - 0.003, 0.468))
        ring = [(c.x + 0.038 * math.cos(2 * math.pi * k / 32), c.y, c.z + 0.016 * math.sin(2 * math.pi * k / 32))
                for k in range(32)]
        mb.polygon(ring, "s13_badge_chrome", outward=(0, -1, 0))
        mb.box((0.0, ye - 0.0045, 0.468), (0.066, 0.002, 0.009), "s13_badge_blue")
    if lip:
        drop, reach, mat = {"lip": (0.030, 0.045, "s13_trim_black"), "deep": (0.045, 0.065, "s1x_carbon"),
                            "flat": (0.010, 0.020, "s13_trim_black")}[lip]
        xs = np.linspace(-0.74, 0.74, 41)
        inner, outer = [], []
        for x in xs:
            y = surf.y_front(float(x), 0.245)
            if y is None:
                continue
            inner.append((float(x), y + 0.012, 0.236))
            outer.append((float(x), y - reach * (1 - (abs(x) / 0.8) ** 4), 0.236 - drop))
        n = len(inner)
        verts = inner + outer + [(x, y, z - 0.008) for x, y, z in outer]
        faces = [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)]
        faces += [(n + i, n + i + 1, 2 * n + i + 1, 2 * n + i) for i in range(n - 1)]
        faces += [(2 * n + i, 2 * n + i + 1, i + 1, i) for i in range(n - 1)]
        mb.add_faces(verts, faces, mat, smooth=False)
    if intercooler:
        mb.rbox((0.0, -2.10, 0.33), (0.86, 0.06, 0.15), 0.01, "s1x_intercooler")
    return mb.to_object()


def post_solidify(out):
    joins = {}

    def add(target, ob):
        joins.setdefault(target, []).append(ob)

    # ---- body-kit bumper variants -----------------------------------------------
    for key, (opens, lamps, lip) in FRONT_VARIANTS.items():
        name = f"s13_bumper_F_{key}"
        add(name, _front_inserts(key, out[name], _openings(opens), lamps, lip, intercooler=key in ("race", "drift")))
        _assign_by(out[name], "s13_trim_black", lambda c, n: c.z < F_LIP_Z)
    for key, kind in REAR_VARIANTS.items():
        name = f"s13_bumper_R_{key}"
        mb = MeshBuilder(f"__rv_{key}")
        mb.box((0.0, R_PLATE["wall_y"], R_PLATE["cz"]), (R_PLATE["w"] + 0.01, 0.004, R_PLATE["h"] + 0.01), "s13_paint")
        if kind == "valance":
            rs = Surface(out[name])
            xs = np.linspace(-0.70, 0.70, 31)
            row_a, row_b = [], []
            for x in xs:
                y = rs.y_rear(float(x), 0.27)
                if y is None:
                    continue
                row_a.append((float(x), y - 0.01, 0.268))
                row_b.append((float(x), y + 0.035, 0.225))
            n = len(row_a)
            mb.add_faces(row_a + row_b, [(i + 1, i, n + i, n + i + 1) for i in range(n - 1)], "s13_trim_black", smooth=False)
        add(name, mb.to_object())
        _assign_by(out[name], "s13_trim_black", lambda c, n: c.z < 0.262)

    # ---- front bumper ---------------------------------------------------------
    bf = out["s13_bumper_F"]
    surf = Surface(bf)
    mb = MeshBuilder("__bf_inserts")
    for m in (False, True):
        lamp = _rect(F_LAMP["cx"], F_LAMP["cz"], F_LAMP["w"], F_LAMP["h"], F_LAMP["r"], m)
        _lens(mb, surf, lamp, "s13_signal_R" if m else "s13_signal_L")
        _recess_grille(mb, surf, _rect(F_SIDE_GRILLE["cx"], F_SIDE_GRILLE["cz"], F_SIDE_GRILLE["w"], F_SIDE_GRILLE["h"],
                                       F_SIDE_GRILLE["r"], m))
    _recess_grille(mb, surf, _rect(**{k: F_CENTER_GRILLE[k] for k in ("cx", "cz", "w", "h", "r")}))
    # side markers (amber, glow with the parking lights) on the bumper flanks
    for s in (1, -1):
        y0, y1, zc = -1.86, -1.76, 0.420
        pts = []
        for y, z in ((y0, zc - 0.014), (y1, zc - 0.014), (y1, zc + 0.014), (y0, zc + 0.014)):
            x = surf.x_side(y, z, s)
            if x is None:
                x = s * side_x(SPEC, y, z)
            pts.append((x + s * 0.002, y, z))
        mb.polygon(pts, "s13_sidemarker_F", outward=(s, 0, 0))
    # emblem
    ye = surf.y_front(0.0, 0.468)
    if ye is not None:
        c = Vector((0.0, ye - 0.003, 0.468))
        ring = [(c.x + 0.038 * math.cos(2 * math.pi * k / 32), c.y, c.z + 0.016 * math.sin(2 * math.pi * k / 32))
                for k in range(32)]
        mb.polygon(ring, "s13_badge_chrome", outward=(0, -1, 0))
        mb.box((0.0, ye - 0.0045, 0.468), (0.066, 0.002, 0.009), "s13_badge_blue")
    sm = mb.to_object()
    add("s13_bumper_F", sm)
    _assign_by(bf, "s13_trim_black", lambda c, n: c.z < F_LIP_Z)

    # ---- side rub strips + door handles ---------------------------------------
    for s, side in ((1, "L"), (-1, "R")):
        targets = [("s13_bumper_F", np.linspace(-2.08, -1.61, 14)), (f"s13_fender_{side}", np.linspace(-1.60, -0.67, 24)),
                   (f"s13_door_{side}", np.linspace(-0.635, 0.565, 26)), ("s13_body_hatch", np.linspace(0.61, 1.72, 26)),
                   ("s13_bumper_R", np.linspace(1.63, 2.06, 12))]
        targets += [(f"s13_bumper_F_{k}", np.linspace(-2.08, -1.61, 14)) for k in FRONT_VARIANTS]
        targets += [(f"s13_bumper_R_{k}", np.linspace(1.63, 2.06, 12)) for k in REAR_VARIANTS]
        for target, ys in targets:
            mb = MeshBuilder(f"__strip_{target}_{side}")
            _band(mb, ys, *STRIP_Z, s, "s13_trim_black", surf=Surface(out[target]))
            if mb.bm.faces:
                add(target, mb.to_object())
            else:
                mb.bm.free()
        # door handle (black pull, rear upper corner)
        door = out[f"s13_door_{side}"]
        ds = Surface(door)
        y, z = 0.43, 0.785
        x = ds.x_side(y, z, s) or s * side_x(SPEC, y, z)
        mb = MeshBuilder(f"__handle_{side}")
        mb.rbox((x + s * 0.006, y, z), (0.012, 0.12, 0.030), 0.006, "s13_trim_black")
        mb.rbox((x + s * 0.002, y + 0.04, z), (0.006, 0.05, 0.022), 0.004, "s1x_dark")
        add(f"s13_door_{side}", mb.to_object())

    # ---- rear: markers, reflectors, plate recess, badges -----------------------
    br = out["s13_bumper_R"]
    rs = Surface(br)
    mb = MeshBuilder("__br_inserts")
    for s in (1, -1):
        y0, y1, zc = 1.86, 1.96, 0.440
        pts = []
        for y, z in ((y1, zc - 0.014), (y0, zc - 0.014), (y0, zc + 0.014), (y1, zc + 0.014)):
            x = rs.x_side(y, z, s) or s * side_x(SPEC, y, z)
            pts.append((x + s * 0.002, y, z))
        mb.polygon(pts, "s13_sidemarker_R", outward=(s, 0, 0))
        # rear reflectors on the bumper face
        pts = []
        for x, z in _rect(s * 0.60, 0.43, 0.10, 0.03, 0.008):
            y = rs.y_rear(x, z)
            if y is not None:
                pts.append((x, y + 0.002, z))
        if len(pts) > 3:
            mb.polygon(pts, "s13_lights_red", outward=(0, 1, 0))
    # plate recess back wall
    mb.box((0.0, R_PLATE["wall_y"], R_PLATE["cz"]), (R_PLATE["w"] + 0.01, 0.004, R_PLATE["h"] + 0.01), "s13_paint")
    add("s13_bumper_R", mb.to_object())
    _assign_by(br, "s13_trim_black", lambda c, n: c.z < 0.262)

    # NISSAN letters on the tail garnish, 240SX on the hatch
    body = out["s13_body_hatch"]
    bs = Surface(out["s13_taillights"])
    yg = bs.y_rear(0.0, 0.75)
    if yg is not None:
        t = text_mesh("__nissan", "N I S S A N", 0.034, "s13_badge_chrome", location=(0.0, yg + 0.003, 0.75),
                      rotation=(math.radians(90), 0, math.radians(180)), extrude=0.0012)
        add("s13_taillights", t)
        y2 = bs.y_rear(-0.22, 0.685)
        if y2 is not None:
            t = text_mesh("__240sx", "240SX", 0.024, "s13_badge_chrome", location=(-0.22, y2 + 0.003, 0.685),
                          rotation=(math.radians(90), 0, math.radians(180)), extrude=0.0012)
            add("s13_taillights", t)

    # fuel door (right rear quarter) and wipers (cowl)
    s = -1
    qs = Surface(body)
    mb = MeshBuilder("__fueldoor")
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
                     [(0, 1, 2, 3) if s > 0 else (3, 2, 1, 0)], "s1x_dark", smooth=False)
    add("s13_body_hatch", mb.to_object())

    mb = MeshBuilder("__wipers")
    for x0, x1 in ((-0.52, 0.06), (-0.02, 0.55)):
        pts = []
        for x in np.linspace(x0, x1, 10):
            y = -0.755
            pts.append((float(x), y, top_z(SPEC, y, abs(float(x))) + 0.012))
        mb.tube(pts, 0.006, "s1x_dark", segs=6)
        px = x0 + 0.06
        mb.cylinder((px, -0.80, top_z(SPEC, -0.80, abs(px)) - 0.005), (px, -0.80, top_z(SPEC, -0.80, abs(px)) + 0.02), 0.012,
                    "s1x_dark", segs=10)
        mb.tube([(px, -0.80, top_z(SPEC, -0.80, abs(px)) + 0.018), ((x0 + x1) / 2, -0.76,
                 top_z(SPEC, -0.76, abs((x0 + x1) / 2)) + 0.02)], 0.005, "s1x_dark", segs=6)
    add("s13_windshield_trim", mb.to_object())

    for target, obs in joins.items():
        out[target] = P.join([out[target]] + obs, target)
    return out


def mirrors():
    """Door mirrors (stock: triangular sail + rounded head; aero: slim racing head) and the interior mirror."""
    from tools.vehicle.s13.panels_jb import MIRROR
    out = []
    for kind in ("oem", "aero"):
        for side, s in (("L", 1), ("R", -1)):
            name = f"s13_mirror_{side}" if kind == "oem" else f"s13_mirror_aero_{side}"
            mb = MeshBuilder(name)
            yb, zb = MIRROR["base"]
            yh, zh = MIRROR["head"]
            xb = side_x(SPEC, yb, zb)
            # sail plate on the door's front window corner
            sail = [(s * xb, yb - 0.04, zb - 0.005), (s * xb, yb + 0.07, zb - 0.01), (s * (xb - 0.01), yb - 0.02, zb + 0.085)]
            mb.polygon(sail, "s13_trim_black", outward=(s, 0, 0))
            mb.polygon([(x + s * 0.008, y, z) for x, y, z in sail], "s13_trim_black", outward=(s, 0, 0))
            hx = s * (xb + (0.085 if kind == "oem" else 0.075))
            if kind == "oem":
                mb.tube([(s * (xb + 0.004), yb + 0.02, zb + 0.03), (hx - s * 0.04, yh + 0.01, zh - 0.01)], 0.012,
                        "s13_trim_black", segs=8)
                mb.rbox((hx, yh, zh), (0.140, 0.075, 0.090), 0.025, "s13_trim_black",
                        rot=Matrix.Rotation(math.radians(-8 * s), 3, "Z"))
                gx, gw, gh = hx, 0.120, 0.072
            else:
                mb.tube([(s * (xb + 0.004), yb + 0.02, zb + 0.03), (hx - s * 0.03, yh, zh)], 0.008, "s1x_carbon", segs=8)
                mb.rbox((hx, yh, zh), (0.120, 0.060, 0.055), 0.02, "s1x_carbon")
                gx, gw, gh = hx, 0.105, 0.040
            # glass faces rearward (+y)
            gy = yh + (0.0385 if kind == "oem" else 0.031)
            glass = [(gx - gw / 2, gy, zh - gh / 2), (gx + gw / 2, gy, zh - gh / 2), (gx + gw / 2, gy, zh + gh / 2),
                     (gx - gw / 2, gy, zh + gh / 2)]
            mb.polygon(glass, "mirror", outward=(0, 1, 0))
            out.append(mb)
    mb = MeshBuilder("s13_mirror_int")
    c = Vector((0.0, -0.15, 1.115))
    mb.tube([(0.0, -0.13, 1.205), (0.0, -0.155, 1.15)], 0.007, "s13_interior_plastic", segs=8)
    mb.rbox(tuple(c), (0.22, 0.03, 0.06), 0.015, "s13_interior_plastic")
    mb.polygon([(0.10, c.y + 0.0155, c.z - 0.025), (-0.10, c.y + 0.0155, c.z - 0.025), (-0.10, c.y + 0.0155, c.z + 0.025),
                (0.10, c.y + 0.0155, c.z + 0.025)], "mirror", outward=(0, 1, 0))
    out.append(mb)
    return out


def side_skirts():
    mb = MeshBuilder("s13_sideskirts_aero")
    for s in (1, -1):
        rows = []
        for y in np.linspace(-0.87, 0.87, 30):
            x0 = side_x(SPEC, float(y), 0.21)
            prof = [(x0 - 0.01, 0.235), (x0 + 0.012, 0.232), (x0 + 0.026, 0.205), (x0 + 0.028, 0.150), (x0 + 0.012, 0.125),
                    (x0 - 0.035, 0.122)]
            rows.append([(s * x, float(y), z) for x, z in prof])
        n = len(rows[0])
        verts = [v for r in rows for v in r]
        faces = []
        for i in range(len(rows) - 1):
            for k in range(n - 1):
                f = (i * n + k, i * n + k + 1, (i + 1) * n + k + 1, (i + 1) * n + k)
                faces.append(f if s < 0 else f[::-1])
        mb.add_faces(verts, faces, "s13_paint", smooth=True)
        for i in (0, len(rows) - 1):
            mb.polygon(rows[i], "s13_paint", outward=(0, -1 if i == 0 else 1, 0))
    return mb


def hatch_spoiler():
    """OEM hatch spoiler with an integrated centre high-mount stop lamp."""
    mb = MeshBuilder("s13_spoiler_oem")
    span, chord = 0.56, 0.13
    y_le, z0 = 2.105, 0.985
    loop = [(0.0, 0.0), (0.03, 0.012), (0.08, 0.016), (chord, 0.010), (chord, 0.0), (0.06, -0.006)]
    n = len(loop)
    verts = [(-span, y_le + u, z0 + v) for u, v in loop] + [(span, y_le + u, z0 + v) for u, v in loop]
    mb.add_faces(verts, [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)], "s13_paint", smooth=True)
    for x in (-span, span):
        mb.polygon([(x, y_le + u, z0 + v) for u, v in loop], "s13_paint", outward=(1 if x > 0 else -1, 0, 0))
    for s in (1, -1):
        mb.rbox((s * 0.40, y_le + 0.06, z0 - 0.035), (0.05, 0.07, 0.07), 0.012, "s13_paint")
    mb.rbox((0.0, y_le + chord - 0.005, z0 + 0.006), (0.30, 0.012, 0.014), 0.004, "s13_chmsl")
    return mb


def interior_faces(out):
    """Give the cabin-facing faces of the solidified shell an interior trim material instead of body paint."""
    from . import materials as MR
    rules = {"s13_body_hatch": "s13_interior_trim", "s13_hatch": "s13_interior_trim", "s13_door_L": "s13_interior_trim",
             "s13_door_R": "s13_interior_trim"}
    for name, matname in rules.items():
        ob = out.get(name)
        if ob is None:
            continue
        me = ob.data
        mat = MR.blender_material(matname)
        names = [m.name for m in me.materials if m]
        if matname not in names:
            me.materials.append(mat)
            names.append(matname)
        idx = names.index(matname)
        paint = names.index("s13_paint") if "s13_paint" in names else -1
        for poly in me.polygons:
            if poly.material_index != paint:
                continue
            c, n = poly.center, poly.normal
            if not (-0.86 < c.y < 2.15 and c.z > 0.22):
                continue
            radial = Vector((c.x, 0.0, c.z - 0.62))
            if radial.length < 1e-6:
                continue
            if n.dot(radial) < -0.2 * radial.length:
                poly.material_index = idx


def sun_visors_and_belts():
    """Static cabin trim mapped to the body: sun visors, B-pillar seat belts and grab handles."""
    from tools.vehicle.s13 import dims as D
    mb = MeshBuilder("s13_cabin_trim")
    for s in (1, -1):
        x = s * 0.33
        y, z = -0.12, top_z(SPEC, -0.12, 0.33) - 0.06
        mb.rbox((x, y, z), (0.36, 0.17, 0.018), 0.01, "s13_interior_plastic_light",
                rot=Matrix.Rotation(math.radians(-12), 3, "X"))
        # seat belt: from the B-pillar upper anchor down to the floor beside the seat
        top = (s * 0.70, 0.62, 0.98)
        mb.tube([top, (s * 0.66, 0.50, 0.78), (s * 0.60, 0.40, 0.40), (s * 0.58, 0.35, 0.20)], 0.006, "s1x_strap_black", segs=4)
        mb.rbox(top, (0.03, 0.04, 0.06), 0.008, "s13_interior_plastic")
    return mb
