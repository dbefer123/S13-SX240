"""Render an assembled configuration for review.

    python -m tools.render.preview_car OUTDIR [--config file.pc] [--views a,b] [--res 1600x900] [--samples 24]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import bpy

from tools.model import bl
from tools.render.assemble import assemble

VIEWS = {
    "q_front_left": dict(loc=(3.4, -5.0, 1.15), target=(0, -0.4, 0.55), lens=38),
    "q_rear_left": dict(loc=(3.7, 5.3, 1.3), target=(0, 0.4, 0.6), lens=38),
    "q_front_right": dict(loc=(-3.4, -5.0, 1.15), target=(0, -0.4, 0.55), lens=38),
    "side": dict(loc=(12, 0.0, 0.65), target=(0, 0, 0.65), ortho=5.0),
    "front": dict(loc=(0, -12, 0.65), target=(0, 0, 0.65), ortho=2.4),
    "rear": dict(loc=(0, 12, 0.65), target=(0, 0, 0.65), ortho=2.4),
    "low_front": dict(loc=(1.8, -4.2, 0.35), target=(0, -1.2, 0.35), lens=30),
    "cockpit": dict(loc=(0.365, 0.21, 1.08), target=(0.25, -1.2, 0.85), lens=18),
    "dash_pass": dict(loc=(0.30, 0.15, 1.10), target=(-0.45, -0.95, 0.88), lens=24),
    "dash_gap": dict(loc=(0.36, 0.20, 1.08), target=(-0.25, -1.0, 0.84), lens=80),
    "windshield": dict(loc=(1.25, -2.30, 1.45), target=(0.25, -0.55, 0.95), lens=40),
    "dash_side": dict(loc=(1.9, -0.55, 0.98), target=(0.3, -0.58, 0.93), lens=45,
                      hide=("s13_door_L", "s13_doorglass_L", "s13_doorcard_L", "s13_fender_L", "s13_mirror_L")),
    "dash_close": dict(loc=(0.36, 0.05, 1.10), target=(0.36, -0.6, 0.93), lens=24),
    "popup": dict(loc=(1.6, -3.3, 1.0), target=(0.5, -2.0, 0.62), lens=40),
    "racetach": dict(loc=(0.37, -0.20, 1.04), target=(0.365, -0.485, 0.93), lens=35,
                     hide=("s13_steer_stock", "s1x_steer_race", "s1x_steer_deepdish", "s13_body_*", "s14_body_*")),
    "wing": dict(loc=(2.2, 3.9, 1.6), target=(0.0, 2.25, 1.15), lens=35),
    "front_detail": dict(loc=(1.3, -4.0, 0.75), target=(0.0, -2.1, 0.40), lens=45),
    "rear_detail": dict(loc=(-1.4, 4.2, 0.95), target=(0.0, 2.15, 0.55), lens=45),
    "engine_close": dict(loc=(0.95, -1.55, 1.25), target=(0.05, -1.35, 0.62), lens=30,
                         hide=("s13_hood*",)),
    "corner": dict(loc=(1.35, -2.75, 0.85), target=(0.66, -2.05, 0.6), lens=50),
    "engine": dict(loc=(1.3, -2.6, 1.9), target=(0, -1.35, 0.55), lens=30),
    "under": dict(loc=(0.0, 0.0, -6.0), target=(0, 0, 0), ortho=5.2),
    "wheel_FL": dict(loc=(2.0, -1.9, 0.4), target=(0.73, -1.24, 0.3), lens=40),
    "interior_cut": dict(loc=(2.3, 0.35, 1.05), target=(0.0, -0.25, 0.75), lens=24,
                         hide=("s13_door_L", "s13_doorglass_L", "s13_doorcard_L")),
    "dash_cut": dict(loc=(1.6, -0.05, 1.0), target=(0.2, -0.55, 0.85), lens=30,
                     hide=("s13_door_L", "s13_doorglass_L", "s13_doorcard_L")),
}


def _hidden(name, pats):
    """View hide list: exact names or trailing-* prefixes; s13_ entries also cover the S14 (s14_) meshes."""
    for p in pats:
        for q in {p, p.replace("s13_", "s14_")}:
            if (q.endswith("*") and name.startswith(q[:-1])) or name == q:
                return True
    return False


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--mod", default="mod")
    ap.add_argument("--veh", default="s13_240sx")
    ap.add_argument("--blend", default="", help="mesh library (default .cache/build/<s13|s14>_meshes.blend)")
    ap.add_argument("--config", default="")
    ap.add_argument("--views", default="q_front_left,q_rear_left,side,cockpit")
    ap.add_argument("--res", default="1400x800")
    ap.add_argument("--samples", type=int, default=24)
    ap.add_argument("--hide", default="", help="comma separated mesh name prefixes to hide (e.g. body panels)")
    ap.add_argument("--prefix", default="")
    ap.add_argument("--cull", action="store_true", help="render back faces transparent (as the game culls them)")
    a = ap.parse_args(argv)
    a.blend = a.blend or f".cache/build/{a.veh.split('_')[0]}_meshes.blend"
    cfg = {"parts": {}, "vars": {}}
    if a.config:
        with open(a.config) as f:
            cfg = json.load(f)
    paint = None
    if a.config:
        from tools.render.thumbnails import paint_for
        vdir = os.path.join(a.mod, "vehicles", a.veh)
        key = os.path.splitext(os.path.basename(a.config))[0]
        try:
            with open(os.path.join(vdir, "info.json")) as f:
                paint = paint_for(os.path.join(vdir, f"info_{key}.json"), json.load(f).get("paints", {}))
        except OSError:
            paint = None
    res, shown = assemble(a.mod, a.veh, cfg, a.blend, paint=paint)
    if a.cull:
        from tools.render.assemble import cull_backfaces
        cull_backfaces()
    if a.hide:
        pre = tuple(a.hide.split(","))
        for o in shown:
            if o.name.split("__")[0].startswith(pre):
                o.hide_render = True
    os.makedirs(a.out, exist_ok=True)
    bl.ground(color=(0.2, 0.2, 0.21, 1))
    bl.world_flat((0.62, 0.66, 0.72), 0.55)
    bl.sun(2.6, rot=(math.radians(50), 0, math.radians(35)))
    w, h = (int(x) for x in a.res.split("x"))
    bl.setup_render((w, h), samples=a.samples)
    for vn in a.views.split(","):
        v = VIEWS[vn]
        cam = bl.camera(vn, v["loc"], v["target"], lens=v.get("lens", 50), ortho=v.get("ortho"))
        cam.data.clip_start = 0.01
        hidden = [o for o in shown if _hidden(o.name.split("__")[0], v.get("hide", ())) and not o.hide_render]
        for o in hidden:
            o.hide_render = True
        if vn == "under":
            bpy.data.objects["__ground"].hide_render = True
        bl.render(os.path.join(a.out, f"{a.prefix}{vn}.png"))
        if vn == "under":
            bpy.data.objects["__ground"].hide_render = False
        for o in hidden:
            o.hide_render = False
    return 0


if __name__ == "__main__":
    sys.exit(main())
