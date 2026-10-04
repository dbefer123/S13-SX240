"""Assemble a vehicle configuration in Blender from the built mesh library
(.cache/build/<veh>_meshes.blend) the way the game places it:

* flexbodies at their mesh position, or at the row's pos/rot (wheels, tires);
* props at their pivot, oriented by the ref-node frame (idRef -> idX = frame X,
  idRef -> idY = frame Y, mesh axes X,Y,Z -> frame X, Z, -Y) plus baseRotation;
* paint colours from the config's "paints".

Used by the preview renders and the config thumbnails.  Requires bpy.
"""
from __future__ import annotations

import math
import os

import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

from tools.jbeam import PartDB, resolve


def _frame(res, ref, idx, idy):
    p0 = res.nodes[ref]["pos"]
    fx = res.nodes[idx]["pos"] - p0
    fy = res.nodes[idy]["pos"] - p0
    fx = fx / np.linalg.norm(fx)
    fy = fy - fx * fy.dot(fx)
    fy = fy / np.linalg.norm(fy)
    fz = np.cross(fx, fy)
    # mesh X,Y,Z -> frame X, Z, -Y
    R = np.column_stack([fx, fz, -fy])
    return Matrix([list(R[0]), list(R[1]), list(R[2])])


def _v(d, default=0.0):
    if not isinstance(d, dict):
        return (default, default, default)
    return tuple(float(d.get(k, default) or default) for k in ("x", "y", "z"))


def assemble(mod, veh, config, blend, paint=None, hide_props=False):
    """Open the mesh library and keep only the parts of `config` (dict with parts/vars/paints)."""
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
    db = PartDB(os.path.join(mod, "vehicles", veh))
    res = resolve(db, config)
    lib = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
    for o in lib.values():
        o.hide_render = True
        o.hide_viewport = True
    col = bpy.context.scene.collection
    shown = []

    def place(name, M=None, loc=None):
        src = lib.get(name)
        if src is None:
            print("assemble: missing mesh", name)
            return None
        o = src.copy()                    # linked duplicate (shares mesh data)
        o.name = f"{name}__inst"
        col.objects.link(o)
        o.hide_render = False
        o.hide_viewport = False
        o.matrix_world = Matrix.Identity(4)
        if M is not None:
            o.matrix_world = M
        elif loc is not None:
            o.location = loc
        shown.append(o)
        return o

    for r in res.tables.get("flexbodies", []):
        mesh = r.get("mesh")
        if not mesh:
            continue
        pos, rot = r.get("pos"), r.get("rot")
        if isinstance(pos, dict) or isinstance(rot, dict):
            T = Matrix.Translation(Vector(_v(pos)))
            rx, ry, rz = (math.radians(a) for a in _v(rot))
            R = Euler((rx, ry, rz), "XYZ").to_matrix().to_4x4()
            place(mesh, T @ R)
        else:
            place(mesh, Matrix.Identity(4))
    if not hide_props:
        for r in res.tables.get("props", []):
            mesh = r.get("mesh")
            if mesh in (None, "SPOTLIGHT", "POINTLIGHT") or mesh not in lib:
                continue
            try:
                F = _frame(res, r["idRef:"], r["idX:"], r["idY:"])
            except Exception:  # noqa: BLE001
                F = Matrix.Identity(3)
            br = _v(r.get("baseRotation"))
            B = Euler(tuple(math.radians(a) for a in br), "XYZ").to_matrix()
            loc = r.get("baseTranslationGlobal")
            loc = Vector(_v(loc)) if isinstance(loc, dict) else lib[mesh].location.copy()
            M = Matrix.Translation(loc) @ (F @ B).to_4x4()
            place(mesh, M)

    # paint
    paints = config.get("paints") or ([paint] if paint else None)
    if paints:
        p = paints[0]
        rgba = p.get("baseColor", [0.5, 0.05, 0.05, 1]) if isinstance(p, dict) else p
        for mname in ("s13_paint", "s13_enginebay_paint", "s14_paint", "s14_enginebay_paint"):
            m = bpy.data.materials.get(mname)
            if m and m.node_tree:
                b = m.node_tree.nodes.get("Principled BSDF")
                b.inputs["Base Color"].default_value = (*rgba[:3], 1.0)
                if isinstance(p, dict):
                    b.inputs["Metallic"].default_value = float(p.get("metallic", 0.2))
                    b.inputs["Roughness"].default_value = float(p.get("roughness", 0.25))
    return res, shown
