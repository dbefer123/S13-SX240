"""S13 unibody (hatchback) node/beam structure.

Naming: left-side nodes end in 'l' (x>0), right-side mirrors end in 'r',
centre nodes have no suffix.  Groups:
    s13_body      body shell flexbody mapping
Hard points used by other parts (suspension, engine, panels) are listed in
HARDPOINTS so the tube chassis can provide the same names.
"""
from __future__ import annotations

from tools.vehicle.common.jb import Part
from . import dims as D

# (name, x, y, z, weight)  left side (x>0) or centre (x == 0)
FRONT = [
    # front end / radiator support
    ("fe1l", 0.450, -2.090, 0.300, 2.0), ("fe1", 0.0, -2.100, 0.290, 1.6),
    ("fe2l", 0.460, -2.060, 0.540, 1.6), ("fe2", 0.0, -2.080, 0.545, 1.4),
    # front rails / aprons / fender supports
    ("fr1l", 0.420, -1.800, 0.270, 2.6), ("fa1l", 0.690, -1.800, 0.500, 1.8), ("ft1l", 0.720, -1.800, 0.640, 1.6),
    ("fr2l", 0.420, -1.500, 0.250, 2.8), ("fa2l", 0.650, -1.500, 0.470, 2.0), ("ft2l", 0.740, -1.500, 0.700, 1.8),
    ("fr3l", 0.420, -1.180, 0.240, 3.2), ("fa3l", 0.620, -1.180, 0.500, 2.4), ("ft3l", 0.745, -1.180, 0.755, 2.0),
    ("fs1l", D.FS1[0], D.FS1[1], D.FS1[2], 3.2),
    # front crossmember (suspension + engine mounts)
    ("fc1l", 0.300, -1.240, 0.200, 3.0), ("fc2l", 0.390, -1.600, 0.215, 2.4), ("fc1", 0.0, -1.240, 0.205, 2.4),
    # firewall / cowl
    ("fw1l", 0.420, -0.880, 0.215, 3.0), ("fw1", 0.0, -0.880, 0.240, 2.4),
    ("fw2l", 0.600, -0.880, 0.500, 2.4), ("fw2", 0.0, -0.900, 0.540, 2.2),
    ("fw3l", 0.700, -0.860, 0.800, 2.0), ("fw4l", 0.360, -0.860, 0.820, 1.8), ("fw3", 0.0, -0.850, 0.825, 1.8),
    # hinge pillar (A-pillar base) + front sill end
    ("si0l", 0.780, -0.860, 0.180, 2.6), ("hp1l", 0.805, -0.860, 0.340, 2.4),
    ("hp2l", 0.815, -0.800, 0.620, 2.2), ("hp3l", 0.770, -0.760, 0.840, 2.0),
]
CABIN = [
    ("fl1", 0.0, -0.500, 0.250, 2.2), ("fl1l", 0.420, -0.500, 0.170, 2.4), ("si1l", 0.790, -0.500, 0.175, 2.6),
    ("fl2", 0.0, -0.100, 0.265, 2.2), ("fl2l", 0.420, -0.100, 0.165, 2.4), ("si2l", 0.790, -0.100, 0.175, 2.6),
    ("fl3", 0.0, 0.300, 0.265, 2.2), ("fl3l", 0.420, 0.300, 0.165, 2.4), ("si3l", 0.790, 0.300, 0.175, 2.6),
    ("fl4", 0.0, 0.640, 0.255, 2.2), ("fl4l", 0.420, 0.640, 0.170, 2.4), ("si4l", 0.790, 0.640, 0.175, 2.6),
    # B-pillar
    ("bp1l", 0.815, 0.660, 0.400, 2.2), ("bp2l", 0.815, 0.660, 0.660, 2.0), ("bp3l", 0.760, 0.660, 0.895, 1.8),
    # A-pillar and roof
    ("ap1l", 0.665, -0.420, 1.050, 1.6),
    ("rf1l", 0.545, -0.130, 1.195, 1.6), ("rf1", 0.0, -0.130, 1.215, 1.4),
    ("rf2l", 0.530, 0.300, 1.222, 1.5), ("rf2", 0.0, 0.300, 1.272, 1.3),
    ("rf3l", 0.522, 0.660, 1.212, 1.6), ("rf3", 0.0, 0.660, 1.258, 1.3),
    ("rf4l", 0.500, 0.860, 1.180, 1.6), ("rf4", 0.0, 0.860, 1.222, 1.4),
]
REAR = [
    ("fl5", 0.0, 0.980, 0.300, 2.2), ("fl5l", 0.420, 0.980, 0.230, 2.4), ("si5l", 0.780, 0.900, 0.180, 2.6),
    ("qp1l", 0.825, 0.860, 0.420, 2.0), ("qp2l", 0.830, 0.950, 0.680, 2.0), ("qp3l", 0.760, 0.950, 0.915, 1.8),
    ("cp1l", 0.630, 1.000, 1.060, 1.6),
    ("rr1l", 0.420, 1.250, 0.330, 3.0), ("fl6", 0.0, 1.250, 0.340, 2.2),
    ("rt1l", D.RS1[0], D.RS1[1], D.RS1[2], 3.0),
    ("qp4l", 0.835, 1.250, 0.720, 2.0), ("qp5l", 0.755, 1.250, 0.930, 1.8), ("cp2l", 0.555, 1.300, 1.070, 1.6),
    ("rr2l", 0.420, 1.620, 0.280, 2.6), ("fl7", 0.0, 1.620, 0.240, 2.2),
    ("si6l", 0.780, 1.650, 0.300, 2.2), ("qp6l", 0.815, 1.620, 0.500, 2.0), ("qp7l", 0.810, 1.620, 0.710, 1.9),
    ("qp8l", 0.735, 1.620, 0.940, 1.8), ("cp3l", 0.560, 1.650, 0.995, 1.6),
    ("rr3l", 0.420, 1.950, 0.285, 2.4), ("fl8", 0.0, 1.950, 0.265, 2.0),
    ("tp1l", 0.730, 1.950, 0.450, 1.9), ("tp2l", 0.765, 1.950, 0.700, 1.8), ("tp3l", 0.700, 1.950, 0.930, 1.7),
    ("tl1l", 0.450, 2.180, 0.320, 2.0), ("tl1", 0.0, 2.180, 0.300, 1.8),
    ("tl2l", 0.620, 2.200, 0.560, 1.8), ("tl2", 0.0, 2.215, 0.560, 1.6),
    ("tl3l", 0.620, 2.195, 0.880, 1.6), ("tl3", 0.0, 2.210, 0.890, 1.5),
    # rear subframe mounts (body side)
    ("rm1l", 0.420, 1.050, 0.250, 2.4), ("rm2l", 0.420, 1.420, 0.300, 2.4),
]

HARDPOINTS = ["fs1l", "fc1l", "fc2l", "fc1", "fw1", "fw1l", "fr3l", "rt1l", "rm1l", "rm2l", "fl4", "fl5",
              "rr1l", "fe1l", "fe2l", "fe2", "tl1l", "tl2l", "tl2", "tl3l", "tl3", "rf4l", "rf4"]


def mir(name: str) -> str:
    """Swap the side suffix: ...l <-> ...r (ll <-> rr)."""
    if name.endswith("ll"):
        return name[:-2] + "rr"
    if name.endswith("rr"):
        return name[:-2] + "ll"
    if name.endswith("l"):
        return name[:-1] + "r"
    if name.endswith("r"):
        return name[:-1] + "l"
    return name


def is_center(name):
    return not (name.endswith("l") or name.endswith("r"))


def all_nodes():
    out = {}
    for tbl in (FRONT, CABIN, REAR):
        for n, x, y, z, w in tbl:
            out[n] = ((x, y, z), w)
            if x != 0.0:
                out[mir(n)] = ((-x, y, z), w)
    return out


def _lr(pairs):
    """Expand beam pairs written for the left side to left+right (dedup centre beams)."""
    out, seen = [], set()
    for a, b in pairs:
        for p in ((a, b), (mir(a), mir(b))):
            key = tuple(sorted(p))
            if key not in seen:
                seen.add(key)
                out.append(p)
    return out


# --- beam groups (written for the left side + centre) ------------------------------
FRONT_RAILS = [("fe1l", "fr1l"), ("fr1l", "fr2l"), ("fr2l", "fr3l"), ("fr3l", "fw1l"),
               ("fe1l", "fe1"), ("fe1l", "fe2l"), ("fe2l", "fe2"), ("fe1", "fe2"), ("fe1l", "fe2"), ("fe2l", "fe1"),
               ("fe1l", "fr1r"), ("fe1l", "fr1l")]
FRONT_APRON = [("fe2l", "fa1l"), ("fe2l", "ft1l"), ("fe1l", "fa1l"),
               ("fa1l", "fa2l"), ("fa2l", "fa3l"), ("fa3l", "fw2l"),
               ("ft1l", "ft2l"), ("ft2l", "ft3l"), ("ft3l", "fw3l"), ("ft3l", "hp3l"),
               ("fr1l", "fa1l"), ("fr2l", "fa2l"), ("fr3l", "fa3l"),
               ("fa1l", "ft1l"), ("fa2l", "ft2l"), ("fa3l", "ft3l"),
               ("fr1l", "fa2l"), ("fr2l", "fa1l"), ("fr2l", "fa3l"), ("fr3l", "fa2l"),
               ("fa1l", "ft2l"), ("fa2l", "ft1l"), ("fa2l", "ft3l"), ("fa3l", "ft2l"),
               ("fr1l", "ft1l"), ("fr2l", "ft2l"), ("fr3l", "ft3l"),
               ("fa3l", "fw3l"), ("ft3l", "fw2l"), ("fr3l", "fw2l"), ("fa3l", "fw1l"),
               ("fe2l", "ft2l"), ("fe1l", "fa2l")]
STRUT_TOWER = [("fs1l", "fa3l"), ("fs1l", "ft3l"), ("fs1l", "ft2l"), ("fs1l", "fa2l"), ("fs1l", "fw2l"),
               ("fs1l", "fw3l"), ("fs1l", "fw4l"), ("fs1l", "fr3l"), ("fs1l", "fw1l")]
CROSSMEMBER = [("fc1l", "fc1"), ("fc1l", "fr3l"), ("fc1l", "fr2l"), ("fc1l", "fa3l"), ("fc1", "fr3l"),
               ("fc1", "fr2l"), ("fc2l", "fr1l"), ("fc2l", "fr2l"), ("fc2l", "fa1l"), ("fc2l", "fc1l"),
               ("fc2l", "fc1"), ("fc1l", "fw1l"), ("fc1", "fw1"), ("fc2l", "fe1l"), ("fc1", "fc1r")]
FIREWALL = [("fw1l", "fw1"), ("fw2l", "fw2"), ("fw3l", "fw4l"), ("fw4l", "fw3"),
            ("fw1l", "fw2l"), ("fw2l", "fw3l"), ("fw1", "fw2"), ("fw2", "fw3"), ("fw2l", "fw4l"),
            ("fw1l", "fw2"), ("fw1", "fw2l"), ("fw2", "fw4l"), ("fw2l", "fw3"), ("fw2l", "fw4l"),
            ("fw3l", "hp3l"), ("fw2l", "hp2l"), ("fw1l", "si0l"), ("fw1l", "hp1l"), ("fw2l", "hp1l"),
            ("fw3l", "hp2l"), ("fw2l", "hp3l"), ("fw4l", "hp3l"), ("fw3l", "fw2"),
            ("si0l", "hp1l"), ("hp1l", "hp2l"), ("hp2l", "hp3l"), ("si0l", "hp2l"), ("hp1l", "hp3l"),
            ("fw3", "fw4l"), ("fr3l", "fw1"), ("fw1l", "fw1")]
FLOOR = [("fw1l", "fl1l"), ("fl1l", "fl2l"), ("fl2l", "fl3l"), ("fl3l", "fl4l"), ("fl4l", "fl5l"),
         ("fw1", "fl1"), ("fl1", "fl2"), ("fl2", "fl3"), ("fl3", "fl4"), ("fl4", "fl5"),
         ("si0l", "si1l"), ("si1l", "si2l"), ("si2l", "si3l"), ("si3l", "si4l"), ("si4l", "si5l"),
         ("fl1", "fl1l"), ("fl2", "fl2l"), ("fl3", "fl3l"), ("fl4", "fl4l"), ("fl5", "fl5l"),
         ("fl1l", "si1l"), ("fl2l", "si2l"), ("fl3l", "si3l"), ("fl4l", "si4l"), ("fl5l", "si5l"),
         ("fw1l", "si0l"),
         # shear diagonals
         ("fw1l", "fl1"), ("fw1", "fl1l"), ("fl1l", "fl2"), ("fl1", "fl2l"), ("fl2l", "fl3"), ("fl2", "fl3l"),
         ("fl3l", "fl4"), ("fl3", "fl4l"), ("fl4l", "fl5"), ("fl4", "fl5l"),
         ("fw1l", "si1l"), ("si0l", "fl1l"), ("fl1l", "si2l"), ("si1l", "fl2l"), ("fl2l", "si3l"), ("si2l", "fl3l"),
         ("fl3l", "si4l"), ("si3l", "fl4l"), ("fl4l", "si5l"), ("si4l", "fl5l")]
PILLARS = [  # A pillar, B pillar, roof
    ("hp3l", "ap1l"), ("ap1l", "rf1l"), ("hp2l", "ap1l"), ("fw3l", "ap1l"), ("fw4l", "ap1l"),
    ("rf1l", "rf2l"), ("rf2l", "rf3l"), ("rf3l", "rf4l"),
    ("rf1", "rf2"), ("rf2", "rf3"), ("rf3", "rf4"),
    ("rf1l", "rf1"), ("rf2l", "rf2"), ("rf3l", "rf3"), ("rf4l", "rf4"),
    ("rf1l", "rf2"), ("rf1", "rf2l"), ("rf2l", "rf3"), ("rf2", "rf3l"), ("rf3l", "rf4"), ("rf3", "rf4l"),
    ("si4l", "bp1l"), ("bp1l", "bp2l"), ("bp2l", "bp3l"), ("bp3l", "rf3l"), ("bp2l", "rf3l"),
    ("si4l", "bp2l"), ("bp1l", "bp3l"), ("fl4l", "bp1l"), ("fl4l", "bp2l"), ("si3l", "bp1l"), ("si5l", "bp1l"),
    ("bp3l", "rf2l"), ("bp3l", "rf4l"),
    # cabin box: floor <-> roof diagonals through the pillars (rigidity)
    ("hp3l", "rf1l"), ("hp2l", "rf1l"), ("fw3l", "rf1l"), ("fw3l", "rf1"), ("ap1l", "rf1"),
    ("fw4l", "rf1l"),
    ("bp2l", "rf3"), ("fl4l", "rf3l"), ("bp3l", "fl4"),
]
REAR_BODY = [
    ("si5l", "qp1l"), ("qp1l", "qp2l"), ("qp2l", "qp3l"), ("qp3l", "cp1l"), ("cp1l", "rf4l"), ("bp3l", "qp3l"),
    ("bp2l", "qp2l"), ("bp1l", "qp1l"), ("bp2l", "qp1l"), ("bp1l", "qp2l"), ("bp3l", "qp2l"), ("bp2l", "qp3l"),
    ("qp3l", "rf4l"), ("cp1l", "rf3l"), ("bp3l", "cp1l"), ("qp2l", "cp1l"),
    ("fl5l", "qp1l"), ("si5l", "fl5l"), ("fl5l", "rm1l"), ("si5l", "rm1l"), ("rm1l", "fl4l"), ("rm1l", "fl5"),
    ("rm1l", "rr1l"), ("rm1l", "qp1l"), ("rm2l", "rr1l"), ("rm2l", "rr2l"), ("rm2l", "fl6"), ("rm2l", "fl7"),
    ("fl5l", "rr1l"), ("fl5", "fl6"), ("fl5", "rr1l"), ("fl6", "rr1l"), ("fl5l", "fl6"),
    ("rr1l", "rr2l"), ("rr2l", "rr3l"), ("fl6", "fl7"), ("fl7", "fl8"), ("fl7", "rr2l"), ("fl8", "rr3l"),
    ("fl6", "rr2l"), ("fl7", "rr1l"), ("fl7", "rr3l"), ("fl8", "rr2l"),
    ("rt1l", "rr1l"), ("rt1l", "qp4l"), ("rt1l", "qp5l"), ("rt1l", "qp2l"), ("rt1l", "qp7l"), ("rt1l", "rm2l"),
    ("rt1l", "rm1l"), ("rt1l", "cp2l"), ("rt1l", "fl6"), ("rt1l", "qp3l"), ("rt1l", "qp8l"),
    ("qp2l", "qp4l"), ("qp4l", "qp7l"), ("qp3l", "qp5l"), ("qp5l", "qp8l"), ("cp1l", "cp2l"), ("cp2l", "cp3l"),
    ("qp4l", "qp5l"), ("qp5l", "cp2l"), ("qp7l", "qp8l"), ("qp8l", "cp3l"), ("qp2l", "qp5l"), ("qp3l", "qp4l"),
    ("qp4l", "qp8l"), ("qp5l", "qp7l"), ("qp3l", "cp2l"), ("qp5l", "cp1l"), ("cp2l", "qp8l"), ("cp3l", "qp5l"),
    ("rf4l", "cp2l"), ("cp1l", "rf4"),
    ("si6l", "qp6l"), ("qp6l", "qp7l"), ("si6l", "rr2l"), ("qp6l", "rr2l"), ("si6l", "qp7l"), ("qp6l", "qp4l"),
    ("rr2l", "qp7l"), ("rm2l", "qp6l"), ("rm2l", "si6l"),
    ("rr3l", "tp1l"), ("tp1l", "tp2l"), ("tp2l", "tp3l"), ("si6l", "tp1l"), ("qp6l", "tp1l"), ("qp7l", "tp2l"),
    ("qp8l", "tp3l"), ("cp3l", "tp3l"), ("qp6l", "tp2l"), ("qp7l", "tp1l"), ("qp7l", "tp3l"), ("qp8l", "tp2l"),
    ("rr3l", "si6l"), ("rr3l", "tp2l"),
    ("rr3l", "tl1l"), ("fl8", "tl1"), ("tl1l", "tl1"), ("tp1l", "tl1l"), ("tp1l", "tl2l"), ("tp2l", "tl2l"),
    ("tp2l", "tl3l"), ("tp3l", "tl3l"), ("tl1l", "tl2l"), ("tl2l", "tl3l"), ("tl1", "tl2"), ("tl2", "tl3"),
    ("tl2l", "tl2"), ("tl3l", "tl3"), ("tl1l", "tl2"), ("tl2l", "tl1"), ("tl2l", "tl3"), ("tl3l", "tl2"),
    ("rr3l", "tl1"), ("fl8", "tl1l"), ("tp3l", "tl2l"), ("tp1l", "tl1"),
    ("cp3l", "tl3l"), ("cp3l", "tp2l"),
    # shelf / rear crossmember tying the quarters together
    ("cp2l", "cp2r"), ("qp5l", "qp5r"), ("cp3l", "cp3r"), ("rt1l", "rt1r"),
    ("cp2l", "cp3r"), ("cp3l", "cp2r"), ("tp3l", "tl3"),
]
EXTRA_BRACES = [
    # radiator support centre out-of-plane bracing
    ("fe1", "fr1l"), ("fe2", "fr1l"), ("fe1", "fc2l"), ("fe2", "fa1l"), ("fe2", "ft1l"),
    # sills: tie mid-sill nodes to the pillars and tunnel (box section)
    ("si1l", "hp1l"), ("si2l", "hp1l"), ("si2l", "bp1l"), ("si3l", "bp1l"), ("si1l", "hp2l"), ("si3l", "bp2l"),
    ("si1l", "fl2"), ("si2l", "fl1"), ("si2l", "fl3"), ("si3l", "fl2"), ("si3l", "fl4"),
    ("fl1l", "fl2r"), ("fl2l", "fl3r"), ("fl3l", "fl4r"),
    # windshield frame / A-pillars
    ("rf1l", "fw4r"), ("rf1", "fw3"), ("ap1l", "fw2l"), ("ap1l", "rf2l"), ("rf1l", "hp3r"),
    ("rf2l", "ap1l"), ("rf1l", "rf2r"), ("rf2l", "rf3r"), ("rf3l", "rf4r"),
    ("fc1", "fa3l"), ("fc1", "fa2l"), ("tl2", "tp1l"), ("tl2", "rr3l"), ("tl3", "tp2l"), ("fl8", "tp1l"),
    ("ap1l", "hp1l"), ("ap1l", "rf1r"),
]
CABIN_X = [  # left-right ties across the cabin (written once, both directions present)
    ("hp3l", "hp3r"), ("fw3l", "fw4l"), ("bp3l", "bp3r"), ("bp2l", "bp2r"),
    ("ap1l", "ap1r"), ("si4l", "fl4"), ("bp1l", "fl4"), ("qp3l", "qp3r"),
    ("rf1l", "rf1"),
]


_EMITTED = set()


def _beam_set(groups):
    """Mirror + dedupe (also against beams already emitted in this part)."""
    pairs = []
    for g in groups:
        pairs += g
    out = []
    for a, b in _lr(pairs):
        k = tuple(sorted((a, b)))
        if k in _EMITTED:
            continue
        _EMITTED.add(k)
        out.append((a, b))
    return out


def unibody_hatch() -> Part:
    _EMITTED.clear()
    p = Part("s13_body_hatch", "Unibody (Hatchback)", "s13_body", value=5200)
    nodes = all_nodes()
    p.nodes_props(selfCollision=True, collision=True, nodeMaterial="|NM_METAL", frictionCoef=0.5, group="s13_body")
    # emit nodes grouped by weight to keep the file readable
    for name, (pos, w) in nodes.items():
        p.node(name, *pos, nodeWeight=w)
    p.nodes_props(group="")

    p.beams_props(deformLimitExpansion=1.2)
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    # crumple zone ahead of the strut towers
    p.beam_comment("front crumple zone")
    p.beams_props(beamSpring=1501000, beamDamp=120, beamDeform=32000, beamStrength="FLT_MAX")
    for a, b in _beam_set([FRONT_RAILS, FRONT_APRON]):
        p.beam(a, b)
    p.beam_comment("strut towers, crossmember")
    p.beams_props(beamSpring=2001000, beamDamp=150, beamDeform=70000, beamStrength="FLT_MAX")
    for a, b in _beam_set([STRUT_TOWER, CROSSMEMBER]):
        p.beam(a, b)
    p.beam_comment("firewall, floor, sills")
    p.beams_props(beamSpring=2501000, beamDamp=150, beamDeform=95000, beamStrength="FLT_MAX")
    for a, b in _beam_set([FIREWALL, FLOOR]):
        p.beam(a, b)
    p.beam_comment("pillars and roof")
    p.beams_props(beamSpring=1801000, beamDamp=120, beamDeform=48000, beamStrength="FLT_MAX")
    for a, b in _beam_set([PILLARS, CABIN_X, EXTRA_BRACES]):
        p.beam(a, b)
    p.beam_comment("rear structure")
    p.beams_props(beamSpring=1801000, beamDamp=120, beamDeform=42000, beamStrength="FLT_MAX")
    for a, b in _beam_set([REAR_BODY]):
        p.beam(a, b)
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(deformLimitExpansion=1.2)
    return p, nodes
