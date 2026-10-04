"""Render config thumbnails (<config>.jpg) and the vehicle default.jpg.

    python -m tools.render.thumbnails [--veh s13_240sx] [--only a,b] [--res 640x360] [--samples 20]
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys

import bpy

from tools.model import bl
from tools.render.assemble import assemble


def paint_for(info_path, paints):
    try:
        with open(info_path) as f:
            name = json.load(f).get("defaultPaintName1")
        return paints.get(name)
    except Exception:  # noqa: BLE001
        return None


def render_one(mod, veh, blend, cfg, paint, out, res, samples):
    assemble(mod, veh, cfg, blend, paint=paint)
    bl.ground(size=60, color=(0.32, 0.33, 0.35, 1))
    bl.world_flat((0.70, 0.74, 0.80), 0.6)
    bl.sun(2.8, rot=(math.radians(48), 0, math.radians(-35)))
    w, h = res
    bl.setup_render((w, h), samples=samples)
    cam = bl.camera("thumb", (4.1, -5.0, 1.45), (0.0, -0.10, 0.50), lens=55)
    cam.data.sensor_width = 36
    bl.render(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod", default="mod")
    ap.add_argument("--veh", default="s13_240sx")
    ap.add_argument("--blend", default=".cache/build/s13_meshes.blend")
    ap.add_argument("--only", default="")
    ap.add_argument("--res", default="640x360")
    ap.add_argument("--samples", type=int, default=20)
    a = ap.parse_args(argv)
    vdir = os.path.join(a.mod, "vehicles", a.veh)
    with open(os.path.join(vdir, "info.json")) as f:
        info = json.load(f)
    paints = info.get("paints", {})
    res = tuple(int(x) for x in a.res.split("x"))
    only = set(s for s in a.only.split(",") if s)
    for pc in sorted(glob.glob(os.path.join(vdir, "*.pc"))):
        key = os.path.splitext(os.path.basename(pc))[0]
        if only and key not in only:
            continue
        with open(pc) as f:
            cfg = json.load(f)
        paint = paint_for(os.path.join(vdir, f"info_{key}.json"), paints)
        out = os.path.abspath(os.path.join(vdir, f"{key}.jpg"))
        render_one(a.mod, a.veh, a.blend, cfg, paint, out, res, a.samples)
        print("thumbnail", key)
        if key == info.get("default_pc"):
            import shutil
            shutil.copy(out, os.path.join(vdir, "default.jpg"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
