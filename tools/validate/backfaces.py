"""Find surfaces the game would cull: back faces that are the first thing seen from typical viewpoints.

    python -m tools.validate.backfaces --veh s13_240sx --config mod/vehicles/s13_240sx/se_1991.pc [...]

BeamNG renders single-sided, so an open sheet (dash top, door card, aero plate) that faces away from the
camera is invisible and the player sees through it.  The closed-island check (tools.validate.normals)
cannot judge open sheets, so this assembles a configuration and ray-casts from the driver's and the
passenger's eye, the rear seat, a ring of points around the car and above the open engine bay.  Glass is
looked through.  Meshes whose first hits are mostly back faces are reported (requires bpy).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from tools.render.assemble import assemble

SEE_THROUGH = ("glass", "window", "windshield", "lens", "softtop_window")


def _fib(n):
    g = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(n):
        z = 1.0 - 2.0 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1.0 - z * z))
        yield Vector((math.cos(g * i) * r, math.sin(g * i) * r, z))


def viewpoints(eye):
    ex, ey, ez = eye
    inside = [("driver", (ex, ey, ez), None), ("passenger", (-ex, ey, ez), None), ("rear seat", (0.0, ey + 0.75, ez - 0.05), None)]
    ring = []
    for k in range(12):
        a = 2 * math.pi * k / 12
        for h in (0.45, 1.7):
            p = (4.6 * math.sin(a), 5.2 * math.cos(a), h)
            ring.append((f"outside {k * 30:03d}deg h{h}", p, (Vector((0, 0, 0.6)) - Vector(p)).normalized()))
    ring.append(("above", (0.0, 0.0, 5.0), Vector((0, 0, -1))))
    return inside + ring


def _is_glass(ob, index):
    me = ob.data
    if index < 0 or index >= len(me.polygons):
        return False
    m = me.materials[me.polygons[index].material_index] if me.materials else None
    name = (m.name if m else "") + " " + ob.name
    return any(s in name for s in SEE_THROUGH)


def _bvh(ob, dg, cache):
    if ob.name not in cache:
        mw = ob.matrix_world.copy()
        cache[ob.name] = (BVHTree.FromObject(ob, dg), mw, mw.to_3x3().inverted().transposed())
    return cache[ob.name]


def scan(rays=12000, eye=(0.37, 0.10, 1.07), cone=math.radians(40), engine_bay=None):
    dg = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    hits = defaultdict(lambda: [0, 0, Vector((0, 0, 0)), defaultdict(lambda: [0, 0])])
    trees = {}
    pts = list(viewpoints(eye))
    if engine_bay:
        pts.append(("engine bay", engine_bay, Vector((0, 0, -1))))
    for label, p, axis in pts:
        origin0 = Vector(p)
        for d in _fib(rays):
            if axis is not None and d.angle(axis) > (cone if label != "engine bay" else math.radians(55)):
                continue
            origin = origin0.copy()
            for _ in range(8):
                ok, loc, nrm, idx, ob, _m = sc.ray_cast(dg, origin, d, distance=30.0)
                if not ok:
                    break
                name = ob.name.split("__")[0]
                src = ob.original if hasattr(ob, "original") else ob
                if _is_glass(src, idx):
                    origin = loc + d * 1e-4
                    continue
                h = hits[name]
                h[0] += 1
                w = h[3][label.split(" ")[0]]
                w[0] += 1
                back = nrm.dot(d) > 0.0
                if back:
                    # a double-sided sheet keeps its two sides on (nearly) the same plane: a front face at the
                    # hit point is what the game draws
                    tree, mw, nmat = _bvh(ob, dg, trees)
                    lp = mw.inverted() @ loc
                    for _co, n2, _i, _dist in tree.find_nearest_range(lp, 1e-4):
                        if (nmat @ n2).dot(d) < 0.0:
                            back = False
                            break
                if back:
                    h[1] += 1
                    h[2] += loc
                    w[1] += 1
                break
    return hits


def report(hits, min_hits=25, min_frac=0.12):
    bad = []
    for name, (n, b, acc, where) in sorted(hits.items(), key=lambda kv: -kv[1][1]):
        if b >= min_hits and b / max(n, 1) >= min_frac:
            c = acc / b
            bad.append((name, n, b, tuple(round(x, 2) for x in c),
                        [f"{k} {v[1]}/{v[0]}" for k, v in sorted(where.items()) if v[1]]))
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod", default="mod")
    ap.add_argument("--veh", default="s13_240sx")
    ap.add_argument("--blend", default="")
    ap.add_argument("--config", action="append", default=[])
    ap.add_argument("--all", action="store_true", help="every configuration of the vehicle")
    ap.add_argument("--rays", type=int, default=12000)
    ap.add_argument("--hide-hood", action="store_true", help="also look into the engine bay with the hood off")
    a = ap.parse_args(argv)
    a.blend = a.blend or f".cache/build/{a.veh.split('_')[0]}_meshes.blend"
    if a.veh.startswith("s14"):
        from tools.vehicle.s14 import dims as D
    else:
        from tools.vehicle.s13 import dims as D
    eye = tuple(D.EYE)
    if a.all:
        vdir = os.path.join(a.mod, "vehicles", a.veh)
        a.config += sorted(os.path.join(vdir, f) for f in os.listdir(vdir) if f.endswith(".pc"))
    total = 0
    for cfgp in a.config:
        with open(cfgp) as f:
            cfg = json.load(f)
        assemble(a.mod, a.veh, cfg, a.blend)
        bay = None
        if a.hide_hood:
            for o in bpy.context.scene.objects:
                if "_hood" in o.name.split("__")[0]:
                    o.hide_viewport = True
            bay = (0.0, (D.ENGINE_FRONT_Y + D.ENGINE_REAR_Y) / 2 if hasattr(D, "ENGINE_FRONT_Y") else -1.45, 1.7)
        bad = report(scan(a.rays, eye, engine_bay=bay))
        print(f"== {os.path.basename(cfgp)}: {len(bad)} mesh(es) seen from behind")
        for name, n, b, c, where in bad:
            print(f"   {name:34s} back {b:5d}/{n:<6d} ({100 * b / n:4.0f}%) around {c} from {', '.join(where)}")
        total += len(bad)
    print(f"back-facing meshes: {total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
