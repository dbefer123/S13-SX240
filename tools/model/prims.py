"""Procedural mesh primitives (bmesh based) for mechanical/interior parts."""
from __future__ import annotations

import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

from . import bl


class MeshBuilder:
    """Accumulate geometry from several primitives into one object."""

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.mats = []
        self.uv = self.bm.loops.layers.uv.new("UVMap")

    def mat_index(self, mat_name):
        if mat_name not in self.mats:
            self.mats.append(mat_name)
        return self.mats.index(mat_name)

    def add_faces(self, verts, faces, mat, smooth=True, uv_scale=1.0, uv_mode="box"):
        bm = self.bm
        vs = [bm.verts.new(tuple(map(float, v))) for v in verts]
        mi = self.mat_index(mat)
        out = []
        for f in faces:
            try:
                face = bm.faces.new([vs[i] for i in f])
            except ValueError:
                continue
            face.material_index = mi
            face.smooth = smooth
            out.append(face)
        bm.normal_update()
        for face in out:
            n = face.normal
            for loop in face.loops:
                co = loop.vert.co
                if uv_mode == "box":
                    ax = max(range(3), key=lambda i: abs(n[i]))
                    if ax == 0:
                        u, v = co.y, co.z
                    elif ax == 1:
                        u, v = co.x, co.z
                    else:
                        u, v = co.x, co.y
                else:
                    u, v = co.x, co.y
                loop[self.uv].uv = (u * uv_scale, v * uv_scale)
        return out

    def polygon(self, verts, mat, outward, smooth=False):
        """Single n-gon whose normal is flipped (if needed) to face `outward`."""
        P = [Vector(v) for v in verts]
        n = Vector((0.0, 0.0, 0.0))
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]
            n.x += (a.y - b.y) * (a.z + b.z)
            n.y += (a.z - b.z) * (a.x + b.x)
            n.z += (a.x - b.x) * (a.y + b.y)
        order = list(range(len(P)))
        if n.dot(Vector(outward)) < 0:
            order = order[::-1]
        return self.add_faces(verts, [tuple(order)], mat, smooth)

    def to_object(self, col=None, smooth_angle=None):
        orient_closed_islands(self.bm)
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        ob = bpy.data.objects.new(self.name, me)
        (col or bpy.context.scene.collection).objects.link(ob)
        for m in self.mats:
            me.materials.append(bpy.data.materials.get(m) or bl.material(m))
        if smooth_angle:
            bl.set_auto_smooth(ob, smooth_angle)
        return ob

    # ------------------------------------------------------------------ prims
    def lathe(self, profile, mat, segs=32, axis="x", center=(0, 0, 0), closed=False, smooth=True, angle=(0, 2 * math.pi),
              uv_scale=1.0):
        """Revolve a (r, a) profile around an axis. profile: [(radius, axial_pos)]."""
        cx, cy, cz = center
        full = abs(angle[1] - angle[0] - 2 * math.pi) < 1e-6
        n = segs if full else segs + 1
        verts = []
        for j in range(n):
            t = angle[0] + (angle[1] - angle[0]) * j / segs
            c, s = math.cos(t), math.sin(t)
            for r, a in profile:
                if axis == "x":
                    verts.append((cx + a, cy + r * c, cz + r * s))
                elif axis == "y":
                    verts.append((cx + r * c, cy + a, cz + r * s))
                else:
                    verts.append((cx + r * c, cy + r * s, cz + a))
        m = len(profile)
        faces = []
        for j in range(segs):
            j2 = (j + 1) % n
            for i in range(m - 1 if not closed else m):
                i2 = (i + 1) % m
                f = (j * m + i, j2 * m + i, j2 * m + i2, j * m + i2)
                # the y-axis mapping (r cos, a, r sin) is mirrored w.r.t. x/z: keep one winding convention
                faces.append(f[::-1] if axis == "y" else f)
        return self.add_faces(verts, faces, mat, smooth, uv_scale)

    def tube(self, path, radius, mat, segs=12, caps=True, smooth=True, radii=None):
        """Sweep a circle along a polyline path [(x,y,z)...]."""
        P = [Vector(p) for p in path]
        n = len(P)
        verts, faces = [], []
        prev_side = None
        for i, p in enumerate(P):
            if i == 0:
                t = (P[1] - P[0]).normalized()
            elif i == n - 1:
                t = (P[-1] - P[-2]).normalized()
            else:
                t = ((P[i + 1] - P[i]).normalized() + (P[i] - P[i - 1]).normalized()).normalized()
            if prev_side is None:
                ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
                side = t.cross(ref).normalized()
            else:
                side = (prev_side - t * prev_side.dot(t)).normalized()
            up = side.cross(t).normalized()
            prev_side = side
            r = radii[i] if radii else radius
            for k in range(segs):
                a = 2 * math.pi * k / segs
                verts.append(tuple(p + (side * math.cos(a) + up * math.sin(a)) * r))
        for i in range(n - 1):
            for k in range(segs):
                k2 = (k + 1) % segs
                faces.append((i * segs + k, (i + 1) * segs + k, (i + 1) * segs + k2, i * segs + k2))   # outward
        if caps:
            faces.append(tuple(range(segs)))
            faces.append(tuple((n - 1) * segs + k for k in range(segs))[::-1])
        return self.add_faces(verts, faces, mat, smooth)

    def box(self, center, size, mat, rot=None, bevel=0.0, smooth=False):
        cx, cy, cz = center
        sx, sy, sz = (s / 2 for s in size)
        corners = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
                   (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
        R = rot if rot is not None else Matrix.Identity(3)
        verts = [tuple(Vector(center) + R @ Vector(c)) for c in corners]
        faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        return self.add_faces(verts, faces, mat, smooth)

    def rbox(self, center, size, radius, mat, segs=4, rot=None):
        """Rounded box (superellipse-ish) via a lofted rounded rectangle in X-Y extruded along Z with rounded top/bottom."""
        sx, sy, sz = size
        r = min(radius, sx / 2 - 1e-4, sy / 2 - 1e-4, sz / 2 - 1e-4)
        ring = rounded_rect(sx, sy, r, segs)
        prof = []
        for k in range(segs + 1):  # bottom rounding
            a = -math.pi / 2 + (math.pi / 2) * k / segs
            prof.append((math.cos(a), -sz / 2 + r + r * math.sin(a), r * (1 - math.cos(a))))
        for k in range(segs + 1):  # top rounding
            a = (math.pi / 2) * k / segs
            prof.append((math.cos(a), sz / 2 - r + r * math.sin(a), r * (1 - math.cos(a))))
        verts, faces = [], []
        m = len(ring)
        for _, z, inset in prof:
            inner = rounded_rect(sx - 2 * inset, sy - 2 * inset, max(r - inset, 1e-4), segs)
            for x, y in inner:
                verts.append((x, y, z))
        nprof = len(prof)
        for j in range(nprof - 1):
            for i in range(m):
                i2 = (i + 1) % m
                faces.append((j * m + i, j * m + i2, (j + 1) * m + i2, (j + 1) * m + i))
        faces.append(tuple(range(m))[::-1])
        faces.append(tuple((nprof - 1) * m + i for i in range(m)))
        R = rot if rot is not None else Matrix.Identity(3)
        verts = [tuple(Vector(center) + R @ Vector(v)) for v in verts]
        return self.add_faces(verts, faces, mat, True)

    def extrude(self, outline, depth, mat, origin=(0, 0, 0), axis="z", smooth=False, bevel_frac=0.0):
        """Extrude a closed 2D outline [(u,v)] along an axis."""
        o = Vector(origin)
        n = len(outline)
        verts = []
        for d in (0.0, depth):
            for u, v in outline:
                if axis == "z":
                    verts.append(tuple(o + Vector((u, v, d))))
                elif axis == "y":
                    verts.append(tuple(o + Vector((u, d, v))))
                else:
                    verts.append(tuple(o + Vector((d, u, v))))
        faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        faces.append(tuple(range(n))[::-1])
        faces.append(tuple(range(n, 2 * n)))
        area = sum(outline[i][0] * outline[(i + 1) % n][1] - outline[(i + 1) % n][0] * outline[i][1] for i in range(n))
        if (area < 0) != (axis == "y"):            # clockwise outline or mirrored axis mapping -> flip
            faces = [f[::-1] for f in faces]
        return self.add_faces(verts, faces, mat, smooth)

    def helix(self, p0, p1, radius, wire, turns, mat, segs_per_turn=16, wire_segs=6):
        p0, p1 = Vector(p0), Vector(p1)
        axis = (p1 - p0)
        L = axis.length
        t = axis.normalized()
        ref = Vector((1, 0, 0)) if abs(t.x) < 0.9 else Vector((0, 1, 0))
        u = t.cross(ref).normalized()
        v = t.cross(u).normalized()
        pts = []
        N = int(turns * segs_per_turn)
        for i in range(N + 1):
            a = 2 * math.pi * turns * i / N
            pts.append(tuple(p0 + t * (L * i / N) + (u * math.cos(a) + v * math.sin(a)) * radius))
        return self.tube(pts, wire, mat, segs=wire_segs, caps=True)

    def cylinder(self, p0, p1, radius, mat, segs=16, caps=True):
        return self.tube([p0, p1], radius, mat, segs=segs, caps=caps, smooth=True)

    def disc(self, center, axis, r_out, r_in, thickness, mat, segs=32):
        """Flat ring/disc between two radii (axis 'x' typical for wheels)."""
        prof = [(r_in, -thickness / 2), (r_out, -thickness / 2), (r_out, thickness / 2), (r_in, thickness / 2)]
        return self.lathe(prof, mat, segs=segs, axis=axis, center=center, closed=True)


def orient_closed_islands(bm, min_vol=1e-12):
    """Make every watertight island enclose a positive volume (outward normals).  Open surfaces are left alone."""
    import bmesh as _bmesh
    bm.faces.ensure_lookup_table()
    seen = set()
    flipped = 0
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
        if any(len(e.link_faces) != 2 for g in island for e in g.edges):
            continue
        vol = 0.0
        for g in island:
            vs = [v.co for v in g.verts]
            for i in range(1, len(vs) - 1):
                vol += vs[0].dot(vs[i].cross(vs[i + 1]))
        if vol < -min_vol:
            _bmesh.ops.reverse_faces(bm, faces=island, flip_multires=False)
            flipped += 1
    if flipped:
        bm.normal_update()
    return flipped


def orient_object(ob):
    """orient_closed_islands for an existing mesh object."""
    import bmesh as _bmesh
    bm = _bmesh.new()
    bm.from_mesh(ob.data)
    n = orient_closed_islands(bm)
    if n:
        bm.to_mesh(ob.data)
        ob.data.update()
    bm.free()
    return n


def rounded_rect(w, h, r, segs=4):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, math.pi / 2),
                       (-w / 2 + r, -h / 2 + r, math.pi), (w / 2 - r, -h / 2 + r, 1.5 * math.pi)):
        for k in range(segs + 1):
            a = a0 + (math.pi / 2) * k / segs
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def rot_to(direction, up=(0, 0, 1)):
    """3x3 rotation whose local Z points along `direction`."""
    d = Vector(direction).normalized()
    u = Vector(up)
    if abs(d.dot(u)) > 0.95:
        u = Vector((1, 0, 0))
    x = u.cross(d).normalized()
    y = d.cross(x).normalized()
    return Matrix((x, y, d)).transposed()


def text_mesh(name, text, size, mat, location=(0, 0, 0), rotation=(0, 0, 0), extrude=0.001, font=None, col=None):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = text
    cu.size = size
    cu.extrude = extrude
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    ob = bpy.data.objects.new(name, cu)
    (col or bpy.context.scene.collection).objects.link(ob)
    ob.location = location
    ob.rotation_euler = rotation
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.view_layer.objects.active
    ob.data.materials.clear()
    ob.data.materials.append(bpy.data.materials.get(mat) or bl.material(mat))
    return ob


def apply_transform(ob):
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def join_into(target, others):
    bpy.context.view_layer.objects.active = target
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    target.select_set(True)
    for o in others:
        o.select_set(True)
    bpy.ops.object.join()
    return target
