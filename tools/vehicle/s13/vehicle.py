"""Assemble and write the s13_240sx vehicle (JBeam, configs, info files)."""
from __future__ import annotations

import json
import os
from collections import OrderedDict

from tools.jbeam import dumps, dumps_json
from tools.vehicle.common.jb import Part
from . import catalog as C
from . import dims as D
from . import panels_jb as PJ
from . import structure as ST
from . import race as RACE

VEH = "s13_240sx"
PFX = "s13"
TITLE = "240SX (S13)"


# ---------------------------------------------------------------------------
# main part
# ---------------------------------------------------------------------------
def main_part():
    p = Part(VEH, "Nissan 240SX (S13)", "main", value=9000)
    p.slot(f"{PFX}_body", f"{PFX}_body_hatch", "Body", coreSlot=True)
    p.slot(f"{PFX}_engine", f"{PFX}_engine_ka24de", "Engine")
    p.slot(f"{PFX}_suspension_F", f"{PFX}_suspension_F", "Front Suspension", coreSlot=True)
    p.slot(f"{PFX}_suspension_R", f"{PFX}_suspension_R", "Rear Suspension", coreSlot=True)
    p.slot(f"{PFX}_fueltank", f"{PFX}_fueltank_stock", "Fuel Tank")
    p.slot(f"{PFX}_exhaust", f"{PFX}_exhaust_stock", "Exhaust")
    p.slot(f"{PFX}_radiator", f"{PFX}_radiator_stock", "Radiator")
    p.slot(f"{PFX}_electronics", f"{PFX}_electronics_none", "Race Electronics")
    p.slot(f"{PFX}_handbrake", f"{PFX}_handbrake_stock", "Handbrake", coreSlot=True)
    p.slot("paint_design", "", "Paint Design")
    p.slot("licenseplate_design_2_1", "", "License Plate Design")
    p.slot(f"{PFX}_mod", "", "Additional Modification")
    p.controller("vehicleController")
    p.variable("$brakestrength", "", "Brakes", 1.0, 0.6, 1.0, "Brake Force", "Scales the overall brake torque",
               minDis=60, maxDis=100)
    p.variable("$brakebias", "", "Brakes", 0.66, 0.0, 1.0, "Front/Rear Bias", "Share of brake torque on the front wheels",
               minDis=0, maxDis=100)
    p.variable("$ffbstrength", "", "Chassis", 1.0, 0.5, 1.5, "Force Feedback", "Scales the force feedback strength",
               minDis=50, maxDis=150)
    p.set("components", {"electrics": {
        "customValues": [["electricsName", "electricsFunction"],
                         ["lowbeam_filament", "electrics.lowbeam * electrics.electricalLoadCoef"],
                         ["highbeam_filament", "electrics.highbeam * electrics.electricalLoadCoef"],
                         ["tail_filament", "electrics.lowhighbeam * electrics.electricalLoadCoef"],
                         ["brake_filament", "electrics.brakelights * electrics.electricalLoadCoef"],
                         ["reverse_filament", "electrics.reverse * electrics.electricalLoadCoef"],
                         ["signal_L_filament", "electrics.signal_L * electrics.electricalLoadCoef"],
                         ["signal_R_filament", "electrics.signal_R * electrics.electricalLoadCoef"]],
        "smoothers": [["electricsName", "smootherType", "params"],
                      ["lowbeam_filament", "temporalNonLinear", [10, 10]],
                      ["highbeam_filament", "temporalNonLinear", [10, 10]],
                      ["tail_filament", "temporalNonLinear", [10, 10]],
                      ["brake_filament", "temporalNonLinear", [12, 12]],
                      ["reverse_filament", "temporalNonLinear", [10, 10]],
                      ["signal_L_filament", "temporalNonLinear", [15, 15]],
                      ["signal_R_filament", "temporalNonLinear", [15, 15]]],
    }})
    lm = lambda base: {"off": base, "on": base + "_on", "on_intense": base + "_on_intense"}  # noqa: E731
    p.set("glowMap", {
        "s13_headlight": {"simpleFunction": {"lowbeam_filament": 0.49, "highbeam_filament": 1}, **lm("s13_lights"),
                          "materialEmissiveScaling": {"on_max": 1}},
        "s13_taillight": {"simpleFunction": {"tail_filament": 0.49, "brake_filament": 1}, **lm("s13_lights_red"),
                          "materialEmissiveScaling": {"on_max": 1}},
        "s13_reverselight": {"simpleFunction": {"reverse_filament": 0.49}, **lm("s13_lights_reverse"),
                             "materialEmissiveScaling": {"on_max": 0.49}},
        "s13_signal_L": {"simpleFunction": {"signal_L_filament": 0.49}, **lm("s13_lights_amber"),
                         "materialEmissiveScaling": {"on_max": 0.49}},
        "s13_signal_R": {"simpleFunction": {"signal_R_filament": 0.49}, **lm("s13_lights_amber"),
                         "materialEmissiveScaling": {"on_max": 0.49}},
        "s13_gaugeface": {"simpleFunction": {"lowhighbeam": 0.6}, "off": "s13_gauges", "on": "s13_gauges_on"},
        "s13_needle": {"simpleFunction": {"lowhighbeam": 0.6}, "off": "s13_needle_off", "on": "s13_needle_on"},
        "s13_sidemarker_F": {"simpleFunction": {"tail_filament": 0.49}, **lm("s13_lights_amber")},
        "s13_chmsl": {"simpleFunction": {"brake_filament": 1}, **lm("s13_lights_red")},
        "s13_sidemarker_R": {"simpleFunction": {"tail_filament": 0.49}, **lm("s13_lights_red")},
    })
    return p


# ---------------------------------------------------------------------------
# body (unibody hatch + glass + cameras)
# ---------------------------------------------------------------------------
REF = dict(ref=(0.0, 0.30, 0.30), back=(0.0, 0.80, 0.30), left=(0.40, 0.30, 0.30), up=(0.0, 0.30, 0.70))


BODY_INFO = {"hatch": "Unibody (Hatchback)", "coupe": "Unibody (Coupe)", "convertible": "Unibody (Convertible)"}


def body(kind="hatch"):
    p, nodes = ST.unibody(kind)
    p.d["information"]["name"] = BODY_INFO[kind]
    slots = [(f"{PFX}_hood", f"{PFX}_hood", "Hood"), (f"{PFX}_popup_L", f"{PFX}_popup_L", "Left Pop-up Headlight"),
             (f"{PFX}_popup_R", f"{PFX}_popup_R", "Right Pop-up Headlight"),
             (f"{PFX}_fender_L", f"{PFX}_fender_L", "Left Fender"), (f"{PFX}_fender_R", f"{PFX}_fender_R", "Right Fender")]
    dsfx = "_conv" if kind == "convertible" else ""
    slots += [(f"{PFX}_door_L", f"{PFX}_door{dsfx}_L", "Left Door"), (f"{PFX}_door_R", f"{PFX}_door{dsfx}_R", "Right Door")]
    if kind == "hatch":
        slots.append((f"{PFX}_hatch", f"{PFX}_hatch", "Hatch"))
    else:
        slots.append((f"{PFX}_trunk", f"{PFX}_trunk", "Trunk Lid"))
    slots += [(f"{PFX}_bumper_F", f"{PFX}_bumper_F", "Front Bumper"), (f"{PFX}_bumper_R", f"{PFX}_bumper_R", "Rear Bumper"),
              (f"{PFX}_taillights", f"{PFX}_taillights" if kind == "hatch" else f"{PFX}_taillights_coupe", "Tail Lights"),
              (f"{PFX}_interior", f"{PFX}_interior_stock", "Interior")]
    if kind == "convertible":
        slots.append((f"{PFX}_softtop", f"{PFX}_softtop_up", "Convertible Top"))
    else:
        slots.append((f"{PFX}_headliner", f"{PFX}_headliner" if kind == "hatch" else f"{PFX}_headliner_coupe", "Headliner"))
        slots.append((f"{PFX}_rollcage", f"{PFX}_rollcage_none", "Roll Cage"))
    for slot, default, desc in slots:
        p.slot(slot, default, desc)
    for slot, d_uni, d_tube, desc in RACE.AERO_SLOTS:
        p.slot(f"{PFX}_{slot}", f"{PFX}_{d_uni}" if d_uni else "", desc)
    p.flexbody(f"{PFX}_body_{kind}", [f"{PFX}_body"])
    p.flexbody(f"{PFX}_underbody", [f"{PFX}_body"])
    p.flexbody(f"{PFX}_wheelwells", [f"{PFX}_body"])
    p.flexbody(f"{PFX}_enginebay", [f"{PFX}_body"])
    if kind == "coupe":
        p.flexbody(f"{PFX}_parcelshelf", [f"{PFX}_body"])
    body_common(p, kind)
    return p


def body_hatch():
    return body("hatch")


def body_common(p, kind="hatch"):
    """Glass, reference nodes, cameras, glass-break triggers and collision skin shared by every body."""
    nodes = ST.all_nodes(kind)
    roof = kind != "convertible"
    p.flex_props(deformGroup="windshield_break", deformMaterialBase="s13_glass", deformMaterialDamaged="s13_glass_dmg")
    p.flexbody(f"{PFX}_windshield", [f"{PFX}_body"], deformSound="event:>Destruction>Vehicle>Glass>glassbreaksound4", deformVolume=0.8)
    p.flex_props(deformGroup="")
    p.flexbody(f"{PFX}_windshield_trim", [f"{PFX}_body"])
    if kind == "hatch":
        for s in ("L", "R"):
            p.flex_props(deformGroup=f"quarterglass_{s}_break", deformMaterialBase="s13_glass", deformMaterialDamaged="s13_glass_dmg")
            p.flexbody(f"{PFX}_quarterglass_{s}", [f"{PFX}_body"])
            p.flex_props(deformGroup="")
            p.flexbody(f"{PFX}_quarterglass_trim_{s}", [f"{PFX}_body"])
    elif kind == "coupe":
        for s in ("L", "R"):
            p.flex_props(deformGroup=f"quarterglass_{s}_break", deformMaterialBase="s13_glass", deformMaterialDamaged="s13_glass_dmg")
            p.flexbody(f"{PFX}_quarterglass_coupe_{s}", [f"{PFX}_body"])
        p.flex_props(deformGroup="rearwindow_break")
        p.flexbody(f"{PFX}_rearwindow", [f"{PFX}_body"], deformSound="event:>Destruction>Vehicle>Glass>glassbreaksound4",
                   deformVolume=0.7)
        p.flex_props(deformGroup="")
    # reference nodes (collision off) aligned exactly on the axes
    p.nodes_props(group="", collision=False, selfCollision=False, nodeWeight=1.0)
    for nm, key in (("ref", "ref"), ("refb", "back"), ("refl", "left"), ("refu", "up")):
        p.node(nm, *REF[key])
    p.nodes_props(collision=True, selfCollision=True)
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=1501000, beamDamp=100, beamDeform=80000, beamStrength="FLT_MAX")
    up_links = ("rf2", "rf2l", "rf2r", "fl3") if roof else ("bp2l", "bp2r", "fl3", "fl2")
    for a, links in (("ref", ("fl3", "fl3l", "fl3r", "fl2", "fl4")), ("refb", ("fl4", "fl4l", "fl4r", "fl5")),
                     ("refl", ("fl3l", "si3l", "fl2l", "fl4l")), ("refu", up_links)):
        for b in links:
            p.beam(a, b)
    # windshield / glass break trigger beams
    p.beams_props(deformGroup="windshield_break", deformationTriggerRatio=0.008)
    for a, b in (("rf1l", "fp3r"), ("rf1r", "fp3l"), ("rf1", "fp3")):
        p.beam(a, b, beamSpring=0, beamDamp=0, beamDeform=500, beamStrength="FLT_MAX")
    if kind == "hatch":
        p.beams_props(deformGroup="quarterglass_L_break")
        p.beam("cp1l", "qp3l", beamSpring=0, beamDamp=0, beamDeform=500, beamStrength="FLT_MAX")
        p.beams_props(deformGroup="quarterglass_R_break")
        p.beam("cp1r", "qp3r", beamSpring=0, beamDamp=0, beamDeform=500, beamStrength="FLT_MAX")
    elif kind == "coupe":
        p.beams_props(deformGroup="quarterglass_L_break")
        p.beam("rf3l", "qp3l", beamSpring=0, beamDamp=0, beamDeform=500, beamStrength="FLT_MAX")
        p.beams_props(deformGroup="quarterglass_R_break")
        p.beam("rf3r", "qp3r", beamSpring=0, beamDamp=0, beamDeform=500, beamStrength="FLT_MAX")
        p.beams_props(deformGroup="rearwindow_break", deformationTriggerRatio=0.01)
        for a, b in (("rf4l", "rw1"), ("rf4r", "rw1"), ("rf4", "cp2l"), ("rf4", "cp2r")):
            p.beam(a, b, beamSpring=0, beamDamp=0, beamDeform=500, beamStrength="FLT_MAX")
    p.beams_props(deformGroup="")
    p.set("refNodes", [["ref:", "back:", "left:", "up:", "leftCorner:", "rightCorner:"],
                       ["ref", "refb", "refl", "refu", "fe2l", "fe2r"]])
    p.set("cameraExternal", {"distance": 5.4, "distanceMin": 2.0, "offset": {"x": 0.0, "y": 0.10, "z": 0.48}, "fov": 65})
    p.set("cameraChase", {"distance": 5.4, "distanceMin": 2.0, "defaultRotation": {"x": 0, "y": -11, "z": 0},
                          "offset": {"x": 0.0, "y": 0.10, "z": 0.75}, "fov": 65})
    dash_links = ["rf2l", "rf2r", "fl3l", "fl3r", "bp3l", "ap1l"] if roof else ["ap1l", "ap1r", "fl3l", "fl3r", "bp3l", "bp3r"]
    cams = [["type", "x", "y", "z", "fov", "id1:", "id2:", "id3:", "id4:", "id5:", "id6:"],
            {"nodeWeight": 1.3}, {"selfCollision": False}, {"collision": False},
            {"beamSpring": 46000, "beamDamp": 450},
            ["hood", 0.0, -1.10, 0.98, 65, "fp3", "fp3l", "fp3r", "ft3l", "ft3r", "fs1l",
             {"beamDeform": 5001000, "beamStrength": "FLT_MAX"}],
            {"beamSpring": 3000, "beamDamp": 110},
            ["dash", D.EYE[0], D.EYE[1], D.EYE[2], 62, *dash_links,
             {"beamDeform": 5001000, "beamStrength": "FLT_MAX"}],
            {"selfCollision": True}, {"collision": True}]
    p.set("camerasInternal", cams)
    p.set("sounds", {"cabinFilterCoef": 0.30 if roof else 0.08})
    p.tris_props(dragCoef=10, groundModel="metal", triangleType="NORMALTYPE")
    for q in body_skin_quads(kind):
        if all(n in nodes for n in q):
            if len(q) == 3:
                p.tri(*q)
            else:
                p.quad(*q)
    return p


def body_skin_quads(kind="hatch"):
    """Collision skin of the unibody (left side written, mirrored with reversed winding)."""
    L = []
    if kind in ("coupe", "convertible"):
        L += [("rf4l", "cp2l", "rw1", "rf4"), ("cp2l", "cp3l", "rw1")]
    L += [("si0l", "si1l", "fl1l", "fp1l"), ("si1l", "si2l", "fl2l", "fl1l"), ("si2l", "si3l", "fl3l", "fl2l"),
         ("si3l", "si4l", "fl4l", "fl3l"), ("si4l", "si5l", "fl5l", "fl4l"),
         ("fl1l", "fl2l", "fl2", "fl1"), ("fl2l", "fl3l", "fl3", "fl2"), ("fl3l", "fl4l", "fl4", "fl3"),
         ("fl4l", "fl5l", "fl5", "fl4"), ("fp1l", "fl1l", "fl1", "fp1"),
         ("rf1l", "rf2l", "rf2", "rf1"), ("rf2l", "rf3l", "rf3", "rf2"), ("rf3l", "rf4l", "rf4", "rf3"),
         ("si4l", "bp1l", "qp1l", "si5l"), ("bp1l", "bp2l", "qp2l", "qp1l"), ("bp2l", "bp3l", "qp3l", "qp2l"),
         ("qp2l", "qp4l", "qp5l", "qp3l"), ("qp3l", "qp5l", "cp2l", "cp1l"), ("qp4l", "qp7l", "qp8l", "qp5l"),
         ("qp5l", "qp8l", "cp3l", "cp2l"), ("qp6l", "tp1l", "tp2l", "qp7l"), ("qp7l", "tp2l", "tp3l", "qp8l"),
         ("fa1l", "fa2l", "ft2l", "ft1l"), ("fa2l", "fa3l", "ft3l", "ft2l"), ("fe1l", "fa1l", "ft1l", "fe2l"),
         ("tl1l", "tl2l", "tl2", "tl1"), ("tl2l", "tl3l", "tl3", "tl2"), ("tp1l", "tl2l", "tl3l", "tp2l"),
         ("rr2l", "rr3l", "fl8", "fl7"), ("rr3l", "tl1l", "tl1", "fl8")]
    out = []
    for q in L:
        out.append(q)
        mq = tuple(ST.mir(n) for n in q)
        if mq != q:
            out.append(mq[::-1])
    return out


# ---------------------------------------------------------------------------
# small parts: fuel tank, exhaust, radiator, tail lights, interior
# ---------------------------------------------------------------------------
def fueltank(key="stock", title="Stock 60L Fuel Tank", capacity=60, value=180, y=(0.76, 1.02), mesh="s13_fueltank"):
    p = Part(f"{PFX}_fueltank_{key}", title, f"{PFX}_fueltank", value=value)
    p.variable("$fuel", "L", "Chassis", round(capacity * 0.75), 0, capacity, "Fuel Volume", "Initial fuel volume", stepDis=0.5)
    p.set("energyStorage", [["type", "name"], ["fuelTank", "mainTank"]])
    p.set("mainTank", {"energyType": "gasoline", "fuelCapacity": capacity, "startingFuelCapacity": "$fuel",
                       "fuel": {"[engineGroup]:": ["fuel"]}, "breakTriggerBeam": "fuelTank"})
    p.flexbody(mesh, ["fueltank"])
    p.nodes_props(selfCollision=False, collision=True, nodeMaterial="|NM_PLASTIC", frictionCoef=0.6, group="fueltank",
                  engineGroup="fuel")
    w = 2.5 if capacity > 20 else 1.5
    for nm, x, yy, z in (("ftk1l", 0.36, y[0], 0.22), ("ftk1r", -0.36, y[0], 0.22), ("ftk2l", 0.36, y[1], 0.24),
                         ("ftk2r", -0.36, y[1], 0.24)):
        p.node(nm, x, yy, z, nodeWeight=w, chemEnergy=1000, burnRate=0.39, flashPoint=300, specHeat=0.2,
               smokePoint=150, selfIgnitionCoef=False, baseTemp="thermals", conductionRadius=0.2)
    p.nodes_props(group="", engineGroup="", chemEnergy=False, burnRate=False, flashPoint=False, specHeat=False,
                  smokePoint=False, selfIgnitionCoef=False, baseTemp=False, conductionRadius=False)
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=801000, beamDamp=50, beamDeform=6000, beamStrength="FLT_MAX")
    p.beam("ftk1l", "ftk1r", name="fuelTank", containerBeam="fuelTank")
    for a, b in (("ftk2l", "ftk2r"), ("ftk1l", "ftk2l"), ("ftk1r", "ftk2r"), ("ftk1l", "ftk2r"), ("ftk1r", "ftk2l")):
        p.beam(a, b)
    p.beams_props(beamSpring=601000, beamDamp=50, beamDeform=9000, beamStrength=40000)
    for a, bs in (("ftk1l", ("fl4l", "fl4", "si4l")), ("ftk1r", ("fl4r", "fl4", "si4r")), ("ftk2l", ("fl5l", "fl5", "rm1l")),
                  ("ftk2r", ("fl5r", "fl5", "rm1r"))):
        for b in bs:
            p.beam(a, b)
    return p


def exhaust(key="stock", title="Stock Exhaust", value=420, muffling=0.6, gain=-4, afterfire=0.2, mesh="s13_exhaust_stock"):
    p = Part(f"{PFX}_exhaust_{key}", title, f"{PFX}_exhaust", value=value)
    p.flexbody(mesh, ["exhaust"])
    pts = [("exa1", -0.24, -1.05, 0.30), ("exa2", -0.14, -0.55, 0.205), ("exa2b", -0.14, -0.08, 0.205),
           ("exa3", -0.14, 0.40, 0.205),
           ("exa4", -0.30, 1.00, 0.230), ("exa5", -0.45, 1.70, 0.270), ("exa6", -0.50, 2.27, 0.250)]
    p.nodes_props(selfCollision=False, collision=True, nodeMaterial="|NM_METAL", frictionCoef=0.5, group="exhaust")
    for nm, x, y, z in pts[:-1]:
        p.node(nm, x, y, z, nodeWeight=2.2)
    nm, x, y, z = pts[-1]
    p.node(nm, x, y, z, nodeWeight=1.5, afterFireAudioCoef=afterfire, afterFireVisualCoef=afterfire,
           afterFireVolumeCoef=afterfire * 1.5, afterFireMufflingCoef=muffling * 0.5,
           exhaustAudioMufflingCoef=muffling, exhaustAudioGainChange=gain)
    p.nodes_props(group="")
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=1001000, beamDamp=50, beamDeform=8000, beamStrength="FLT_MAX")
    names = [q[0] for q in pts]
    p.beam("e4r", names[0], isExhaust="mainEngine")
    for a, b in zip(names, names[1:]):
        p.beam(a, b, isExhaust="mainEngine")
    p.beam_comment("hangers")
    p.beams_props(beamSpring=201000, beamDamp=200, beamDeform=4000, beamStrength=9000)
    for a, bs in (("exa1", ("e3r", "e4r", "e1r")), ("exa2", ("fl1", "fl1r", "fp1")), ("exa2b", ("fl2", "fl2r", "fl1")),
                  ("exa3", ("fl3", "fl3r", "fl2")),
                  ("exa4", ("fl5r", "fl5", "rm1r")), ("exa5", ("rr2r", "fl7", "si6r")), ("exa6", ("tl1r", "rr3r", "tl1"))):
        for b in bs:
            p.beam(a, b)
    return p


def radiator(key="stock", title="Stock Radiator", value=180, mesh="s13_radiator"):
    p = Part(f"{PFX}_radiator_{key}", title, f"{PFX}_radiator", value=value)
    p.flexbody(mesh, ["radiator"])
    p.nodes_props(selfCollision=False, collision=True, nodeMaterial="|NM_METAL", frictionCoef=0.5, group="radiator")
    for nm, x, z in (("rad1l", 0.30, 0.53), ("rad1r", -0.30, 0.53), ("rad2l", 0.30, 0.31), ("rad2r", -0.30, 0.31)):
        p.node(nm, x, -1.96, z, nodeWeight=1.6)
    p.nodes_props(group="")
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=601000, beamDamp=40, beamDeform=5000, beamStrength="FLT_MAX")
    for a, b in (("rad1l", "rad1r"), ("rad2l", "rad2r"), ("rad1l", "rad2l"), ("rad1r", "rad2r"), ("rad1l", "rad2r"),
                 ("rad1r", "rad2l")):
        p.beam(a, b)
    p.beams_props(beamSpring=401000, beamDamp=40, beamDeform=6000, beamStrength=20000)
    for a, bs in (("rad1l", ("fe2l", "fe2", "fr1l")), ("rad1r", ("fe2r", "fe2", "fr1r")), ("rad2l", ("fe1l", "fe1", "fr1l")),
                  ("rad2r", ("fe1r", "fe1", "fr1r"))):
        for b in bs:
            p.beam(a, b)
    return p


def taillights():
    p = Part(f"{PFX}_taillights", "Stock Tail Lights", f"{PFX}_taillights", value=260)
    p.flex_props(deformGroup="taillight_break", deformMaterialBase="s13_lights_red", deformMaterialDamaged="s13_lights_red_dmg")
    p.flexbody(f"{PFX}_taillights", [f"{PFX}_body"])
    p.flex_props(deformGroup="")
    p.props_props(lightInnerAngle=40, lightOuterAngle=90, lightColor={"r": 255, "g": 20, "b": 10, "a": 255},
                  flareName="vehicleBrakeLightFlare", lightCastShadows=False)
    for side, s in (("l", 1), ("r", -1)):
        for func, rng, bright, col in (("lowhighbeam", 4, 0.25, None), ("brakelights", 8, 0.8, None)):
            p.prop(func, "POINTLIGHT", "tl3" + side, "tl3", "tl2" + side, {"x": 0, "y": 0, "z": 0},
                   {"x": 0, "y": 0, "z": 0}, {"x": 0, "y": 0, "z": 0}, 0, 0, 0, 1,
                   baseTranslationGlobal={"x": s * 0.66, "y": 2.27, "z": 0.76}, lightRange=rng,
                   lightIntensityLm=400 * bright, flareScale=0.04, deformGroup="taillight_break")
        p.prop("reverse", "POINTLIGHT", "tl3" + side, "tl3", "tl2" + side, {"x": 0, "y": 0, "z": 0},
               {"x": 0, "y": 0, "z": 0}, {"x": 0, "y": 0, "z": 0}, 0, 0, 0, 1,
               baseTranslationGlobal={"x": s * 0.39, "y": 2.27, "z": 0.76}, lightRange=6, lightIntensityLm=250,
               lightColor={"r": 255, "g": 255, "b": 240, "a": 255}, flareName="vehicleReverseLightFlare",
               flareScale=0.03, deformGroup="taillight_break")
    p.beams_props(deformGroup="taillight_break", deformationTriggerRatio=0.02)
    for a, b in (("tl3l", "tl2"), ("tl3r", "tl2"), ("tl3l", "tl3r")):
        p.beam(a, b, beamSpring=0, beamDamp=0, beamDeform=1000, beamStrength="FLT_MAX")
    p.beams_props(deformGroup="")
    return p


def taillights_coupe():
    p = Part(f"{PFX}_taillights_coupe", "Stock Tail Lights (Coupe / Convertible)", f"{PFX}_taillights", value=300)
    p.flex_props(deformGroup="taillight_break", deformMaterialBase="s13_lights_red", deformMaterialDamaged="s13_lights_red_dmg")
    p.flexbody(f"{PFX}_taillights_coupe", [f"{PFX}_body"])
    p.flex_props(deformGroup="")
    p.props_props(lightInnerAngle=40, lightOuterAngle=90, lightColor={"r": 255, "g": 20, "b": 10, "a": 255},
                  flareName="vehicleBrakeLightFlare", lightCastShadows=False)
    for side, s in (("l", 1), ("r", -1)):
        for func, rng, bright in (("lowhighbeam", 4, 0.25), ("brakelights", 8, 0.8)):
            p.prop(func, "POINTLIGHT", "tl3" + side, "tl3", "tl2" + side, {"x": 0, "y": 0, "z": 0},
                   {"x": 0, "y": 0, "z": 0}, {"x": 0, "y": 0, "z": 0}, 0, 0, 0, 1,
                   baseTranslationGlobal={"x": s * 0.56, "y": 2.27, "z": 0.672}, lightRange=rng,
                   lightIntensityLm=400 * bright, flareScale=0.04, deformGroup="taillight_break")
        p.prop("reverse", "POINTLIGHT", "tl3" + side, "tl3", "tl2" + side, {"x": 0, "y": 0, "z": 0},
               {"x": 0, "y": 0, "z": 0}, {"x": 0, "y": 0, "z": 0}, 0, 0, 0, 1,
               baseTranslationGlobal={"x": s * 0.385, "y": 2.27, "z": 0.758}, lightRange=6, lightIntensityLm=250,
               lightColor={"r": 255, "g": 255, "b": 240, "a": 255}, flareName="vehicleReverseLightFlare",
               flareScale=0.03, deformGroup="taillight_break")
    p.beams_props(deformGroup="taillight_break", deformationTriggerRatio=0.02)
    for a, b in (("tl3l", "tl2"), ("tl3r", "tl2"), ("tl3l", "tl3r")):
        p.beam(a, b, beamSpring=0, beamDamp=0, beamDeform=1000, beamStrength="FLT_MAX")
    p.beams_props(deformGroup="")
    return p


def headliners():
    out = []
    for key, title, mesh in (("headliner", "Stock Headliner", f"{PFX}_headliner"),
                             ("headliner_coupe", "Stock Headliner (Coupe)", f"{PFX}_headliner_coupe")):
        p = Part(f"{PFX}_{key}", title, f"{PFX}_headliner", value=120)
        p.flexbody(mesh, [f"{PFX}_body"])
        out.append(p)
    return out


RACE_TACH = (D.STEER_CENTER[0], D.GAUGE_Y, 0.920)   # race tach pod face centre (on the column, under the glass)
SHIFT_LED_MATS = ["s13_led_green", "s13_led_green", "s13_led_amber", "s13_led_amber", "s13_led_red"]


def skins():
    from tools.textures.liveries import LIVERIES
    out = []
    for key, (title, fn, number) in LIVERIES.items():
        p = Part(f"{PFX}_skin_{key}", title, "paint_design", value=900)
        p.set("globalSkin", key)
        out.append(p)
    return out


def licenseplates():
    """US-format plates using BeamNG's shared 'licenseplate' mesh (vehicles/common/empty.dae)."""
    from tools.model.s13_details import R_PLATE, PLATE_F
    out = []
    p = Part(f"{PFX}_licenseplate_F", "Front License Plate", f"{PFX}_licenseplate_F", value=0)
    p.flexbody("licenseplate", [f"{PFX}_bumper_F"], pos={"x": PLATE_F["x"], "y": -2.262, "z": PLATE_F["z"]},
               rot={"x": 0, "y": 0, "z": 0}, scale={"x": 1, "y": 1, "z": 1})
    out.append(p)
    p = Part(f"{PFX}_licenseplate_R", "Rear License Plate", f"{PFX}_licenseplate_R", value=0)
    p.flexbody("licenseplate", [f"{PFX}_bumper_R"], pos={"x": 0.0, "y": R_PLATE["wall_y"] + 0.006, "z": R_PLATE["cz"]},
               rot={"x": 0, "y": 0, "z": 180}, scale={"x": 1, "y": 1, "z": 1})
    out.append(p)
    return out


def interior_stock(key="stock", title="Stock Interior (Cloth)", value=800, seats="s13_seats_cloth", mass_bias=1.0,
                   kind="stock", wheel=None, rear="s13_rearseat"):
    """Dash, seats, trim.  kind: stock | stripped (stock dash, buckets, no trim) | race (carbon dash, race tach,
    single race seat, extinguisher).  Props use the 'left/down' node frame convention:
    idX = node displaced +x (left) of idRef, idY = node displaced -z (down) -> baseRotation 0 = modelled pose."""
    p = Part(f"{PFX}_interior_{key}", title, f"{PFX}_interior", value=value)
    p.slot(f"{PFX}_steering_wheel", wheel or (f"{PFX}_steering_wheel_stock" if kind == "stock" else f"{PFX}_steering_wheel_race"),
           "Steering Wheel")
    if kind == "race":
        for m, g in (("dash_race", "dash"), ("race_tach", "dash"), ("seat_race", "body"), ("extinguisher", "body"),
                     ("race_switchpanel", "dash"), ("pedals_static", "body")):
            p.flexbody(f"{PFX}_{m}", [f"{PFX}_{g}"] + ([f"{PFX}_body"] if m == "race_tach" else []))
        p.set("glowMap", {f"s13_shiftled_{i}": {"simpleFunction": {f"s13sl{i}": 1}, "off": m, "on": m + "_on"}
                          for i, m in enumerate(SHIFT_LED_MATS)})
    else:
        p.flexbody(f"{PFX}_dash", [f"{PFX}_dash"])
        p.flexbody(f"{PFX}_gauges", [f"{PFX}_dash"])
        p.flexbody(f"{PFX}_console", [f"{PFX}_body"])
        p.flexbody(seats, [f"{PFX}_body"])
        p.flexbody(f"{PFX}_pedals_static", [f"{PFX}_body"])
        p.flexbody(f"{PFX}_mirror_int", [f"{PFX}_body"])
        p.set("mirrors", [["mesh", "idRef:", "id1:", "id2:"],
                          [f"{PFX}_mirror_int", "rf1", "rf1l", "fp3", {"refBaseTranslation": {"x": 0.0, "y": -0.02, "z": -0.10}}]])
        p.flexbody(f"{PFX}_cabin_trim", [f"{PFX}_body"])
        if kind == "stock":
            p.flexbody(f"{PFX}_carpet", [f"{PFX}_body"])
            p.flexbody(f"{PFX}_doorcard_L", [f"{PFX}_door_L"])
            p.flexbody(f"{PFX}_doorcard_R", [f"{PFX}_door_R"])
            p.flexbody(rear, [f"{PFX}_body"])
    seat_scale = {"stock": 1.0, "stripped": 0.45, "race": 0.0}[kind]
    # dash nodes
    cx, cy, cz = D.STEER_CENTER
    gy, gz = D.GAUGE_Y, D.GAUGE_Z  # gauge pivot plane
    p.nodes_props(selfCollision=False, collision=True, nodeMaterial="|NM_PLASTIC", frictionCoef=0.6, group=f"{PFX}_dash")
    for nm, x, y, z, w in (("dsh1l", 0.62, -0.62, 0.88, 2.5), ("dsh1r", -0.62, -0.62, 0.88, 2.5), ("dsh1", 0.0, -0.62, 0.90, 2.0),
                           ("dsh2l", 0.62, -0.42, 0.70, 2.5), ("dsh2r", -0.62, -0.42, 0.70, 2.5), ("dsh2", 0.0, -0.40, 0.60, 3.0)):
        p.node(nm, x, y, z, nodeWeight=w * mass_bias)
    # seats / trim mass (front buckets, rear bench, carpet, trim, HVAC)
    p.nodes_props(group=f"{PFX}_body", collision=True, selfCollision=False, nodeMaterial="|NM_PLASTIC")
    for nm, x, y, z, w in (("st1l", 0.37, -0.05, 0.30, 9.0), ("st2l", 0.37, 0.35, 0.33, 9.0), ("st3l", 0.37, 0.48, 0.80, 4.0),
                           ("st1r", -0.37, -0.05, 0.30, 9.0), ("st2r", -0.37, 0.35, 0.33, 9.0), ("st3r", -0.37, 0.48, 0.80, 4.0),
                           ("rs1l", 0.40, 0.85, 0.38, 6.0), ("rs1r", -0.40, 0.85, 0.38, 6.0), ("hv1", 0.0, -0.55, 0.62, 12.0),
                           ("cs1", 0.0, -0.10, 0.50, 2.0)):
        if kind != "stock":
            if nm.startswith("rs1"):
                w = 0.4                                       # rear seat removed
            elif nm.startswith("st"):
                w = w * seat_scale if seat_scale else (3.2 if nm.endswith("l") else 0.4)   # race: driver seat only
            elif nm == "hv1" and kind == "race":
                w = 2.5                                       # HVAC deleted
        p.node(nm, x, y, z, nodeWeight=round(w * mass_bias, 3))
    p.nodes_props(group="", collision=False)
    # prop frames: gauge cluster, steering column, pedals
    p.node("gref", cx, gy, gz, nodeWeight=0.5)
    p.node("grefx", cx + 0.10, gy, gz, nodeWeight=0.5)
    p.node("grefd", cx, gy, gz - 0.10, nodeWeight=0.5)
    import math
    a = math.radians(23.0)  # column angle above horizontal (column points back-up toward the driver)
    p.node("sw1", cx, cy, cz, nodeWeight=0.8)
    p.node("sw1x", cx + 0.10, cy, cz, nodeWeight=0.5)
    p.node("sw1d", cx, cy + 0.10 * math.sin(a), cz - 0.10 * math.cos(a), nodeWeight=0.5)
    p.node("pd1", cx, -0.86, 0.47, nodeWeight=0.5)
    p.node("pd1x", cx + 0.10, -0.86, 0.47, nodeWeight=0.5)
    p.node("pd1d", cx, -0.86, 0.37, nodeWeight=0.5)
    p.nodes_props(collision=True)
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=801000, beamDamp=60, beamDeform=12000, beamStrength="FLT_MAX")
    for a2, b in (("dsh1l", "dsh1"), ("dsh1", "dsh1r"), ("dsh2l", "dsh2"), ("dsh2", "dsh2r"), ("dsh1l", "dsh2l"),
                  ("dsh1r", "dsh2r"), ("dsh1", "dsh2"), ("dsh1l", "dsh2"), ("dsh1", "dsh2l"), ("dsh1r", "dsh2"),
                  ("dsh1", "dsh2r"), ("dsh1l", "fp3l"), ("dsh1l", "hp3l"), ("dsh1l", "hp2l"), ("dsh1r", "fp3r"),
                  ("dsh1r", "hp3r"), ("dsh1r", "hp2r"), ("dsh1", "fp3"), ("dsh1", "fp4l"), ("dsh1", "fp4r"),
                  ("dsh2l", "hp2l"), ("dsh2l", "fp2l"), ("dsh2r", "hp2r"), ("dsh2r", "fp2r"), ("dsh2", "fp2"),
                  ("dsh2", "fl1"), ("dsh2l", "hp1l"), ("dsh2r", "hp1r")):
        p.beam(a2, b)
    p.beams_props(beamSpring=601000, beamDamp=60, beamDeform=15000, beamStrength=60000)
    for side in ("l", "r"):
        for a2, bs in (("st1", ("fl2", "fl2", "si2", "fl1")), ("st2", ("fl3", "si3", "fl4")), ("st3", ("st1", "st2", "fl3", "si3"))):
            for b in bs:
                bb = b + side if b not in ("fl2", "fl1", "fl3", "fl4") or a2 == "st3" and b in ("fl3",) else b
                if bb in ("fl1", "fl2", "fl3", "fl4") or bb.endswith(side):
                    p.beam(a2 + side, bb if bb.endswith(side) or bb in ("fl1", "fl2", "fl3", "fl4") else bb + side)
        p.beam("st1" + side, "st2" + side)
        p.beam("st1" + side, "fl2" + side)
        p.beam("st2" + side, "fl3" + side)
        p.beam("rs1" + side, "fl5" + side)
        p.beam("rs1" + side, "fl5")
        p.beam("rs1" + side, "si5" + side)
        p.beam("rs1" + side, "fl4" + side)
    for b in ("fp2", "fp3", "fp2l", "fp2r", "dsh2", "dsh1"):
        p.beam("hv1", b)
    for b in ("hv1", "fl2", "fl3", "fl2l", "fl2r", "fl3l", "fl3r"):
        p.beam("cs1", b)
    p.beams_props(beamSpring=401000, beamDamp=40)
    for n in ("gref", "grefx", "grefd", "sw1", "sw1x", "sw1d"):
        for b in ("dsh1", "dsh1l", "dsh2", "dsh2l"):
            p.beam(n, b)
    for n in ("pd1", "pd1x", "pd1d"):
        for b in ("fp2", "fp2l", "fp1l", "dsh2"):
            p.beam(n, b)
    p.props_props()
    zero = {"x": 0, "y": 0, "z": 0}
    if kind == "race":
        # race tach: 0..10000 rpm over 270 deg, zero at 135 deg CCW from straight up
        tx, ty, tz_ = RACE_TACH
        p.prop("rpmTacho", f"{PFX}_needle_race", "gref", "grefx", "grefd", zero, {"x": 0, "y": 0, "z": -0.027}, zero,
               0, 10000, -5000, 1, baseTranslationGlobal=dict(x=tx, y=ty + 0.006, z=tz_))
    else:
        # gauge needles (pivot positions in world space; needles modelled pointing straight up at their zero)
        # S13 cluster as seen by the driver: temp | tach | speedo | fuel  (driver's left is +x)
        tach_c = (cx + D.GAUGE_TACH_DX, gy + 0.004, gz)
        speedo_c = (cx - D.GAUGE_TACH_DX, gy + 0.004, gz)
        temp_c = (cx + D.GAUGE_SMALL_DX, gy + 0.003, gz + D.GAUGE_SMALL_DZ)
        fuel_c = (cx - D.GAUGE_SMALL_DX, gy + 0.003, gz + D.GAUGE_SMALL_DZ)
        # tach: 0..8000 rpm over 240 deg, starting at -120 deg (clockwise seen by driver -> negative about +y)
        p.prop("rpmTacho", f"{PFX}_needle_tach", "gref", "grefx", "grefd", zero, {"x": 0, "y": 0, "z": -0.03}, zero,
               0, 8000, -4000, 1, baseTranslationGlobal=dict(x=tach_c[0], y=tach_c[1], z=tach_c[2]))
        # speedo: 0..140 mph over 240 deg; wheelspeed is m/s -> 140 mph = 62.6 m/s
        p.prop("wheelspeed", f"{PFX}_needle_speedo", "gref", "grefx", "grefd", zero, {"x": 0, "y": 0, "z": -240 / 62.6}, zero,
               0, 62.6, -31.3, 1, baseTranslationGlobal=dict(x=speedo_c[0], y=speedo_c[1], z=speedo_c[2]))
        p.prop("fuel", f"{PFX}_needle_small", "gref", "grefx", "grefd", zero, {"x": 0, "y": 0, "z": -90}, zero,
               0, 1, -0.5, 1, baseTranslationGlobal=dict(x=fuel_c[0], y=fuel_c[1], z=fuel_c[2]))
        p.prop("oiltemp", f"{PFX}_needle_small", "gref", "grefx", "grefd", zero, {"x": 0, "y": 0, "z": -1.5}, zero,
               40, 130, -85, 1, baseTranslationGlobal=dict(x=temp_c[0], y=temp_c[1], z=temp_c[2]))
    # pedals (pivot at top, rotate about vehicle x)
    for func, mesh, dx in (("throttle", "pedal_gas", -0.07), ("brake", "pedal_brake", 0.02), ("clutch", "pedal_clutch", 0.12)):
        p.prop(func, f"{PFX}_{mesh}", "pd1", "pd1x", "pd1d", zero, {"x": -22, "y": 0, "z": 0}, zero, 0, 1, 0, 1,
               baseTranslationGlobal=dict(x=cx + dx, y=-0.86, z=0.47))
    return p


def steering_wheels():
    out = []
    for key, title, mesh, value in (("stock", "Stock Steering Wheel", "s13_steer_stock", 120),
                                    ("deepdish", "Deep-Dish Steering Wheel", "s1x_steer_deepdish", 350),
                                    ("race", "Quick-Release Race Steering Wheel", "s1x_steer_race", 650)):
        p = Part(f"{PFX}_steering_wheel_{key}", title, f"{PFX}_steering_wheel", value=value)
        cx, cy, cz = D.STEER_CENTER
        p.props_props()
        p.prop("steering", mesh, "sw1", "sw1x", "sw1d", {"x": 0, "y": 0, "z": 0}, {"x": 0, "y": 0, "z": 1},
               {"x": 0, "y": 0, "z": 0}, -1000, 1000, 0, 1, baseTranslationGlobal={"x": cx, "y": cy, "z": cz},
               breakGroup="steeringWheelBreak")
        out.append(p)
    return out


def handbrakes():
    """Handbrake slot: the hydraulic lever multiplies the rear parking-brake torque (see brake parts)."""
    out = []
    p = Part(f"{PFX}_handbrake_stock", "Stock Handbrake", f"{PFX}_handbrake", value=0)
    p.variable("$handbrake_mult", "x", "Brakes", 1.0, 0.8, 1.2, "Handbrake Strength", "Rear parking-brake torque multiplier",
               stepDis=0.05)
    out.append(p)
    p = Part(f"{PFX}_handbrake_hydro", "Hydraulic Drift Handbrake", f"{PFX}_handbrake", value=450)
    p.flexbody(f"{PFX}_handbrake_hydro", [f"{PFX}_body"])
    p.variable("$handbrake_mult", "x", "Brakes", 2.6, 1.0, 4.0, "Hydraulic Handbrake Strength",
               "Rear parking-brake torque multiplier", stepDis=0.1)
    out.append(p)
    return out


def shifters():
    out = []
    for key, title, mesh, func in (("stock", "Stock Shifter", "s13_shifter_stock", "nop"),
                                   ("short", "Short Shifter", "s1x_shifter_short", "nop"),
                                   ("sequential", "Sequential Shift Lever", "s1x_shifter_seq", "nop"),
                                   ("auto", "Automatic Shift Lever", "s13_shifter_auto", "nop")):
        p = Part(f"{PFX}_shifter_{key}", title, f"{PFX}_shifter", value=150)
        p.flexbody(mesh, [f"{PFX}_body"])
        out.append(p)
    return out


# ---------------------------------------------------------------------------
# all parts + writing
# ---------------------------------------------------------------------------
def all_files():
    """Return {filename: [parts...]}"""
    files = OrderedDict()
    files[f"{VEH}.jbeam"] = [main_part()]
    files[f"{PFX}_body.jbeam"] = [body("hatch"), body("coupe"), body("convertible")] + headliners()
    files[f"{PFX}_panels.jbeam"] = [PJ.hood(), PJ.popup("L"), PJ.popup("R"), PJ.fender("L"), PJ.fender("R"),
                                    PJ.door("L"), PJ.door("R"), PJ.hatch(), PJ.bumper_front(), PJ.bumper_rear(),
                                    taillights()]
    files[f"{PFX}_coupe.jbeam"] = ([PJ.trunk(), PJ.trunk(name=f"{PFX}_trunk_light", mesh=f"{PFX}_trunk_carbon",
                                                          title="Carbon Fiber Trunk Lid", value=1500,
                                                          mass=6.0).scale_springs(6.0 / 16.0),
                                    taillights_coupe()] + PJ.trunk_spoilers() + PJ.convertible_doors() + PJ.softtops())
    files[f"{PFX}_interior.jbeam"] = ([interior_stock(),
                                       interior_stock("leather", "Leather Interior (LE)", 1600, seats=f"{PFX}_seats_leather",
                                                      rear=f"{PFX}_rearseat_leather"),
                                       interior_stock("stripped", "Stripped Interior (Bucket Seats)", 400,
                                                      seats=f"{PFX}_seats_bucket", kind="stripped", wheel=f"{PFX}_steering_wheel_deepdish"),
                                       interior_stock("race", "Race Interior (Carbon Dash, Single Seat)", 2600, kind="race")]
                                      + steering_wheels() + shifters() + handbrakes())
    files[f"{PFX}_suspension.jbeam"] = C.suspension_parts()
    files[f"{PFX}_wheels.jbeam"] = C.wheel_parts()
    files[f"{PFX}_powertrain.jbeam"] = C.powertrain_parts()
    files[f"{PFX}_misc.jbeam"] = licenseplates() + [fueltank(), exhaust(),
                                  exhaust("race", "Race Exhaust (3\" Straight Through)", 1400, muffling=0.12, gain=3,
                                          afterfire=1.0, mesh=f"{PFX}_exhaust_race"),
                                  radiator(), radiator("race", "Race Aluminium Radiator", 900, mesh=f"{PFX}_radiator")]
    files[f"{PFX}_panels.jbeam"] += PJ.mirrors() + [PJ.spoiler_oem()]
    files[f"{PFX}_skins.jbeam"] = skins()
    files[f"{PFX}_race.jbeam"] = RACE.race_parts(body_common)
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
            f.write(dumps(d, header_comment=f"{TITLE} - generated by tools/vehicle/s13 (do not edit by hand; edit the generator)"))
    return vdir
