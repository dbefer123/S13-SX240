"""S13 race hardware: roll cages, the tube-chassis body, lightweight panels, aero
(splitter, canards, swan-neck wing, diffuser, wicker bill), drag gear (wheelie
bar, parachute, fuel cells), race electronics and race interiors.

Cage and tube-frame geometry is defined once here and used both for the JBeam
and for the tube meshes (tools/model/s13_race.py sweeps tubes along the same
node pairs), so visuals and physics coincide.
"""
from __future__ import annotations

import math

import numpy as np

from tools.vehicle.common.jb import Part
from . import dims as D
from . import structure as ST
from .structure import mir

PFX = "s13"

# ---------------------------------------------------------------------------
# cage geometry (left side + centre; mirrored)
# ---------------------------------------------------------------------------
CAGE_NODES = [  # name, x, y, z, weight, body attachments
    ("cg0l", 0.690, -0.770, 0.230, 2.0, ("si0l", "hp1l", "fp1l", "fl1l")),     # front hoop foot
    ("cg6l", 0.700, -0.680, 0.520, 1.6, ("hp1l", "hp2l", "si0l")),             # front hoop, door-bar height
    ("cg1l", 0.650, -0.590, 0.820, 1.6, ("hp3l", "hp2l", "fp3l")),             # A-pillar bar / dash bar junction
    ("cg2l", 0.545, -0.270, 1.120, 1.6, ("ap1l", "rf1l")),                     # front roof corner
    ("cg3l", 0.540, 0.580, 1.150, 1.8, ("rf3l", "bp3l", "rf2l")),              # main hoop corner
    ("cg5l", 0.700, 0.580, 0.620, 1.6, ("bp2l", "bp1l")),                      # main hoop, door-bar height
    ("cg4l", 0.700, 0.580, 0.210, 2.0, ("si4l", "fl4l", "bp1l")),              # main hoop foot
    ("cg7l", 0.540, 1.200, 0.800, 1.6, ("rt1l", "qp4l", "qp5l", "rr1l")),      # rear stay foot (rear strut tower)
    ("cg8l", 0.600, -0.960, 0.700, 1.6, ("fs1l", "fp3l", "fp2l", "ft3l")),     # front down-bar through the firewall
]
CAGE_CENTER = [
    ("cg2", 0.0, -0.270, 1.150, 1.4, ("rf1",)),
    ("cg3", 0.0, 0.580, 1.185, 1.6, ("rf3",)),
    ("cg9", 0.0, 0.580, 0.700, 1.2, ()),                                         # harness bar centre
]
CAGE_LEVELS = {
    "rollbar": {
        "nodes": ["cg3", "cg4", "cg5", "cg7", "cg9"],
        "tubes": [("cg4l", "cg5l"), ("cg5l", "cg3l"), ("cg3l", "cg3"), ("cg5l", "cg9"), ("cg3l", "cg7l"),
                  ("cg3l", "cg9"), ("cg7l", "cg4l")],
    },
    "cage6": {
        "nodes": ["cg0", "cg1", "cg2", "cg6"],
        "tubes": [("cg0l", "cg6l"), ("cg6l", "cg1l"), ("cg1l", "cg2l"), ("cg2l", "cg3l"), ("cg2l", "cg2"),
                  ("cg1l", "cg1r"), ("cg6l", "cg5l"), ("cg0l", "cg4l")],
    },
    "full": {
        "nodes": ["cg8"],
        "tubes": [("cg6l", "cg4l"), ("cg0l", "cg5l"), ("cg2l", "cg3r"), ("cg1l", "cg8l"), ("cg8l", "fs1l"),
                  ("cg7l", "rt1l"), ("cg3l", "cg7r")],
    },
}
LEVEL_ORDER = ["rollbar", "cage6", "full"]
TUBE_R = {"cage": 0.022, "frame": 0.019}

# tube-chassis frame tubes (body nodes) shown as visible tubes
FRAME_TUBES = [
    # front clip (replaces the inner aprons)
    ("fe1l", "fe1r"), ("fe2l", "fe2r"), ("fe1l", "fe2l"), ("fe1l", "fr1l"), ("fr1l", "fr2l"), ("fr2l", "fr3l"),
    ("fr3l", "fp1l"), ("fe2l", "ft1l"), ("ft1l", "ft2l"), ("ft2l", "ft3l"), ("ft3l", "fp3l"), ("fr1l", "ft1l"),
    ("fr2l", "fs1l"), ("ft2l", "fs1l"), ("ft3l", "fs1l"), ("fs1l", "fp2l"), ("fr1l", "fr1r"), ("fc1l", "fc1r"),
    ("fe2l", "fr1l"),
    # floor perimeter / tunnel
    ("si0l", "si1l"), ("si1l", "si2l"), ("si2l", "si3l"), ("si3l", "si4l"), ("si4l", "si5l"),
    ("fp1l", "fp1r"), ("fl4l", "fl4r"),
    # rear clip
    ("si5l", "rr1l"), ("rr1l", "rr2l"), ("rr2l", "rr3l"), ("rr3l", "tl1l"), ("tl1l", "tl1r"), ("rr3l", "rr3r"),
    ("rr1l", "rt1l"), ("rr2l", "rt1l"), ("rt1l", "rt1r"), ("tl1l", "tl2l"), ("tl2l", "tl2r"), ("rr3l", "tp1l"),
    ("tp1l", "tl2l"), ("cp3l", "tp3l"), ("rr2l", "qp6l"),
]


def cage_nodes(levels):
    """Node table rows (name, x, y, z, w, attach) for the cage levels, left+right."""
    wanted = set()
    for lv in levels:
        wanted |= set(CAGE_LEVELS[lv]["nodes"])
    rows = []
    for nm, x, y, z, w, att in CAGE_NODES:
        if nm[:-1] in wanted:
            rows.append((nm, x, y, z, w, att))
            rows.append((mir(nm), -x, y, z, w, tuple(mir(a) for a in att)))
    for nm, x, y, z, w, att in CAGE_CENTER:
        if nm in wanted:
            rows.append((nm, x, y, z, w, att))
    return rows


def cage_tubes(levels):
    seen, out = set(), []
    for lv in levels:
        for a, b in CAGE_LEVELS[lv]["tubes"]:
            for p in ((a, b), (mir(a), mir(b))):
                k = tuple(sorted(p))
                if k not in seen:
                    seen.add(k)
                    out.append(p)
    return out


def frame_tubes():
    seen, out = set(), []
    for a, b in FRAME_TUBES:
        for p in ((a, b), (mir(a), mir(b))):
            k = tuple(sorted(p))
            if k not in seen:
                seen.add(k)
                out.append(p)
    return out


def node_positions(levels=("rollbar", "cage6", "full")):
    """All body + cage node positions (for the mesh builder)."""
    pos = {n: np.array(p) for n, (p, w) in ST.all_nodes().items()}
    for nm, x, y, z, w, att in cage_nodes(levels):
        pos[nm] = np.array((x, y, z))
    return pos


def _cage_jbeam(p, levels, group, weight_scale=1.0):
    rows = cage_nodes(levels)
    p.nodes_props(selfCollision=True, collision=True, nodeMaterial="|NM_METAL", frictionCoef=0.5, group=group)
    for nm, x, y, z, w, att in rows:
        p.node(nm, x, y, z, nodeWeight=round(w * weight_scale, 3))
    p.nodes_props(group="")
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beam_comment("cage tubes")
    p.beams_props(beamSpring=2401000, beamDamp=140, beamDeform=110000, beamStrength="FLT_MAX", deformLimitExpansion=1.1)
    seen = set()
    for a, b in cage_tubes(levels):
        seen.add(tuple(sorted((a, b))))
        p.beam(a, b)
    p.beam_comment("cage mounting plates / bracing to the shell")
    p.beams_props(beamSpring=1801000, beamDamp=110, beamDeform=80000, beamStrength="FLT_MAX")
    names = {r[0] for r in rows}
    for nm, x, y, z, w, att in rows:
        for b in att:
            k = tuple(sorted((nm, b)))
            if k not in seen:
                seen.add(k)
                p.beam(nm, b)
    # stabilise the centre nodes and give every cage node a 3D brace
    braces = [("cg9", "cg4l"), ("cg9", "cg4r"), ("cg9", "fl4"), ("cg9", "cg3"), ("cg3", "cg5l"), ("cg3", "cg5r"),
              ("cg2", "cg1l"), ("cg2", "cg1r"), ("cg2", "cg3"), ("cg7l", "cg5l"), ("cg7r", "cg5r"), ("cg7l", "cg9"),
              ("cg7r", "cg9"), ("cg1l", "cg5l"), ("cg1r", "cg5r"), ("cg6l", "si1l"), ("cg6r", "si1r"),
              ("cg8l", "cg2l"), ("cg8r", "cg2r"), ("cg5l", "si3l"), ("cg5r", "si3r"), ("cg3l", "cg3r"),
              ("cg2l", "cg2r"), ("cg0l", "cg0r"), ("cg4l", "cg4r"), ("cg5l", "cg5r"), ("cg6l", "cg1r"), ("cg6r", "cg1l")]
    for a, b in braces:
        k = tuple(sorted((a, b)))
        if a in names and (b in names or not b.startswith("cg")) and k not in seen:
            seen.add(k)
            p.beam(a, b)
    p.beams_props(deformLimitExpansion=1.2)


CAGE_TITLES = {"rollbar": ("4-Point Roll Bar", 650, ["rollbar"]),
               "cage6": ("6-Point Roll Cage", 1600, ["rollbar", "cage6"]),
               "full": ("Full Weld-In Roll Cage", 3200, ["rollbar", "cage6", "full"])}


def rollcages():
    out = [Part(f"{PFX}_rollcage_none", "No Roll Cage", f"{PFX}_rollcage", value=0)]
    for key, (title, value, levels) in CAGE_TITLES.items():
        p = Part(f"{PFX}_rollcage_{key}", title, f"{PFX}_rollcage", value=value)
        p.flexbody(f"{PFX}_rollcage_{key}", [f"{PFX}_cage", f"{PFX}_body"])
        _cage_jbeam(p, levels, f"{PFX}_cage")
        out.append(p)
    return out


# ---------------------------------------------------------------------------
# tube chassis
# ---------------------------------------------------------------------------
TUBE_SCALE = 0.88   # node weight scale vs. the raw unibody weights (unibody uses 1.40)
HARD = set(ST.HARDPOINTS) | {"fc1", "fc2l", "fr2l", "fa3l", "fs1l", "rt1l", "rm1l", "rm2l", "rr1l", "fl5", "fl6", "fl7"}

RACE_BODY_SLOTS = [  # slot, default for the tube chassis, description
    ("hood", "hood_vented", "Hood"), ("popup_L", "popup_delete_L", "Left Headlight"),
    ("popup_R", "popup_delete_R", "Right Headlight"), ("fender_L", "fender_wide_L", "Left Fender"),
    ("fender_R", "fender_wide_R", "Right Fender"), ("door_L", "door_light_L", "Left Door"),
    ("door_R", "door_light_R", "Right Door"), ("hatch", "hatch_light", "Hatch"),
    ("bumper_F", "bumper_F_light", "Front Bumper"), ("bumper_R", "bumper_R_light", "Rear Bumper"),
    ("taillights", "taillights", "Tail Lights"), ("interior", "interior_race", "Interior"),
]
AERO_SLOTS = [  # common to unibody + tube chassis: slot, default unibody, default tube, description
    ("splitter", "", "splitter_race", "Front Splitter"), ("canards", "", "", "Canards"),
    ("wing", "", "wing_gt", "Rear Wing / Spoiler"), ("diffuser", "", "diffuser_race", "Rear Diffuser"),
    ("overfenders_R", "", "overfenders_R", "Rear Over-Fenders"), ("sideskirts", "", "", "Side Skirts"),
    ("wheeliebar", "", "", "Wheelie Bar"),
    ("parachute", "", "", "Parachute"),
]


def tube_chassis(body_common):
    """`body_common(p)` adds the shared glass/ref nodes/cameras/skin from vehicle.py."""
    ST._EMITTED.clear()
    p = Part(f"{PFX}_body_tube", "Tube Chassis (Race Spaceframe)", f"{PFX}_body", value=48000)
    for slot, default, desc in RACE_BODY_SLOTS:
        p.slot(f"{PFX}_{slot}", f"{PFX}_{default}", desc)
    for slot, d_uni, d_tube, desc in AERO_SLOTS:
        p.slot(f"{PFX}_{slot}", f"{PFX}_{d_tube}" if d_tube else "", desc)
    nodes = ST.all_nodes()
    p.nodes_props(selfCollision=True, collision=True, nodeMaterial="|NM_METAL", frictionCoef=0.5, group=f"{PFX}_body")
    for name, (pos, w) in nodes.items():
        inline = {}
        if name in ("fs1l", "fs1r"):
            inline["group"] = [f"{PFX}_body", f"{PFX}_shocktop_F"]
        if name in ("rt1l", "rt1r"):
            inline["group"] = [f"{PFX}_body", f"{PFX}_shocktop_R"]
        # suspension / engine hard points keep the unibody weights (they carry the stiff link beams)
        hard = name in HARD or mir(name) in HARD
        p.node(name, *pos, nodeWeight=round(w * (ST.BODY_MASS_SCALE if hard else TUBE_SCALE), 3), **inline)
    p.nodes_props(group="")
    p.beams_props(deformLimitExpansion=1.2)
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beam_comment("front clip (chromoly tube)")
    p.beams_props(beamSpring=1501000, beamDamp=110, beamDeform=45000, beamStrength="FLT_MAX")
    for a, b in ST._beam_set([ST.FRONT_RAILS, ST.FRONT_APRON]):
        p.beam(a, b)
    p.beams_props(beamSpring=1801000, beamDamp=130, beamDeform=90000, beamStrength="FLT_MAX")
    for a, b in ST._beam_set([ST.STRUT_TOWER, ST.CROSSMEMBER, ST.BATTERY]):
        p.beam(a, b)
    p.beam_comment("centre section: floor tubes and sills")
    p.beams_props(beamSpring=2001000, beamDamp=130, beamDeform=120000, beamStrength="FLT_MAX")
    for a, b in ST._beam_set([ST.FIREWALL, ST.FLOOR]):
        p.beam(a, b)
    p.beams_props(beamSpring=1501000, beamDamp=110, beamDeform=60000, beamStrength="FLT_MAX")
    for a, b in ST._beam_set([ST.PILLARS, ST.CABIN_X, ST.EXTRA_BRACES]):
        p.beam(a, b)
    p.beam_comment("rear clip")
    p.beams_props(beamSpring=1501000, beamDamp=110, beamDeform=55000, beamStrength="FLT_MAX")
    for a, b in ST._beam_set([ST.REAR_BODY]):
        p.beam(a, b)
    _cage_jbeam(p, LEVEL_ORDER, f"{PFX}_body", weight_scale=1.0)
    # fiberglass shell + visible frame
    p.flexbody(f"{PFX}_body_hatch", [f"{PFX}_body"])
    p.flexbody(f"{PFX}_tubeframe", [f"{PFX}_body"])
    p.flexbody(f"{PFX}_tube_floor", [f"{PFX}_body"])
    body_common(p)
    return p


# ---------------------------------------------------------------------------
# aero
# ---------------------------------------------------------------------------
def _plate(p, front, rear, lift, drag=20, stall=0.4, flip=False):
    p.tris_props(dragCoef=drag, liftCoef=lift, stallAngle=stall, groundModel="metal", triangleType="NORMALTYPE")
    for i in range(len(front) - 1):
        q = [front[i], front[i + 1], rear[i + 1], rear[i]]
        p.quad(*(q[::-1] if flip else q))
    p.tris_props(liftCoef=0, stallAngle=0.58, dragCoef=10)


def splitter():
    p = Part(f"{PFX}_splitter_race", "Carbon Race Splitter", f"{PFX}_splitter", value=1400)
    p.flexbody(f"{PFX}_splitter_race", [f"{PFX}_splitter"])
    p.nodes_props(selfCollision=True, collision=True, nodeMaterial="|NM_PLASTIC", frictionCoef=0.4,
                  group=f"{PFX}_splitter")
    front = [("sp1", 0.0, -2.340, 0.150), ("sp1l", 0.450, -2.315, 0.150), ("sp1ll", 0.760, -2.170, 0.158)]
    rear = [("sp2", 0.0, -2.060, 0.168), ("sp2l", 0.450, -2.050, 0.168), ("sp2ll", 0.760, -1.960, 0.172)]
    for nm, x, y, z in front + rear:
        p.node(nm, x, y, z, nodeWeight=0.9)
        if x:
            p.node(mir(nm), -x, y, z, nodeWeight=0.9)
    p.nodes_props(group="")
    F = ["sp1rr", "sp1r", "sp1", "sp1l", "sp1ll"]
    R = ["sp2rr", "sp2r", "sp2", "sp2l", "sp2ll"]
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=801000, beamDamp=40, beamDeform=9000, beamStrength="FLT_MAX")
    for row in (F, R):
        for a, b in zip(row, row[1:]):
            p.beam(a, b)
    for i in range(len(F)):
        p.beam(F[i], R[i])
        if i < len(F) - 1:
            p.beam(F[i], R[i + 1]); p.beam(F[i + 1], R[i])
    p.beam_comment("mounts + support rods")
    p.beams_props(beamSpring=601000, beamDamp=40, beamDeform=7000, beamStrength=16000, breakGroup="splitter")
    for a, bs in (("sp2", ("fe1", "fr1l", "fr1r")), ("sp2l", ("fe1l", "fr1l", "fe1")), ("sp2r", ("fe1r", "fr1r", "fe1")),
                  ("sp2ll", ("fe1l", "fa1l", "fr1l")), ("sp2rr", ("fe1r", "fa1r", "fr1r")),
                  ("sp1", ("fe1", "fe2")), ("sp1l", ("fe1l", "fe2l")), ("sp1r", ("fe1r", "fe2r")),
                  ("sp1ll", ("fe1l", "fa1l")), ("sp1rr", ("fe1r", "fa1r"))):
        for b in bs:
            p.beam(a, b)
    p.beams_props(breakGroup="")
    # front edge 18 mm lower than the rear edge: 'tilted down' -> downforce
    _plate(p, F, R, lift=180, drag=15, stall=0.35)
    return p


def canards():
    """Two dive planes per side on the bumper corners: inner-front, inner-rear (higher) and outer tip."""
    p = Part(f"{PFX}_canards_race", "Carbon Dive Planes (Canards)", f"{PFX}_canards", value=450)
    p.flexbody(f"{PFX}_canards_race", [f"{PFX}_canards"])
    p.nodes_props(selfCollision=False, collision=True, nodeMaterial="|NM_PLASTIC", frictionCoef=0.4,
                  group=f"{PFX}_canards")
    fins = {1: (0.330, 0.0), 2: (0.450, 0.010)}   # fin: (z at front, extra)
    for k, (z, dz) in fins.items():
        for nm, x, y, zz in ((f"cn{k}a", 0.770, -2.080 + dz, z), (f"cn{k}b", 0.800, -1.960 + dz, z + 0.030),
                             (f"cn{k}c", 0.860, -2.000 + dz, z + 0.016)):
            p.node(nm + "l", x, y, zz, nodeWeight=0.25)
            p.node(nm + "r", -x, y, zz, nodeWeight=0.25)
    p.nodes_props(group="")
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=301000, beamDamp=20, beamDeform=3000, beamStrength=6000, breakGroup="canards")
    for s in ("l", "r"):
        for k in fins:
            a, b, c = f"cn{k}a{s}", f"cn{k}b{s}", f"cn{k}c{s}"
            p.beam(a, b); p.beam(b, c); p.beam(c, a)
            for n_, bs in ((a, ("fe1", "fa1", "fe2")), (b, ("fa1", "ft1", "fr1")), (c, ("fa1", "fe2"))):
                for t in bs:
                    p.beam(n_, t + s)
        p.beam(f"cn1a{s}", f"cn2a{s}"); p.beam(f"cn1b{s}", f"cn2b{s}"); p.beam(f"cn1c{s}", f"cn2c{s}")
    p.beams_props(breakGroup="")
    # leading edge lower than the trailing edge -> downforce on the front axle
    p.tris_props(dragCoef=30, liftCoef=150, stallAngle=0.40, groundModel="metal", triangleType="NORMALTYPE")
    for k in fins:
        p.tri(f"cn{k}al", f"cn{k}bl", f"cn{k}cl")
        p.tri(f"cn{k}ar", f"cn{k}cr", f"cn{k}br")
    p.tris_props(liftCoef=0, stallAngle=0.58, dragCoef=10)
    return p


# --- swan-neck GT wing ------------------------------------------------------------
WING = dict(span=0.80, chord=0.30, x_mount=0.40, y_le=2.090, z_le=1.175, default_angle=10.0, min_angle=2.0, max_angle=20.0,
            foot=(2.185, 0.905))


def wing_points(angle_deg):
    """Leading/trailing edge (y, z) for a wing angle (positive = trailing edge up = downforce)."""
    a = math.radians(angle_deg)
    y_le, z_le, c = WING["y_le"], WING["z_le"], WING["chord"]
    return (y_le, z_le), (y_le + c * math.cos(a), z_le + c * math.sin(a))


def _angle_link_factor():
    """beamPrecompression per degree for the trailing-edge link (upright -> trailing edge)."""
    up = np.array((WING["y_le"] + 0.05, WING["z_le"] - 0.17))   # upright lower attachment (y, z) at x_mount
    lens = []
    for ang in (WING["default_angle"], WING["default_angle"] + 1.0):
        le, te = wing_points(ang)
        lens.append(np.linalg.norm(np.array(te) - up))
    return (lens[1] - lens[0]) / lens[0], up


def wing_gt():
    p = Part(f"{PFX}_wing_gt", "Swan-Neck GT Wing (Adjustable)", f"{PFX}_wing", value=3800)
    k, up = _angle_link_factor()
    p.variable("$wing_angle", "deg", "Aerodynamics", WING["default_angle"], WING["min_angle"], WING["max_angle"],
               "Wing Angle", "Main plane angle of attack: more angle = more downforce and drag", stepDis=0.5)
    p.flexbody(f"{PFX}_wing_gt", [f"{PFX}_wing"])
    p.flexbody(f"{PFX}_wing_gt_mounts", [f"{PFX}_wing", f"{PFX}_wingmount"])
    (yl, zl), (yt, zt) = wing_points(WING["default_angle"])
    sp, xm = WING["span"], WING["x_mount"]
    p.nodes_props(selfCollision=True, collision=True, nodeMaterial="|NM_PLASTIC", frictionCoef=0.4, group=f"{PFX}_wing")
    for tag, x in (("", 0.0), ("m", xm), ("e", sp)):
        for edge, (y, z) in (("1", (yl, zl)), ("2", (yt, zt))):
            nm = f"wg{edge}{tag}"
            if x == 0:
                p.node(nm, 0.0, y, z, nodeWeight=0.8)
            else:
                p.node(nm + "l", x, y, z, nodeWeight=0.8)
                p.node(nm + "r", -x, y, z, nodeWeight=0.8)
    p.nodes_props(group=f"{PFX}_wingmount")
    for s, sx in (("l", 1), ("r", -1)):
        p.node("wu1" + s, sx * xm, float(up[0]), float(up[1]), nodeWeight=1.0)          # upright knee
        p.node("wu0" + s, sx * xm, WING["foot"][0], WING["foot"][1], nodeWeight=1.2)      # deck foot
    p.nodes_props(group="")
    L = ["wg1er", "wg1mr", "wg1", "wg1ml", "wg1el"]
    T = ["wg2er", "wg2mr", "wg2", "wg2ml", "wg2el"]
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=801000, beamDamp=40, beamDeform=15000, beamStrength="FLT_MAX")
    for row in (L, T):
        for a, b in zip(row, row[1:]):
            p.beam(a, b)
    for i in range(len(L)):
        p.beam(L[i], T[i])
        if i < len(L) - 1:
            p.beam(L[i], T[i + 1]); p.beam(L[i + 1], T[i])
    p.beam("wg1el", "wg1er"); p.beam("wg2el", "wg2er")
    p.beam_comment("swan-neck uprights")
    p.beams_props(beamSpring=901000, beamDamp=50, beamDeform=20000, beamStrength=60000, breakGroup="wing_mount")
    for s in ("l", "r"):
        for a, b in (("wu0", "wu1"), ("wu1", "wg1m"), ("wu0", "wg1m")):
            p.beam(a + s, b + s)
        for b in ("tl3", "tp3", "cp3", "tl2"):
            p.beam("wu0" + s, b + s)
        p.beam("wu0" + s, "tl3")
        p.beam("wu1" + s, "cp3" + s)
        p.beam("wu1" + s, "tl3" + s)
    p.beam("wu0l", "wu0r"); p.beam("wu1l", "wu1r"); p.beam("wu1l", "wg1mr"); p.beam("wu1r", "wg1ml")
    p.beam_comment("angle adjuster links (precompression sets the angle of attack)")
    p.beams_props(beamPrecompression=f"$=1 + ($wing_angle - {WING['default_angle']}) * {k:.6f}")
    for s in ("l", "r"):
        p.beam("wu1" + s, "wg2m" + s)
    p.beams_props(beamPrecompression=1, breakGroup="")
    p.beams_props(deformLimitExpansion=1.2)
    # main plane: leading edge lower than trailing edge -> downforce; endplates add drag only
    _plate(p, L, T, lift=260, drag=28, stall=0.36)
    return p


def wicker_bill():
    p = Part(f"{PFX}_wing_wicker", "Drag Wicker Bill Spoiler", f"{PFX}_wing", value=260)
    p.flexbody(f"{PFX}_wing_wicker", [f"{PFX}_wing"])
    p.nodes_props(selfCollision=False, collision=True, nodeMaterial="|NM_PLASTIC", frictionCoef=0.4, group=f"{PFX}_wing")
    rows = [("wk1", 0.0, 2.205, 0.905), ("wk1l", 0.62, 2.190, 0.900), ("wk2", 0.0, 2.235, 0.965), ("wk2l", 0.62, 2.220, 0.960)]
    for nm, x, y, z in rows:
        p.node(nm, x, y, z, nodeWeight=0.35)
        if x:
            p.node(mir(nm), -x, y, z, nodeWeight=0.35)
    p.nodes_props(group="")
    B = ["wk1r", "wk1", "wk1l"]
    Tp = ["wk2r", "wk2", "wk2l"]
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=601000, beamDamp=40, beamDeform=6000, beamStrength=12000)
    for row in (B, Tp):
        for a, b in zip(row, row[1:]):
            p.beam(a, b)
    for i in range(3):
        p.beam(B[i], Tp[i])
        if i < 2:
            p.beam(B[i], Tp[i + 1]); p.beam(B[i + 1], Tp[i])
    for a, bs in (("wk1", ("tl3", "tl3l", "tl3r")), ("wk1l", ("tl3l", "tp3l", "tl3")), ("wk1r", ("tl3r", "tp3r", "tl3"))):
        for b in bs:
            p.beam(a, b)
    p.beams_props(beamSpring=401000, beamDamp=30, beamDeform=5000, beamStrength=9000)
    for a, b in (("wk2", "tl3"), ("wk2l", "tl3l"), ("wk2r", "tl3r"), ("wk2l", "tp3l"), ("wk2r", "tp3r")):
        p.beam(a, b)
    # near-vertical lip: mostly drag, small downforce for high-speed stability
    p.tris_props(dragCoef=35, liftCoef=60, stallAngle=0.6, groundModel="metal")
    for i in range(2):
        p.quad(B[i], B[i + 1], Tp[i + 1], Tp[i])
    p.tris_props(liftCoef=0, stallAngle=0.58, dragCoef=10)
    return p


def diffuser():
    p = Part(f"{PFX}_diffuser_race", "Carbon Rear Diffuser", f"{PFX}_diffuser", value=1100)
    p.flexbody(f"{PFX}_diffuser_race", [f"{PFX}_diffuser"])
    p.nodes_props(selfCollision=True, collision=True, nodeMaterial="|NM_PLASTIC", frictionCoef=0.4, group=f"{PFX}_diffuser")
    F = [("df1", 0.0, 1.900, 0.205), ("df1l", 0.300, 1.900, 0.205), ("df1ll", 0.620, 1.900, 0.215)]
    R = [("df2", 0.0, 2.300, 0.330), ("df2l", 0.300, 2.300, 0.330), ("df2ll", 0.620, 2.280, 0.335)]
    for nm, x, y, z in F + R:
        p.node(nm, x, y, z, nodeWeight=0.7)
        if x:
            p.node(mir(nm), -x, y, z, nodeWeight=0.7)
    p.nodes_props(group="")
    Fn = ["df1rr", "df1r", "df1", "df1l", "df1ll"]
    Rn = ["df2rr", "df2r", "df2", "df2l", "df2ll"]
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=701000, beamDamp=40, beamDeform=8000, beamStrength="FLT_MAX")
    for row in (Fn, Rn):
        for a, b in zip(row, row[1:]):
            p.beam(a, b)
    for i in range(len(Fn)):
        p.beam(Fn[i], Rn[i])
        if i < len(Fn) - 1:
            p.beam(Fn[i], Rn[i + 1]); p.beam(Fn[i + 1], Rn[i])
    p.beams_props(beamSpring=501000, beamDamp=40, beamDeform=7000, beamStrength=15000, breakGroup="diffuser")
    for a, bs in (("df1", ("fl8", "rr3l", "rr3r")), ("df1l", ("rr3l", "fl8", "rr2l")), ("df1r", ("rr3r", "fl8", "rr2r")),
                  ("df1ll", ("rr3l", "si6l")), ("df1rr", ("rr3r", "si6r")), ("df2", ("tl1", "fl8")),
                  ("df2l", ("tl1l", "rr3l")), ("df2r", ("tl1r", "rr3r")), ("df2ll", ("tl1l", "tp1l")), ("df2rr", ("tl1r", "tp1r"))):
        for b in bs:
            p.beam(a, b)
    p.beams_props(breakGroup="")
    # ramp: leading edge low, trailing edge high (inverted-wing sense) -> downforce
    _plate(p, Fn, Rn, lift=140, drag=12, stall=0.45, flip=True)
    return p


def sideskirts():
    p = Part(f"{PFX}_sideskirts_aero", "Aero Side Skirts", f"{PFX}_sideskirts", value=420)
    p.flexbody(f"{PFX}_sideskirts_aero", [f"{PFX}_body"])
    return p


def overfenders_R():
    p = Part(f"{PFX}_overfenders_R", "Rear Over-Fenders (+50 mm)", f"{PFX}_overfenders_R", value=900)
    p.flexbody(f"{PFX}_overfenders_R", [f"{PFX}_body"])
    return p


# ---------------------------------------------------------------------------
# drag gear
# ---------------------------------------------------------------------------
WHEELIE = dict(x=0.32, y_end=3.40, z_axle=0.135, hub_r=0.085)


def wheelie_bar():
    p = Part(f"{PFX}_wheeliebar", "Adjustable Wheelie Bar", f"{PFX}_wheeliebar", value=1300)
    p.flexbody(f"{PFX}_wheeliebar", [f"{PFX}_wheeliebar"])
    x, ye, za = WHEELIE["x"], WHEELIE["y_end"], WHEELIE["z_axle"]
    p.nodes_props(selfCollision=False, collision=True, nodeMaterial="|NM_METAL", frictionCoef=0.4,
                  group=f"{PFX}_wheeliebar")
    for s, sx in (("l", 1), ("r", -1)):
        p.node("wb0" + s, sx * x, 2.10, 0.250, nodeWeight=1.6)          # lower frame pivot
        p.node("wb1" + s, sx * x, 2.10, 0.420, nodeWeight=1.4)          # upper frame mount
        p.node("wb2" + s, sx * x, 2.85, 0.205, nodeWeight=1.4)       # mid
        p.node("wb3" + s, sx * x, ye, za, nodeWeight=1.4)            # axle inner
        p.node("wb4" + s, sx * (x + 0.04), ye, za, nodeWeight=1.0)   # axle outer
    p.node("wb2", 0.0, 2.85, 0.205, nodeWeight=1.0)
    p.nodes_props(group="")
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=1001000, beamDamp=60, beamDeform=30000, beamStrength="FLT_MAX")
    for s in ("l", "r"):
        for a, b in (("wb0", "wb2"), ("wb1", "wb2"), ("wb2", "wb3"), ("wb0", "wb3"), ("wb1", "wb3"), ("wb3", "wb4"),
                     ("wb2", "wb4"), ("wb0", "wb1"), ("wb1", "wb4"), ("wb0", "wb4")):
            p.beam(a + s, b + s)
    for a, b in (("wb2l", "wb2"), ("wb2r", "wb2"), ("wb3l", "wb3r"), ("wb2l", "wb3r"), ("wb2r", "wb3l"), ("wb0l", "wb0r"),
                 ("wb1l", "wb1r"), ("wb0l", "wb2"), ("wb0r", "wb2"), ("wb2l", "wb2r")):
        p.beam(a, b)
    p.beam_comment("mounts to the rear frame")
    p.beams_props(beamSpring=1201000, beamDamp=70, beamDeform=30000, beamStrength=80000, breakGroup="wheeliebar")
    for s in ("l", "r"):
        for a, bs in (("wb0", ("rr3", "rr2", "tl1", "fl8")), ("wb1", ("rr3", "tl1", "tl2", "tp1"))):
            for b in bs:
                p.beam(a + s, (b + s) if b not in ("fl8",) else b)
    p.beams_props(breakGroup="")
    pw_head = ["name", "hubGroup", "group", "node1:", "node2:", "nodeS", "nodeArm:", "wheelDir"]
    rows = [
        {"hubRadius": WHEELIE["hub_r"]}, {"hubWidth": 0.035}, {"numRays": 10}, {"hasTire": False},
        {"hubBeamSpring": 251000, "hubBeamDamp": 5}, {"hubBeamDeform": 40000, "hubBeamStrength": 160000},
        {"hubNodeWeight": 0.12}, {"hubNodeMaterial": "|NM_RUBBER"}, {"hubFrictionCoef": 0.8},
        {"brakeTorque": 0}, {"parkingTorque": 0}, {"selfCollision": True}, {"collision": True},
        ["WBL", f"{PFX}_wbwheel_L", f"{PFX}_wbwheel_L", "wb3l", "wb4l", 9999, "wb2l", 1, {"speedo": False}],
        ["WBR", f"{PFX}_wbwheel_R", f"{PFX}_wbwheel_R", "wb3r", "wb4r", 9999, "wb2r", -1, {"speedo": False}],
        {"hasTire": True},
    ]
    t = p.table("pressureWheels", pw_head)
    t.extend(rows)
    for s, sx in (("L", 1), ("R", -1)):
        p.flexbody(f"{PFX}_wheeliebar_wheel", [f"{PFX}_wbwheel_{s}"], pos={"x": sx * (x + 0.02), "y": ye, "z": za},
                   rot={"x": 0, "y": 0, "z": 0 if sx > 0 else 180}, scale={"x": 1, "y": 1, "z": 1})
    return p


def parachute():
    p = Part(f"{PFX}_parachute", "Drag Parachute Pack", f"{PFX}_parachute", value=700)
    p.flexbody(f"{PFX}_parachute", [f"{PFX}_body"])
    return p


def fuelcell(key, title, capacity, value, mesh, y=1.80):
    p = Part(f"{PFX}_fueltank_{key}", title, f"{PFX}_fueltank", value=value)
    p.variable("$fuel", "L", "Chassis", round(capacity * 0.6), 0, capacity, "Fuel Volume", "Initial fuel volume", stepDis=0.5)
    p.set("energyStorage", [["type", "name"], ["fuelTank", "mainTank"]])
    p.set("mainTank", {"energyType": "gasoline", "fuelCapacity": capacity, "startingFuelCapacity": "$fuel",
                       "fuel": {"[engineGroup]:": ["fuel"]}, "breakTriggerBeam": "fuelTank"})
    p.flexbody(mesh, ["fueltank"])
    p.nodes_props(selfCollision=False, collision=True, nodeMaterial="|NM_METAL", frictionCoef=0.6, group="fueltank",
                  engineGroup="fuel")
    w = 1.6 if capacity > 20 else 1.0
    hw = 0.26 if capacity > 20 else 0.16
    for nm, x, yy, z in (("ftk1l", hw, y - 0.15, 0.33), ("ftk1r", -hw, y - 0.15, 0.33), ("ftk2l", hw, y + 0.15, 0.33),
                         ("ftk2r", -hw, y + 0.15, 0.33)):
        p.node(nm, x, yy, z, nodeWeight=w, chemEnergy=1000, burnRate=0.39, flashPoint=300, specHeat=0.2,
               smokePoint=150, selfIgnitionCoef=False, baseTemp="thermals", conductionRadius=0.2)
    p.nodes_props(group="", engineGroup="", chemEnergy=False, burnRate=False, flashPoint=False, specHeat=False,
                  smokePoint=False, selfIgnitionCoef=False, baseTemp=False, conductionRadius=False)
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=801000, beamDamp=50, beamDeform=9000, beamStrength="FLT_MAX")
    p.beam("ftk1l", "ftk1r", name="fuelTank", containerBeam="fuelTank")
    for a, b in (("ftk2l", "ftk2r"), ("ftk1l", "ftk2l"), ("ftk1r", "ftk2r"), ("ftk1l", "ftk2r"), ("ftk1r", "ftk2l")):
        p.beam(a, b)
    p.beams_props(beamSpring=601000, beamDamp=50, beamDeform=12000, beamStrength=60000)
    for a, bs in (("ftk1l", ("rr2l", "fl7", "rr1l")), ("ftk1r", ("rr2r", "fl7", "rr1r")), ("ftk2l", ("rr3l", "fl8", "rr2l")),
                  ("ftk2r", ("rr3r", "fl8", "rr2r"))):
        for b in bs:
            p.beam(a, b)
    return p


# ---------------------------------------------------------------------------
# electronics
# ---------------------------------------------------------------------------
SHIFT_LEDS = ["s13sl0", "s13sl1", "s13sl2", "s13sl3", "s13sl4"]


def electronics():
    out = [Part(f"{PFX}_electronics_none", "No Race Electronics", f"{PFX}_electronics", value=0)]
    p = Part(f"{PFX}_electronics_track", "Race Electronics: Shift Lights", f"{PFX}_electronics", value=600)
    p.set("controller", [["fileName"], ["shiftLights"]])
    p.set("shiftLights", {"engineName": "mainEngine", "maxEngineRPMOffset": 300, "rpmRange": 2200,
                             "keepLEDsActive": True, "outputElectrics": SHIFT_LEDS,
                             "flashingOutputElectrics": SHIFT_LEDS[-2:]})
    out.append(p)
    p = Part(f"{PFX}_electronics_drag", "Drag Electronics: Transbrake, Line Lock, Shift Lights", f"{PFX}_electronics",
             value=2400)
    p.set("controller", [["fileName"], ["transbrake", {}], ["lineLock", {"lockedLines": ["FR", "FL"]}],
                         ["shiftLights"]])
    p.set("shiftLights", {"engineName": "mainEngine", "maxEngineRPMOffset": 150, "rpmRange": 1500,
                             "keepLEDsActive": True, "outputElectrics": SHIFT_LEDS,
                             "flashingOutputElectrics": SHIFT_LEDS})
    out.append(p)
    return out


# ---------------------------------------------------------------------------
# lightweight panels (reuse the stock panel generators with lighter masses)
# ---------------------------------------------------------------------------
def light_panels():
    from . import panels_jb as PJ
    # lighter panels keep the stock panels' natural frequencies: springs/damping scale with mass
    out = [
        PJ.hood(name=f"{PFX}_hood_vented", title="Vented FRP Race Hood", mesh=f"{PFX}_hood_vented", value=900,
                mass=7.0).scale_springs(7.0 / 16.0),
        PJ.hood(name=f"{PFX}_hood_carbon", title="Carbon Fiber Hood", mesh=f"{PFX}_hood_carbon", value=1600,
                mass=6.0).scale_springs(6.0 / 16.0),
        PJ.hatch(name=f"{PFX}_hatch_light", mesh=f"{PFX}_hatch_carbon", glass=f"{PFX}_hatchglass_poly",
                 title="Carbon Hatch with Polycarbonate Window", value=1800, mass=8.5).scale_springs(8.5 / 21.0),
        PJ.bumper_front(name=f"{PFX}_bumper_F_light", mesh=f"{PFX}_bumper_F_race", title="FRP Race Front Bumper (Big Intake)",
                        value=500, mass=4.5).scale_springs(4.5 / 10.0),
        PJ.bumper_rear(name=f"{PFX}_bumper_R_light", mesh=f"{PFX}_bumper_R_race", title="FRP Race Rear Bumper (Diffuser Cut-Out)",
                       value=420, mass=3.8).scale_springs(3.8 / 8.5),
        PJ.bumper_front(name=f"{PFX}_bumper_F_aero", mesh=f"{PFX}_bumper_F_aero", title="Aero Front Bumper with Lip Spoiler",
                        value=650, mass=10.5),
        PJ.bumper_front(name=f"{PFX}_bumper_F_drift", mesh=f"{PFX}_bumper_F_drift", title="Type-X Style Drift Bumper",
                        value=900, mass=8.0).scale_springs(8.0 / 10.0),
        PJ.bumper_front(name=f"{PFX}_bumper_F_drag", mesh=f"{PFX}_bumper_F_drag", title="Smooth FRP Drag Bumper",
                        value=450, mass=4.0).scale_springs(4.0 / 10.0),
        PJ.bumper_rear(name=f"{PFX}_bumper_R_aero", mesh=f"{PFX}_bumper_R_aero", title="Aero Rear Bumper with Valance",
                       value=550, mass=9.0),
    ]
    for s in ("L", "R"):
        out.append(PJ.door(s, glass=f"{PFX}_doorglass_poly", title="FRP Race Door (Polycarbonate Window)", value=1100,
                           mass=9.0, name=f"{PFX}_door_light_{s}").scale_springs(9.0 / 26.0))
        out.append(PJ.fender(s, mesh=f"{PFX}_fender_wide", title="Wide Body Front Fender (+50 mm)", value=1200, mass=4.0,
                             flare=0.050).scale_springs(4.0 / 5.0))
        out.append(PJ.popup(s, name=f"{PFX}_popup_delete_{s}", mesh_lamp=f"{PFX}_led_projector", fixed=True,
                            title="Pop-up Delete with LED Projectors", value=500, mass=3.0).scale_springs(3.0 / 6.0))
    return out


def race_parts(body_common):
    return ([tube_chassis(body_common)] + rollcages() + light_panels() +
            [splitter(), canards(), wing_gt(), wicker_bill(), diffuser(), overfenders_R(), sideskirts(), wheelie_bar(), parachute(),
             fuelcell("racecell", "40L Race Fuel Cell", 40, 1200, f"{PFX}_fuelcell"),
             fuelcell("dragcell", "10L Drag Fuel Cell", 10, 600, f"{PFX}_fuelcell_drag")] + electronics())
