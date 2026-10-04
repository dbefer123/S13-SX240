"""S14 240SX configurations (zenki 1995-96, kouki 1997-98 and builds).

The part/slot helpers are the S13 ones; their s13_ names are re-prefixed for the S14."""
from __future__ import annotations

from collections import OrderedDict

from tools.vehicle.common.configs import Cfg, write_configs
from tools.vehicle.s13 import configs as C13
from .vehicle import _rename

VEH = "s14_240sx"
P = "s14"


def merge(*ds):
    return _rename(C13.merge(*ds))


engine, chassis, wheels = C13.engine, C13.chassis, C13.wheels

KOUKI = {f"{P}_hood": f"{P}_hood_kouki", f"{P}_bumper_F": f"{P}_bumper_F_kouki",
         f"{P}_headlights": f"{P}_headlights_kouki", f"{P}_taillights": f"{P}_taillights_kouki",
         f"{P}_taillights_inner": f"{P}_taillights_inner_kouki"}
AERO_KIT = {f"{P}_bumper_F": f"{P}_bumper_F_kouki_aero", f"{P}_bumper_R": f"{P}_bumper_R_aero",
            f"{P}_sideskirts": f"{P}_sideskirts_aero"}
CARBON_LIP = {f"{P}_bumper_F": f"{P}_bumper_F_kouki_carbon"}
WING = {f"{P}_trunkspoiler": f"{P}_trunkspoiler_oem"}
LIP = {f"{P}_trunkspoiler": f"{P}_trunkspoiler_lip"}

PAINTS = OrderedDict([
    ("Super Black", C13.PAINTS["Super Black"]),
    ("Aspen White Pearl", {"baseColor": [0.84, 0.84, 0.82, 1.2], "metallic": 0.3, "roughness": 0.3, "clearcoat": 1.0,
                           "clearcoatRoughness": 0.03}),
    ("Cherry Red Pearl", {"baseColor": [0.42, 0.02, 0.03, 1.2], "metallic": 0.5, "roughness": 0.3, "clearcoat": 1.0,
                          "clearcoatRoughness": 0.03}),
    ("Silverstone Metallic", {"baseColor": [0.55, 0.56, 0.57, 1.2], "metallic": 0.85, "roughness": 0.38, "clearcoat": 1.0,
                              "clearcoatRoughness": 0.03}),
    ("Deep Emerald Pearl", {"baseColor": [0.01, 0.07, 0.05, 1.2], "metallic": 0.6, "roughness": 0.35, "clearcoat": 1.0,
                            "clearcoatRoughness": 0.03}),
    ("Midnight Purple Pearl", {"baseColor": [0.05, 0.02, 0.08, 1.2], "metallic": 0.7, "roughness": 0.33, "clearcoat": 1.0,
                               "clearcoatRoughness": 0.03}),
    ("Blue Black Pearl", C13.PAINTS["Blue Black Pearl"]),
    ("Dark Gray Metallic", C13.PAINTS["Dark Gray Metallic"]),
    ("Super Red", C13.PAINTS["Super Red"]),
    ("Racing Yellow", C13.PAINTS["Racing Yellow"]),
    ("Racing Orange", C13.PAINTS["Racing Orange"]),
    ("Grand Prix Blue", C13.PAINTS["Grand Prix Blue"]),
    ("Matte Black", C13.PAINTS["Matte Black"]),
    ("Primer Gray", C13.PAINTS["Primer Gray"]),
])

BASE_INFO = OrderedDict([
    ("Name", "240SX (S14)"), ("Brand", "Nissan"), ("Author", "s13-sx240 mod"), ("Country", "Japan"),
    ("Type", "Car"), ("Body Style", "Coupe"), ("Derby Class", "Compact Car"),
    ("Description", "Mid-90s rear-drive coupe: the S14 240SX with fixed headlamps, in early (zenki) and facelift "
                    "(kouki) form, sharing the S13's drivetrain catalogue up to turbo K20 race builds."),
    ("default_pc", "se_kouki_1998"), ("defaultPaintName1", "Aspen White Pearl"), ("Years", {"min": 1995, "max": 1998}),
])


def configs():
    se = merge(engine("ka24de"), chassis(diff="viscous"), wheels("oem16_s14", "205_55_16_sport"), WING)
    out = [
        Cfg("base_zenki_1995", "Base Zenki (M)", "Factory", (1995, 1996),
            "The early S14: 155 hp KA24DE, five-speed, open differential and 15\" five-spoke alloys.",
            merge(engine("ka24de"), chassis(), wheels("oem15_s14", "205_60_15_allseason")), paint="Cherry Red Pearl",
            value=17900, population=3),
        Cfg("se_zenki_auto_1996", "SE Zenki (A)", "Factory", (1995, 1996),
            "Zenki SE with the four-speed automatic, viscous LSD, 16\" alloys and the rear wing.",
            merge(se, engine("ka24de", trans="4a"), {f"{P}_shifter": f"{P}_shifter_auto"}), paint="Silverstone Metallic",
            value=21200, population=3),
        Cfg("le_kouki_1997", "LE Kouki (A)", "Factory", (1997, 1998),
            "Facelifted kouki front and smoked tail lamps, leather interior and the automatic.",
            merge(engine("ka24de", trans="4a"), chassis(diff="viscous"), wheels("oem15_s14", "205_60_15_allseason"),
                  KOUKI, {f"{P}_shifter": f"{P}_shifter_auto", f"{P}_interior": f"{P}_interior_leather"}),
            paint="Deep Emerald Pearl", value=22400, population=2),
        Cfg("se_kouki_1998", "SE Kouki (M)", "Factory", (1997, 1998),
            "Kouki SE: five-speed, viscous LSD, sport suspension, 16\" alloys and the three-post rear wing.",
            merge(se, KOUKI, chassis(springs="sport", bars=("sport", "sport"), brakes="abs", diff="viscous")),
            paint="Aspen White Pearl", value=22900, population=4),
        Cfg("kouki_street", "Kouki Street", "Custom", (1997, 1998),
            "Clean street build: aero lip, valance and side skirts, intake and header, street coilovers, Z32 brakes, 17\" "
            "deep-dish wheels and a 1.5-way LSD.",
            merge(engine("ka24de", intake="cai", induction="header", flywheel="light"), KOUKI, AERO_KIT, LIP,
                  {f"{P}_shifter": f"{P}_shifter_short", f"{P}_steering_wheel": f"{P}_steering_wheel_deepdish"},
                  chassis(springs="street", bars=("sport", "sport"), brakes="z32", pads="sport", diff="lsd15"),
                  wheels("deepdish17", "215_45_17_sport", "deepdish17", "235_40_17_semislick")),
            vars={"$springheight_F": -0.04, "$springheight_R": -0.04}, paint="Midnight Purple Pearl", value=27500),
        Cfg("sr20det_kouki_swap", "SR20DET Black Top Swap (Kouki Conversion)", "Custom", (1995, 1998),
            "The classic recipe: a zenki shell with a kouki front-end conversion and a black-top SR20DET on a bigger turbo.",
            merge(engine("sr20det", intake="cai", induction="t25_stock", trans="5m_sr", ecu="race", flywheel="light"), KOUKI,
                  CARBON_LIP, WING, chassis(springs="street", bars=("sport", "sport"), brakes="z32", pads="sport", diff="lsd15"),
                  wheels("split18", "235_40_18_drift")),
            vars={"$wastegateStart": 13}, paint="Super Black", value=29800),
        Cfg("drift_missile_s14", "Drift Missile", "Custom", (1995, 1998),
            "Grassroots S14 drift car: SR20DET, welded diff, angle kit, hydraulic handbrake and mismatched wheels.",
            merge(engine("sr20det", intake="cai", induction="t25_stock", trans="5m_sr", flywheel="light"),
                  {f"{P}_steering_wheel": f"{P}_steering_wheel_deepdish", "paint_design": f"{P}_skin_drift",
                   f"{P}_handbrake": f"{P}_handbrake_hydro", f"{P}_interior": f"{P}_interior_stripped", f"{P}_headliner": "",
                   f"{P}_rollcage": f"{P}_rollcage_rollbar"},
                  chassis(springs="drift", bars=("race", "sport"), brakes="z32", pads="sport", diff="welded",
                          steering="anglekit"),
                  wheels("split18", "235_40_18_drift", "deepdish17", "255_40_17_drift")),
            vars={"$wastegateStart": 12, "$tirepressure_R": 40, "$camber_F": 0.975}, paint="Primer Gray",
            paint2="Racing Yellow", value=15500),
    ]
    eng, v = C13.race_engine(24)
    out.append(Cfg(
        "pro_drift_s14", "Pro Drift", "Race", (1997, 1998),
        "Pro-level kouki drift car: 600 hp turbo K20A, six-speed sequential, 2-way LSD, angle kit, wide fenders, full cage "
        "and a GT wing.",
        merge(eng, KOUKI, CARBON_LIP, {f"{P}_fender_L": f"{P}_fender_wide_L", f"{P}_fender_R": f"{P}_fender_wide_R",
                           f"{P}_wing": f"{P}_wing_gt", f"{P}_trunkspoiler": "", f"{P}_rollcage": f"{P}_rollcage_full",
                           f"{P}_hood": f"{P}_hood_vented", f"{P}_interior": f"{P}_interior_stripped", f"{P}_headliner": "",
                           f"{P}_electronics": f"{P}_electronics_track", f"{P}_steering_wheel": f"{P}_steering_wheel_race",
                           f"{P}_fueltank": f"{P}_fueltank_racecell", "paint_design": f"{P}_skin_stripes",
                           f"{P}_handbrake": f"{P}_handbrake_hydro"},
              chassis(springs="drift", bars=("race", "race"), brakes="bbk", pads="full-race", diff="lsd2",
                      steering="anglekit"),
              wheels("split18", "235_40_18_drift", "split18", "265_35_18_drift")),
        vars={**v, "$wing_angle": 6, "$trackoffset_F": 0.035, "$trackoffset_R": 0.045, "$camber_F": 0.975,
              "$tirepressure_R": 38, "$springheight_F": -0.05, "$springheight_R": -0.05},
        paint="Grand Prix Blue", paint2="Super Black", value=88000))
    eng, v = C13.race_engine(26)
    out.append(Cfg(
        "k20_time_attack_s14", "K20 Time Attack", "Race", (1997, 1998),
        "High-downforce time attack S14: 640 hp turbo K20A, sequential, splitter, dive planes, flat-floor diffuser and an "
        "adjustable swan-neck wing, carbon panels, full cage, slicks.",
        merge(eng, KOUKI, {f"{P}_fender_L": f"{P}_fender_wide_L", f"{P}_fender_R": f"{P}_fender_wide_R",
                           f"{P}_splitter": f"{P}_splitter_race", f"{P}_canards": f"{P}_canards_race",
                           f"{P}_wing": f"{P}_wing_gt", f"{P}_diffuser": f"{P}_diffuser_race", f"{P}_trunkspoiler": "",
                           f"{P}_overfenders_R": f"{P}_overfenders_R", f"{P}_rollcage": f"{P}_rollcage_full",
                           f"{P}_hood": f"{P}_hood_carbon", f"{P}_trunk": f"{P}_trunk_light",
                           f"{P}_door_L": f"{P}_door_light_L", f"{P}_door_R": f"{P}_door_light_R",
                           f"{P}_interior": f"{P}_interior_race", f"{P}_headliner": "",
                           f"{P}_electronics": f"{P}_electronics_track", f"{P}_fueltank": f"{P}_fueltank_racecell",
                           "paint_design": f"{P}_skin_track"},
              chassis(springs="track", bars=("race", "race"), brakes="bbk", pads="full-race", diff="lsd15",
                      steering="quick"),
              wheels("race18", "265_35_18_slick", "race18", "285_35_18_slick")),
        vars={**v, "$wing_angle": 12, "$trackoffset_F": 0.040, "$trackoffset_R": 0.050, "$springheight_F": -0.06,
              "$springheight_R": -0.055, "$camber_F": 0.972, "$brakebias": 0.63},
        paint="Racing Yellow", paint2="Super Black", paint3="Grand Prix Blue", value=135000))
    for c in out:
        c.parts = _rename(c.parts)
        c.body = "Coupe"
    return out


def write(mod):
    return write_configs(mod, VEH, configs(), BASE_INFO, PAINTS)
