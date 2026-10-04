"""Render the S13 coupe / convertible exterior (shared hatch front panels + the body-specific rear) for review.

usage: python3 tools/render/preview_body.py OUTDIR coupe|convertible [views...]
"""
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import bpy  # noqa: E402

from tools.model import bl, s13_exterior, s13_coupe  # noqa: E402
from tools.vehicle.s13 import body_spec as B  # noqa: E402

VIEWS = {
    "q_front_left": dict(loc=(3.3, -4.9, 1.05), target=(0, -0.45, 0.55), lens=38),
    "q_rear_left": dict(loc=(3.6, 5.2, 1.45), target=(0, 0.4, 0.6), lens=38),
    "q_rear_right": dict(loc=(-3.4, 5.0, 1.9), target=(0, 0.6, 0.6), lens=38),
    "side": dict(loc=(12, 0.0, 0.65), target=(0, 0, 0.65), ortho=5.0),
    "rear": dict(loc=(0, 12, 0.70), target=(0, 0, 0.70), ortho=2.2),
    "top": dict(loc=(0, 0, 12), target=(0, 0, 0), ortho=5.0),
}
HATCH_ONLY = ("s13_body_hatch", "s13_hatch", "s13_hatchglass", "s13_quarterglass_L", "s13_quarterglass_R",
              "s13_quarterglass_trim_L", "s13_quarterglass_trim_R", "s13_taillights")


def main():
    args = sys.argv[1:]
    out, kind = args[0], args[1]
    only = set(args[2:])
    os.makedirs(out, exist_ok=True)
    bl.reset()
    t = time.time()
    hatch = s13_exterior.build_hatch_exterior()
    for n in list(hatch):
        drop = n in HATCH_ONLY or n.startswith("s13_bumper_F_") or n.startswith("s13_bumper_R_")
        drop |= (n.startswith("s13_door_conv_") if kind == "coupe" else
                 (n.startswith("s13_door_") and not n.startswith("s13_door_conv_")))
        if drop:
            bpy.data.objects.remove(hatch.pop(n), do_unlink=True)
    rear = s13_coupe.build_rear_exterior(kind)
    if kind == "convertible" and "top_down" in only:
        for n in ("s13_softtop", "s13_softtop_glass", "s13_quarterglass_conv_L", "s13_quarterglass_conv_R"):
            bpy.data.objects.remove(rear.pop(n), do_unlink=True)
    mb = s13_coupe.trunk_spoilers()[0]
    mb.to_object()
    print("built in %.1fs" % (time.time() - t), sorted(rear))
    tire = bl.material("tire", (0.02, 0.02, 0.02, 1), roughness=0.8)
    for yy, tr in ((B.AXLE_F_Y, B.TRACK_F), (B.AXLE_R_Y, B.TRACK_R)):
        for s in (1, -1):
            bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.305, depth=0.195,
                                                location=(s * (tr / 2 - 0.02), yy, B.AXLE_Z), rotation=(0, math.pi / 2, 0))
            bl.assign(bpy.context.active_object, tire)
    from tools.model import materials as MR
    m = MR.blender_material("s13_paint")
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.52, 0.015, 0.02, 1)
    bl.ground(color=(0.18, 0.18, 0.19, 1))
    bl.world_flat((0.55, 0.58, 0.62), 0.55)
    bl.sun(2.6, rot=(math.radians(55), 0, math.radians(40)))
    bl.setup_render((1400, 700), samples=24)
    for vn, v in VIEWS.items():
        if only - {"top_down"} and vn not in only:
            continue
        cam = bl.camera(vn, v["loc"], v["target"], lens=v.get("lens", 50), ortho=v.get("ortho"))
        if vn == "top":
            cam.rotation_euler = (0, 0, math.radians(-90))
        bl.render(os.path.join(out, f"{kind}_{vn}.png"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, f"{kind}.blend"))


main()
