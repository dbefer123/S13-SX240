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


def write(mod):
    return write_configs(mod, VEH, hatch_configs(), BASE_INFO, PAINTS)
