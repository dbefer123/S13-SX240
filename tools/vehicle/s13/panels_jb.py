"""JBeam for the S13 removable body panels (hood, pop-ups, fenders, doors,
hatch, bumpers).  Node positions are sampled on the body loft so the panel
meshes map cleanly onto them."""
from __future__ import annotations

import math

import numpy as np

from tools.model.shape import top_z, side_x
from tools.vehicle.common.jb import Part
from . import body_spec as B
from .structure import mir

SPEC = B.hatch_spec()
INSET = 0.012

PANEL_NODE = dict(selfCollision=True, collision=True, nodeMaterial="|NM_METAL", frictionCoef=0.5)
RIGID = dict(selfCollision=False, collision=False)


def tz(y, x, inset=INSET):
    return top_z(SPEC, y, x) - inset


def sx(y, z, inset=INSET):
    return side_x(SPEC, y, z) - inset


def _lr_pairs(pairs):
    out, seen = [], set()
    for a, b in pairs:
        for p in ((a, b), (mir(a), mir(b))):
            k = tuple(sorted(p))
            if k not in seen:
                seen.add(k); out.append(p)
    return out


def _nodes_lr(p, rows, weight):
    """rows: list of (name, x, y, z) with x>=0; x>0 nodes get l/r twins."""
    for name, x, y, z in rows:
        if x == 0:
            p.node(name, 0.0, y, z, nodeWeight=weight)
        else:
            p.node(name + "l", x, y, z, nodeWeight=weight)
            p.node(name + "r", -x, y, z, nodeWeight=weight)


def flare_weight(y, z, axle="F"):
    """0..1 weight of the wide-body flare at (y, z): full around the wheel arch, fading out ~0.25 m beyond it.
    Shared with the mesh builder so wide fenders and their nodes move together."""
    from .panel_spec import ARCH_F, ARCH_R, ARCH_RADIUS
    cy, cz = ARCH_F if axle == "F" else ARCH_R
    d = math.hypot(y - cy, z - cz)
    if z < cz - 0.12:
        return 0.0
    t = (d - (ARCH_RADIUS + 0.06)) / 0.22
    t = min(max(t, 0.0), 1.0)
    w = 1.0 - t * t * (3 - 2 * t)
    zf = min(max((z - (cz - 0.12)) / 0.10, 0.0), 1.0)
    return w * zf


def _std_beams(p, spring, damp, deform, strength="FLT_MAX"):
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=spring, beamDamp=damp, beamDeform=deform, beamStrength=strength)


def _reset_beams(p):
    p.beams_props(breakGroup="", breakGroupType=0)
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(deformLimitExpansion=1.2)


# --------------------------------------------------------------------------
# hood
# --------------------------------------------------------------------------
def hood(name="s13_hood", title="Stock Steel Hood", mesh="s13_hood", value=380, mass=16.0):
    p = Part(name, title, "s13_hood", value=value)
    p.flexbody(mesh, ["s13_hood"])
    layout = [(-2.050, -2.050, 0.62, -1.800), (-1.660, -1.660, 0.65, -1.620),
              (-1.260, -1.260, 0.66, -1.260), (-0.900, -0.900, 0.66, -0.900)]
    p.nodes_props(group="s13_hood", **PANEL_NODE)
    w = mass / 21
    for i, (yc, yl, xo, yo) in enumerate(layout, 1):
        p.node(f"hd{i}", 0.0, yc, tz(yc, 0.0), nodeWeight=w)
        for nm, x, y in ((f"hd{i}l", 0.31, yl), (f"hd{i}ll", xo, yo)):
            p.node(nm, x, y, tz(y, x), nodeWeight=w)
            p.node(mir(nm), -x, y, tz(y, x), nodeWeight=w)
    p.nodes_props(group="", **RIGID)
    p.node("hd0", 0.0, -1.45, 0.50, nodeWeight=w)
    p.nodes_props(group="")
    grid = [["hd%dll" % i, "hd%dl" % i, "hd%d" % i, "hd%dr" % i, "hd%drr" % i] for i in range(1, 5)]
    _std_beams(p, 801000, 40, 9000)
    pairs = []
    for row in grid:
        pairs += list(zip(row, row[1:]))
    for a, b in zip(grid, grid[1:]):
        for j in range(5):
            pairs.append((a[j], b[j]))
            if j < 4:
                pairs.append((a[j], b[j + 1])); pairs.append((a[j + 1], b[j]))
    for a, b in pairs:
        p.beam(a, b)
    p.beam_comment("rigidifier")
    p.beams_props(beamSpring=401000, beamDamp=30, beamDeform=4500, beamStrength="FLT_MAX")
    for row in grid:
        for n in row:
            p.beam(n, "hd0")
    p.beam_comment("hinges (rear) and latch (front)")
    p.beams_props(beamSpring=1001000, beamDamp=60, beamDeform=12000, beamStrength=22000)
    p.beams_props(breakGroup="hood_hinge_L")
    for a, b in (("hd4ll", "fp3l"), ("hd4ll", "ft3l"), ("hd4ll", "fp4l"), ("hd4l", "fp4l"), ("hd4l", "fp3l")):
        p.beam(a, b)
    p.beams_props(breakGroup="hood_hinge_R")
    for a, b in (("hd4ll", "fp3l"), ("hd4ll", "ft3l"), ("hd4ll", "fp4l"), ("hd4l", "fp4l"), ("hd4l", "fp3l")):
        p.beam(mir(a), mir(b))
    p.beams_props(breakGroup="hood_latch", beamDeform=7000, beamStrength=9000)
    for a, b in (("hd1", "fe2"), ("hd1", "fe2l"), ("hd1", "fe2r"), ("hd1l", "fe2l"), ("hd1r", "fe2r")):
        p.beam(a, b)
    p.beams_props(breakGroup="")
    p.beam_comment("support: hood rests on the fender aprons")
    p.beams_props(beamType="|SUPPORT", beamLongBound=3, beamSpring=601000, beamDamp=40, beamDeform=10000, beamStrength=50000)
    for a, b in (("hd2ll", "ft1l"), ("hd3ll", "ft2l"), ("hd3ll", "ft3l"), ("hd1ll", "ft1l")):
        p.beam(a, b); p.beam(mir(a), mir(b))
    _reset_beams(p)
    p.tris_props(dragCoef=8, groundModel="metal", triangleType="NORMALTYPE")
    for a, b in zip(grid, grid[1:]):
        for j in range(4):
            p.quad(a[j], a[j + 1], b[j + 1], b[j])
    return p


# --------------------------------------------------------------------------
# pop-up headlight assemblies (hinged at the rear, raised by a hydro)
# --------------------------------------------------------------------------
from .popup_geom import POPUP_ANGLE, lens_center_closed  # noqa: E402

HEADLIGHT_PROPS = dict(lightInnerAngle=0, lightOuterAngle=110, lightColor={"r": 255, "g": 245, "b": 210, "a": 255},
                       lightCastShadows=True, flareName="vehicleHeadLightFlare",
                       cookieName="art/special/BNG_light_cookie_headlight.dds", texSize=512, shadowSoftness=0.5)


def _rot_about(p, a, b, ang):
    """Rotate point p about axis a->b by ang radians (Rodrigues)."""
    p, a, b = map(np.asarray, (p, a, b))
    k = (b - a) / np.linalg.norm(b - a)
    v = p - a
    return a + v * math.cos(ang) + np.cross(k, v) * math.sin(ang) + k * np.dot(k, v) * (1 - math.cos(ang))


def popup(side="L", name=None, mesh_lid="s13_popup_lid", mesh_lamp="s13_popup_lamp", fixed=False,
          title="Pop-up Headlight", value=260, mass=6.0):
    """Pop-up headlamp unit; fixed=True gives the 'pop-up delete' (lid bolted shut, LED projectors in the bumper)."""
    s = 1 if side == "L" else -1
    sl = side.lower()
    name = name or f"s13_popup_{side}"
    p = Part(name, f"{title} ({'Left' if side == 'L' else 'Right'})", f"s13_popup_{side}", value=value)
    grp = f"s13_popup_{side}"
    p.flexbody(f"{mesh_lid}_{side}", [grp])
    if mesh_lamp:
        p.flexbody(f"{mesh_lamp}_{side}", [grp])
    y_h, y_f = -1.875, -2.080
    x_i, x_o = 0.395, 0.675
    h1 = (s * x_i, y_h, tz(y_h, x_i, 0.006))
    h2 = (s * x_o, y_h, tz(y_h, x_o, 0.006))
    f1 = (s * x_i, y_f, tz(y_f, x_i, 0.006))
    f2 = (s * x_o, y_f + 0.03, tz(y_f + 0.03, x_o, 0.006))
    b1 = (s * x_i, -2.040, f1[2] - 0.105)
    b2 = (s * x_o, -2.010, f2[2] - 0.105)
    p.nodes_props(group=grp, **PANEL_NODE)
    for nm, q in (("puh1", h1), ("puh2", h2), ("puf1", f1), ("puf2", f2), ("pub1", b1), ("pub2", b2)):
        p.node(nm + sl, *q, nodeWeight=round(mass / 6, 3))
    p.nodes_props(group="")
    n = lambda k: k + sl  # noqa: E731
    ring = [n("puh1"), n("puh2"), n("puf2"), n("puf1")]
    _std_beams(p, 901000, 40, 8000)
    for a, b in [(ring[0], ring[1]), (ring[1], ring[2]), (ring[2], ring[3]), (ring[3], ring[0]),
                 (ring[0], ring[2]), (ring[1], ring[3]),
                 (n("pub1"), n("pub2")), (n("pub1"), n("puf1")), (n("pub2"), n("puf2")), (n("pub1"), n("puf2")),
                 (n("pub2"), n("puf1")), (n("pub1"), n("puh1")), (n("pub2"), n("puh2")), (n("pub1"), n("puh2")),
                 (n("pub2"), n("puh1"))]:
        p.beam(a, b)
    # hinge: the two hinge nodes are tied to the body, letting the unit rotate about them
    body = {"fe2": (0.0, -2.08, 0.545)}
    side_b = lambda k: k + sl  # noqa: E731
    p.beam_comment("hinge")
    p.beams_props(beamSpring=901000, beamDamp=50, beamDeform=9000, beamStrength=16000, breakGroup=f"popup_hinge_{side}")
    for a in (n("puh1"), n("puh2")):
        for b in (side_b("ft1"), side_b("fa1"), side_b("fe2"), "fe2"):
            p.beam(a, b)
    p.beams_props(breakGroup="")
    # actuator: hydro from the body to the lamp box bottom; length change computed from the rotation
    act_body = (s * 0.52, -1.80, 0.430)
    p.nodes_props(group="", selfCollision=False, collision=False)
    p.node(n("pua"), *act_body, nodeWeight=0.8)
    p.beam_comment("actuator base")
    p.beams_props(beamSpring=2001000, beamDamp=60, beamDeform=20000, beamStrength="FLT_MAX", breakGroup=f"popup_hinge_{side}")
    for b in (side_b("fa1"), side_b("fr1"), side_b("fe2"), side_b("ft1"), side_b("fe1")):
        p.beam(n("pua"), b)
    p.beams_props(breakGroup="")
    ang = math.radians(POPUP_ANGLE) * (-1 if s > 0 else 1)
    b1_open = _rot_about(b1, h1, h2, -ang if s > 0 else ang)
    # choose rotation direction that lifts the front: check z
    if b1_open[2] < b1[2]:
        b1_open = _rot_about(b1, h1, h2, ang if s > 0 else -ang)
    L0 = np.linalg.norm(np.asarray(b1) - act_body)
    L1 = np.linalg.norm(b1_open - act_body)
    factor = 0.0 if fixed else (L1 - L0) / L0
    if fixed:
        p.beam_comment("bolted shut")
        p.beams_props(beamSpring=1501000, beamDamp=60, beamDeform=12000, beamStrength=20000, breakGroup=f"popup_hinge_{side}")
        for b in (n("pub1"), n("pub2"), n("puf1"), n("puf2")):
            p.beam(n("pua"), b)
        p.beams_props(breakGroup="")
    else:
        p.hydros_props(beamPrecompression=1.0, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
        p.hydros_props(beamSpring=601000, beamDamp=200, beamDeform=9000, beamStrength=14000)
        # inputSource lowhighbeam is 0 (closed) or 1 (open); factor scales length change for input 1
        p.hydro(n("pua"), n("pub1"), inputSource="lowhighbeam", inputFactor=1, inLimit=min(1.0, 1 + factor),
                outLimit=max(1.0, 1 + factor), factor=round(factor, 4), inRate=1.6, outRate=1.6,
                breakGroup=f"popup_hinge_{side}")
        p.hydros_props(breakGroup="")
    _reset_beams(p)
    p.tris_props(dragCoef=8, groundModel="metal", triangleType="NORMALTYPE")
    if s > 0:
        p.quad(ring[3], ring[2], ring[1], ring[0])
    else:
        p.quad(ring[0], ring[1], ring[2], ring[3])
    p.props_props(**HEADLIGHT_PROPS)
    if fixed:
        # LED projectors in the bumper corners, fixed and aimed straight ahead
        pos = {"x": s * 0.52, "y": -2.215, "z": 0.395}
        rot = {"x": 0, "y": 0, "z": 0}
        ref = (n("puh1"), n("puh2"), n("puf1"))
    else:
        # lights ride on the pod: defined in the closed (spawn) pose, lens aimed 45 deg down -> level when raised
        lx, ly, lz = lens_center_closed()
        pos = {"x": s * lx, "y": round(ly, 4), "z": round(lz, 4)}
        rot = {"x": POPUP_ANGLE, "y": 0, "z": 0}
        ref = (n("pub1"), n("pub2"), n("puf1"))
    zero = {"x": 0, "y": 0, "z": 0}
    p.prop("lowbeam", "SPOTLIGHT", *ref, zero, zero, zero, 0, 0, 0, 1, baseTranslationGlobal=pos, baseRotationGlobal=rot,
           lightRange=55 if not fixed else 45, lightIntensityCd=9000 if not fixed else 7000, flareScale=0.06,
           deformGroup=f"headlight_{side}_break")
    p.prop("highbeam", "SPOTLIGHT", *ref, zero, zero, zero, 0, 0, 0, 1, baseTranslationGlobal=pos, baseRotationGlobal=rot,
           lightRange=95 if not fixed else 80, lightIntensityCd=16000 if not fixed else 12000, lightOuterAngle=80,
           flareScale=0.08, deformGroup=f"headlight_{side}_break")
    p.d["_popup_factor"] = round(factor, 4)
    return p


# --------------------------------------------------------------------------
# fenders
# --------------------------------------------------------------------------
def fender(side="L", mesh="s13_fender", title="Stock Front Fender", value=220, mass=5.0, slot=None, flare=0.0):
    s = 1 if side == "L" else -1
    sl = side.lower()
    p = Part(f"{mesh}_{side}" if title == "Stock Front Fender" else f"{mesh}_{side}", f"{title} ({'Left' if s > 0 else 'Right'})",
             slot or f"s13_fender_{side}", value=value)
    grp = f"s13_fender_{side}"
    p.flexbody(f"{mesh}_{side}", [grp])
    pts = {
        "fd1": (-2.030, 0.600), "fd2": (-1.620, 0.700), "fd3": (-1.250, 0.745), "fd4": (-0.930, 0.790),
        "fd5": (-2.020, 0.500), "fd6": (-1.620, 0.535), "fd7": (-1.250, 0.690), "fd8": (-0.880, 0.520),
        "fd9": (-0.860, 0.260),
    }
    p.nodes_props(group=grp, **PANEL_NODE)
    w = mass / len(pts)
    for nm, (y, z) in pts.items():
        x = sx(y, z, 0.010) if z < 0.69 else min(sx(y, z, 0.010), 0.80)
        if nm in ("fd1", "fd2", "fd3", "fd4"):
            x = 0.5 * (0.705 + side_x(SPEC, y, z)) if nm != "fd1" else 0.66
            z = tz(y, x, 0.010)
        x += flare * flare_weight(y, z, "F")
        p.node(nm + sl, s * x, y, z, nodeWeight=w)
    p.nodes_props(group="")
    n = lambda k: k + sl  # noqa: E731
    _std_beams(p, 801000, 40, 8000)
    for a, b in [("fd1", "fd2"), ("fd2", "fd3"), ("fd3", "fd4"), ("fd5", "fd6"), ("fd6", "fd7"), ("fd7", "fd8"),
                 ("fd8", "fd9"), ("fd1", "fd5"), ("fd2", "fd6"), ("fd3", "fd7"), ("fd4", "fd8"), ("fd1", "fd6"),
                 ("fd2", "fd5"), ("fd2", "fd7"), ("fd3", "fd6"), ("fd3", "fd8"), ("fd4", "fd7"), ("fd4", "fd9")]:
        p.beam(n(a), n(b))
    p.beam_comment("attach to body (bolted)")
    p.beams_props(beamSpring=901000, beamDamp=50, beamDeform=9000, beamStrength=14000)
    for i, (a, bs) in enumerate([("fd1", ("fe2", "ft1", "fa1")), ("fd2", ("ft1", "ft2", "fa2")),
                                 ("fd3", ("ft2", "ft3", "fa3")), ("fd4", ("ft3", "fp3", "hp3")),
                                 ("fd5", ("fe1", "fa1", "fe2")), ("fd8", ("hp2", "hp1", "fp2")),
                                 ("fd9", ("hp1", "si0", "fp1"))]):
        p.beams_props(breakGroup=f"fender_{side}_{i // 2}")
        for b in bs:
            p.beam(n(a), n(b))
    p.beams_props(breakGroup="")
    _reset_beams(p)
    p.tris_props(dragCoef=8, groundModel="metal", triangleType="NORMALTYPE")
    quads = [("fd5", "fd6", "fd2", "fd1"), ("fd6", "fd7", "fd3", "fd2"), ("fd7", "fd8", "fd4", "fd3")]
    for q in quads:
        q = [n(k) for k in q]
        p.quad(*(q if s > 0 else q[::-1]))
    return p


# --------------------------------------------------------------------------
# doors
# --------------------------------------------------------------------------
def door(side="L", mesh="s13_door", glass="s13_doorglass", title="Stock Door", value=520, mass=26.0, name=None):
    s = 1 if side == "L" else -1
    sl = side.lower()
    p = Part(name or f"s13_door_{side}", f"{title} ({'Left' if s > 0 else 'Right'})", f"s13_door_{side}", value=value)
    grp = f"s13_door_{side}"
    p.flexbody(f"{mesh}_{side}", [grp])
    p.flex_props(deformGroup=f"doorglass_{side}_break", deformMaterialBase="s13_glass", deformMaterialDamaged="s13_glass_dmg")
    p.flexbody(f"{glass}_{side}", [grp], deformSound="event:>Destruction>Vehicle>Glass>glassbreaksound4", deformVolume=0.6)
    p.flex_props(deformGroup="")
    rows = {
        "dr1": (-0.620, 0.280), "dr2": (-0.650, 0.600), "dr3": (-0.640, 0.860),
        "dr4": (-0.040, 0.250), "dr5": (-0.040, 0.600), "dr6": (-0.040, 0.875),
        "dr7": (0.555, 0.260), "dr8": (0.565, 0.600), "dr9": (0.570, 0.885),
    }
    p.nodes_props(group=grp, **PANEL_NODE)
    w = mass / 12
    for nm, (y, z) in rows.items():
        p.node(nm + sl, s * (side_x(SPEC, y, z) - 0.03), y, z, nodeWeight=w)
    p.node("dr10" + sl, s * 0.640, -0.330, 1.075, nodeWeight=w * 0.5)
    p.node("dr11" + sl, s * 0.565, 0.420, 1.185, nodeWeight=w * 0.5)
    p.nodes_props(group="", **RIGID)
    p.node("dr0" + sl, s * 0.560, -0.030, 0.560, nodeWeight=w)
    p.nodes_props(group="")
    n = lambda k: k + sl  # noqa: E731
    _std_beams(p, 1201000, 50, 14000)
    grid = [["dr1", "dr2", "dr3"], ["dr4", "dr5", "dr6"], ["dr7", "dr8", "dr9"]]
    pairs = []
    for col in grid:
        pairs += list(zip(col, col[1:]))
    for a, b in zip(grid, grid[1:]):
        for j in range(3):
            pairs.append((a[j], b[j]))
            if j < 2:
                pairs += [(a[j], b[j + 1]), (a[j + 1], b[j])]
    pairs += [("dr3", "dr10"), ("dr10", "dr11"), ("dr11", "dr9"), ("dr6", "dr10"), ("dr6", "dr11"), ("dr3", "dr6"),
              ("dr10", "dr9"), ("dr11", "dr3"), ("dr2", "dr10"), ("dr8", "dr11")]
    for a, b in pairs:
        p.beam(n(a), n(b))
    p.beam_comment("rigidifier")
    p.beams_props(beamSpring=601000, beamDamp=40, beamDeform=6000, beamStrength="FLT_MAX")
    for k in ["dr%d" % i for i in range(1, 12)]:
        p.beam(n(k), n("dr0"))
    p.beam_comment("hinges")
    p.beams_props(beamSpring=2001000, beamDamp=80, beamDeform=20000, beamStrength=42000, breakGroup=f"door_hinge_{side}")
    for a, bs in (("dr1", ("hp1", "si0", "fp1")), ("dr2", ("hp2", "hp1", "fp2")), ("dr3", ("hp3", "fp3"))):
        for b in bs:
            p.beam(n(a), n(b))
    p.beam_comment("latch")
    p.beams_props(beamSpring=1501000, beamDamp=60, beamDeform=9000, beamStrength=13000, breakGroup=f"door_latch_{side}")
    for a, bs in (("dr8", ("bp2", "bp1", "bp3")), ("dr9", ("bp3", "rf3"))):
        for b in bs:
            p.beam(n(a), n(b))
    p.beams_props(breakGroup="")
    p.beam_comment("door stops: keep the door out of the cabin")
    p.beams_props(beamType="|SUPPORT", beamLongBound=3, beamSpring=501000, beamDamp=40, beamDeform=12000, beamStrength=60000)
    for a, b in (("dr4", "si2"), ("dr7", "si4"), ("dr1", "si1"), ("dr5", "si2"), ("dr7", "bp1")):
        p.beam(n(a), n(b))
    _reset_beams(p)
    p.beams_props(deformGroup=f"doorglass_{side}_break", deformationTriggerRatio=0.02)
    for a, b in (("dr10", "dr6"), ("dr11", "dr6"), ("dr3", "dr11")):
        p.beam(n(a), n(b), beamSpring=0, beamDamp=0, beamDeform=1000, beamStrength="FLT_MAX")
    p.beams_props(deformGroup="")
    p.tris_props(dragCoef=8, groundModel="metal", triangleType="NORMALTYPE")
    for a, b in zip(grid, grid[1:]):
        for j in range(2):
            q = [n(a[j]), n(b[j]), n(b[j + 1]), n(a[j + 1])]
            p.quad(*(q if s > 0 else q[::-1]))
    return p


# --------------------------------------------------------------------------
# hatch (with glass)
# --------------------------------------------------------------------------
def hatch(name="s13_hatch", mesh="s13_hatch", glass="s13_hatchglass", title="Stock Hatch", value=480, mass=21.0):
    p = Part(name, title, "s13_hatch", value=value)
    grp = "s13_hatch"
    p.flexbody(mesh, [grp])
    p.flex_props(deformGroup="hatchglass_break", deformMaterialBase="s13_glass", deformMaterialDamaged="s13_glass_dmg")
    p.flexbody(glass, [grp], deformSound="event:>Destruction>Vehicle>Glass>glassbreaksound4", deformVolume=0.7)
    p.flex_props(deformGroup="")
    rows = [(0.880, [0.0, 0.43]), (1.300, [0.0, 0.46]), (1.720, [0.0, 0.48]), (2.090, [0.0, 0.40, 0.64])]
    p.nodes_props(group=grp, **PANEL_NODE)
    w = mass / 12
    names = []
    for i, (y, xs) in enumerate(rows, 1):
        r = []
        for j, x in enumerate(xs):
            if x == 0:
                nm = f"ht{i}"; p.node(nm, 0.0, y, tz(y, 0.0), nodeWeight=w); r.append(nm)
            else:
                nm = f"ht{i}" + ("l" if j == 1 else "ll")
                p.node(nm, x, y, tz(y, x), nodeWeight=w); p.node(mir(nm), -x, y, tz(y, x), nodeWeight=w)
                r = [mir(nm)] + r + [nm] if j == 1 else [mir(nm)] + r + [nm]
        names.append(r)
    p.nodes_props(group="", **RIGID)
    p.node("ht0", 0.0, 1.50, 0.82, nodeWeight=w)
    p.nodes_props(group="")
    _std_beams(p, 901000, 40, 9000)
    pairs = []
    for r in names:
        pairs += list(zip(r, r[1:]))
    # connect rows by nearest x
    allpos = {}
    for r, (y, xs) in zip(names, rows):
        for nm in r:
            allpos[nm] = nm
    import itertools
    for ra, rb in zip(names, names[1:]):
        for a in ra:
            for b in rb:
                pairs.append((a, b))
    seen = set()
    for a, b in pairs:
        k = tuple(sorted((a, b)))
        if k in seen:
            continue
        seen.add(k)
        p.beam(a, b)
    p.beam_comment("rigidifier")
    p.beams_props(beamSpring=401000, beamDamp=30, beamDeform=5000, beamStrength="FLT_MAX")
    for r in names:
        for nm in r:
            p.beam(nm, "ht0")
    p.beam_comment("hinges")
    p.beams_props(beamSpring=1501000, beamDamp=60, beamDeform=15000, beamStrength=30000, breakGroup="hatch_hinge")
    for a, bs in (("ht1l", ("rf4l", "rf4", "cp1l")), ("ht1r", ("rf4r", "rf4", "cp1r")), ("ht1", ("rf4", "rf3"))):
        for b in bs:
            p.beam(a, b)
    p.beam_comment("latch + gas struts")
    p.beams_props(beamSpring=1001000, beamDamp=50, beamDeform=8000, beamStrength=11000, breakGroup="hatch_latch")
    for a, b in (("ht4", "tl3"), ("ht4", "tl3l"), ("ht4", "tl3r"), ("ht4ll", "tp3l"), ("ht4rr", "tp3r"),
                 ("ht3l", "cp3l"), ("ht3r", "cp3r")):
        p.beam(a, b)
    p.beams_props(breakGroup="")
    p.beams_props(beamType="|SUPPORT", beamLongBound=3, beamSpring=501000, beamDamp=40, beamDeform=9000, beamStrength=40000)
    for a, b in (("ht2l", "cp2l"), ("ht2r", "cp2r"), ("ht3l", "qp8l"), ("ht3r", "qp8r")):
        p.beam(a, b)
    _reset_beams(p)
    p.tris_props(dragCoef=10, groundModel="metal", triangleType="NORMALTYPE")
    for ra, rb in zip(names[:-1], names[1:-1]):
        for j in range(len(ra) - 1):
            p.quad(ra[j], ra[j + 1], rb[j + 1], rb[j])
    return p


# --------------------------------------------------------------------------
# bumpers
# --------------------------------------------------------------------------
def bumper_front(name="s13_bumper_F", mesh="s13_bumper_F", title="Stock Front Bumper", value=320, mass=10.0):
    p = Part(name, title, "s13_bumper_F", value=value)
    grp = "s13_bumper_F"
    p.flexbody(mesh, [grp])
    p.nodes_props(group=grp, **PANEL_NODE)
    rows = [  # (name, x, y, z)
        ("bf1", 0.0, -2.235, 0.430), ("bf1l", 0.400, -2.215, 0.430), ("bf1ll", 0.640, -2.090, 0.430),
        ("bf2", 0.0, -2.215, 0.265), ("bf2l", 0.400, -2.195, 0.265), ("bf2ll", 0.640, -2.070, 0.280),
        ("bf3ll", 0.800, -1.760, 0.430), ("bf4ll", 0.790, -1.760, 0.270),
    ]
    w = mass / 15
    for nm, x, y, z in rows:
        p.node(nm, x, y, z, nodeWeight=w)
        if x:
            p.node(mir(nm), -x, y, z, nodeWeight=w)
    p.nodes_props(group="", **RIGID)
    p.node("bf0", 0.0, -2.000, 0.350, nodeWeight=w)
    p.nodes_props(group="")
    top = ["bf3rr", "bf1rr", "bf1r", "bf1", "bf1l", "bf1ll", "bf3ll"]
    bot = ["bf4rr", "bf2rr", "bf2r", "bf2", "bf2l", "bf2ll", "bf4ll"]
    _std_beams(p, 801000, 40, 7000)
    pairs = list(zip(top, top[1:])) + list(zip(bot, bot[1:])) + list(zip(top, bot))
    pairs += [(top[i], bot[i + 1]) for i in range(len(top) - 1)] + [(top[i + 1], bot[i]) for i in range(len(top) - 1)]
    for a, b in pairs:
        p.beam(a, b)
    p.beams_props(beamSpring=401000, beamDamp=30, beamDeform=4000, beamStrength="FLT_MAX")
    for k in top + bot:
        p.beam(k, "bf0")
    p.beam_comment("mounts")
    p.beams_props(beamSpring=1001000, beamDamp=50, beamDeform=9000, beamStrength=15000)
    for grp_name, links in (("bumperF_C", [("bf1", "fe2"), ("bf2", "fe1"), ("bf1", "fe1"), ("bf2", "fe2"), ("bf0", "fe1"), ("bf0", "fe2")]),
                            ("bumperF_L", [("bf1l", "fe2l"), ("bf2l", "fe1l"), ("bf1ll", "fe1l"), ("bf2ll", "fe1l"),
                                           ("bf3ll", "fa1l"), ("bf4ll", "fr1l"), ("bf3ll", "ft1l"), ("bf4ll", "fa1l")])):
        p.beams_props(breakGroup=grp_name)
        for a, b in links:
            p.beam(a, b)
        if grp_name == "bumperF_L":
            p.beams_props(breakGroup="bumperF_R")
            for a, b in links:
                p.beam(mir(a), mir(b))
    p.beams_props(breakGroup="")
    _reset_beams(p)
    p.tris_props(dragCoef=12, groundModel="plastic", triangleType="NORMALTYPE")
    for i in range(len(top) - 1):
        p.quad(top[i], top[i + 1], bot[i + 1], bot[i])
    return p


def bumper_rear(name="s13_bumper_R", mesh="s13_bumper_R", title="Stock Rear Bumper", value=280, mass=8.5):
    p = Part(name, title, "s13_bumper_R", value=value)
    grp = "s13_bumper_R"
    p.flexbody(mesh, [grp])
    p.nodes_props(group=grp, **PANEL_NODE)
    rows = [
        ("br1", 0.0, 2.250, 0.500), ("br1l", 0.420, 2.230, 0.500), ("br1ll", 0.680, 2.120, 0.500),
        ("br2", 0.0, 2.240, 0.300), ("br2l", 0.420, 2.220, 0.300), ("br2ll", 0.680, 2.110, 0.310),
        ("br3ll", 0.800, 1.760, 0.480), ("br4ll", 0.790, 1.760, 0.300),
    ]
    w = mass / 15
    for nm, x, y, z in rows:
        p.node(nm, x, y, z, nodeWeight=w)
        if x:
            p.node(mir(nm), -x, y, z, nodeWeight=w)
    p.nodes_props(group="", **RIGID)
    p.node("br0", 0.0, 2.000, 0.400, nodeWeight=w)
    p.nodes_props(group="")
    top = ["br3rr", "br1rr", "br1r", "br1", "br1l", "br1ll", "br3ll"]
    bot = ["br4rr", "br2rr", "br2r", "br2", "br2l", "br2ll", "br4ll"]
    _std_beams(p, 801000, 40, 7000)
    pairs = list(zip(top, top[1:])) + list(zip(bot, bot[1:])) + list(zip(top, bot))
    pairs += [(top[i], bot[i + 1]) for i in range(len(top) - 1)] + [(top[i + 1], bot[i]) for i in range(len(top) - 1)]
    for a, b in pairs:
        p.beam(a, b)
    p.beams_props(beamSpring=401000, beamDamp=30, beamDeform=4000, beamStrength="FLT_MAX")
    for k in top + bot:
        p.beam(k, "br0")
    p.beam_comment("mounts")
    p.beams_props(beamSpring=1001000, beamDamp=50, beamDeform=9000, beamStrength=15000)
    for grp_name, links in (("bumperR_C", [("br1", "tl2"), ("br2", "tl1"), ("br1", "tl1"), ("br2", "tl2"), ("br0", "tl1"), ("br0", "tl2")]),
                            ("bumperR_L", [("br1l", "tl2l"), ("br2l", "tl1l"), ("br1ll", "tl2l"), ("br2ll", "tl1l"),
                                           ("br3ll", "tp1l"), ("br4ll", "si6l"), ("br3ll", "qp6l"), ("br4ll", "tp1l")])):
        p.beams_props(breakGroup=grp_name)
        for a, b in links:
            p.beam(a, b)
        if grp_name == "bumperR_L":
            p.beams_props(breakGroup="bumperR_R")
            for a, b in links:
                p.beam(mir(a), mir(b))
    p.beams_props(breakGroup="")
    _reset_beams(p)
    p.tris_props(dragCoef=12, groundModel="plastic", triangleType="NORMALTYPE")
    for i in range(len(top) - 1):
        p.quad(top[i + 1], top[i], bot[i], bot[i + 1])
    return p
