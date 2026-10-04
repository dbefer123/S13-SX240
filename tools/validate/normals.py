"""Find inside-out geometry in the built mesh library (requires bpy).

    python -m tools.validate.normals [--blend .cache/build/s13_meshes.blend]

Every closed (watertight) island of every mesh should enclose a positive volume with
outward normals; a negative signed volume means its faces point inward, which renders
inside-out in game (back faces are culled).
"""
from __future__ import annotations

import argparse
import os
import sys

import bpy  # noqa: I001  (bpy must be imported before bmesh)
import bmesh


def inverted_islands(ob, min_vol=1e-7):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    seen, bad = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, island = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            island.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        edges = {e for g in island for e in g.edges}
        if any(len(e.link_faces) != 2 for e in edges):
            continue                        # open surface: orientation is by design
        vol = 0.0
        for g in island:
            vs = [v.co for v in g.verts]
            for i in range(1, len(vs) - 1):
                vol += vs[0].dot(vs[i].cross(vs[i + 1])) / 6.0
        if vol < -min_vol:
            c = sum((v.co for g in island for v in g.verts), vs[0] * 0) / sum(len(g.verts) for g in island)
            bad.append((len(island), vol, tuple(round(x, 3) for x in c)))
    bm.free()
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", default=".cache/build/s13_meshes.blend")
    a = ap.parse_args(argv)
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a.blend))
    n_bad = 0
    for ob in sorted(bpy.data.objects, key=lambda o: o.name):
        if ob.type != "MESH":
            continue
        bad = inverted_islands(ob)
        if bad:
            n_bad += len(bad)
            print(f"{ob.name}: {len(bad)} inverted closed island(s)", bad[:4])
    print(f"inverted islands: {n_bad}")
    return 1 if n_bad else 0


if __name__ == "__main__":
    sys.exit(main())
