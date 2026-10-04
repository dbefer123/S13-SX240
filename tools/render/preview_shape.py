"""Quick preview of a body loft: ortho side/top/front + 3/4 perspective renders,
plus a blueprint overlay of the side view.

usage: python3 tools/render/preview_shape.py s13_hatch OUTDIR [views...]
"""
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import bpy  # noqa: E402

from tools.model import bl  # noqa: E402

PX_PER_M = 280.0
RES = (1400, 700)
SIDE_TARGET = (0.0, 0.0, 0.65)

# blueprint side views: (file, crop box, crop zoom, front-axle px (x,y) in zoomed crop, metres per zoomed px)
BLUEPRINTS = {
    "s13_hatch": (".cache/blueprints/s13_hatch_go.gif", (220, 225, 653, 360), 3, (297, 292), 2.475 / 678),
}


def get_spec(name):
    if name.startswith("s13_"):
        from tools.vehicle.s13 import body_spec as m
        return getattr(m, name.split("_", 1)[1] + "_spec")(), m
    raise SystemExit("unknown spec " + name)


def build_skin(spec, mod, paint_rgba=(0.62, 0.62, 0.64, 1)):
    Y, X, Z, tags = spec.grid()
    ob = bl.mesh_from_grid("skin", X, Y, Z, flip=True)
    bl.weld(ob, 1e-5)
    bl.mirror_x(ob)
    paint = bl.material("paint", paint_rgba, metallic=0.0, roughness=0.32, clearcoat=1.0)
    bl.assign(ob, paint)
    tire = bl.material("tire", (0.02, 0.02, 0.02, 1), roughness=0.8)
    for yy, tr in ((mod.AXLE_F_Y, mod.TRACK_F), (mod.AXLE_R_Y, mod.TRACK_R)):
        for s in (1, -1):
            bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.305, depth=0.195,
                                                location=(s * (tr / 2 - 0.02), yy, mod.AXLE_Z),
                                                rotation=(0, math.pi / 2, 0))
            bl.assign(bpy.context.active_object, tire)
    return ob


def overlay(name, render_path, out_path):
    from PIL import Image, ImageOps, ImageChops
    if name not in BLUEPRINTS:
        return
    f, box, zoom, (ax, ay), s = BLUEPRINTS[name]
    bp = Image.open(os.path.join(ROOT, f)).convert("L").crop(box)
    bp = bp.resize((bp.width * zoom, bp.height * zoom), Image.LANCZOS)
    W, H = RES
    # render px (u,v) -> world (y,z): y=(u-W/2)/PX, z=TZ-(v-H/2)/PX ; blueprint px = (ax+(y-AXLE)/s, ay-(z-AXLE_Z)/s)
    from tools.vehicle.s13 import body_spec as m
    a = 1 / (PX_PER_M * s)
    c = ax + (-W / 2 / PX_PER_M - m.AXLE_F_Y) / s
    e = -a
    fz = ay - (SIDE_TARGET[2] + H / 2 / PX_PER_M - m.AXLE_Z) / s
    warped = bp.transform((W, H), Image.AFFINE, (a, 0, c, 0, a, fz), resample=Image.BILINEAR, fillcolor=255)
    ren = Image.open(render_path).convert("RGB")
    lines = ImageOps.invert(warped)
    blue = Image.new("RGB", (W, H), (0, 60, 255))
    comp = Image.composite(blue, ren, lines.point(lambda p: 255 if p > 90 else 0))
    comp.save(out_path)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    name, out = args[0], args[1]
    only = set(args[2:])
    os.makedirs(out, exist_ok=True)
    bl.reset()
    spec, mod = get_spec(name)
    build_skin(spec, mod)
    bl.ground(color=(0.18, 0.18, 0.19, 1))
    bl.world_flat((0.55, 0.58, 0.62), 0.9)
    bl.sun(3.0, rot=(math.radians(55), 0, math.radians(40)))
    bl.setup_render(RES, samples=20, film_exposure=0.0)
    views = {
        "side": dict(loc=(12, 0.0, SIDE_TARGET[2]), target=SIDE_TARGET, ortho=RES[0] / PX_PER_M),
        "top": dict(loc=(0, 0.0, 12), target=(0, 0.0, 0), ortho=RES[0] / PX_PER_M),
        "front": dict(loc=(0, -12, 0.65), target=(0, 0, 0.65), ortho=RES[0] / PX_PER_M / 2.2),
        "rear": dict(loc=(0, 12, 0.65), target=(0, 0, 0.65), ortho=RES[0] / PX_PER_M / 2.2),
        "q_front_left": dict(loc=(3.3, -4.9, 1.05), target=(0, -0.45, 0.55), lens=38),
        "q_rear_left": dict(loc=(4.0, 5.8, 1.6), target=(0, 0.3, 0.55), lens=50),
    }
    for vn, v in views.items():
        if only and vn not in only:
            continue
        cam = bl.camera(vn, v["loc"], v["target"], lens=v.get("lens", 50), ortho=v.get("ortho"))
        if vn == "top":
            cam.rotation_euler = (0, 0, math.radians(-90))
        path = os.path.join(out, f"{name}_{vn}.png")
        bl.render(path)
        if vn == "side":
            overlay(name, path, os.path.join(out, f"{name}_side_overlay.png"))


main()
