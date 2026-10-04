"""Cockpit parts that poke through the windshield (requires bpy).

    python -m tools.validate.clearance [--vehicle s13|s14]

The windshield is raked ~62 degrees, so it passes eye height right above the steering wheel and the dash,
binnacle and race tach must stay under it.  Every vertex of the dash-area meshes ahead of the A-pillar base
is compared with the body's top surface (the outer glass); anything closer than the glass thickness plus a
small gap is reported.
"""
from __future__ import annotations

import argparse
import os
import sys

import bpy

from tools.model.shape import top_z

PATTERNS = ("_dash", "_gauges", "_race_tach", "_needle", "_steer_", "_mirror_int", "_cabin_trim")
CLEAR = 0.006            # 4 mm glass + 2 mm


def check(spec, y_max=-0.40, x_max=0.70):
    bad = []
    for ob in sorted(bpy.data.objects, key=lambda o: o.name):
        if ob.type != "MESH" or not any(p in ob.name for p in PATTERNS):
            continue
        M = ob.matrix_world
        worst, n = 0.0, 0
        for v in ob.data.vertices:
            co = M @ v.co
            if co.y > y_max or abs(co.x) > x_max or co.y < -0.95:
                continue
            d = co.z - (top_z(spec, co.y, abs(co.x)) - CLEAR)
            if d > 0:
                n += 1
                worst = max(worst, d)
        if n:
            bad.append((ob.name, n, worst))
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--vehicle", default="s13")
    ap.add_argument("--blend", default="")
    a = ap.parse_args(argv)
    blend = a.blend or f".cache/build/{a.vehicle}_meshes.blend"
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
    if a.vehicle == "s14":
        from tools.vehicle.s14 import body_spec as B
        spec = B.s14_spec()
    else:
        from tools.vehicle.s13 import body_spec as B
        spec = B.hatch_spec()
    bad = check(spec)
    for name, n, worst in bad:
        print(f"{name}: {n} vertices through the windshield (up to {worst * 1000:.0f} mm)")
    print(f"cockpit parts through the glass: {len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
