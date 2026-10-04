"""Render the S14 exterior (zenki or kouki front) for review.

usage: python3 tools/render/preview_s14.py OUTDIR zenki|kouki [views...]
"""
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import bpy  # noqa: E402

from tools.model import bl, s14_exterior  # noqa: E402
from tools.vehicle.s14 import body_spec as B  # noqa: E402

VIEWS = {
    "q_front_left": dict(loc=(3.3, -5.0, 1.05), target=(0, -0.45, 0.55), lens=38),
    "q_rear_left": dict(loc=(3.6, 5.3, 1.35), target=(0, 0.4, 0.6), lens=38),
    "side": dict(loc=(12, 0.0, 0.65), target=(0, 0, 0.65), ortho=5.0),
    "front": dict(loc=(0, -12, 0.62), target=(0, 0, 0.62), ortho=2.2),
    "rear": dict(loc=(0, 12, 0.62), target=(0, 0, 0.62), ortho=2.2),
    "top": dict(loc=(0, 0, 12), target=(0, 0, 0), ortho=5.0),
    "front_close": dict(loc=(1.3, -4.0, 0.95), target=(0.2, -2.1, 0.55), lens=45),
}


def main():
    args = sys.argv[1:]
    out, kind = args[0], args[1]
    only = set(args[2:])
    os.makedirs(out, exist_ok=True)
    bl.reset()
    t = time.time()
    objs = s14_exterior.build_exterior()
    other = "kouki" if kind == "zenki" else "zenki"
    for n in list(objs):
        if n.endswith("_" + other):
            bpy.data.objects.remove(objs.pop(n), do_unlink=True)
    for mb in s14_exterior.trunk_spoilers()[:1]:
        mb.to_object()
    print("built in %.1fs" % (time.time() - t), sorted(objs))
    tire = bl.material("tire", (0.02, 0.02, 0.02, 1), roughness=0.8)
    for yy, tr in ((B.AXLE_F_Y, B.TRACK_F), (B.AXLE_R_Y, B.TRACK_R)):
        for s in (1, -1):
            bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.31, depth=0.205,
                                                location=(s * (tr / 2 - 0.02), yy, B.AXLE_Z), rotation=(0, math.pi / 2, 0))
            bl.assign(bpy.context.active_object, tire)
    from tools.model import materials as MR
    m = MR.blender_material("s14_paint")
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.75, 0.73, 1)
    bl.ground(color=(0.18, 0.18, 0.19, 1))
    bl.world_flat((0.55, 0.58, 0.62), 0.55)
    bl.sun(2.6, rot=(math.radians(55), 0, math.radians(40)))
    bl.setup_render((1400, 700), samples=24)
    for vn, v in VIEWS.items():
        if only and vn not in only:
            continue
        cam = bl.camera(vn, v["loc"], v["target"], lens=v.get("lens", 50), ortho=v.get("ortho"))
        if vn == "top":
            cam.rotation_euler = (0, 0, math.radians(-90))
        bl.render(os.path.join(out, f"s14_{kind}_{vn}.png"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, f"s14_{kind}.blend"))


main()
