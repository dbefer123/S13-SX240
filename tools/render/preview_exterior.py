"""Render the S13 exterior panels (colour-coded) for review.

usage: python3 tools/render/preview_exterior.py OUTDIR [views...]
"""
import math
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import bpy  # noqa: E402

from tools.model import bl  # noqa: E402
from tools.model import s13_exterior  # noqa: E402
from tools.vehicle.s13 import body_spec as B  # noqa: E402

VIEWS = {
    "q_front_left": dict(loc=(3.3, -4.9, 1.05), target=(0, -0.45, 0.55), lens=38),
    "q_rear_left": dict(loc=(3.6, 5.2, 1.25), target=(0, 0.4, 0.6), lens=38),
    "side": dict(loc=(12, 0.0, 0.65), target=(0, 0, 0.65), ortho=5.0),
    "front": dict(loc=(0, -12, 0.65), target=(0, 0, 0.65), ortho=2.4),
    "top": dict(loc=(0, 0, 12), target=(0, 0, 0), ortho=5.0),
}


def main():
    args = sys.argv[1:]
    out = args[0]
    only = set(args[1:])
    os.makedirs(out, exist_ok=True)
    bl.reset()
    t = time.time()
    objs = s13_exterior.build_hatch_exterior()
    print("built exterior in %.1fs" % (time.time() - t), {k: len(o.data.polygons) for k, o in objs.items()})
    tire = bl.material("tire", (0.02, 0.02, 0.02, 1), roughness=0.8)
    for yy, tr in ((B.AXLE_F_Y, B.TRACK_F), (B.AXLE_R_Y, B.TRACK_R)):
        for s in (1, -1):
            bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.305, depth=0.195,
                                                location=(s * (tr / 2 - 0.02), yy, B.AXLE_Z), rotation=(0, math.pi / 2, 0))
            bl.assign(bpy.context.active_object, tire)
    bl.ground(color=(0.18, 0.18, 0.19, 1))
    bl.world_flat((0.55, 0.58, 0.62), 0.9)
    bl.sun(3.0, rot=(math.radians(55), 0, math.radians(40)))
    bl.setup_render((1400, 700), samples=20)
    for vn, v in VIEWS.items():
        if only and vn not in only:
            continue
        cam = bl.camera(vn, v["loc"], v["target"], lens=v.get("lens", 50), ortho=v.get("ortho"))
        if vn == "top":
            cam.rotation_euler = (0, 0, math.radians(-90))
        bl.render(os.path.join(out, f"ext_{vn}.png"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "exterior.blend"))


main()
