"""Render JBeam nodes/beams over a .blend of the exterior for visual checks.

usage: python3 tools/render/debug_structure.py EXTERIOR.blend JBEAM_DIR OUTDIR [config.pc]
"""
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import bpy  # noqa: E402

from tools.model import bl  # noqa: E402
from tools.jbeam import PartDB, resolve, load  # noqa: E402


def main():
    blend, jdir, out = sys.argv[1:4]
    cfg = load(sys.argv[4]) if len(sys.argv) > 4 else {"parts": {}}
    os.makedirs(out, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=blend)
    for ob in list(bpy.data.objects):
        if ob.type == "CAMERA":
            bpy.data.objects.remove(ob, do_unlink=True)
    ghost = bl.material("__ghost", (0.8, 0.8, 0.85, 1), roughness=0.5, alpha=0.25)
    ghost.blend_method = "BLEND"
    for ob in bpy.data.objects:
        if ob.type == "MESH" and not ob.name.startswith("__"):
            ob.data.materials.clear()
            ob.data.materials.append(ghost)
    r = resolve(PartDB(jdir), cfg)
    print("errors:", r.errors[:10])
    names = list(r.nodes)
    idx = {n: i for i, n in enumerate(names)}
    verts = [tuple(r.nodes[n]["pos"]) for n in names]
    edges = []
    for b in r.tables.get("beams", []):
        a, c = b.get("id1:"), b.get("id2:")
        if a in idx and c in idx:
            edges.append((idx[a], idx[c]))
    me = bpy.data.meshes.new("__beams")
    me.from_pydata(verts, edges, [])
    ob = bpy.data.objects.new("__beams", me)
    bpy.context.scene.collection.objects.link(ob)
    w = ob.modifiers.new("w", "SKIN") if False else None
    # thin tubes for edges via wireframe on a dummy face mesh is awkward; use curve bevel instead
    cu = bpy.data.curves.new("__bcurve", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.004
    for a, c in edges:
        sp = cu.splines.new("POLY")
        sp.points.add(1)
        sp.points[0].co = (*verts[a], 1)
        sp.points[1].co = (*verts[c], 1)
    cob = bpy.data.objects.new("__bcurve", cu)
    bpy.context.scene.collection.objects.link(cob)
    cob.data.materials.append(bl.material("__beam", (0.0, 0.45, 1.0, 1), roughness=0.4, emission=(0, 0.3, 1, 1)))
    nm = bl.material("__node", (1.0, 0.6, 0.0, 1), roughness=0.4, emission=(1, 0.5, 0, 1))
    for n in names:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.014, segments=8, ring_count=6, location=verts[idx[n]])
        s = bpy.context.active_object
        s.data.materials.append(nm)
    bl.setup_render((1400, 700), samples=12)
    views = {
        "dbg_side": dict(loc=(12, 0, 0.65), target=(0, 0, 0.65), ortho=5.0),
        "dbg_q": dict(loc=(4.0, -5.0, 2.2), target=(0, 0, 0.5), lens=35),
        "dbg_top": dict(loc=(0, 0, 12), target=(0, 0, 0), ortho=5.0),
        "dbg_front": dict(loc=(0, -12, 0.65), target=(0, 0, 0.65), ortho=2.4),
    }
    for vn, v in views.items():
        cam = bl.camera(vn, v["loc"], v["target"], lens=v.get("lens", 50), ortho=v.get("ortho"))
        if vn == "dbg_top":
            cam.rotation_euler = (0, 0, math.radians(-90))
        bl.render(os.path.join(out, vn + ".png"))


main()
