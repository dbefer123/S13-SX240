"""Blender helpers shared by the modelling scripts (requires bpy)."""
from __future__ import annotations

import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Vector, Matrix


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    return sc


def collection(name: str, parent=None):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    par = parent or bpy.context.scene.collection
    if col.name not in [c.name for c in par.children]:
        par.children.link(col)
    return col


def mesh_from_grid(name, X, Y, Z, close_u=False, close_v=False, flip=False, col=None):
    """Quad mesh from (nu, nv) coordinate grids."""
    nu, nv = X.shape
    verts = np.stack([X, Y, Z], -1).reshape(-1, 3)
    faces = []
    U = nu if close_u else nu - 1
    V = nv if close_v else nv - 1
    for i in range(U):
        for j in range(V):
            a = i * nv + j
            b = ((i + 1) % nu) * nv + j
            c = ((i + 1) % nu) * nv + (j + 1) % nv
            d = i * nv + (j + 1) % nv
            faces.append((a, d, c, b) if flip else (a, b, c, d))
    return mesh_obj(name, verts, faces, col=col)


def mesh_obj(name, verts, faces, col=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(map(float, v)) for v in verts], [], [tuple(f) for f in faces])
    me.validate(clean_customdata=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    (col or bpy.context.scene.collection).objects.link(ob)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob


def weld(ob, dist=1e-5):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def apply_all(ob):
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def mirror_x(ob, merge=True, threshold=1e-4):
    m = ob.modifiers.new("mirror", "MIRROR")
    m.use_axis = (True, False, False)
    m.use_mirror_merge = merge
    m.merge_threshold = threshold
    apply_all(ob)


def boolean(ob, cutter, op="DIFFERENCE", solver="EXACT"):
    m = ob.modifiers.new("bool", "BOOLEAN")
    m.operation = op
    m.solver = solver
    m.object = cutter
    apply_all(ob)


def material(name, color=(0.8, 0.8, 0.8, 1), metallic=0.0, roughness=0.5, clearcoat=0.0, alpha=1.0, emission=None):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = clearcoat
        bsdf.inputs["Coat Roughness"].default_value = 0.03
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        mat.blend_method = "BLEND" if hasattr(mat, "blend_method") else None
    if emission:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = 3.0
    mat.diffuse_color = color
    return mat


def assign(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)


def set_auto_smooth(ob, angle_deg=35):
    """Blender 4.1+: smooth by angle via modifier node group (applied)."""
    try:
        bpy.context.view_layer.objects.active = ob
        for o in bpy.context.view_layer.objects:
            o.select_set(False)
        ob.select_set(True)
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle_deg))
    except Exception:
        for p in ob.data.polygons:
            p.use_smooth = True


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------
def setup_render(res=(1600, 900), samples=32, engine="CYCLES", transparent=False, film_exposure=0.0):
    sc = bpy.context.scene
    sc.render.engine = engine
    if engine == "CYCLES":
        sc.cycles.device = "CPU"
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        try:
            sc.cycles.denoiser = "OPENIMAGEDENOISE"
        except Exception:
            pass
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = transparent
    sc.view_settings.view_transform = "AgX" if "AgX" in [x for x in ("AgX",)] else "Filmic"
    sc.view_settings.exposure = film_exposure
    return sc


def world_sky(strength=1.0, color=(0.75, 0.82, 0.95)):
    sc = bpy.context.scene
    w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    sky = nt.nodes.new("ShaderNodeTexSky")
    try:
        sky.sky_type = "NISHITA"
        sky.sun_elevation = math.radians(35)
        sky.sun_rotation = math.radians(120)
        nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    except Exception:
        bg.inputs["Color"].default_value = (*color, 1)
    bg.inputs["Strength"].default_value = strength
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])


def world_flat(color=(0.6, 0.62, 0.66), strength=1.0):
    sc = bpy.context.scene
    w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (*color, 1)
    bg.inputs["Strength"].default_value = strength


def sun(energy=3.0, rot=(math.radians(50), 0, math.radians(30))):
    l = bpy.data.lights.new("sun", "SUN")
    l.energy = energy
    l.angle = math.radians(3)
    o = bpy.data.objects.new("sun", l)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = rot
    return o


def ground(size=40, color=(0.35, 0.35, 0.36, 1), z=0.0):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    g = bpy.context.active_object
    g.name = "__ground"
    assign(g, material("__ground", color, roughness=0.8))
    return g


def camera(name="cam", loc=(5, -5, 2), target=(0, 0, 0.6), lens=50, ortho=None):
    cam = bpy.data.cameras.new(name)
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    cam.lens = lens
    cam.clip_end = 500
    o = bpy.data.objects.new(name, cam)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    d = Vector(target) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = o
    return o


def render(path):
    sc = bpy.context.scene
    sc.render.filepath = path
    sc.render.image_settings.file_format = "PNG" if path.endswith(".png") else "JPEG"
    bpy.ops.render.render(write_still=True)
