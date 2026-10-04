"""Assemble and write the s14_240sx vehicle (JBeam).

The S14 keeps the S13 architecture, so most parts are the S13 coupe generators run through
`retarget`: node / prop / camera / flexbody positions go through the S13 -> S14 warp
(tools/vehicle/s14/warp.py), panel nodes are snapped onto the S14 skin, and every name is
re-prefixed s13_ -> s14_.  Wheels, suspension and powertrain come from the shared catalogue
with the S14 hard points.  S14-only parts (fixed headlamps, zenki/kouki tail lamps, licence
plates) are written here directly in S14 coordinates.
"""
from __future__ import annotations

import copy
import os
import re
from collections import OrderedDict

import numpy as np

from tools.jbeam import dumps
from tools.model.shape import side_x, top_z
from tools.vehicle.common.jb import Part
from tools.vehicle.s13 import catalog as C
from tools.vehicle.s13 import panels_jb as PJ
from tools.vehicle.s13 import race as RACE
from tools.vehicle.s13 import vehicle as V13
from . import body_spec as B
from . import dims as D
from . import panel_spec as S
from .warp import warp

VEH = "s14_240sx"
PFX = "s14"
TITLE = "240SX (S14)"
SPEC = B.s14_spec()

# S14 wing: on the shorter deck (S13 coordinates, warped with everything else)
WING_S14 = dict(y_le=1.843, foot=(1.938, 0.912))


# ---------------------------------------------------------------------------
# retargeting
# ---------------------------------------------------------------------------
class Built:
    """A finished part dict (what Part.build() returns) with its name."""

    def __init__(self, name, d):
        self.name, self.d = name, d

    def build(self):
        return self.d


def _rename(o):
    if isinstance(o, str):
        return o.replace("s13_", "s14_").replace("s13sl", "s14sl")
    if isinstance(o, list):
        return [_rename(v) for v in o]
    if isinstance(o, dict):
        return OrderedDict((_rename(k), _rename(v)) for k, v in o.items())
    return o


def rear_y(x, z, y0=1.90, y1=2.32):
    """y of the S14 tail surface (deck rolling into the raked rear face) at height z."""
    ys = np.linspace(y0, y1, 85)
    zs = [top_z(SPEC, float(yy), abs(x)) for yy in ys]
    for a, b, za, zb in zip(ys, ys[1:], zs, zs[1:]):
        if za >= z >= zb:
            return float(a + (b - a) * (za - z) / max(za - zb, 1e-9))
    return None


def _w_y(x, front=True):
    """y where the S14 plan outline reaches half width x (front or rear end)."""
    from tools.model.shape import Guide
    g = Guide(B.W_MAX)
    ys = np.linspace(B.Y_FRONT, -1.6, 120) if front else np.linspace(B.Y_REAR, 1.8, 120)
    for yy in ys:
        if float(g(float(yy))) >= x:
            return float(yy)
    return float(ys[-1])


def _snap(name, group, x, y, z):
    s = 1.0 if x >= 0 else -1.0
    if group == "s13_hood":
        return x, y, top_z(SPEC, y, abs(x)) - 0.012
    if group == "s13_trunk":
        if re.match(r"tk[34]", name):
            ry = rear_y(x, z)
            return x, (ry - 0.012) if ry else y, z
        return x, y, top_z(SPEC, y, abs(x)) - 0.012
    if group.startswith("s13_door_") and re.match(r"dr[1-9][lr]$", name):
        y = min(y, 0.515)                     # the S14 door ends a little earlier than the S13's
        return s * (side_x(SPEC, y, z) - 0.03), y, z
    if group == "s13_bumper_F" and name != "bf0":
        y = max(y, _w_y(abs(x), front=True) + 0.015)
        if abs(x) > 0.55:
            x = s * min(abs(x), side_x(SPEC, y, max(z, 0.25)) - 0.012)
        return x, y, z
    if group == "s13_bumper_R" and name != "br0":
        y = min(y, _w_y(abs(x), front=False) - 0.015)
        if abs(x) > 0.55:
            x = s * min(abs(x), side_x(SPEC, y, max(z, 0.30)) - 0.012)
        return x, y, z
    if group.startswith("s13_fender_"):
        if re.match(r"fd[1-4][lr]$", name):
            return x, y, top_z(SPEC, y, abs(x)) - 0.010
        if re.match(r"fd[5-9][lr]$", name):
            return s * (side_x(SPEC, y, z) - 0.010), y, z
    if group in ("s13_body", "") and name and not name.startswith(("ref", "dsh", "st", "rs1", "hv1", "cs1", "g", "sw", "pd")):
        if name in ("tl3", "tl3l", "tl3r"):
            ry = rear_y(x, z)
            if ry:
                y = min(y, ry - 0.03)
        if z > 0.5:
            z = min(z, top_z(SPEC, y, abs(x)) - 0.012)
        if 0.30 < z < 0.84 and abs(x) > 0.55:
            x = s * min(abs(x), side_x(SPEC, y, z) - 0.012)
    return x, y, z


def retarget(part, snap=True):
    d = copy.deepcopy(part.build())
    nodes = d.get("nodes")
    if nodes:
        group = ""
        for row in nodes[1:]:
            if isinstance(row, dict):
                if "group" in row:
                    group = row["group"] if isinstance(row["group"], str) else (row["group"][0] if row["group"] else "")
                continue
            if isinstance(row, list) and len(row) >= 4 and isinstance(row[1], (int, float)):
                x, y, z = warp(row[1], row[2], row[3])
                g = group
                if len(row) > 4 and isinstance(row[4], dict) and "group" in row[4]:
                    gg = row[4]["group"]
                    g = gg if isinstance(gg, str) else (gg[0] if gg else "")
                if snap:
                    x, y, z = _snap(row[0], g, x, y, z)
                row[1], row[2], row[3] = round(x, 4), round(y, 4), round(z, 4)
    for sec, key in (("props", "baseTranslationGlobal"), ("flexbodies", "pos")):
        for row in d.get(sec, [])[1:]:
            if isinstance(row, list) and row and isinstance(row[-1], dict):
                v = row[-1].get(key)
                if isinstance(v, dict) and all(isinstance(v.get(k), (int, float)) for k in "xyz"):
                    x, y, z = warp(v["x"], v["y"], v["z"])
                    v.update(x=round(x, 4), y=round(y, 4), z=round(z, 4))
    cams = d.get("camerasInternal")
    if cams:
        for row in cams[1:]:
            if isinstance(row, list) and len(row) > 4 and isinstance(row[1], (int, float)):
                row[1], row[2], row[3] = (round(v, 4) for v in warp(row[1], row[2], row[3]))
    return Built(_rename(part.name), _rename(d))


def _slots(b):
    return b.d.setdefault("slots", [["type", "default", "description"]])


def set_slot(b, slot, default, desc=None):
    for row in _slots(b)[1:]:
        if isinstance(row, list) and row[0] == slot:
            row[1] = default
            if desc:
                row[2] = desc
            return
    _slots(b).append([slot, default, desc or slot])


def drop_slot(b, slot):
    b.d["slots"] = [r for r in _slots(b) if not (isinstance(r, list) and r[0] == slot)]


def add_flexbody(b, mesh, groups):
    t = b.d.setdefault("flexbodies", [["mesh", "[group]:", "nonFlexMaterials"]])
    t.append([mesh, list(groups)])


def set_node(b, name, pos):
    for row in b.d.get("nodes", [])[1:]:
        if isinstance(row, list) and row and row[0] == name:
            row[1], row[2], row[3] = (round(v, 4) for v in pos)
            return
    raise KeyError(name)


# ---------------------------------------------------------------------------
# S14-only parts (S14 coordinates)
# ---------------------------------------------------------------------------
def _lamp_centre(outline):
    xs = [p[0] for p in outline]
    zs = [p[1] for p in outline]
    return (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2


def headlights(kind):
    title = {"zenki": "Zenki Headlights (1995-96)", "kouki": "Kouki Headlights (1997-98)"}[kind]
    p = Part(f"{PFX}_headlights_{kind}", title, f"{PFX}_headlights", value=420)
    for s in ("L", "R"):
        pass
    p.flex_props(deformGroup="headlight_break", deformMaterialBase="s14_glass_lens", deformMaterialDamaged="s14_glass_dmg")
    p.flexbody(f"{PFX}_headlights_{kind}", [f"{PFX}_body"])
    p.flex_props(deformGroup="")
    p.props_props(**PJ.HEADLIGHT_PROPS)
    cx, cz = _lamp_centre(S.HEADLIGHTS[kind])
    zero = {"x": 0, "y": 0, "z": 0}
    for sd, s in (("l", 1), ("r", -1)):
        xo = s * (cx + 0.10)
        xi = s * (cx - 0.05)
        yo = -2.04
        for func, x, rng, cd, outer in (("lowbeam", xo, 55, 9000, 110), ("highbeam", xi, 95, 16000, 80)):
            p.prop(func, "SPOTLIGHT", "fe2" + sd, "fe2", "fe1" + sd, zero, zero, zero, 0, 0, 0, 1,
                   baseTranslationGlobal={"x": round(x, 4), "y": yo, "z": round(cz, 4)},
                   baseRotationGlobal={"x": -1.5, "y": 0, "z": 0}, lightRange=rng, lightIntensityCd=cd,
                   lightOuterAngle=outer, flareScale=0.06, deformGroup="headlight_break")
    p.beams_props(deformGroup="headlight_break", deformationTriggerRatio=0.02)
    for a, b in (("fe2l", "ft1l"), ("fe2r", "ft1r"), ("fe2l", "fe1l"), ("fe2r", "fe1r")):
        p.beam(a, b, beamSpring=0, beamDamp=0, beamDeform=1500, beamStrength="FLT_MAX")
    p.beams_props(deformGroup="")
    return p


def _tail_props(p, ref, rows, rev_rows, group):
    p.props_props(lightInnerAngle=40, lightOuterAngle=90, lightColor={"r": 255, "g": 20, "b": 10, "a": 255},
                  flareName="vehicleBrakeLightFlare", lightCastShadows=False)
    zero = {"x": 0, "y": 0, "z": 0}
    for (sd, x, y, z) in rows:
        for func, rng, bright in (("lowhighbeam", 4, 0.25), ("brakelights", 8, 0.8)):
            p.prop(func, "POINTLIGHT", ref[0] + sd, ref[1], ref[2] + sd, zero, zero, zero, 0, 0, 0, 1,
                   baseTranslationGlobal={"x": round(x, 4), "y": round(y, 4), "z": z}, lightRange=rng,
                   lightIntensityLm=400 * bright, flareScale=0.04, deformGroup=group)
    for (sd, x, y, z) in rev_rows:
        p.prop("reverse", "POINTLIGHT", ref[0] + sd, ref[1], ref[2] + sd, zero, zero, zero, 0, 0, 0, 1,
               baseTranslationGlobal={"x": round(x, 4), "y": round(y, 4), "z": z}, lightRange=6, lightIntensityLm=250,
               lightColor={"r": 255, "g": 255, "b": 240, "a": 255}, flareName="vehicleReverseLightFlare",
               flareScale=0.03, deformGroup=group)


def taillights(kind):
    """Outer lamps on the quarter panels (the trunk lid carries the middle/inner lamps)."""
    title = {"zenki": "Zenki Tail Lights (Red / Amber)", "kouki": "Kouki Tail Lights (Smoked)"}[kind]
    p = Part(f"{PFX}_taillights_{kind}", title, f"{PFX}_taillights", value=300)
    base = "s14_lights_red" if kind == "zenki" else "s14_lights_red_smoked"
    p.flex_props(deformGroup="taillight_break", deformMaterialBase=base, deformMaterialDamaged=base + "_dmg")
    p.flexbody(f"{PFX}_taillights_{kind}", [f"{PFX}_body"])
    p.flex_props(deformGroup="")
    x = 0.71
    ry = rear_y(x, 0.81) or 2.17
    _tail_props(p, ("tl3", "tl3", "tl2"), [("l", x, ry + 0.01, 0.81), ("r", -x, ry + 0.01, 0.81)], [], "taillight_break")
    p.beams_props(deformGroup="taillight_break", deformationTriggerRatio=0.02)
    for a, b in (("tl3l", "tl2"), ("tl3r", "tl2"), ("tl3l", "tl3r")):
        p.beam(a, b, beamSpring=0, beamDamp=0, beamDeform=1000, beamStrength="FLT_MAX")
    p.beams_props(deformGroup="")
    return p


def taillights_inner(kind):
    title = {"zenki": "Zenki Trunk Lamps", "kouki": "Kouki Trunk Lamps (Smoked)"}[kind]
    p = Part(f"{PFX}_taillights_inner_{kind}", title, f"{PFX}_taillights_inner", value=200)
    base = "s14_lights_red" if kind == "zenki" else "s14_lights_red_smoked"
    p.flex_props(deformGroup="trunklamp_break", deformMaterialBase=base, deformMaterialDamaged=base + "_dmg")
    p.flexbody(f"{PFX}_taillights_inner_{kind}", [f"{PFX}_trunk"])
    p.flex_props(deformGroup="")
    rows, rev = [], []
    for sd, s in (("l", 1), ("r", -1)):
        x = 0.50
        rows.append((sd, s * x, (rear_y(x, 0.81) or 2.16) + 0.01, 0.81))
        xr = 0.34
        rev.append((sd, s * xr, (rear_y(xr, 0.80) or 2.16) + 0.01, 0.80))
    _tail_props(p, ("tk3", "tk3", "tk2"), rows, rev, "trunklamp_break")
    p.beams_props(deformGroup="trunklamp_break", deformationTriggerRatio=0.02)
    for a, b in (("tk3l", "tk4"), ("tk3r", "tk4"), ("tk3l", "tk3r")):
        p.beam(a, b, beamSpring=0, beamDamp=0, beamDeform=1000, beamStrength="FLT_MAX")
    p.beams_props(deformGroup="")
    return p


def licenseplates():
    out = []
    p = Part(f"{PFX}_licenseplate_F", "Front License Plate", f"{PFX}_licenseplate_F", value=0)
    yf = -2.262
    p.flexbody("licenseplate", [f"{PFX}_bumper_F"], pos={"x": 0.0, "y": yf, "z": 0.468}, rot={"x": 0, "y": 0, "z": 0},
               scale={"x": 1, "y": 1, "z": 1})
    out.append(p)
    p = Part(f"{PFX}_licenseplate_R", "Rear License Plate", f"{PFX}_licenseplate_R", value=0)
    yw = (rear_y(0.0, 0.47, 2.2, 2.33) or 2.29) - 0.008
    p.flexbody("licenseplate", [f"{PFX}_bumper_R"], pos={"x": 0.0, "y": round(yw, 4), "z": 0.525},
               rot={"x": 0, "y": 0, "z": 180}, scale={"x": 1, "y": 1, "z": 1})
    out.append(p)
    return out


# ---------------------------------------------------------------------------
# vehicle
# ---------------------------------------------------------------------------
def main_part():
    b = retarget(V13.main_part(), snap=False)
    b.name = VEH
    b.d["information"]["name"] = "Nissan 240SX (S14)"
    set_slot(b, f"{PFX}_body", f"{PFX}_body_coupe")
    lm = lambda base: {"off": base, "on": base + "_on", "on_intense": base + "_on_intense"}  # noqa: E731
    g = b.d["glowMap"]
    g["s14_taillight_k"] = {"simpleFunction": {"tail_filament": 0.49, "brake_filament": 1}, **lm("s14_lights_red_smoked"),
                            "materialEmissiveScaling": {"on_max": 1}}
    for sd in ("L", "R"):
        g[f"s14_signal_{sd}_k"] = {"simpleFunction": {f"signal_{sd}_filament": 0.49}, **lm("s14_lights_clear_amber"),
                                   "materialEmissiveScaling": {"on_max": 0.49}}
    return b


# The S14 shell is about 60 kg heavier than the S13 coupe and markedly stiffer: scale the unibody's node
# weights and its beam springs/dampers by the same factor (unchanged node frequencies and damping ratios,
# so the explicit-integration stability margin is the same as the S13's).
BODY_SCALE = 1.13


def _scale_body(b, f):
    def props(row, n):
        if isinstance(row, dict):
            return row
        if isinstance(row, list) and len(row) > n and isinstance(row[-1], dict):
            return row[-1]
        return None
    for row in b.d.get("nodes", [])[1:]:
        d = props(row, 4)
        if d and isinstance(d.get("nodeWeight"), (int, float)) and not isinstance(d["nodeWeight"], bool):
            d["nodeWeight"] = round(d["nodeWeight"] * f, 3)
    for row in b.d.get("beams", [])[1:]:
        d = props(row, 2)
        if not d:
            continue
        for k in ("beamSpring", "beamDamp"):
            v = d.get(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
                d[k] = int(round(v * f)) if k == "beamSpring" else round(v * f, 2)


def body():
    b = retarget(V13.body("coupe"))
    b.d["information"]["name"] = "Unibody (S14 Coupe)"
    _scale_body(b, BODY_SCALE)
    for sd in ("L", "R"):
        drop_slot(b, f"{PFX}_popup_{sd}")
    set_slot(b, f"{PFX}_hood", f"{PFX}_hood_zenki")
    set_slot(b, f"{PFX}_bumper_F", f"{PFX}_bumper_F_zenki")
    set_slot(b, f"{PFX}_taillights", f"{PFX}_taillights_zenki")
    set_slot(b, f"{PFX}_headlights", f"{PFX}_headlights_zenki", "Headlights")
    add_flexbody(b, f"{PFX}_grille", [f"{PFX}_body"])
    return b


def trunk_parts():
    out = []
    for p in (PJ.trunk(), PJ.trunk(name="s13_trunk_light", mesh="s13_trunk_carbon", title="Carbon Fiber Trunk Lid", value=1500,
                                   mass=6.0).scale_springs(6.0 / 16.0)):
        b = retarget(p)
        set_slot(b, f"{PFX}_taillights_inner", f"{PFX}_taillights_inner_zenki", "Trunk Lamps")
        # S14 deck is shorter and the tail raked: rear deck row further forward, lower face row at the lamp bottoms
        for row in b.d["nodes"][1:]:
            if not (isinstance(row, list) and isinstance(row[1], (int, float))):
                continue
            nm, x = row[0], row[1]
            if nm.startswith("tk2"):
                row[2], row[3] = 1.960, round(top_z(SPEC, 1.96, abs(x)) - 0.012, 4)
            elif nm.startswith("tk4"):
                row[3] = 0.768
                row[2] = round((rear_y(x, 0.768) or row[2]) - 0.012, 4)
        out.append(b)
    for p in PJ.trunk_spoilers():
        b = retarget(p)
        for row in b.d.get("props", [])[1:]:
            if isinstance(row, list) and isinstance(row[-1], dict) and "baseTranslationGlobal" in row[-1]:
                row[-1]["baseTranslationGlobal"] = {"x": 0.0, "y": 2.142, "z": 1.018}
        out.append(b)
    return out


def all_files():
    saved = dict(RACE.WING)
    RACE.WING.update(WING_S14)
    try:
        files = OrderedDict()
        files[f"{VEH}.jbeam"] = [main_part()]
        files[f"{PFX}_body.jbeam"] = [body(), retarget(V13.headliners()[1])]
        panels = [PJ.hood(name="s13_hood_zenki", title="Stock Hood (Zenki)", mesh="s13_hood_zenki"),
                  PJ.hood(name="s13_hood_kouki", title="Stock Hood (Kouki)", mesh="s13_hood_kouki", value=420),
                  PJ.fender("L"), PJ.fender("R"), PJ.door("L"), PJ.door("R"),
                  PJ.bumper_front(name="s13_bumper_F_zenki", mesh="s13_bumper_F_zenki", title="Stock Front Bumper (Zenki)"),
                  PJ.bumper_front(name="s13_bumper_F_kouki", mesh="s13_bumper_F_kouki", title="Stock Front Bumper (Kouki)",
                                  value=380),
                  PJ.bumper_rear(),
                  PJ.bumper_rear(name="s13_bumper_R_aero", mesh="s13_bumper_R_aero", title="Rear Bumper with Aero Valance",
                                 value=460, mass=9.2)] + PJ.mirrors()
        for kind, title in (("zenki", "Zenki"), ("kouki", "Kouki")):
            panels += [PJ.bumper_front(name=f"s13_bumper_F_{kind}_aero", mesh=f"s13_bumper_F_{kind}_aero",
                                       title=f"{title} Front Bumper with Aero Lip", value=560, mass=10.8),
                       PJ.bumper_front(name=f"s13_bumper_F_{kind}_carbon", mesh=f"s13_bumper_F_{kind}_carbon",
                                       title=f"{title} Front Bumper with Carbon Lip", value=980, mass=10.6)]
        files[f"{PFX}_panels.jbeam"] = ([retarget(p) for p in panels] + trunk_parts()
                                        + [headlights(k) for k in ("zenki", "kouki")]
                                        + [taillights(k) for k in ("zenki", "kouki")]
                                        + [taillights_inner(k) for k in ("zenki", "kouki")])
        interiors = [V13.interior_stock(),
                     V13.interior_stock("leather", "Leather Interior (LE)", 1600, seats="s13_seats_leather",
                                        rear="s13_rearseat_leather"),
                     V13.interior_stock("stripped", "Stripped Interior (Bucket Seats)", 400, seats="s13_seats_bucket",
                                        kind="stripped", wheel="s13_steering_wheel_deepdish"),
                     V13.interior_stock("race", "Race Interior (Carbon Dash, Single Seat)", 2600, kind="race")]
        files[f"{PFX}_interior.jbeam"] = [retarget(p) for p in interiors + V13.steering_wheels() + V13.shifters()
                                          + V13.handbrakes()]
        files[f"{PFX}_suspension.jbeam"] = C.suspension_parts(PFX, D, default_wheel="oem15_s14")
        files[f"{PFX}_wheels.jbeam"] = C.wheel_parts(PFX, D)
        files[f"{PFX}_powertrain.jbeam"] = C.powertrain_parts(pfx=PFX, dims=D)
        misc = [V13.fueltank(), V13.exhaust(),
                V13.exhaust("race", "Race Exhaust (3\" Straight Through)", 1400, muffling=0.12, gain=3, afterfire=1.0,
                            mesh="s13_exhaust_race"),
                V13.radiator(), V13.radiator("race", "Race Aluminium Radiator", 900, mesh="s13_radiator")]
        files[f"{PFX}_misc.jbeam"] = licenseplates() + [retarget(p) for p in misc]
        files[f"{PFX}_skins.jbeam"] = [retarget(p) for p in V13.skins()]
        light = [p for p in RACE.light_panels() if p.name in (
            "s13_hood_vented", "s13_hood_carbon", "s13_door_light_L", "s13_door_light_R", "s13_fender_wide_L",
            "s13_fender_wide_R")]
        race = (RACE.rollcages() + light
                + [RACE.splitter(), RACE.canards(), RACE.wing_gt(), RACE.diffuser(), RACE.overfenders_R(), RACE.sideskirts(),
                   RACE.fuelcell("racecell", "40L Race Fuel Cell", 40, 1200, "s13_fuelcell"),
                   RACE.fuelcell("dragcell", "10L Drag Fuel Cell", 10, 600, "s13_fuelcell_drag")]
                + RACE.electronics())
        files[f"{PFX}_race.jbeam"] = [retarget(p) for p in race]
    finally:
        RACE.WING.clear()
        RACE.WING.update(saved)
    return files


def write(out_dir):
    vdir = os.path.join(out_dir, "vehicles", VEH)
    os.makedirs(vdir, exist_ok=True)
    names = set()
    for fn, parts in all_files().items():
        d = OrderedDict()
        for p in parts:
            if p.name in names:
                raise ValueError(f"duplicate part {p.name}")
            names.add(p.name)
            d[p.name] = p.build()
        with open(os.path.join(vdir, fn), "w", encoding="utf-8", newline="\n") as f:
            f.write(dumps(d, header_comment=f"{TITLE} - generated by tools/vehicle/s14 (do not edit by hand; edit the generator)"))
    return vdir
