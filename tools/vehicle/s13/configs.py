"""S13 240SX configurations (hatchback; coupe/convertible configs live with their bodies)."""
from __future__ import annotations

from collections import OrderedDict

from tools.vehicle.common.configs import Cfg, write_configs
from . import catalog as C

VEH = "s13_240sx"
P = "s13"

WHEEL_DIA = {w.key: w.dia for w in C.WHEELS}


def wheels(front, tire_f, rear=None, tire_r=None):
    rear = rear or front
    tire_r = tire_r or tire_f
    return {
        f"{P}_wheel_F": f"{P}_wheel_F_{front}", f"{P}_tire_F_{WHEEL_DIA[front]}": f"{P}_tire_F_{tire_f}",
        f"{P}_wheel_R": f"{P}_wheel_R_{rear}", f"{P}_tire_R_{WHEEL_DIA[rear]}": f"{P}_tire_R_{tire_r}",
    }


def engine(key, intake="stock", induction=None, ecu="stock", internals="stock", trans="5m", flywheel="stock"):
    d = {f"{P}_engine": f"{P}_engine_{key}", f"{P}_{key}_intake": f"{P}_{key}_intake_{intake}",
         f"{P}_{key}_ecu": f"{P}_{key}_ecu_{ecu}", f"{P}_{key}_internals": f"{P}_{key}_internals_{internals}",
         f"{P}_transmission": f"{P}_transmission_{trans}", f"{P}_flywheel": f"{P}_flywheel_{flywheel}"}
    if induction:
        d[f"{P}_{key}_induction"] = f"{P}_{key}_induction_{induction}"
    return d


def chassis(springs="stock", bars=("stock", "stock"), brakes="stock", pads="basic", diff="open", steering="stock"):
    return {f"{P}_spring_F": f"{P}_spring_F_{springs}", f"{P}_spring_R": f"{P}_spring_R_{springs}",
            f"{P}_swaybar_F": f"{P}_swaybar_F_{bars[0]}", f"{P}_swaybar_R": f"{P}_swaybar_R_{bars[1]}",
            f"{P}_brake_F": f"{P}_brake_F_{brakes}", f"{P}_brake_R": f"{P}_brake_R_{brakes}",
            f"{P}_brakepad_F": f"{P}_brakepad_F_{pads}", f"{P}_brakepad_R": f"{P}_brakepad_R_{pads}",
            f"{P}_differential_R": f"{P}_differential_R_{diff}", f"{P}_steering": f"{P}_steering_{steering}"}


def merge(*ds):
    out = OrderedDict()
    for d in ds:
        out.update(d)
    return out


PAINTS = OrderedDict([
    ("Super Red", {"baseColor": [0.52, 0.015, 0.02, 1.2], "metallic": 0.0, "roughness": 0.25, "clearcoat": 1.0, "clearcoatRoughness": 0.03}),
    ("Super Black", {"baseColor": [0.012, 0.012, 0.013, 1.2], "metallic": 0.0, "roughness": 0.22, "clearcoat": 1.0, "clearcoatRoughness": 0.02}),
    ("Crystal White", {"baseColor": [0.82, 0.82, 0.80, 1.2], "metallic": 0.0, "roughness": 0.3, "clearcoat": 1.0, "clearcoatRoughness": 0.04}),
    ("Cool Silver Metallic", {"baseColor": [0.48, 0.49, 0.50, 1.2], "metallic": 0.85, "roughness": 0.42, "clearcoat": 1.0, "clearcoatRoughness": 0.03}),
    ("Dark Green Pearl", {"baseColor": [0.02, 0.09, 0.06, 1.2], "metallic": 0.6, "roughness": 0.35, "clearcoat": 1.0, "clearcoatRoughness": 0.03}),
    ("Blue Black Pearl", {"baseColor": [0.012, 0.018, 0.045, 1.2], "metallic": 0.7, "roughness": 0.35, "clearcoat": 1.0, "clearcoatRoughness": 0.03}),
    ("Dark Gray Metallic", {"baseColor": [0.11, 0.11, 0.115, 1.2], "metallic": 0.85, "roughness": 0.4, "clearcoat": 1.0, "clearcoatRoughness": 0.03}),
    ("Warm White Pearl", {"baseColor": [0.86, 0.84, 0.78, 1.2], "metallic": 0.3, "roughness": 0.3, "clearcoat": 1.0, "clearcoatRoughness": 0.03}),
    ("Lime Green Metallic", {"baseColor": [0.32, 0.45, 0.12, 1.2], "metallic": 0.7, "roughness": 0.35, "clearcoat": 1.0, "clearcoatRoughness": 0.03}),
    ("Champagne Gold Metallic", {"baseColor": [0.55, 0.45, 0.30, 1.2], "metallic": 0.8, "roughness": 0.38, "clearcoat": 1.0, "clearcoatRoughness": 0.03}),
    ("Racing Yellow", {"class": "custom", "baseColor": [0.85, 0.62, 0.02, 1.2], "metallic": 0.0, "roughness": 0.25, "clearcoat": 1.0, "clearcoatRoughness": 0.03}),
    ("Racing Orange", {"class": "custom", "baseColor": [0.85, 0.22, 0.02, 1.2], "metallic": 0.0, "roughness": 0.25, "clearcoat": 1.0, "clearcoatRoughness": 0.03}),
    ("Grand Prix Blue", {"class": "custom", "baseColor": [0.02, 0.15, 0.55, 1.2], "metallic": 0.2, "roughness": 0.28, "clearcoat": 1.0, "clearcoatRoughness": 0.03}),
    ("Matte Black", {"class": "custom", "baseColor": [0.02, 0.02, 0.02, 1.2], "metallic": 0.0, "roughness": 0.85, "clearcoat": 0.0, "clearcoatRoughness": 0.6}),
    ("Primer Gray", {"class": "custom", "baseColor": [0.22, 0.22, 0.21, 1.2], "metallic": 0.0, "roughness": 0.9, "clearcoat": 0.0, "clearcoatRoughness": 0.8}),
])

BASE_INFO = OrderedDict([
    ("Name", "240SX (S13)"), ("Brand", "Nissan"), ("Author", "s13-sx240 mod"), ("Country", "Japan"),
    ("Type", "Car"), ("Body Style", "Hatchback"), ("Derby Class", "Compact Car"),
    ("Description", "Late-80s front-engine, rear-drive Japanese sports coupe. Fastback hatch with pop-up headlights, "
                    "built from scratch for this mod with a deep tuning catalogue up to tube-chassis K20 race cars."),
    ("default_pc", "se_1991"), ("defaultPaintName1", "Super Red"), ("Years", {"min": 1989, "max": 1994}),
])


def hatch_configs():
    se = merge(engine("ka24de"), chassis(diff="viscous"), wheels("oem15_se", "205_60_15_allseason"))
    out = [
        Cfg("base_1989", "Base (M)", "Factory", (1989, 1990),
            "The entry-level fastback: 140 hp KA24E SOHC, five-speed, open differential and 14\" steel wheels with hubcaps.",
            merge(engine("ka24e"), chassis(), wheels("steel14", "195_60_14_allseason")), paint="Super Black", value=13200,
            population=3),
        Cfg("xe_auto_1989", "XE (A)", "Factory", (1989, 1990),
            "Better equipped XE with the four-speed automatic and 15\" seven-spoke alloys.",
            merge(engine("ka24e", trans="4a"), {f"{P}_shifter": f"{P}_shifter_auto"}, chassis(),
                  wheels("oem15_le", "195_60_15_allseason")), paint="Crystal White", value=14500, population=3),
        Cfg("se_1991", "SE (M)", "Factory", (1991, 1994),
            "155 hp twin-cam KA24DE, five-speed manual and a viscous limited-slip differential.",
            dict(se), paint="Super Red", value=15900, population=4),
        Cfg("se_auto_1993", "SE (A)", "Factory", (1991, 1994),
            "SE with the electronically controlled four-speed automatic.",
            merge(se, engine("ka24de", trans="4a"), {f"{P}_shifter": f"{P}_shifter_auto"}), paint="Cool Silver Metallic",
            value=16600, population=3),
        Cfg("se_sport_1992", "SE Sport Package", "Factory", (1992, 1993),
            "SE with the Sport Package: firmer springs and dampers, thicker sway bars, ABS and summer tires.",
            merge(se, chassis(springs="sport", bars=("sport", "sport"), brakes="abs", diff="viscous"),
                  wheels("oem15_se", "205_55_15_sport")), paint="Dark Green Pearl", value=17400, population=2),
        Cfg("street_tuned", "Street Tuned", "Custom", (1991, 1994),
            "Tasteful street build: intake and header, street coilovers, Z32 brakes, 16\" forged wheels and a 1.5-way LSD.",
            merge(engine("ka24de", intake="cai", induction="header", flywheel="light"),
                  {f"{P}_shifter": f"{P}_shifter_short", f"{P}_steering_wheel": f"{P}_steering_wheel_deepdish"},
                  chassis(springs="street", bars=("sport", "sport"), brakes="z32", pads="sport", diff="lsd15"),
                  wheels("sixspoke16", "215_45_16_sport")), paint="Blue Black Pearl", value=21500),
        Cfg("kat_street", "KA-T Street", "Custom", (1991, 1994),
            "Turbocharged KA24DE on 14 psi: around 300 hp of torque-rich boost, coilovers and big brakes.",
            merge(engine("ka24de", intake="cai", induction="kat_kit", ecu="race", internals="forged", flywheel="light"),
                  {f"{P}_shifter": f"{P}_shifter_short"},
                  chassis(springs="street", bars=("sport", "sport"), brakes="z32", pads="sport", diff="lsd15"),
                  wheels("sixspoke16", "225_45_16_semislick")),
            vars={"$wastegateStart": 14, "$revLimiterRPM": 6800}, paint="Dark Gray Metallic", value=26800),
        Cfg("sr20det_swap", "SR20DET Swap", "Custom", (1991, 1994),
            "The classic swap: Silvia SR20DET with the stock T25 turned up, SR-ratio five-speed, coilovers and an LSD.",
            merge(engine("sr20det", intake="cai", induction="t25_stock", trans="5m_sr", flywheel="light"),
                  chassis(springs="street", bars=("sport", "sport"), brakes="z32", pads="sport", diff="lsd15"),
                  wheels("deepdish17", "215_45_17_sport")),
            vars={"$wastegateStart": 10}, paint="Crystal White", value=24500),
        Cfg("drift_missile", "Drift Missile", "Custom", (1991, 1994),
            "Grassroots drift car: SR20DET, welded diff, angle kit, drift coilovers and mismatched wheels.",
            merge(engine("sr20det", intake="cai", induction="t25_stock", trans="5m_sr", flywheel="light"),
                  {f"{P}_steering_wheel": f"{P}_steering_wheel_deepdish"},
                  chassis(springs="drift", bars=("race", "sport"), brakes="z32", pads="sport", diff="welded",
                          steering="anglekit"),
                  wheels("split18", "235_40_18_drift", "deepdish17", "255_40_17_drift")),
            vars={"$wastegateStart": 12, "$tirepressure_R": 40, "$camber_F": 0.975}, paint="Primer Gray",
            paint2="Racing Orange", value=14800),
        Cfg("k20_na_trackday", "K20 N/A Track Day", "Custom", (1991, 1994),
            "High-revving Honda K20A on individual throttle bodies, close-ratio six-speed, track coilovers and R-compound tires.",
            merge(engine("k20a", intake="itb", induction="header", ecu="race", trans="6m_cd009", flywheel="light"),
                  {f"{P}_shifter": f"{P}_shifter_short", f"{P}_steering_wheel": f"{P}_steering_wheel_race"},
                  chassis(springs="track", bars=("race", "race"), brakes="bbk", pads="semi-race", diff="lsd15",
                          steering="quick"),
                  wheels("race17", "235_40_17_semislick")),
            paint="Racing Yellow", value=38500),
        Cfg("autocross", "Autocross / Street Touring", "Custom", (1991, 1994),
            "Street Touring class build: KA24DE breathing mods, adjustable bars and grippy 16\" R-compound tires.",
            merge(engine("ka24de", intake="cai", induction="header"),
                  {f"{P}_shifter": f"{P}_shifter_short"},
                  chassis(springs="track", bars=("race", "race"), brakes="z32", pads="semi-race", diff="lsd15",
                          steering="quick"),
                  wheels("sixspoke16", "225_45_16_semislick")),
            vars={"$tirepressure_F": 30, "$tirepressure_R": 30}, paint="Grand Prix Blue", value=24800),
        Cfg("gravel_rally", "Gravel Rally", "Race", (1991, 1994),
            "Raised, long-travel gravel car with a tight 2-way LSD and quick steering.",
            merge(engine("ka24de", intake="cai", induction="header", ecu="race"),
                  {f"{P}_steering_wheel": f"{P}_steering_wheel_deepdish"},
                  chassis(springs="rally", bars=("sport", "stock"), brakes="z32", pads="semi-race", diff="lsd2",
                          steering="quick"),
                  wheels("mesh15", "195_60_15_allseason")),
            vars={"$finaldrive_R": 4.375}, paint="Crystal White", value=29500),
        Cfg("sleeper_k20", "Sleeper", "Custom", (1991, 1994),
            "Looks like a tired SE. Hides a turbocharged K20A making about 450 hp through a six-speed.",
            merge(engine("k20a", intake="stock", induction="street_k20", ecu="race", internals="forged",
                         trans="6m_cd009", flywheel="light"),
                  chassis(springs="sport", bars=("sport", "sport"), brakes="z32", pads="sport", diff="lsd15"),
                  wheels("oem15_se", "205_55_15_sport")),
            vars={"$wastegateStart": 17}, paint="Champagne Gold Metallic", value=31000),
        Cfg("stance", "Stance / Show", "Custom", (1991, 1994),
            "Slammed on coilovers with aggressive camber and wide 18\" wheels. Built for the parking lot.",
            merge(engine("ka24de", intake="cai", induction="header"),
                  {f"{P}_steering_wheel": f"{P}_steering_wheel_deepdish"},
                  chassis(springs="street", diff="viscous"),
                  wheels("split18", "235_40_18_drift")),
            vars={"$springheight_F": -0.075, "$springheight_R": -0.075, "$camber_F": 0.972, "$camber_R": 0.955,
                  "$trackoffset_F": 0.025, "$trackoffset_R": 0.035}, paint="Warm White Pearl", value=22000),
        Cfg("budget_drift", "Budget Drift Beater", "Custom", (1989, 1994),
            "Stock KA24DE, welded diff, lowering springs and whatever tires were cheapest.",
            merge(se, chassis(springs="sport", diff="welded"), wheels("oem15_se", "205_60_15_allseason",
                                                                        "oem15_se", "195_60_15_allseason")),
            vars={"$tirepressure_R": 42}, paint="Lime Green Metallic", value=6500),
    ]
    return out


def race_engine(boost, trans="6s_race"):
    return merge(engine("k20a_race", intake="cai", ecu="race", internals="forged", trans=trans, flywheel="race"),
                 {f"{P}_exhaust": f"{P}_exhaust_race", f"{P}_radiator": f"{P}_radiator_race",
                  f"{P}_shifter": f"{P}_shifter_sequential" if "s_" in trans else f"{P}_shifter_short"}), \
        {"$wastegateStart": boost}


def aero(splitter=True, canards=True, wing="wing_gt", diffuser=True, overfenders=True):
    return {f"{P}_splitter": f"{P}_splitter_race" if splitter else "", f"{P}_canards": f"{P}_canards_race" if canards else "",
            f"{P}_wing": f"{P}_{wing}" if wing else "", f"{P}_diffuser": f"{P}_diffuser_race" if diffuser else "",
            f"{P}_overfenders_R": f"{P}_overfenders_R" if overfenders else ""}


WIDE = {f"{P}_fender_L": f"{P}_fender_wide_L", f"{P}_fender_R": f"{P}_fender_wide_R"}
POPUP_DELETE = {f"{P}_popup_L": f"{P}_popup_delete_L", f"{P}_popup_R": f"{P}_popup_delete_R"}


def race_configs():
    out = []
    eng, v = race_engine(24)
    out.append(Cfg(
        "pro_drift", "Pro Drift", "Race", (1991, 1994),
        "Pro-level drift car: 600 hp turbo K20A, sequential box, wide body, full cage, angle kit and a 2-way LSD.",
        merge(eng, WIDE, POPUP_DELETE, aero(splitter=False, canards=False, wing="wing_gt", diffuser=False),
              {f"{P}_rollcage": f"{P}_rollcage_full", f"{P}_hood": f"{P}_hood_vented",
               f"{P}_interior": f"{P}_interior_stripped", f"{P}_electronics": f"{P}_electronics_track",
               f"{P}_steering_wheel": f"{P}_steering_wheel_race", f"{P}_fueltank": f"{P}_fueltank_racecell"},
              chassis(springs="drift", bars=("race", "race"), brakes="bbk", pads="full-race", diff="lsd2",
                      steering="anglekit"),
              wheels("split18", "235_40_18_drift", "split18", "265_35_18_drift")),
        vars={**v, "$wing_angle": 6, "$trackoffset_F": 0.035, "$trackoffset_R": 0.045, "$camber_F": 0.975,
              "$tirepressure_R": 38, "$springheight_F": -0.05, "$springheight_R": -0.05},
        paint="Racing Orange", value=85000))
    eng, v = race_engine(29)
    out.append(Cfg(
        "k20_track_spec", "K20 Track Spec (Tube Chassis, High Downforce)", "Race", (1994, 1994),
        "Purpose-built time attack weapon on a chromoly spaceframe: built K20A turbo at about 700 hp, six-speed sequential, "
        "slicks, full carbon aero with splitter, dive planes, flat floor diffuser and an adjustable swan-neck wing. "
        "About 1000 kg.",
        merge(eng, {f"{P}_body": f"{P}_body_tube", f"{P}_electronics": f"{P}_electronics_track",
                    f"{P}_fueltank": f"{P}_fueltank_racecell", f"{P}_canards": f"{P}_canards_race"},
              chassis(springs="track", bars=("race", "race"), brakes="bbk", pads="full-race", diff="lsd15",
                      steering="quick"),
              wheels("race18", "265_35_18_slick", "race18", "285_35_18_slick")),
        vars={**v, "$wing_angle": 12, "$trackoffset_F": 0.040, "$trackoffset_R": 0.050, "$springheight_F": -0.065,
              "$springheight_R": -0.06, "$camber_F": 0.972, "$camber_R": 0.975, "$brakebias": 0.62,
              "$tirepressure_F": 27, "$tirepressure_R": 27, "$finaldrive_R": 4.1},
        paint="Grand Prix Blue", paint2="Racing Yellow", value=165000))
    eng, v = race_engine(29, trans="4s_drag")
    out.append(Cfg(
        "k20_drag_spec", "K20 Drag Spec (Tube Chassis, Low Downforce)", "Race", (1994, 1994),
        "Tube-chassis drag car with the same 700 hp K20A turbo: four-speed sequential, spool, drag radials on beadlocks, "
        "front runners, wheelie bar, transbrake, two-step, line lock and a parachute. Low-drag wicker bill only. "
        "About 930 kg.",
        merge(eng, {f"{P}_body": f"{P}_body_tube", f"{P}_electronics": f"{P}_electronics_drag",
                    f"{P}_fueltank": f"{P}_fueltank_dragcell", f"{P}_wheeliebar": f"{P}_wheeliebar",
                    f"{P}_parachute": f"{P}_parachute", f"{P}_steering_wheel": f"{P}_steering_wheel_race",
                    f"{P}_hood": f"{P}_hood_carbon"},
              aero(splitter=False, canards=False, wing="wing_wicker", diffuser=False, overfenders=True),
              chassis(springs="drag", bars=("none", "race"), brakes="drag", pads="semi-race", diff="spool"),
              wheels("runner15", "165_80_15_runner", "beadlock15", "275_60_15_dragradial")),
        vars={**v, "$tirepressure_R": 14, "$tirepressure_F": 32, "$trackoffset_R": 0.030, "$revLimiterRPM": 9300,
              "$brakebias": 0.45, "$finaldrive_R": 3.9},
        paint="Super Black", paint2="Racing Orange", value=145000))
    eng, v = race_engine(22)
    out.append(Cfg(
        "k20_time_attack", "K20 Time Attack (Unibody)", "Race", (1991, 1994),
        "Street-chassis time attack car: 550 hp K20A turbo, seam-welded shell with a full cage, wide body and full aero.",
        merge(eng, WIDE, POPUP_DELETE, aero(),
              {f"{P}_rollcage": f"{P}_rollcage_full", f"{P}_hood": f"{P}_hood_carbon",
               f"{P}_interior": f"{P}_interior_race", f"{P}_electronics": f"{P}_electronics_track",
               f"{P}_fueltank": f"{P}_fueltank_racecell", f"{P}_door_L": f"{P}_door_light_L",
               f"{P}_door_R": f"{P}_door_light_R", f"{P}_hatch": f"{P}_hatch_light"},
              chassis(springs="track", bars=("race", "race"), brakes="bbk", pads="full-race", diff="lsd15",
                      steering="quick"),
              wheels("race18", "265_35_18_slick", "race18", "285_35_18_slick")),
        vars={**v, "$wing_angle": 10, "$trackoffset_F": 0.040, "$trackoffset_R": 0.050, "$springheight_F": -0.06,
              "$springheight_R": -0.055, "$camber_F": 0.972, "$brakebias": 0.63},
        paint="Super Black", value=120000))
    eng, v = race_engine(24, trans="6m_cd009")
    out.append(Cfg(
        "k20_drag_and_drive", "K20 Drag & Drive (Unibody)", "Race", (1991, 1994),
        "Street-registered drag car: 600 hp turbo K20A, six-speed, spool, drag radials, a 6-point cage and the interior "
        "still in place for the long drive home.",
        merge(eng, {f"{P}_shifter": f"{P}_shifter_short", f"{P}_rollcage": f"{P}_rollcage_cage6",
                    f"{P}_electronics": f"{P}_electronics_drag", f"{P}_interior": f"{P}_interior_stock",
                    f"{P}_steering_wheel": f"{P}_steering_wheel_deepdish"},
              chassis(springs="drag", bars=("none", "sport"), brakes="z32", pads="sport", diff="spool"),
              wheels("oem15_se", "205_60_15_allseason", "beadlock15", "275_60_15_dragradial")),
        vars={**v, "$tirepressure_R": 16, "$trackoffset_R": 0.020},
        paint="Super Red", value=72000))
    eng, v = race_engine(25)
    out.append(Cfg(
        "imsa_gto_tribute", "IMSA GTO Tribute", "Race", (1991, 1994),
        "Homage to the early-90s IMSA GTO 240SX: tube chassis, huge flares, pop-up delete and a tall wing, with a "
        "modern turbo K20A instead of the original V6.",
        merge(eng, {f"{P}_body": f"{P}_body_tube", f"{P}_electronics": f"{P}_electronics_track",
                    f"{P}_fueltank": f"{P}_fueltank_racecell", f"{P}_hood": f"{P}_hood_vented"},
              aero(canards=False),
              chassis(springs="track", bars=("race", "race"), brakes="bbk", pads="full-race", diff="lsd15",
                      steering="quick"),
              wheels("race17", "245_40_17_slick", "race18", "285_35_18_slick")),
        vars={**v, "$wing_angle": 14, "$trackoffset_F": 0.045, "$trackoffset_R": 0.055, "$springheight_F": -0.07,
              "$springheight_R": -0.065},
        paint="Crystal White", paint2="Super Red", paint3="Grand Prix Blue", value=150000))
    return out


def write(mod):
    return write_configs(mod, VEH, hatch_configs() + race_configs(), BASE_INFO, PAINTS)
