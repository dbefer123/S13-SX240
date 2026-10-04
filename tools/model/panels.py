"""Cutting a lofted skin into car panels with Blender booleans.

Panel outlines are 2D polygons drawn in one of the orthographic views and
extruded into prisms:
    view "side":  points (y, z), extruded along x over [x0, x1]
    view "plan":  points (x, y), extruded along z over [z0, z1]
    view "front": points (x, z), extruded along y over [y0, y1]

``extract(skin, prism)`` returns a new object = skin ∩ prism, and the skin is
replaced by skin − inflated(prism), leaving a real panel gap.
"""
from __future__ import annotations

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from . import bl


def _to3(view, a, b, c):
    if view == "side":
        return (c, a, b)        # (x=c, y=a, z=b)
    if view == "plan":
        return (a, b, c)        # (x=a, y=b, z=c)
    if view == "front":
        return (a, c, b)        # (x=a, y=c, z=b)
    raise ValueError(view)


def polygon_area(pts):
    p = np.asarray(pts, float)
    return 0.5 * float(np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]))


def offset_polygon(pts, d):
    """Offset a simple polygon outward by d (negative = inward), miter joins."""
    p = np.asarray(pts, float)
    if polygon_area(p) < 0:
        p = p[::-1]
    n = len(p)
    out = []
    for i in range(n):
        a, b, c = p[i - 1], p[i], p[(i + 1) % n]
        e1, e2 = b - a, c - b
        n1 = np.array([e1[1], -e1[0]]) / (np.linalg.norm(e1) + 1e-12)
        n2 = np.array([e2[1], -e2[0]]) / (np.linalg.norm(e2) + 1e-12)
        m = n1 + n2
        m /= (np.linalg.norm(m) + 1e-12)
        cosang = max(np.dot(m, n1), 0.35)
        out.append(b + m * d / cosang)
    return np.array(out)


def smooth_polygon(pts, radius=0.0, samples=6, closed=True):
    """Round polygon corners with circular-ish fillets (Chaikin-like subdivision)."""
    p = np.asarray(pts, float)
    if radius <= 0:
        return p
    out = []
    n = len(p)
    rng = range(n) if closed else range(1, n - 1)
    if not closed:
        out.append(p[0])
    for i in rng:
        a, b, c = p[i - 1], p[i], p[(i + 1) % n]
        da, dc = a - b, c - b
        la, lc = np.linalg.norm(da), np.linalg.norm(dc)
        r = min(radius, la * 0.45, lc * 0.45)
        p0 = b + da / la * r
        p2 = b + dc / lc * r
        for t in np.linspace(0, 1, samples):
            q = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * b + t ** 2 * p2
            out.append(q)
    if not closed:
        out.append(p[-1])
    return np.array(out)


def prism(name, view, pts, lo, hi, col=None):
    """Closed prism mesh from a 2D polygon extruded over [lo, hi]."""
    p = np.asarray(pts, float)
    if polygon_area(p) < 0:
        p = p[::-1]
    n = len(p)
    verts = [_to3(view, a, b, lo) for a, b in p] + [_to3(view, a, b, hi) for a, b in p]
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    faces.append(tuple(range(n))[::-1])
    faces.append(tuple(range(n, 2 * n)))
    ob = bl.mesh_obj(name, verts, faces, col=col, smooth=False)
    # make normals consistent / outward
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
    ob.display_type = "WIRE"
    ob.hide_render = True
    return ob


def duplicate(ob, name):
    new = ob.copy()
    new.data = ob.data.copy()
    new.name = name
    new.data.name = name
    for c in ob.users_collection:
        c.objects.link(new)
    return new


def _bool(ob, cutter, op):
    m = ob.modifiers.new("b", "BOOLEAN")
    m.operation = op
    m.solver = "EXACT"
    m.object = cutter
    try:
        m.use_hole_tolerant = True
    except AttributeError:
        pass
    bl.apply_all(ob)


def _from3(view, x, y, z):
    """Inverse of _to3: (a, b) polygon coordinates and the extrusion coordinate c."""
    if view == "side":
        return y, z, x
    if view == "plan":
        return x, y, z
    return x, z, y


def strip_cutter_faces(ob, view, pts, lo, hi, tol=3e-5):
    """Delete faces lying entirely on a cutter prism wall or cap (the hole-tolerant EXACT boolean on an
    open skin can keep pieces of the cutter, which show up as flat fins)."""
    p = np.asarray(pts, float)
    n = len(p)
    me = ob.data
    co = np.array([v.co[:] for v in me.vertices]) if len(me.vertices) else np.zeros((0, 3))
    if not len(co):
        return 0
    ab = np.array([_from3(view, *c)[:2] for c in co])
    cc = np.array([_from3(view, *c)[2] for c in co])
    on_cap = (np.abs(cc - lo) < tol) | (np.abs(cc - hi) < tol)
    on_wall = np.full((len(co), n), False)
    for i in range(n):
        a, b = p[i], p[(i + 1) % n]
        e = b - a
        L = np.linalg.norm(e)
        if L < 1e-9:
            continue
        d = np.abs((ab[:, 0] - a[0]) * e[1] - (ab[:, 1] - a[1]) * e[0]) / L
        t = ((ab - a) @ e) / (L * L)
        on_wall[:, i] = (d < tol) & (t > -1e-3) & (t < 1 + 1e-3)
    bm = bmesh.new(); bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    kill = []
    for f in bm.faces:
        idx = [v.index for v in f.verts]
        if on_cap[idx].all() or on_wall[idx].all(axis=0).any():
            kill.append(f)
    if kill:
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        bm.to_mesh(me)
    bm.free()
    me.update()
    return len(kill)


def extract(skin, name, view, pts, lo, hi, gap=0.0035, keep_cutter=False):
    """Split `skin` along a prism: returns the extracted panel object."""
    cut_in = prism(name + "__cut", view, pts, lo, hi)
    panel = duplicate(skin, name)
    _bool(panel, cut_in, "INTERSECT")
    strip_cutter_faces(panel, view, pts, lo, hi)
    if gap > 0:
        gpts = offset_polygon(pts, gap)
        cut_out = prism(name + "__gap", view, gpts, lo - 0.001, hi + 0.001)
        glo, ghi = lo - 0.001, hi + 0.001
    else:
        cut_out = cut_in
        gpts, glo, ghi = pts, lo, hi
    _bool(skin, cut_out, "DIFFERENCE")
    strip_cutter_faces(skin, view, gpts, glo, ghi)
    if not keep_cutter:
        for c in {cut_in, cut_out}:
            bpy.data.objects.remove(c, do_unlink=True)
    return panel


def cut_away(skin, view, pts, lo, hi):
    c = prism("__cut", view, pts, lo, hi)
    _bool(skin, c, "DIFFERENCE")
    strip_cutter_faces(skin, view, pts, lo, hi)
    bpy.data.objects.remove(c, do_unlink=True)


def cylinder_cut(skin, center_yz, radius, x0, x1, segs=64):
    """Remove a cylinder (axis along x) from the skin: wheel arch openings."""
    a = np.linspace(0, 2 * np.pi, segs, endpoint=False)
    pts = np.stack([center_yz[0] + radius * np.cos(a), center_yz[1] + radius * np.sin(a)], 1)
    cut_away(skin, "side", pts, x0, x1)


def remove_small_islands(ob, min_faces=6):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    seen = set()
    kill = []
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
                        seen.add(h.index); stack.append(h)
        if len(island) < min_faces:
            kill.extend(island)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(ob.data); bm.free()


def cleanup(ob, dist=2e-5):
    """Remove degenerate/loose geometry left by booleans."""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, dist=dist, edges=bm.edges)
    loose_e = [e for e in bm.edges if not e.link_faces]
    bmesh.ops.delete(bm, geom=loose_e, context="EDGES")
    loose_v = [v for v in bm.verts if not v.link_edges]
    bmesh.ops.delete(bm, geom=loose_v, context="VERTS")
    bm.to_mesh(ob.data); bm.free()
    ob.data.update()


def clamp_to_bbox(ob, lo, hi, margin=0.03):
    """Delete faces with vertices that escaped the expected bounding box (solidify spikes)."""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    lo = np.asarray(lo) - margin; hi = np.asarray(hi) + margin
    bad = [f for f in bm.faces if any((np.asarray(v.co) < lo).any() or (np.asarray(v.co) > hi).any() for v in f.verts)]
    if bad:
        bmesh.ops.delete(bm, geom=bad, context="FACES")
        loose_v = [v for v in bm.verts if not v.link_edges]
        bmesh.ops.delete(bm, geom=loose_v, context="VERTS")
    bm.to_mesh(ob.data); bm.free()
    return len(bad)


def bbox(ob):
    v = np.array([tuple(x.co) for x in ob.data.vertices])
    return v.min(0), v.max(0)


def solidify(ob, thickness=0.002, offset=-1.0, rim=True):
    cleanup(ob)
    lo, hi = bbox(ob) if len(ob.data.vertices) else (np.zeros(3), np.zeros(3))
    m = ob.modifiers.new("solid", "SOLIDIFY")
    m.thickness = thickness
    m.offset = offset
    m.use_rim = rim
    m.use_even_offset = False   # even offset explodes on folded slivers at boolean seams
    m.use_quality_normals = True
    bl.apply_all(ob)
    clamp_to_bbox(ob, lo, hi, margin=thickness * 4 + 0.01)


def split_by_side(ob):
    """Separate an object into its x>0 (L) and x<0 (R) halves (loose parts by centroid)."""
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    parts = [o for o in bpy.context.selected_objects]
    return parts


def join(objs, name):
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    bpy.context.view_layer.objects.active = objs[0]
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    return ob


def shade(ob, angle=40):
    bl.set_auto_smooth(ob, angle)
