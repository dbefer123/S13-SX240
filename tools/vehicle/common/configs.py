"""Config (.pc) + info file generation with estimated performance figures.

Stats come from the resolved part tree: engine torque table (+ intake/exhaust
torque mods) times the turbo boost factor, mass from the nodes + wheels + fuel,
gearing for top speed, and a simple longitudinal simulation for 0-60/0-100.
They are estimates written into info_*.json (the game's own test tool can
regenerate them).
"""
from __future__ import annotations

import json
import math
import os
from collections import OrderedDict
from dataclasses import dataclass, field

import numpy as np

from tools.jbeam import PartDB, resolve
from tools.validate import physics as PH

PSI_ATM = 14.7
G = 9.81


@dataclass
class Cfg:
    key: str
    title: str
    ctype: str                       # Factory / Custom / Race
    years: tuple
    desc: str
    parts: dict
    vars: dict = field(default_factory=dict)
    paint: str = "Super Red"
    paint2: str | None = None
    paint3: str | None = None
    value: int = 10000
    population: int = 0
    phase: int = 2                   # build phase that provides every part (for staged generation)


def _interp(table, x):
    xs = [r[0] for r in table]
    ys = [r[1] for r in table]
    return float(np.interp(x, xs, ys))


def engine_curve(res):
    """(rpm array, torque Nm array, boost psi) of the main engine with mods and turbo."""
    me = res.dicts.get("mainEngine", {})
    tq = [r for r in me.get("torque", []) if isinstance(r[0], (int, float))]
    if not tq:
        return None
    rpm = np.arange(500, float(me.get("maxRPM", 7000)) + 1, 50.0)
    base = np.array([_interp(tq, r) for r in rpm])
    for k in ("torqueModIntake", "torqueModExhaust"):
        mod = [r for r in me.get(k, []) if isinstance(r[0], (int, float))]
        if mod:
            base = base + np.array([_interp(mod, r) for r in rpm])
    boost = 0.0
    tc = res.dicts.get("turbocharger") if me.get("turbocharger") else None
    if tc:
        boost = float(tc.get("wastegateStart", 0) or 0)
        eff = [r for r in tc.get("engineDef", []) if isinstance(r[0], (int, float))]
        e = np.array([_interp([[a, b] for a, b, *_ in eff], r) for r in rpm]) if eff else np.ones_like(rpm)
        # boost builds with rpm (spool): full boost from ~45 % of max rpm
        spool = np.clip((rpm - 0.25 * rpm.max()) / (0.25 * rpm.max()), 0, 1)
        base = base * (1 + boost / PSI_ATM * e * spool)
    lim = float(me.get("revLimiterRPM", me.get("maxRPM", 7000)) or 7000)
    mask = rpm <= lim
    return rpm[mask], base[mask], boost


def gearing(res):
    gb = res.dicts.get("gearbox", {})
    ratios = gb.get("gearRatios") or []
    fwd = [float(r) for r in ratios if isinstance(r, (int, float)) and r > 0]
    fd = float(res.variables.get("$finaldrive_R", 4.0) or 4.0)
    gtype = next((r.get("type") for r in res.tables.get("powertrain", []) if r.get("name") == "gearbox"), "manualGearbox")
    return fwd, fd, gtype


def tire_radius(res):
    rs = [float(r.get("radius")) for r in res.tables.get("pressureWheels", []) if r.get("name") and r.get("radius")]
    return max(rs) if rs else 0.30


def estimate(res, cda=0.72, crr=0.014, mu=1.0, drag_cda=None, downforce_cla=0.0):
    out = {}
    curve = engine_curve(res)
    nodes_mass, cog = PH.mass_props(res.nodes)
    wheels = 0.0
    for r in res.tables.get("pressureWheels", []):
        if r.get("name"):
            nr = float(r.get("numRays", 16) or 16)
            wheels += 2 * nr * (float(r.get("hubNodeWeight", 0) or 0) + float(r.get("nodeWeight", 0) or 0))
    fuel = float(res.variables.get("$fuel", 0) or 0) * 0.74
    mass = nodes_mass + wheels + fuel
    out["Weight"] = round(mass)
    if not curve:
        return out
    rpm, tq, boost = curve
    pw = tq * rpm / 7121.0                              # hp (mechanical)
    i = int(np.argmax(pw))
    j = int(np.argmax(tq))
    out["Power"] = round(float(pw[i]))
    out["Torque"] = round(float(tq[j]))
    out["PowerPeakRPM"] = f"{int(rpm[i] // 100 * 100)}"
    out["TorquePeakRPM"] = f"{int(rpm[j] // 100 * 100)}"
    out["Weight/Power"] = round(mass / max(out["Power"], 1), 2)
    out["Induction Type"] = "Turbo" if boost > 0 else "NA"
    fwd, fd, gtype = gearing(res)
    rr = tire_radius(res)
    if fwd:
        eta = 0.85
        v_lim = rpm.max() * 2 * math.pi / 60 / (fwd[-1] * fd) * rr
        # aero/rolling limited top speed
        p_max = float(pw.max()) * 745.7 * eta
        v = 10.0
        for _ in range(200):
            f = 0.5 * 1.2 * cda * v ** 2 + crr * mass * G
            v = 0.5 * v + 0.5 * p_max / f
        out["Top Speed"] = round(min(v, v_lim), 2)
        # 0-100 km/h sim (traction-limited RWD)
        rear_share = 0.5
        if res.nodes:
            ys = [n["pos"][1] for n in res.nodes.values()]
            rear_share = float(np.clip(0.45 + 0.0 * max(ys), 0.4, 0.6))
        dt, t, vel, gear, acc_prev = 0.01, 0.0, 0.0, 0, 0.0
        times = {}
        shift_t = 0.0 if "sequential" in gtype else (0.35 if "manual" in gtype else 0.25)
        pause = 0.0
        while t < 60 and vel < 62.6:
            if pause > 0:
                pause -= dt
                acc = -(0.5 * 1.2 * cda * vel ** 2 + crr * mass * G) / mass
            else:
                wrpm = max(vel / rr * 60 / (2 * math.pi) * fwd[gear] * fd, 0.0)
                if wrpm >= rpm.max() * 0.985 and gear < len(fwd) - 1:
                    gear += 1
                    pause = shift_t
                    continue
                eng = max(wrpm, rpm.max() * 0.45 if vel < 8 else wrpm)   # launch rpm
                T = _interp(list(zip(rpm, tq)), min(eng, rpm.max()))
                F = T * fwd[gear] * fd * eta / rr
                Fmax = mu * (mass * G * rear_share + mass * max(acc_prev, 0.0) * 0.46 / 2.48
                             + 0.5 * 1.2 * downforce_cla * vel ** 2 * 0.5) * 1.1
                F = min(F, Fmax)
                m_eff = mass * (1.04 + 0.0015 * (fwd[gear] * fd) ** 2)     # rotating drivetrain inertia
                acc = (F - 0.5 * 1.2 * cda * vel ** 2 - crr * mass * G) / m_eff
                acc_prev = acc
            vel += acc * dt
            t += dt
            for lbl, target in (("0-60 mph", 26.82), ("0-100 km/h", 27.78), ("0-100 mph", 44.7), ("0-200 km/h", 55.56)):
                if lbl not in times and vel >= target:
                    times[lbl] = round(t, 1)
        out.update(times)
    out["Transmission"] = {"manualGearbox": "Manual", "automaticGearbox": "Automatic",
                           "sequentialGearbox": "Sequential"}.get(gtype, "Manual")
    return out


def write_configs(mod, veh, configs, base_info, paints):
    """Write <key>.pc, info_<key>.json and the vehicle info.json; returns {key: stats}."""
    vdir = os.path.join(mod, "vehicles", veh)
    db = PartDB(vdir)
    stats = {}
    for c in configs:
        pc = OrderedDict([("format", 2), ("model", veh), ("parts", c.parts), ("vars", c.vars), ("mainPartName", veh)])
        with open(os.path.join(vdir, f"{c.key}.pc"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(pc, f, indent=2)
            f.write("\n")
        res = resolve(db, {"parts": c.parts, "vars": c.vars})
        if res.errors:
            raise RuntimeError(f"config {c.key}: {res.errors[:5]}")
        st = estimate(res)
        info = OrderedDict()
        info["Configuration"] = c.title
        info["Config Type"] = c.ctype
        info["Description"] = c.desc
        info["Years"] = {"min": c.years[0], "max": c.years[1]}
        info["Drivetrain"] = "RWD"
        info["Fuel Type"] = "Gasoline"
        info["Propulsion"] = "ICE"
        info["Value"] = c.value
        info["Population"] = c.population
        info["defaultPaintName1"] = c.paint
        info["defaultPaintName2"] = c.paint2 or c.paint
        info["defaultPaintName3"] = c.paint3 or "Super Black"
        info.update(st)
        with open(os.path.join(vdir, f"info_{c.key}.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(info, f, indent=2)
            f.write("\n")
        stats[c.key] = st
    main = OrderedDict(base_info)
    main["paints"] = paints
    with open(os.path.join(vdir, "info.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(main, f, indent=2)
        f.write("\n")
    return stats
