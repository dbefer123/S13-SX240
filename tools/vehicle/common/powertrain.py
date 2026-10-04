"""Engines, gearboxes, driveshaft and differentials (shared S13/S14).

Syntax for combustionEngine / frictionClutch / manualGearbox / torsionReactor /
differential / shaft follows the official BeamNG modding template.  Items NOT
covered by the docs/template and written from knowledge of vanilla content are
marked UNVERIFIED and listed in the README check list: turbocharger section,
sequentialGearbox, automaticGearbox + torqueConverter.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .jb import Part

SAMPLE_ENGINE = "i4p_01600cc_motorsport_02_engine"
SAMPLE_EXHAUST = "i4p_01600cc_motorsport_02_exhaust"
STARTER = dict(starterSample="event:>Engine>Starter>box4_1960_eng", starterSampleExhaust="event:>Engine>Starter>box4_1960_exh",
               shutOffSampleEngine="event:>Engine>Shutoff>box4_1960_eng", shutOffSampleExhaust="event:>Engine>Shutoff>box4_1960_exh",
               starterVolume=0.8, starterVolumeExhaust=0.6, shutOffVolumeEngine=0.5, shutOffVolumeExhaust=0.5,
               starterThrottleKillTime=1.2, idleRPMStartRate=1.5, idleRPMStartCoef=1.25, maxIdleThrottle=0.1)
AFTERFIRE = dict(instantAfterFireSound="event:>Vehicle>Afterfire>box4_01>muffled>race_single",
                 sustainedAfterFireSound="event:>Vehicle>Afterfire>box4_01>muffled>race_multi",
                 shiftAfterFireSound="event:>Vehicle>Afterfire>box4_01>muffled>race_shift")


@dataclass
class EngineDef:
    key: str                 # e.g. "ka24de"
    title: str
    torque: list             # [[rpm, Nm], ...] (naturally aspirated base curve)
    idle: int
    max_rpm: int
    limiter: int
    inertia: float
    friction: float
    dyn_friction: float
    brake_torque: float
    mass: float              # kg (long block + accessories)
    value: int
    block: str = "iron"
    displacement: float = 2.4
    max_torque_rating: float = 300
    mesh: str = ""
    length: float = 0.66     # block length (m)
    width: float = 0.42
    height: float = 0.52
    intake_muffling: float = 0.8
    main_gain_engine: float = -9
    main_gain_exhaust: float = 1
    turbo: dict | None = None  # stock turbo (name of kit default)
    redline_note: str = ""


ENGINES = {
    "ka24e": EngineDef("ka24e", "2.4L KA24E SOHC I4",
                       [[0, 0], [500, 100], [1000, 160], [1500, 175], [2000, 185], [2500, 193], [3000, 199], [3500, 203],
                        [4000, 206], [4400, 206], [5000, 199], [5600, 178], [6000, 160], [6500, 135], [7000, 105]],
                       idle=750, max_rpm=6900, limiter=6600, inertia=0.22, friction=16, dyn_friction=0.025,
                       brake_torque=40, mass=160, value=1800, mesh="engine_ka24", max_torque_rating=290),
    "ka24de": EngineDef("ka24de", "2.4L KA24DE DOHC I4",
                        [[0, 0], [500, 110], [1000, 168], [1500, 183], [2000, 194], [2500, 203], [3000, 209], [3500, 214],
                         [4000, 216], [4400, 217], [5000, 211], [5600, 197], [6000, 183], [6500, 160], [7000, 128]],
                        idle=750, max_rpm=7000, limiter=6700, inertia=0.21, friction=16, dyn_friction=0.024,
                        brake_torque=40, mass=165, value=2400, mesh="engine_ka24", max_torque_rating=340),
    "sr20det": EngineDef("sr20det", "2.0L SR20DET Turbo I4",
                         [[0, 0], [500, 70], [1000, 112], [1500, 130], [2000, 145], [2500, 153], [3000, 160], [3500, 165],
                          [4000, 170], [4500, 170], [5000, 168], [5500, 166], [6000, 162], [6500, 150], [7000, 135], [7500, 112]],
                         idle=800, max_rpm=7600, limiter=7300, inertia=0.17, friction=14, dyn_friction=0.022,
                         brake_torque=34, mass=150, value=4200, block="iron", displacement=2.0, mesh="engine_sr20",
                         max_torque_rating=420, turbo="t25_stock"),
    "k20a": EngineDef("k20a", "2.0L K20A DOHC i-VTEC I4",
                      [[0, 0], [500, 85], [1000, 130], [1500, 145], [2000, 155], [3000, 165], [4000, 175], [5000, 185],
                       [5800, 190], [6000, 198], [6500, 203], [7000, 206], [7500, 203], [8000, 196], [8500, 183], [9000, 165],
                       [9500, 140]],
                      idle=850, max_rpm=9100, limiter=8600, inertia=0.13, friction=12, dyn_friction=0.020,
                      brake_torque=30, mass=135, value=6500, block="aluminium", displacement=2.0, mesh="engine_k20",
                      max_torque_rating=360, intake_muffling=0.6),
    "k20a_race": EngineDef("k20a_race", "2.0L K20A Built Turbo I4 (Race)",
                           [[0, 0], [500, 80], [1000, 120], [2000, 150], [3000, 165], [4000, 178], [5000, 188], [6000, 198],
                            [7000, 205], [7500, 207], [8000, 205], [8500, 200], [9000, 190], [9500, 175], [10000, 155]],
                           idle=1100, max_rpm=9800, limiter=9300, inertia=0.11, friction=13, dyn_friction=0.022,
                           brake_torque=28, mass=128, value=32000, block="aluminium", displacement=2.0, mesh="engine_k20",
                           max_torque_rating=1100, intake_muffling=0.2, main_gain_engine=-6, main_gain_exhaust=3,
                           turbo="race_k20"),
}

# --- turbo kits (UNVERIFIED section syntax, see module docstring) -----------------------
TURBOS = {
    "t25_stock": dict(title="Stock T25 Turbocharger", wg=7.5, wg_max=14, size=0.42, value=900, mesh="turbo_small",
                      curve=[[0, -3.5], [30000, -1.5], [60000, 3.0], [90000, 7.5], [130000, 11.0], [170000, 14.0], [220000, 18.0]]),
    "gt28_kit": dict(title="Ball-Bearing Turbo Kit (GT28 size)", wg=16, wg_max=24, size=0.55, value=3200, mesh="turbo_medium",
                     curve=[[0, -3.5], [30000, -1.5], [60000, 4.0], [90000, 10.0], [130000, 17.0], [170000, 22.0], [220000, 26.0]]),
    "kat_kit": dict(title="KA-T Turbo Kit (T3/T4)", wg=10, wg_max=20, size=0.58, value=2800, mesh="turbo_medium",
                    curve=[[0, -3.5], [30000, -1.5], [60000, 3.5], [90000, 9.0], [130000, 15.0], [170000, 20.0], [220000, 24.0]]),
    "race_k20": dict(title="Race Turbo Kit (GTX35 size)", wg=31, wg_max=42, size=0.80, value=9800, mesh="turbo_large",
                     curve=[[0, -3.0], [30000, -1.0], [60000, 6.0], [90000, 15.0], [130000, 28.0], [170000, 38.0], [220000, 46.0]]),
    "street_k20": dict(title="Street Turbo Kit (GT30 size)", wg=14, wg_max=26, size=0.62, value=5200, mesh="turbo_medium",
                       curve=[[0, -3.5], [30000, -1.5], [60000, 4.5], [90000, 11.0], [130000, 19.0], [170000, 24.0], [220000, 28.0]]),
}

ENGINE_EFF = [[0, 0.0, 0.0], [700, 0.45, 0.12], [1500, 0.62, 0.25], [2500, 0.80, 0.38], [3500, 0.88, 0.50],
              [4500, 0.91, 0.62], [5500, 0.93, 0.74], [6500, 0.94, 0.85], [7500, 0.94, 0.94], [8500, 0.92, 1.0],
              [9500, 0.90, 1.0], [10500, 0.86, 1.0]]


def engine_part(prefix, e: EngineDef, layout, body_mounts, default_trans, mounts_extra=(), exhaust_side=-1):
    """layout: dict with front_y, rear_y, bottom_z, top_z, half_w, mount=(x,y,z)."""
    p = Part(f"{prefix}_engine_{e.key}", e.title, f"{prefix}_engine", value=e.value)
    p.slot(f"{prefix}_{e.key}_intake", f"{prefix}_{e.key}_intake_stock", "Intake", coreSlot=True)
    p.slot(f"{prefix}_{e.key}_induction", f"{prefix}_{e.key}_induction_{'na' if not e.turbo else e.turbo}",
           "Exhaust Manifold / Turbo", coreSlot=True)
    p.slot(f"{prefix}_{e.key}_ecu", f"{prefix}_{e.key}_ecu_stock", "Engine Management", coreSlot=True)
    p.slot(f"{prefix}_{e.key}_internals", f"{prefix}_{e.key}_internals_stock", "Engine Long Block", coreSlot=True)
    p.slot(f"{prefix}_transmission", default_trans, "Transmission")
    p.slot(f"{prefix}_flywheel", f"{prefix}_flywheel_stock", "Flywheel")
    p.powertrain("combustionEngine", "mainEngine", "dummy", 0)
    me = {
        "torque": [["rpm", "torque"]] + e.torque,
        "idleRPM": e.idle, "idleRPMRoughness": 60, "maxRPM": e.max_rpm, "hasRevLimiter": True,
        "revLimiterType": "timeBased", "revLimiterRPM": e.limiter, "revLimiterCutTime": 0.12,
        "inertia": e.inertia, "friction": e.friction, "dynamicFriction": e.dyn_friction, "engineBrakeTorque": e.brake_torque,
        "burnEfficiency": [[0, 0.10], [0.05, 0.25], [0.4, 0.31], [0.7, 0.34], [1, 0.27]],
        "energyStorage": "mainTank", "requiredEnergyType": "gasoline",
        # thermals: block air-cooling model from the official template (known good)
        "thermalsEnabled": True, "isAirCooledOnly": True, "airRegulatorTemperature": 90, "airRegulatorClosedCoef": 0.1,
        "engineBlockAirCoolingEfficiency": 28, "blockFanMaxAirSpeed": 30, "engineBlockAirflowCoef": 1.3,
        "engineBlockMaterial": e.block, "oilVolume": 4.5,
        "engineBlockTemperatureDamageThreshold": 180, "cylinderWallTemperatureDamageThreshold": 210,
        "headGasketDamageThreshold": 1500000, "pistonRingDamageThreshold": 1500000, "connectingRodDamageThreshold": 1500000,
        "maxTorqueRating": e.max_torque_rating, "maxOverTorqueDamage": e.max_torque_rating * 0.6,
        "particulates": 0.04, "instantAfterFireCoef": 0.6, "sustainedAfterFireCoef": 0.6,
        "torqueReactionNodes:": ["e1l", "e3l", "e4r"],
        "waterDamage": {"[engineGroup]:": ["engine_intake"]},
        "engineBlock": {"[engineGroup]:": ["engine_block"]},
        "breakTriggerBeam": "engine", "uiName": "Engine",
        "soundConfig": "soundConfig", "soundConfigExhaust": "soundConfigExhaust",
    }
    me.update(STARTER)
    p.set("mainEngine", me)
    p.set("soundConfig", {
        "sampleName": SAMPLE_ENGINE, "intakeMuffling": e.intake_muffling, "mainGain": e.main_gain_engine,
        "onLoadGain": 1.0, "offLoadGain": 0.5, "maxLoadMix": 0.7, "minLoadMix": 0,
        "eqLowGain": 2, "eqLowFreq": 300, "eqLowWidth": 0.2, "eqHighGain": -2, "eqHighFreq": 3000, "eqHighWidth": 0.2,
        "lowShelfGain": -3, "lowShelfFreq": 100, "highShelfGain": 0, "highShelfFreq": 6000,
        "fundamentalFrequencyCylinderCount": 4, "eqFundamentalGain": -2,
    })
    p.set("soundConfigExhaust", {
        "sampleName": SAMPLE_EXHAUST, "mainGain": e.main_gain_exhaust, "onLoadGain": 1.0, "offLoadGain": 0.55,
        "maxLoadMix": 0.75, "minLoadMix": 0, "eqLowGain": 4, "eqLowFreq": 200, "eqLowWidth": 0.3,
        "eqHighGain": -4, "eqHighFreq": 4500, "eqHighWidth": 0.3, "lowShelfGain": 0, "lowShelfFreq": 120,
        "highShelfGain": -2, "highShelfFreq": 6000, "fundamentalFrequencyCylinderCount": 4, "eqFundamentalGain": -1,
    })
    p.set("vehicleController", {
        "clutchLaunchStartRPM": 1700, "clutchLaunchTargetRPM": 2400,
        "highShiftUpRPM": e.limiter - 250,
        "highShiftDownRPM": [0, 0, 0, 2400, 3000, 3200, 3300, 3300],
    })
    mesh = f"{prefix}_{e.mesh}" if e.mesh else f"{prefix}_engine_{e.key}"
    p.flexbody(mesh, ["engine"])
    fy, ry, bz, tz, hw = layout["front_y"], layout["rear_y"], layout["bottom_z"], layout["top_z"], layout["half_w"]
    mx, my, mz = layout["mount"]
    w8 = e.mass * 0.78 / 8
    p.nodes_props(selfCollision=False, collision=True, nodeMaterial="|NM_METAL", frictionCoef=0.7, group="engine")
    p.nodes_props(engineGroup="engine_block")
    for nm, x, y, z in (("e1", hw * 0.80, fy, bz), ("e2", hw, fy, tz - 0.10), ("e3", hw * 0.80, ry, bz),
                        ("e4", hw, ry, tz - 0.10)):
        ex = {"isExhaust": "mainEngine"} if nm in ("e2", "e4") else {}
        p.node(nm + "l", x, y, z, nodeWeight=w8, **({} if exhaust_side < 0 else ex))
        p.node(nm + "r", -x, y, z, nodeWeight=w8, **(ex if exhaust_side < 0 else {}))
    p.nodes_props(engineGroup="engine_intake")
    p.node("e5", 0.0, (fy + ry) / 2, tz, nodeWeight=e.mass * 0.12,
           chemEnergy=2000, burnRate=0.39, flashPoint=800, specHeat=0.1, selfIgnitionCoef=False, smokePoint=650,
           baseTemp="thermals", conductionRadius=0.15)
    p.nodes_props(engineGroup="")
    p.nodes_props(collision=False, selfCollision=False)
    p.node("em1l", mx, my, mz, nodeWeight=e.mass * 0.05)
    p.node("em1r", -mx, my, mz, nodeWeight=e.mass * 0.05)
    p.nodes_props(group="", collision=True)
    p.beams_props(deformLimitExpansion=1.2)
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=9001000, beamDamp=250, beamDeform=200000, beamStrength="FLT_MAX")
    corners = ["e1l", "e1r", "e2l", "e2r", "e3l", "e3r", "e4l", "e4r"]
    for i, a in enumerate(corners):
        for b in corners[i + 1:]:
            p.beam(a, b)
    p.beams_props(beamSpring=5001000, beamDamp=200)
    for a in ("e2l", "e2r", "e4l", "e4r", "e1l", "e3r"):
        p.beam("e5", a)
    p.beam_comment("engine mounts (soft)")
    p.beams_props(beamSpring=601000, beamDamp=4500, beamDeform=40000, beamStrength=120000)
    p.beam("e1l", "em1l", name="engine", dampCutoffHz=500)
    for a in ("e2l", "e3l", "e4l", "e1r"):
        p.beam(a, "em1l", dampCutoffHz=500)
    p.beam("e1r", "em1r", dampCutoffHz=500)
    for a in ("e2r", "e3r", "e4r", "e1l"):
        p.beam(a, "em1r", dampCutoffHz=500)
    p.beam_comment("mount brackets to crossmember")
    p.beams_props(beamSpring=3001000, beamDamp=150, beamDeform=60000, beamStrength=250000)
    for side in ("l", "r"):
        for b in body_mounts:
            bn = b[:-1] if b.endswith("!") else b + side
            p.beam("em1" + side, bn)
    for a, b in mounts_extra:
        p.beam(a, b)
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.tris_props(dragCoef=5)
    for a, b, c in (("e1l", "e2l", "e4l"), ("e1l", "e4l", "e3l"), ("e1r", "e3r", "e4r"), ("e1r", "e4r", "e2r"),
                    ("e2l", "e2r", "e4r"), ("e2l", "e4r", "e4l"), ("e1l", "e3r", "e1r"), ("e1l", "e3l", "e3r"),
                    ("e1l", "e1r", "e2r"), ("e1l", "e2r", "e2l")):
        p.tri(a, b, c)
    return p


def engine_subparts(prefix, e: EngineDef):
    """intake / induction / ecu / internals variants for one engine."""
    out = []
    k = e.key
    # intakes
    intakes = [("stock", "Stock Air Box", 0, 120, 0, 0.0)]
    if k.startswith("k20"):
        intakes += [("itb", "Individual Throttle Bodies", 1, 2600, 22, -0.4), ("cai", "Cold Air Intake", 1, 380, 8, -0.2)]
    else:
        intakes += [("cai", "Cold Air Intake", 1, 300, 7, -0.2)]
    for key, title, mod, value, gain, muff in intakes:
        p = Part(f"{prefix}_{k}_intake_{key}", title, f"{prefix}_{k}_intake", value=value)
        if gain:
            top = e.torque[-1][0]
            p.set("mainEngine", {"torqueModIntake": [["rpm", "torque"]] + [[r, round(gain * min(1.0, r / (top * 0.8)) ** 2, 1)] for r, _ in e.torque]})
            p.set("soundConfig", {"$+intakeMuffling": muff, "$+mainGain": 1.5})
        p.flexbody(f"{prefix}_intake_{k.split('_')[0]}_{key}", ["engine"])
        out.append(p)
    # induction: N/A manifolds or turbo kits
    if not e.turbo:
        for key, title, value, gain in (("na", "Stock Exhaust Manifold", 150, 0), ("header", "Performance Header", 900, 9)):
            p = Part(f"{prefix}_{k}_induction_{key}", title, f"{prefix}_{k}_induction", value=value)
            if gain:
                p.set("mainEngine", {"torqueModExhaust": [["rpm", "torque"]] + [[r, round(gain * min(1.0, r / 6000.0), 1)] for r, _ in e.torque]})
                p.set("soundConfigExhaust", {"$+mainGain": 1.5})
            p.flexbody(f"{prefix}_manifold_{k.split('_')[0]}_{key}", ["engine"])
            out.append(p)
    kits = []
    if k == "sr20det":
        kits = ["t25_stock", "gt28_kit"]
    elif k == "ka24de":
        kits = ["kat_kit"]
    elif k == "k20a":
        kits = ["street_k20"]
    elif k == "k20a_race":
        kits = ["race_k20"]
    for tk in kits:
        out.append(turbo_part(prefix, k, tk))
    # ECUs
    p = Part(f"{prefix}_{k}_ecu_stock", "Stock ECU", f"{prefix}_{k}_ecu", value=200)
    p.set("mainEngine", {"revLimiterRPM": e.limiter})
    out.append(p)
    p = Part(f"{prefix}_{k}_ecu_race", "Standalone Race ECU (Adjustable)", f"{prefix}_{k}_ecu", value=1800)
    p.variable("$revLimiterRPM", "rpm", "Engine", e.limiter + (200 if k.startswith("k20") else 100), 3000,
               e.max_rpm - 100, "RPM Limit", "RPM where the rev limiter prevents further revving", stepDis=50)
    p.variable("$revLimiterCutTime", "s", "Engine", 0.08, 0.01, 0.5, "RPM Limit Cut Time", "How fast the rev limiter cycles",
               stepDis=0.01)
    p.controller("twoStepLaunch", rpmLimit=4500)
    p.set("mainEngine", {"hasRevLimiter": True, "revLimiterType": "timeBased", "revLimiterRPM": "$revLimiterRPM",
                         "revLimiterCutTime": "$revLimiterCutTime", "revLimiterMaxRPMDrop": 250,
                         "$*instantAfterFireCoef": 2.0, "$*sustainedAfterFireCoef": 2.0, **AFTERFIRE})
    p.set("vehicleController", {"highShiftUpRPM": "$=$revLimiterRPM - 200"})
    out.append(p)
    # internals
    p = Part(f"{prefix}_{k}_internals_stock", "Stock Long Block", f"{prefix}_{k}_internals", value=100)
    p.set("mainEngine", {})
    out.append(p)
    p = Part(f"{prefix}_{k}_internals_forged", "Forged Long Block", f"{prefix}_{k}_internals", value=4200)
    p.set("mainEngine", {"$*maxTorqueRating": 1.9, "$*maxOverTorqueDamage": 2.2, "$+maxRPM": 400, "$*inertia": 0.95,
                         "connectingRodDamageThreshold": 2600000, "pistonRingDamageThreshold": 2200000,
                         "headGasketDamageThreshold": 2200000, "cylinderWallTemperatureDamageThreshold": 260})
    out.append(p)
    return out


def turbo_part(prefix, engine_key, kit):
    t = TURBOS[kit]
    p = Part(f"{prefix}_{engine_key}_induction_{kit}", t["title"], f"{prefix}_{engine_key}_induction", value=t["value"])
    p.variable("$wastegateStart", "psi", "Engine", t["wg"], 3, t["wg_max"], "Wastegate Pressure",
               "Boost pressure where the wastegate starts to open", stepDis=0.5)
    p.flexbody(f"{prefix}_{t['mesh']}", ["engine"])
    p.flexbody(f"{prefix}_manifold_{engine_key.split('_')[0]}_turbo", ["engine"])
    # UNVERIFIED: turbocharger section layout written from vanilla content knowledge
    p.set("turbocharger", {
        "bovSoundFileName": "event:>Vehicle>Forced_Induction>Turbo_01>turbo_bov",
        "hissLoopEvent": "event:>Vehicle>Forced_Induction>Turbo_01>turbo_hiss",
        "whineLoopEvent": "event:>Vehicle>Forced_Induction>Turbo_01>turbo_spin",
        "turboSizeCoef": t["size"], "bovSoundVolumeCoef": 0.6, "hissVolumePerPSI": 0.035,
        "whineVolumePer10kRPM": 0.009, "whinePitchPer10kRPM": 0.05,
        "wastegateStart": "$wastegateStart", "wastegateLimit": "$=$wastegateStart + 1",
        "maxExhaustPower": int(6000 + 30000 * t["size"]), "backPressureCoef": 0.00003,
        "pressureRatePSI": 30, "frictionCoef": round(18 + 20 * t["size"], 1), "inertia": round(0.6 + 1.6 * t["size"], 2),
        "damageThresholdTemperature": 650,
        "pressurePSI": [["turbineRPM", "pressure"]] + t["curve"],
        "engineDef": [["engineRPM", "efficiency", "exhaustFactor"]] + ENGINE_EFF,
    })
    p.set("mainEngine", {"turbocharger": "turbocharger", "$*instantAfterFireCoef": 1.5, "$*sustainedAfterFireCoef": 1.5,
                         **AFTERFIRE})
    p.set("soundConfig", {"$+intakeMuffling": -0.2})
    return p


# --------------------------------------------------------------------------
# flywheel / clutch
# --------------------------------------------------------------------------
def flywheels(prefix):
    out = []
    for key, title, inertia, value, torque in (("stock", "Stock Flywheel & Clutch", 0.06, 200, 520),
                                               ("light", "Lightweight Flywheel & Sport Clutch", 0.025, 900, 800),
                                               ("race", "Twin-Plate Race Clutch", 0.012, 2600, 1400)):
        p = Part(f"{prefix}_flywheel_{key}", title, f"{prefix}_flywheel", value=value)
        p.set("clutch", {"uiName": "Clutch", "additionalEngineInertia": inertia, "clutchMass": 4 if key == "stock" else 3})
        out.append(p)
    return out


# --------------------------------------------------------------------------
# transmissions
# --------------------------------------------------------------------------
@dataclass
class GearboxDef:
    key: str
    title: str
    kind: str            # manual / sequential / automatic
    ratios: list         # forward
    reverse: float
    value: int
    mass: float = 40
    friction: float = 3
    whine: str = "straight_01"


GEARBOXES = {
    "5m": GearboxDef("5m", "5-Speed Manual (FS5W71C)", "manual", [3.321, 1.902, 1.308, 1.000, 0.759], 3.382, 1500, 42),
    "5m_sr": GearboxDef("5m_sr", "5-Speed Manual (FS5W71C, SR ratios)", "manual", [3.321, 1.902, 1.308, 1.000, 0.838], 3.382, 1600, 42),
    "4a": GearboxDef("4a", "4-Speed Automatic (RE4R01A)", "automatic", [2.785, 1.545, 1.000, 0.694], 2.272, 1700, 62),
    "6m_cd009": GearboxDef("6m_cd009", "6-Speed Manual (CD009 K-Swap Kit)", "manual", [3.794, 2.324, 1.624, 1.271, 1.000, 0.794], 3.446, 3200, 48),
    "6s_race": GearboxDef("6s_race", "6-Speed Sequential Dog Box (Track)", "sequential", [2.850, 2.050, 1.620, 1.330, 1.130, 0.980], 2.900, 16500, 36, 2.5),
    "4s_drag": GearboxDef("4s_drag", "4-Speed Sequential Dog Box (Drag)", "sequential", [2.350, 1.620, 1.240, 1.000], 2.600, 14500, 32, 2.2),
}


def gearbox_part(prefix, g: GearboxDef, layout, body_links):
    p = Part(f"{prefix}_transmission_{g.key}", g.title, f"{prefix}_transmission", value=g.value)
    p.slot(f"{prefix}_driveshaft", f"{prefix}_driveshaft", "Driveshaft", coreSlot=True)
    n = len(g.ratios)
    for i, r in enumerate(g.ratios, 1):
        p.variable(f"$gear_{i}", ":1", "Transmission", r, 0.5, 5.0, f"Gear {i} Ratio", "Torque multiplication ratio",
                   stepDis=0.001)
    p.variable("$gear_R", ":1", "Transmission", g.reverse, 0.5, 5.0, "Reverse Gear Ratio", "Torque multiplication ratio",
               stepDis=0.001)
    ratios = ["$=-$gear_R", 0] + [f"$gear_{i}" for i in range(1, n + 1)]
    whine_in = 0.55 if g.kind == "sequential" else 0.35
    gb = {"uiName": "Gearbox", "gearRatios": ratios, "friction": g.friction, "gearboxNode:": ["tra1"],
          "gearWhineCoefsInput": [whine_in] * (n + 2), "gearWhineCoefsOutput": [whine_in * 0.8] * (n + 2),
          "gearWhineInputEvent": "event:>Vehicle>Transmission>straight_01>twine_in_race",
          "gearWhineOutputEvent": "event:>Vehicle>Transmission>straight_01>twine_out_race"}
    if g.kind == "manual":
        p.powertrain("frictionClutch", "clutch", "mainEngine", 1)
        p.powertrain("manualGearbox", "gearbox", "clutch", 1)
        p.set("clutch", {"clutchFreePlay": 0.25, "warningTemp": 250, "maxSafeClutchTemp": 350, "maxClutchTemp": 600})
        p.set("vehicleController", {"calculateOptimalLoadShiftPoints": True, "shiftDownRPMOffsetCoef": 1.15,
                                    "lowShiftDownRPM": [0, 0, 0] + [1500] * (n - 1), "lowShiftUpRPM": [0, 0] + [2800] * (n - 1)})
        p.slot(f"{prefix}_shifter", f"{prefix}_shifter_stock", "Shifter")
    elif g.kind == "sequential":
        # UNVERIFIED device name "sequentialGearbox"
        p.powertrain("frictionClutch", "clutch", "mainEngine", 1)
        p.powertrain("sequentialGearbox", "gearbox", "clutch", 1)
        p.set("clutch", {"clutchFreePlay": 0.25, "warningTemp": 300, "maxSafeClutchTemp": 450, "maxClutchTemp": 700})
        p.set("vehicleController", {"calculateOptimalLoadShiftPoints": True, "ignitionCutTime": 0.08,
                                    "clutchLaunchStartRPM": 3500, "clutchLaunchTargetRPM": 5200})
        gb["gearWhineInputEvent"] = "event:>Vehicle>Transmission>straight_01>twine_in_race"
        p.slot(f"{prefix}_shifter", f"{prefix}_shifter_sequential", "Shifter")
    else:
        # UNVERIFIED: torqueConverter + automaticGearbox parameters
        p.powertrain("torqueConverter", "torqueConverter", "mainEngine", 1)
        p.powertrain("automaticGearbox", "gearbox", "torqueConverter", 1)
        p.set("torqueConverter", {"uiName": "Torque Converter", "converterDiameter": 0.24, "converterStiffness": 10,
                                  "couplingAVRatio": 0.9, "stallTorqueRatio": 1.9, "lockupClutchTorque": 320,
                                  "additionalEngineInertia": 0.08})
        gb.update({"parkLockTorque": 2500, "oneWayViscousCoef": 25, "gearChangeTime": 0.4})
        p.set("vehicleController", {"automaticModes": "PRND21", "useSmartAggressionCalculation": True,
                                    "lowShiftDownRPM": [0, 0, 0, 1300, 1500, 1500], "lowShiftUpRPM": [0, 0, 2300, 2200, 2100]})
        p.slot(f"{prefix}_shifter", f"{prefix}_shifter_auto", "Shifter")
    p.set("gearbox", gb)
    fy, ry, z = layout["front_y"], layout["rear_y"], layout["z"]
    p.flexbody(f"{prefix}_gearbox_{g.kind}", ["engine", "transmission"])
    p.nodes_props(selfCollision=False, collision=True, nodeMaterial="|NM_METAL", frictionCoef=0.7, group="transmission")
    p.node("tra1", 0.0, ry, z, nodeWeight=g.mass * 0.4)
    p.nodes_props(collision=False)
    p.node("tra2l", 0.11, fy + 0.15, z + 0.02, nodeWeight=g.mass * 0.3)
    p.node("tra2r", -0.11, fy + 0.15, z + 0.02, nodeWeight=g.mass * 0.3)
    p.nodes_props(group="", collision=True)
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=10001000, beamDamp=250, beamDeform=150000, beamStrength="FLT_MAX")
    for a, b in (("e3l", "tra1"), ("e3r", "tra1"), ("e4l", "tra1"), ("e4r", "tra1"), ("tra2l", "tra2r"),
                 ("tra2l", "e3l"), ("tra2r", "e3r"), ("tra2l", "e4l"), ("tra2r", "e4r"), ("tra2l", "e3r"),
                 ("tra2r", "e3l"), ("tra2l", "tra1"), ("tra2r", "tra1"), ("tra2l", "e1l"), ("tra2r", "e1r")):
        p.beam(a, b)
    p.beam_comment("transmission mount (rubber)")
    p.beams_props(beamSpring=801000, beamDamp=2000, beamDeform=40000, beamStrength=100000)
    for b in body_links:
        p.beam("tra1", b, dampCutoffHz=500)
    return p


def driveshaft_part(prefix, front_y, rear_y, z_front, z_rear, body_links):
    p = Part(f"{prefix}_driveshaft", "Two-Piece Driveshaft", f"{prefix}_driveshaft", value=300)
    p.powertrain("shaft", "driveshaft", "gearbox", 1, friction=1.5, breakTriggerBeam="driveshaft", uiName="Driveshaft")
    p.nodes_props(selfCollision=False, collision=True, nodeMaterial="|NM_METAL", frictionCoef=0.6, group="driveshaft")
    mid_y = 0.5 * (front_y + rear_y)
    p.node("ds1", 0.0, mid_y, 0.5 * (z_front + z_rear) - 0.01, nodeWeight=4.0)
    p.nodes_props(group="")
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=2001000, beamDamp=80, beamDeform=20000, beamStrength=40000)
    p.beam("ds1", "tra1", name="driveshaft")
    p.beam("ds1", "dh3")
    for b in body_links:
        p.beam("ds1", b)
    p.flexbody(f"{prefix}_driveshaft", ["transmission", "driveshaft", "differential"])
    return p


# --------------------------------------------------------------------------
# differentials (in the rear suspension)
# --------------------------------------------------------------------------
DIFFS = {
    "open": ("Open Differential", 250, dict(diffType="open")),
    "viscous": ("Viscous Limited Slip Differential", 650, dict(diffType="lsd", lsdPreload=30, lsdLockCoef=0.08, lsdRevLockCoef=0.03)),
    "lsd15": ("1.5-Way Clutch LSD (Adjustable)", 1450, dict(diffType="lsd", lsdPreload="$lsdpreload_R", lsdLockCoef="$lsdlockcoef_R",
                                                             lsdRevLockCoef="$lsdlockcoefrev_R")),
    "lsd2": ("2-Way Clutch LSD (Drift)", 1500, dict(diffType="lsd", lsdPreload="$lsdpreload_R", lsdLockCoef="$lsdlockcoef_R",
                                                    lsdRevLockCoef="$lsdlockcoefrev_R")),
    "welded": ("Welded Differential", 40, dict(diffType="lsd", lsdPreload=4000, lsdLockCoef=1.0, lsdRevLockCoef=1.0)),
    "spool": ("Drag Spool", 900, dict(diffType="lsd", lsdPreload=6000, lsdLockCoef=1.0, lsdRevLockCoef=1.0)),
}
LSD_DEFAULTS = {"lsd15": (120, 0.25, 0.12), "lsd2": (180, 0.35, 0.35)}


def diff_part(prefix, key, final_default, layout, body_links):
    title, value, args = DIFFS[key]
    p = Part(f"{prefix}_differential_R_{key}", title, f"{prefix}_differential_R", value=value)
    p.variable("$finaldrive_R", ":1", "Differentials", final_default, 2.5, 6.0, "Final Drive Gear Ratio",
               "Torque multiplication ratio", stepDis=0.01)
    if key in LSD_DEFAULTS:
        pre, lock, rev = LSD_DEFAULTS[key]
        p.variable("$lsdpreload_R", "N/m", "Differentials", pre, 0, 500, "Pre-load Torque", "Initial locking torque")
        p.variable("$lsdlockcoef_R", "", "Differentials", lock, 0, 0.6, "Power Lock Rate",
                   "Additional locking torque proportional to engine torque", minDis=0, maxDis=100)
        p.variable("$lsdlockcoefrev_R", "", "Differentials", rev, 0, 0.6, "Coast Lock Rate",
                   "Additional locking torque proportional to engine braking", minDis=0, maxDis=100)
    p.powertrain("torsionReactor", "torsionReactorR", "driveshaft", 1, gearRatio="$finaldrive_R")
    p.powertrain("differential", "differential_R", "torsionReactorR", 1, gearRatio=1, friction=4, uiName="Rear Differential",
                 defaultVirtualInertia=0.25, **args)
    p.set("torsionReactorR", {"torqueReactionNodes:": ["dh1", "dh2l", "dh2r"]})
    p.flexbody(f"{prefix}_diff_R", ["differential"])
    y, z = layout["y"], layout["z"]
    p.nodes_props(selfCollision=False, collision=True, nodeMaterial="|NM_METAL", frictionCoef=0.6, group="differential")
    p.node("dh1", 0.0, y, z, nodeWeight=12)
    p.node("dh2l", 0.16, y, z + 0.02, nodeWeight=7)
    p.node("dh2r", -0.16, y, z + 0.02, nodeWeight=7)
    p.node("dh3", 0.0, y - 0.24, z + 0.01, nodeWeight=5)
    p.nodes_props(group="")
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=8001000, beamDamp=200, beamDeform=120000, beamStrength="FLT_MAX")
    for a, b in (("dh1", "dh2l"), ("dh1", "dh2r"), ("dh2l", "dh2r"), ("dh3", "dh1"), ("dh3", "dh2l"), ("dh3", "dh2r")):
        p.beam(a, b)
    p.beam_comment("diff mounts to rear subframe")
    p.beams_props(beamSpring=3001000, beamDamp=300, beamDeform=60000, beamStrength=300000)
    for a, b in body_links:
        p.beam(a, b)
    p.beam_comment("half shafts")
    p.beams_props(beamPrecompression=1, beamType="|BOUNDED", beamLongBound=0.06, beamShortBound=0.06)
    p.beams_props(beamSpring=0, beamDamp=0, beamDeform=5000, beamStrength=8000, beamLimitSpring=5001000, beamLimitDamp=100)
    p.beams_props(breakGroupType=1, optional=True)
    p.beams_props(breakGroup="wheel_RR")
    p.beam("rw1r", "dh2r", name="halfshaft_RR")
    p.beams_props(breakGroup="wheel_RL")
    p.beam("rw1l", "dh2l", name="halfshaft_RL")
    p.beams_props(breakGroup="", breakGroupType=0, optional=False, beamLimitSpring=0, beamLimitDamp=0)
    p.beams_props(beamPrecompression=1, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.flexbody(f"{prefix}_halfshaft_RL", ["differential", "wheelhub_RL"])
    p.flexbody(f"{prefix}_halfshaft_RR", ["differential", "wheelhub_RR"])
    return p
