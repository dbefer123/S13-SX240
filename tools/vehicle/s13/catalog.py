"""S13 parts catalogue: wheels, tires, brakes, springs, sway bars, steering,
engines, gearboxes, differentials (data + generator calls)."""
from __future__ import annotations

from tools.vehicle.common import powertrain as PT
from tools.vehicle.common import suspension as SU
from tools.vehicle.common import wheels as WH
from . import dims as D

PFX = "s13"

# ---------------------------------------------------------------------------
# wheels / tires
# ---------------------------------------------------------------------------
WHEELS = [
    WH.WheelDef("steel14", "14x6 Steel Wheel with Hubcap", 14, 6.0, 8.5, 60, 4, "steel", hubcap=True),
    WH.WheelDef("oem15_le", "15x6 OEM Alloy (LE 7-spoke)", 15, 6.0, 7.6, 220, 4, "alloy"),
    WH.WheelDef("oem15_se", "15x6.5 OEM Alloy (SE 5-hole)", 15, 6.5, 7.8, 240, 4, "alloy"),
    WH.WheelDef("mesh15", "15x7 3-Piece Mesh", 15, 7.0, 7.4, 1100, 4, "mesh"),
    WH.WheelDef("sixspoke16", "16x7 Six-Spoke Forged", 16, 7.0, 6.6, 1300, 4, "race"),
    WH.WheelDef("deepdish17", "17x9 Deep-Dish 3-Piece", 17, 9.0, 9.8, 1800, 5, "deepdish"),
    WH.WheelDef("split18", "18x9.5 Split-Spoke Drift Wheel", 18, 9.5, 10.5, 1500, 5, "split"),
    WH.WheelDef("race17", "17x9 Six-Spoke Race Wheel", 17, 9.0, 7.9, 2400, 5, "race"),
    WH.WheelDef("race18", "18x10.5 Six-Spoke Race Wheel", 18, 10.5, 8.6, 2800, 5, "race"),
    WH.WheelDef("beadlock15", "15x10 Drag Beadlock", 15, 10.0, 8.2, 1400, 5, "beadlock"),
    WH.WheelDef("runner15", "15x3.5 Drag Front Runner", 15, 3.5, 3.6, 900, 5, "runner"),
]

TIRES = [
    WH.TireDef("195_60_14_allseason", "195/60R14 All-Season", 195, 60, 14, "allseason", 8.0, 90, 32),
    WH.TireDef("195_60_15_allseason", "195/60R15 All-Season", 195, 60, 15, "allseason", 8.5, 100, 32),
    WH.TireDef("205_60_15_allseason", "205/60R15 All-Season", 205, 60, 15, "allseason", 9.0, 110, 32),
    WH.TireDef("205_55_15_sport", "205/55R15 Summer Sport", 205, 55, 15, "sport", 8.8, 140, 32),
    WH.TireDef("205_50_15_semislick", "205/50R15 Semi-Slick", 205, 50, 15, "semislick", 8.5, 260, 30),
    WH.TireDef("215_45_16_sport", "215/45R16 Summer Sport", 215, 45, 16, "sport", 9.0, 170, 32),
    WH.TireDef("225_45_16_semislick", "225/45R16 Semi-Slick", 225, 45, 16, "semislick", 9.4, 290, 30),
    WH.TireDef("215_45_17_sport", "215/45R17 Summer Sport", 215, 45, 17, "sport", 9.2, 180, 32),
    WH.TireDef("235_40_17_semislick", "235/40R17 Semi-Slick", 235, 40, 17, "semislick", 9.8, 310, 30),
    WH.TireDef("255_40_17_drift", "255/40R17 Drift Tire", 255, 40, 17, "drift", 10.8, 160, 36),
    WH.TireDef("245_40_17_slick", "245/40R17 Racing Slick", 245, 40, 17, "slick", 9.4, 420, 26),
    WH.TireDef("235_40_18_drift", "235/40R18 Drift Tire", 235, 40, 18, "drift", 10.4, 170, 36),
    WH.TireDef("265_35_18_drift", "265/35R18 Drift Tire", 265, 35, 18, "drift", 11.2, 190, 36),
    WH.TireDef("265_35_18_slick", "265/35R18 Racing Slick", 265, 35, 18, "slick", 9.8, 460, 26),
    WH.TireDef("285_35_18_slick", "285/35R18 Racing Slick", 285, 35, 18, "slick", 10.4, 480, 26),
    WH.TireDef("275_60_15_dragradial", "275/60R15 Drag Radial", 275, 60, 15, "dragradial", 12.0, 420, 16),
    WH.TireDef("28x10_15_dragslick", "28x10.5-15 Drag Slick", 267, 75, 15, "dragslick", 11.5, 520, 12,
               radius_override=0.3556),
    WH.TireDef("165_80_15_runner", "26x4.5-15 Front Runner", 115, 80, 15, "runner", 4.2, 260, 35,
               radius_override=0.3302),
]

DEFAULT_TIRE = {14: "195_60_14_allseason", 15: "205_60_15_allseason", 16: "215_45_16_sport", 17: "215_45_17_sport",
                18: "265_35_18_slick"}
WHEEL_DEFAULT_TIRE = {"runner15": "165_80_15_runner", "beadlock15": "275_60_15_dragradial",
                      "split18": "265_35_18_drift", "race17": "245_40_17_slick", "race18": "265_35_18_slick",
                      "deepdish17": "255_40_17_drift"}

BRAKES = [
    WH.BrakeDef("stock", "Stock Disc Brakes", 1600, 820, 0.257, 0.258, 5.5, 4.8, 1.0, 0.7, "disc", "basic", 1100, 300),
    WH.BrakeDef("abs", "Stock Disc Brakes with ABS", 1600, 820, 0.257, 0.258, 5.5, 4.8, 1.0, 0.7, "disc", "basic", 1100, 650, abs=True),
    WH.BrakeDef("z32", "Z32 4-Piston Brake Upgrade", 2150, 1150, 0.296, 0.297, 7.6, 6.5, 1.15, 0.9, "vented-disc", "sport", 1300, 1400,
                mesh_F="s1x_brake_z32_F", mesh_R="s1x_brake_z32_R", caliper_F="s1x_caliper_z32_F", caliper_R="s1x_caliper_z32_R"),
    WH.BrakeDef("bbk", "Race Big Brake Kit (6-Piston)", 2900, 1500, 0.330, 0.310, 8.5, 6.8, 1.5, 1.2, "vented-disc", "full-race", 1500, 4200,
                mesh_F="s1x_brake_bbk_F", mesh_R="s1x_brake_bbk_R", caliper_F="s1x_caliper_bbk_F", caliper_R="s1x_caliper_bbk_R"),
    WH.BrakeDef("drag", "Lightweight Drag Brakes", 1500, 700, 0.280, 0.280, 3.2, 3.0, 1.0, 1.0, "disc", "semi-race", 1800, 1900,
                mesh_F="s1x_brake_drag_F", mesh_R="s1x_brake_drag_R", caliper_F="s1x_caliper_drag_F", caliper_R="s1x_caliper_drag_R"),
]

# static spring loads (N) for the reference SE hatch; configs adjust ride height through vars
STATIC_LOAD_F = 2950.0
STATIC_LOAD_R = 2600.0

SPRINGS_F = [  # key, title, k, bump, rebound, height default/min/max, value, adjustable, travel_c, travel_d
    ("stock", "Stock Struts", 24000, 1500, 3200, 0.0, -0.02, 0.02, 250, False, 0.075, 0.095),
    ("sport", "Lowering Springs & Sport Shocks", 34000, 2000, 4200, -0.030, -0.05, 0.0, 600, False, 0.060, 0.085),
    ("street", "Street Coilovers", 58000, 2600, 5200, -0.040, -0.08, 0.02, 1400, True, 0.055, 0.080),
    ("track", "Track Coilovers (2-Way Adjustable)", 98000, 3800, 7600, -0.055, -0.09, 0.0, 3400, True, 0.045, 0.070),
    ("drift", "Drift Coilovers", 78000, 3000, 6400, -0.050, -0.09, 0.0, 2200, True, 0.050, 0.075),
    ("drag", "Drag Struts (Front)", 26000, 900, 5500, 0.020, -0.03, 0.06, 2600, True, 0.070, 0.140),
    ("rally", "Gravel Rally Struts", 40000, 2600, 5000, 0.040, 0.0, 0.08, 2800, True, 0.090, 0.120),
]
SPRINGS_R = [
    ("stock", "Stock Shocks & Springs", 22000, 1500, 3000, 0.0, -0.02, 0.02, 250, False, 0.080, 0.100),
    ("sport", "Lowering Springs & Sport Shocks", 30000, 1900, 3900, -0.030, -0.05, 0.0, 600, False, 0.065, 0.090),
    ("street", "Street Coilovers", 50000, 2400, 4800, -0.040, -0.08, 0.02, 1400, True, 0.060, 0.085),
    ("track", "Track Coilovers (2-Way Adjustable)", 82000, 3400, 6800, -0.055, -0.09, 0.0, 3400, True, 0.050, 0.075),
    ("drift", "Drift Coilovers", 62000, 2800, 5600, -0.050, -0.09, 0.0, 2200, True, 0.055, 0.080),
    ("drag", "Drag Coilovers (Rear)", 46000, 2400, 3200, -0.010, -0.05, 0.04, 2600, True, 0.070, 0.090),
    ("rally", "Gravel Rally Shocks", 36000, 2400, 4600, 0.040, 0.0, 0.08, 2800, True, 0.095, 0.125),
]
SWAYBARS_F = [("stock", "Stock Front Sway Bar", 26000, 120, False), ("sport", "Sport Front Sway Bar", 42000, 380, False),
              ("race", "Adjustable Race Front Sway Bar", 60000, 900, True), ("none", "No Front Sway Bar", 0, 0, False)]
SWAYBARS_R = [("stock", "Stock Rear Sway Bar", 12000, 110, False), ("sport", "Sport Rear Sway Bar", 22000, 340, False),
              ("race", "Adjustable Race Rear Sway Bar", 32000, 850, True), ("none", "No Rear Sway Bar", 0, 0, False)]
STEERING = [("stock", "Stock Power Steering Rack", 470, 36, 200), ("quick", "Quick Ratio Rack", 360, 36, 900),
            ("anglekit", "Drift Angle Kit (Extended Lock)", 420, 58, 1500)]

GEARBOX_DEFAULT_FINAL = {"5m": 4.083, "5m_sr": 4.111, "4a": 4.083, "6m_cd009": 4.300, "6s_race": 4.300, "4s_drag": 3.700}

ENGINE_LAYOUT = dict(front_y=D.ENGINE_FRONT_Y + 0.04, rear_y=D.ENGINE_REAR_Y - 0.02, bottom_z=0.215, top_z=0.735,
                     half_w=0.205, mount=(0.300, -1.300, 0.360))
ENGINE_BODY_MOUNTS = ["fc1", "fr3", "fr2", "fa3"]
TRANS_LAYOUT = dict(front_y=D.ENGINE_REAR_Y, rear_y=D.TRANS_REAR_Y, z=0.300)
TRANS_BODY_LINKS = ["fl1", "fl1l", "fl1r", "fp1"]
DIFF_LAYOUT = dict(y=D.DIFF_Y, z=D.DIFF_Z)
DIFF_BODY_LINKS = [("dh1", "rx1l"), ("dh1", "rx1r"), ("dh1", "rx3l"), ("dh1", "rx3r"), ("dh2l", "rx1l"), ("dh2r", "rx1r"),
                   ("dh2l", "rx2l"), ("dh2r", "rx2r"), ("dh3", "rx1l"), ("dh3", "rx1r"), ("dh2l", "rx3l"), ("dh2r", "rx3r")]

FRONT_SUSP_LINKS = {
    "fx1": ["fc1", "fr3", "fr2", "fc1!"],
    "fx2": ["fc2", "fr1", "fr2", "fa1"],
    "fu1": ["fa2", "fr2", "fa3", "fs1", "ft2"],
    "fu2": ["fa3", "fr3", "fs1", "fp2", "ft3"],
}
RACK_LINKS = ["fc2", "fc1", "fr2", "fc1!"]
REAR_SUSP_LINKS = {
    "rx1": ["rm1", "rr1", "fl5!"],
    "rx2": ["rm2", "rr1", "fl6!"],
    "rx3": ["rr1", "rm2", "rt1", "rm1"],
    "rx4": ["rm2", "rr2", "fl7!"],
    "rx5": ["rm1", "fl4", "si5", "fl5"],
}


def wheel_parts():
    parts = []
    for axle in ("F", "R"):
        cx = f"{(D.TRACK_F if axle == 'F' else D.TRACK_R) / 2:.4f}+$trackoffset_{axle}"
        for w in WHEELS:
            tkey = WHEEL_DEFAULT_TIRE.get(w.key, DEFAULT_TIRE[w.dia])
            parts.append(WH.wheel_part(PFX, w, axle, cx, f"{PFX}_tire_{axle}_{tkey}"))
        for t in TIRES:
            parts.append(WH.tire_part(PFX, t, axle, cx))
        parts.append(WH.hubcap_part(PFX, axle, 14, cx))
    for b in BRAKES:
        parts.append(WH.brake_part(PFX, b, "F", f"{PFX}_hub_F"))
        parts.append(WH.brake_part(PFX, b, "R", f"{PFX}_hub_R"))
    parts += WH.pad_parts(PFX)
    return parts


def suspension_parts():
    parts = [
        SU.front_suspension(PFX, D, FRONT_SUSP_LINKS, default_wheel=f"{PFX}_wheel_F_oem15_se"),
        SU.wheeldata_front(PFX, D),
        SU.rear_suspension(PFX, D, REAR_SUSP_LINKS, default_wheel=f"{PFX}_wheel_R_oem15_se"),
        SU.wheeldata_rear(PFX),
    ]
    for key, title, k, b, r, hd, hmin, hmax, value, adj, tc, td in SPRINGS_F:
        parts.append(SU.struts_front(PFX, key, title, k, b, r, hd, hmin, hmax, value, STATIC_LOAD_F,
                                     travel_c=tc, travel_d=td, adjustable=adj))
    for key, title, k, b, r, hd, hmin, hmax, value, adj, tc, td in SPRINGS_R:
        parts.append(SU.shocks_rear(PFX, key, title, k, b, r, hd, hmin, hmax, value, STATIC_LOAD_R,
                                    travel_c=tc, travel_d=td, adjustable=adj))
    for key, title, rate, value, adj in SWAYBARS_F:
        p = SU.swaybar_front(PFX, key, title, rate, value, adjustable=adj)
        if rate == 0:
            p._tables.pop("torsionbars", None)
            p._tables.pop("flexbodies", None)
        parts.append(p)
    for key, title, rate, value, adj in SWAYBARS_R:
        p = SU.swaybar_rear(PFX, key, title, rate, value, adjustable=adj)
        if rate == 0:
            p._tables.pop("torsionbars", None)
            p._tables.pop("flexbodies", None)
        parts.append(p)
    for key, title, lock, angle, value in STEERING:
        parts.append(SU.steering(PFX, D, key, title, lock, angle, value, RACK_LINKS))
    return parts


def powertrain_parts(engines=("ka24e", "ka24de", "sr20det", "k20a", "k20a_race")):
    parts = []
    for k in engines:
        e = PT.ENGINES[k]
        default_trans = {"ka24e": "5m", "ka24de": "5m", "sr20det": "5m_sr", "k20a": "6m_cd009", "k20a_race": "6s_race"}[k]
        parts.append(PT.engine_part(PFX, e, ENGINE_LAYOUT, ENGINE_BODY_MOUNTS, f"{PFX}_transmission_{default_trans}"))
        parts += PT.engine_subparts(PFX, e)
    for g in PT.GEARBOXES.values():
        parts.append(PT.gearbox_part(PFX, g, TRANS_LAYOUT, TRANS_BODY_LINKS))
    parts += PT.flywheels(PFX)
    parts.append(PT.driveshaft_part(PFX, D.TRANS_REAR_Y, D.DIFF_Y - 0.24, 0.30, 0.31, ["fl3", "fl3l", "fl3r"]))
    for key in PT.DIFFS:
        parts.append(PT.diff_part(PFX, key, 4.083, DIFF_LAYOUT, DIFF_BODY_LINKS))
    return parts
