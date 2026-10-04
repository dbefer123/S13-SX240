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
        if name == "licenseplate" and name not in lib:      # vanilla mesh: preview stand-in (30 x 15 cm plate)
            me = bpy.data.meshes.new("licenseplate")
            me.from_pydata([(-0.152, 0, -0.076), (0.152, 0, -0.076), (0.152, 0, 0.076), (-0.152, 0, 0.076)], [], [(0, 1, 2, 3)])
            ob = bpy.data.objects.new("licenseplate", me)
            m = bpy.data.materials.new("__plate"); m.use_nodes = True
            m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.85, 0.85, 0.8, 1)
            me.materials.append(m)
            lib[name] = ob
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

    # paint (+ palette livery preview: paint slots mixed by the palette's RGB channels on UV1)
    skin = res.dicts.get("__globals", {}).get("globalSkin")
    if isinstance(paint, list):
        paints = paint
    else:
        paints = config.get("paints") or ([paint] if paint else None)
    if skin and paints:
        _livery_preview(skin, paints, mod, veh)
        return res, shown
    if paints:
        p = paints[0] if isinstance(paints, list) else paints
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


def _livery_preview(skin, paints, mod, veh="s13_240sx"):
    """Replace the body paint preview with palette * paint colours (UV1)."""
    pfx = veh.split("_")[0]
    path = os.path.join(mod, "vehicles", veh, "textures", f"{pfx}_livery_{skin}.color.png")
    m = bpy.data.materials.get(f"{pfx}_paint")
    if m is None or not os.path.exists(path):
        return
    cols = []
    for k in range(3):
        p = paints[min(k, len(paints) - 1)]
        c = p.get("baseColor", [0.5, 0.5, 0.5]) if isinstance(p, dict) else p
        cols.append((*c[:3], 1.0))
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    uv = nt.nodes.new("ShaderNodeUVMap"); uv.uv_map = "UVMap1"
    img = nt.nodes.new("ShaderNodeTexImage"); img.image = bpy.data.images.load(path, check_existing=True)
    img.image.colorspace_settings.name = "Non-Color"
    nt.links.new(uv.outputs["UV"], img.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(img.outputs["Color"], sep.inputs["Color"])
    acc = None
    for k, ch in enumerate(("Red", "Green", "Blue")):
        mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        mul.inputs[6].default_value = (1, 1, 1, 1)
        mul.inputs[7].default_value = cols[k]
        val = nt.nodes.new("ShaderNodeCombineColor")
        for c in ("Red", "Green", "Blue"):
            nt.links.new(sep.outputs[ch], val.inputs[c])
        nt.links.new(val.outputs["Color"], mul.inputs[6])
        if acc is None:
            acc = mul
        else:
            add = nt.nodes.new("ShaderNodeMix"); add.data_type = "RGBA"; add.blend_type = "ADD"
            add.inputs["Factor"].default_value = 1.0
            nt.links.new(acc.outputs[2], add.inputs[6]); nt.links.new(mul.outputs[2], add.inputs[7])
            acc = add
    nt.links.new(acc.outputs[2], bsdf.inputs["Base Color"])


def cull_backfaces():
    """Preview the game's back-face culling: every material renders its back faces fully transparent, so
    inside-out or one-sided surfaces seen from behind show up as holes, like in BeamNG."""
    for m in bpy.data.materials:
        if not m.use_nodes or m.node_tree is None:
            continue
        nt = m.node_tree
        out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
        if out is None or not out.inputs["Surface"].links:
            continue
        src = out.inputs["Surface"].links[0].from_socket
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(geo.outputs["Backfacing"], mix.inputs["Fac"])
        nt.links.new(src, mix.inputs[1])
        nt.links.new(tr.outputs["BSDF"], mix.inputs[2])
        nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
