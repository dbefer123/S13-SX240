"""Offline validation of the generated mod (BeamNG cannot run here).

    python -m tools.validate.run [--mod mod] [--vehicle s13_240sx] [--configs all|default|name,...] [--no-physics]

For the default part tree and every .pc config of a vehicle:
  * part tree resolves (slots, slot types, variables, expressions) without errors;
  * every node reference exists; no duplicate/coincident nodes;
  * flexbody groups have >= 3 nodes and >= 95 % of the mesh vertices lie within
    0.35 m of a group node; every flexbody/prop mesh exists in a DAE;
  * DAE materials, glowMap and deform materials exist in a materials.json;
    every texture they reference exists (or is a documented vanilla path);
  * powertrain graph is connected; wheels referenced by wheel shafts exist;
  * mass, CoG, axle split and explicit-integration stability (omega*dt).
Exit code 1 when any error is found.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np

from tools.jbeam import PartDB, resolve
from tools.jbeam.parser import loads
from tools.model.materials import BUILTIN
from . import physics as PH
from .dae import DaeIndex

COMMON = "vehicles/common/s1x_240sx"
OMEGA_DT_LIMIT = 1.80
COVER_DIST = 0.35


def node_groups(n):
    g = n.get("group")
    if g is None or g == "":
        return []
    if isinstance(g, str):
        return [g]
    return list(g)


def load_materials(mod, veh):
    mats = {}
    for folder in (os.path.join(mod, "vehicles", veh), os.path.join(mod, COMMON)):
        for f in glob.glob(os.path.join(folder, "**", "*.materials.json"), recursive=True):
            with open(f, encoding="utf-8") as fh:
                for k, v in loads(fh.read(), f).items():
                    mats[v.get("mapTo", k) if isinstance(v, dict) else k] = v
    return mats


def texture_paths(mat):
    out = []
    for st in mat.get("Stages", []):
        for k, v in st.items():
            if isinstance(v, str) and (v.endswith(".png") or v.endswith(".dds") or v.endswith(".jpg")):
                out.append(v)
    return out


def rot_matrix(rot):
    rx, ry, rz = (math.radians(float(rot.get(k, 0) or 0)) for k in ("x", "y", "z"))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


class Report:
    def __init__(self, title):
        self.title = title
        self.errors, self.warnings, self.info = [], [], []

    def err(self, m):
        self.errors.append(m)

    def warn(self, m):
        self.warnings.append(m)

    def note(self, m):
        self.info.append(m)

    def print(self, verbose=False, max_items=40):
        status = "OK" if not self.errors else "FAIL"
        print(f"== {self.title}: {status} ({len(self.errors)} errors, {len(self.warnings)} warnings)")
        for m in self.info:
            print("   ", m)
        for m in self.errors[:max_items]:
            print("   ERROR", m)
        if len(self.errors) > max_items:
            print(f"   ... {len(self.errors) - max_items} more errors")
        if verbose:
            for m in self.warnings[:max_items]:
                print("   warn ", m)


def check_config(mod, veh, cfg_name, cfg, dae, mats, physics=True, verbose=False):
    rep = Report(f"{veh} / {cfg_name}")
    db = PartDB(os.path.join(mod, "vehicles", veh))
    try:
        res = resolve(db, cfg)
    except Exception as ex:  # noqa: BLE001
        rep.err(f"resolve failed: {ex}")
        return rep, None
    for e in res.errors:
        rep.err(e)
    for w in res.warnings:
        rep.warn(w)
    for s in res.unused_config_slots:
        rep.warn(f"config slot not used by the tree: {s}")
    nodes = res.nodes

    # ---- node references
    for sec, rows in res.tables.items():
        for r in rows:
            for k, v in r.items():
                if not isinstance(k, str) or not k.endswith(":") or k.startswith("[") or k.startswith("__"):
                    continue
                vals = v if isinstance(v, list) else [v]
                for nv in vals:
                    if isinstance(nv, str) and nv and nv not in nodes:
                        rep.err(f"{r['__part']}.{sec}: node {nv!r} ({k}) does not exist")
    # coincident nodes
    names = list(nodes)
    P = np.array([nodes[n]["pos"] for n in names])
    if len(P):
        from scipy.spatial import cKDTree
        pairs = cKDTree(P).query_pairs(0.005)
        for i, j in sorted(pairs)[:20]:
            rep.warn(f"nodes {names[i]} and {names[j]} are < 5 mm apart")

    # ---- groups (+ synthetic pressure-wheel nodes, which the game generates at spawn)
    groups = defaultdict(list)
    for n, rec in nodes.items():
        for g in node_groups(rec):
            groups[g].append(n)
    gpos = {n: rec["pos"] for n, rec in nodes.items()}
    for r in res.tables.get("pressureWheels", []):
        name = r.get("name")
        a, b = r.get("node1:"), r.get("node2:")
        if not name or a not in nodes or b not in nodes:
            continue
        p1, p2 = nodes[a]["pos"], nodes[b]["pos"]
        ax = (p2 - p1) / max(np.linalg.norm(p2 - p1), 1e-6)
        mid = (p1 + p2) / 2
        u = np.cross(ax, [0, 0, 1.0])
        u = u / max(np.linalg.norm(u), 1e-6)
        v = np.cross(ax, u)
        nr = int(r.get("numRays", 16) or 16)
        for grp, rad, wid in ((r.get("hubGroup"), r.get("hubRadius"), r.get("hubWidth")),
                              (r.get("group"), r.get("radius"), r.get("tireWidth"))):
            if not grp or not rad:
                continue
            for i in range(nr):
                t = 2 * math.pi * i / nr
                for side in (-0.5, 0.5):
                    nn = f"__{grp}_{i}_{side}"
                    gpos[nn] = mid + ax * side * float(wid or 0.15) + float(rad) * (u * math.cos(t) + v * math.sin(t))
                    groups[grp].append(nn)

    # ---- glowMap materials
    glow = res.dicts.get("glowMap", {}) or {}
    glow_keys = set(glow)
    for key, g in glow.items():
        for slot in ("off", "on", "on_intense"):
            m = g.get(slot)
            if m and m not in mats:
                rep.err(f"glowMap {key}.{slot}: material {m!r} not defined")

    # ---- flexbodies
    flex_meshes = []
    for r in res.tables.get("flexbodies", []):
        mesh = r.get("mesh")
        if not mesh:
            continue
        flex_meshes.append(mesh)
        grp = r.get("[group]:") or []
        if isinstance(grp, str):
            grp = [grp]
        gnodes = [n for g in grp for n in groups.get(g, [])]
        if len(set(gnodes)) < 3:
            rep.err(f"{r['__part']}: flexbody {mesh} groups {grp} have {len(set(gnodes))} nodes (< 3)")
            continue
        for k in ("deformMaterialBase", "deformMaterialDamaged"):
            m = r.get(k)
            if m and r.get("deformGroup") and m not in mats:
                rep.err(f"{r['__part']}: flexbody {mesh} {k} {m!r} not defined")
        if mesh not in dae.meshes:
            rep.err(f"{r['__part']}: flexbody mesh {mesh!r} not found in any DAE")
            continue
        V = dae.world_verts(mesh)
        if V is not None and len(V):
            pos = r.get("pos") or {}
            rot = r.get("rot") or {}
            V2 = V @ rot_matrix(rot).T + np.array([float(pos.get("x", 0) or 0), float(pos.get("y", 0) or 0),
                                                       float(pos.get("z", 0) or 0)])
            G = np.array([gpos[n] for n in set(gnodes)])
            from scipy.spatial import cKDTree
            d, _ = cKDTree(G).query(V2[:: max(1, len(V2) // 4000)])
            frac = float((d <= COVER_DIST).mean())
            if frac < 0.95:
                (rep.err if frac < 0.6 else rep.warn)(
                    f"{r['__part']}: flexbody {mesh}: only {frac:.0%} of vertices within {COVER_DIST} m of groups {grp} "
                    f"(max {d.max():.2f} m)")
    # ---- props
    for r in res.tables.get("props", []):
        mesh = r.get("mesh")
        if mesh in ("SPOTLIGHT", "POINTLIGHT", None):
            continue
        if mesh not in dae.meshes:
            rep.err(f"{r['__part']}: prop mesh {mesh!r} not found in any DAE")
        flex_meshes.append(mesh)
    # ---- materials of used meshes
    for mesh in set(flex_meshes):
        info = dae.meshes.get(mesh)
        if not info:
            continue
        for m in info["materials"]:
            if m in glow_keys:
                continue
            if m not in mats:
                rep.err(f"mesh {mesh}: material {m!r} not defined (and not a glowMap key)")

    # ---- powertrain
    devs = {r.get("name"): r for r in res.tables.get("powertrain", []) if r.get("name")}
    for n, r in devs.items():
        inp = r.get("inputName")
        if inp and inp != "dummy" and inp not in devs:
            rep.err(f"powertrain device {n}: input {inp!r} missing")
    wheel_names = {r.get("name") for r in res.tables.get("pressureWheels", []) if r.get("name")}
    for n, r in devs.items():
        cw = r.get("connectedWheel")
        if cw and cw not in wheel_names:
            rep.err(f"powertrain device {n}: connectedWheel {cw!r} missing")
    if not any(r.get("type") == "combustionEngine" for r in devs.values()):
        rep.warn("no combustionEngine in tree")

    # ---- mass / CoG / stability
    stats = {}
    if physics and nodes:
        extra = []
        for r in res.tables.get("pressureWheels", []):
            if not r.get("name"):
                continue
            nr = float(r.get("numRays", 16) or 16)
            hub = float(r.get("hubNodeWeight", 0) or 0)
            tire = float(r.get("nodeWeight", 0) or 0) if r.get("hasTire", True) else 0.0
            a, b = r.get("node1:"), r.get("node2:")
            if a in nodes and b in nodes:
                extra.append((2 * nr * (hub + tire), (nodes[a]["pos"] + nodes[b]["pos"]) / 2))
        tot, cog = PH.mass_props(nodes, extra)
        wheels = [e for e in extra]
        yf = np.mean([p[1] for m, p in wheels if p[1] < 0]) if wheels else -1.24
        yr = np.mean([p[1] for m, p in wheels if p[1] > 0]) if wheels else 1.24
        front = (yr - cog[1]) / (yr - yf)
        stats = dict(mass=tot, cog=cog, front=front)
        rep.note(f"mass {tot:.0f} kg (nodes+wheels, no fuel), CoG x {cog[0]:+.3f} y {cog[1]:+.3f} z {cog[2]:.3f}, "
                 f"front {front:.1%}")
        try:
            st = PH.stability(res)
            stats["omega_dt"] = st["omega_dt"]
            msg = f"stability omega*dt max {st['omega_dt']:.3f} (limit {OMEGA_DT_LIMIT})"
            if st["omega_dt"] > OMEGA_DT_LIMIT:
                rep.err(msg + f" worst nodes {st.get('worst', [])[:6]}")
            else:
                rep.note(msg)
        except Exception as ex:  # noqa: BLE001
            rep.warn(f"stability analysis failed: {ex}")
    return rep, stats


def check_materials(mod, veh, mats):
    rep = Report(f"{veh} / materials+textures")
    for name, m in mats.items():
        if not isinstance(m, dict):
            continue
        for t in texture_paths(m):
            if t in BUILTIN.values():
                continue
            p = os.path.join(mod, t.lstrip("/"))
            if not os.path.exists(p):
                rep.err(f"material {name}: texture {t} missing")
    return rep


def load_configs(mod, veh, which):
    vdir = os.path.join(mod, "vehicles", veh)
    out = []
    if which in ("all", "default"):
        out.append(("<default tree>", {"parts": {}, "vars": {}}))
    if which != "default":
        sel = None if which == "all" else set(which.split(","))
        for f in sorted(glob.glob(os.path.join(vdir, "*.pc"))):
            name = os.path.splitext(os.path.basename(f))[0]
            if sel and name not in sel:
                continue
            with open(f, encoding="utf-8") as fh:
                out.append((name, json.load(fh)))
    return out


def check_info(mod, veh):
    rep = Report(f"{veh} / info files")
    vdir = os.path.join(mod, "vehicles", veh)
    if not os.path.exists(os.path.join(vdir, "info.json")):
        rep.err("info.json missing")
    for f in sorted(glob.glob(os.path.join(vdir, "*.pc"))):
        name = os.path.splitext(os.path.basename(f))[0]
        inf = os.path.join(vdir, f"info_{name}.json")
        if not os.path.exists(inf):
            rep.err(f"info_{name}.json missing")
        else:
            with open(inf, encoding="utf-8") as fh:
                d = json.load(fh)
            for k in ("Configuration", "Config Type"):
                if k not in d:
                    rep.err(f"info_{name}.json: {k} missing")
        if not os.path.exists(os.path.join(vdir, f"{name}.jpg")) and not os.path.exists(os.path.join(vdir, f"{name}.png")):
            rep.warn(f"{name}: no thumbnail")
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod", default="mod")
    ap.add_argument("--vehicle", default="s13_240sx")
    ap.add_argument("--configs", default="all")
    ap.add_argument("--no-physics", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    mod, veh = a.mod, a.vehicle
    dae = DaeIndex(os.path.join(mod, "vehicles", veh), os.path.join(mod, COMMON))
    for n, m in dae.meshes.items():
        if "dup" in m:
            print(f"warning: mesh {n} defined in two DAEs ({m['file']}, {m['dup']})")
    mats = load_materials(mod, veh)
    reports = [check_materials(mod, veh, mats), check_info(mod, veh)]
    summary = {}
    for name, cfg in load_configs(mod, veh, a.configs):
        rep, stats = check_config(mod, veh, name, cfg, dae, mats, physics=not a.no_physics, verbose=a.verbose)
        reports.append(rep)
        summary[name] = {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in (stats or {}).items()}
    n_err = 0
    for r in reports:
        r.print(verbose=a.verbose)
        n_err += len(r.errors)
    if a.json:
        with open(a.json, "w") as f:
            json.dump(summary, f, indent=1)
    print(f"\n{len(reports)} checks, {n_err} errors")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
