"""Build all meshes for a vehicle in (headless) Blender and export DAEs + materials.

    python -m tools.model.build_meshes --vehicle s13 [--mod mod] [--blend .cache/build/s13.blend]

Only meshes referenced by the generated JBeam (flexbodies/props) are exported;
missing ones are reported.  Every exported mesh gets two UV layers:
UV0 = box projection in metres (tiling/detail maps), UV1 = livery atlas for
body panels (box metres for everything else).
"""
from __future__ import annotations

import argparse
import glob
import math
import os
import sys
import time

import bpy
from mathutils import Vector

from tools.jbeam import load
from . import bl, materials as MR, mech, wheels_mesh as WM
from .prims import MeshBuilder

LIVERY_SCALE = 1.0 / 5.2       # metres -> UV1 units for the body livery atlas


# ---------------------------------------------------------------------------
# jbeam references
# ---------------------------------------------------------------------------
def referenced_meshes(veh_dir):
    flex, props = set(), set()
    for f in glob.glob(os.path.join(veh_dir, "*.jbeam")):
        for pn, p in load(f).items():
            for sec in ("flexbodies", "props"):
                hdr = None
                for r in p.get(sec, []):
                    if not isinstance(r, list):
                        continue
                    if hdr is None:
                        hdr = r
                        continue
                    if sec == "flexbodies":
                        flex.add(r[0])
                    else:
                        m = r[hdr.index("mesh")]
                        if m not in ("SPOTLIGHT", "POINTLIGHT"):
                            props.add(m)
    return flex, props


# ---------------------------------------------------------------------------
# UVs
# ---------------------------------------------------------------------------
def _ensure_layers(me):
    while len(me.uv_layers) < 2:
        me.uv_layers.new(name="UVMap" if len(me.uv_layers) == 0 else "UVMap1")
    me.uv_layers[0].name = "UVMap"
    me.uv_layers[1].name = "UVMap1"


def box_uv(me, layer, scale=1.0):
    uv = me.uv_layers[layer].data
    co = [v.co for v in me.vertices]
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            c = co[me.loops[li].vertex_index]
            if ax == 0:
                u, v = c.y, c.z
            elif ax == 1:
                u, v = c.x, c.z
            else:
                u, v = c.x, c.y
            uv[li].uv = (u * scale, v * scale)


def livery_uv(me, layer=1):
    """Body livery atlas: left side top band, right side below, plan view, front/rear strips at the bottom."""
    s = LIVERY_SCALE
    uv = me.uv_layers[layer].data
    co = [v.co for v in me.vertices]
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            x, y, z = co[me.loops[li].vertex_index]
            if ax == 0 and n.x > 0:                       # left side (+x): front on the left of the image
                u, v = (y + 2.6) * s, 0.74 + z * s
            elif ax == 0:                                 # right side: front on the right
                u, v = (2.6 - y) * s, 0.48 + z * s
            elif ax == 2:                                 # plan (top & bottom)
                u, v = (y + 2.6) * s, 0.146 + (x + 0.9) * s
            elif n.y < 0:                                 # front
                u, v = (x + 0.9) * s, min(z * s, 0.144)
            else:                                         # rear
                u, v = 0.5 + (0.9 - x) * s, min(z * s, 0.144)
            uv[li].uv = (u, v)


def finalize_uvs(ob, livery=False):
    me = ob.data
    had = len(me.uv_layers)
    _ensure_layers(me)
    if had == 0 or livery:
        box_uv(me, 0)
    if livery:
        livery_uv(me, 1)
    else:
        src, dst = me.uv_layers[0].data, me.uv_layers[1].data
        for i in range(len(src)):
            dst[i].uv = src[i].uv


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
class Scene:
    def __init__(self, mod_root):
        self.mod = mod_root
        self.objs = {}            # name -> (object, dae_key)

    def add_mb(self, mb, dae, smooth_angle=None):
        ob = mb.to_object(smooth_angle=smooth_angle)
        return self.add_ob(ob, dae)

    def add_ob(self, ob, dae):
        name = ob.name
        if name in self.objs:
            raise ValueError(f"duplicate mesh {name}")
        ob.data.name = name
        self.objs[name] = (ob, dae)
        return ob


def make_materials(mod_root):
    for name in MR.REGISTRY:
        MR.blender_material(name, mod_root)


def _purge_unregistered():
    bad = sorted({m.name for ob in bpy.data.objects if ob.type == "MESH" for m in ob.data.materials if m and
                  m.name not in MR.REGISTRY})
    return bad


def export_dae(objs, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.wm.collada_export(filepath=path, selected=True, apply_modifiers=True, triangulate=True,
                              include_children=False, include_animations=False, use_texture_copies=False,
                              use_object_instantiation=False, sort_by_name=True, export_mesh_type_selection="render",
                              limit_precision=True, keep_bind_info=False)


def strip_dae_images(path):
    """Remove texture/image references the exporter adds from preview materials (BeamNG uses materials.json)."""
    import re
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"<library_images>.*?</library_images>", "<library_images/>", s, flags=re.S)
    s = re.sub(r"<newparam sid=\"[^\"]*-(surface|sampler)\">.*?</newparam>", "", s, flags=re.S)
    s = re.sub(r"<texture texture=\"[^\"]*\" texcoord=\"[^\"]*\"/>", "<color sid=\"diffuse\">0.8 0.8 0.8 1</color>", s)
    s = re.sub(r"<author>[^<]*</author>", "<author>s13-sx240 build</author>", s)
    open(path, "w", encoding="utf-8", newline="\n").write(s)


# ---------------------------------------------------------------------------
# S13 contents
# ---------------------------------------------------------------------------
def build_s13(sc: Scene):
    from tools.vehicle.s13 import dims as D, catalog as C
    from . import s13_exterior as EXT, s13_parts as SP

    t0 = time.time()
    ext = EXT.build_hatch_exterior()
    for name, ob in ext.items():
        ob.name = name
        sc.add_ob(ob, "s13_body")
    print(f"  exterior {time.time() - t0:.1f}s")
    for mb in (SP.underbody(), SP.wheelwells(), SP.enginebay(), *SP.popup_lamps(), *SP.led_projectors(), SP.radiator(),
               SP.fueltank()):
        sc.add_mb(mb, "s13_body")
    # race body variants derived from the stock panels
    from . import s13_race as RM
    derived = {}
    for side, sg in (("L", 1), ("R", -1)):
        derived[f"s13_fender_wide_{side}"] = RM.widen_fender(ext[f"s13_fender_{side}"], f"s13_fender_wide_{side}", sg, 0.050)
        derived[f"s13_doorglass_poly_{side}"] = RM.recolor_copy(ext[f"s13_doorglass_{side}"], f"s13_doorglass_poly_{side}",
                                                                  "s13_glass_poly")
    derived["s13_hood_carbon"] = RM.recolor_copy(ext["s13_hood"], "s13_hood_carbon", {"s13_paint": "s1x_carbon"})
    derived["s13_hood_vented"] = RM.vented_hood(ext["s13_hood"])
    derived["s13_hatch_carbon"] = RM.recolor_copy(ext["s13_hatch"], "s13_hatch_carbon", {"s13_paint": "s1x_carbon"})
    derived["s13_hatchglass_poly"] = RM.recolor_copy(ext["s13_hatchglass"], "s13_hatchglass_poly", "s13_glass_poly")
    for name, ob in derived.items():
        sc.add_ob(ob, "s13_body")
    # coupe + convertible rear bodies (trunk lid and coupe tail lamps are shared: keep the coupe's)
    from . import s13_coupe as CP
    t1 = time.time()
    rear = {}
    for kind in ("coupe", "convertible"):
        objs = CP.build_rear_exterior(kind)
        for name, ob in objs.items():
            if name in rear:
                bpy.data.objects.remove(ob, do_unlink=True)
                continue
            ob.name = name
            rear[name] = ob
            sc.add_ob(ob, "s13_body_coupe")
    for mb in CP.trunk_spoilers():
        sc.add_mb(mb, "s13_body_coupe")
        rear[mb.name] = sc.objs[mb.name][0]
    from . import s13_race as RM
    rear["s13_trunk_carbon"] = sc.add_ob(RM.recolor_copy(rear["s13_trunk"], "s13_trunk_carbon", {"s13_paint": "s1x_carbon"}),
                                         "s13_body_coupe")
    for mb in (CP.parcel_shelf(), CP.headliner_coupe()):
        sc.add_mb(mb, "s13_interior")
    print(f"  coupe/convertible {time.time() - t1:.1f}s")
    from . import s13_details as DET
    for mb in DET.mirrors():
        sc.add_mb(mb, "s13_body" if mb.name != "s13_mirror_int" else "s13_interior")
    for mb in (DET.side_skirts(), DET.hatch_spoiler()):
        sc.add_mb(mb, "s13_body")
    sc.add_mb(DET.sun_visors_and_belts(), "s13_interior")
    for mb in RM.race_all():
        dae = "s13_interior" if mb.name in ("s13_dash_race", "s13_race_tach", "s13_needle_race", "s13_seat_race",
                                            "s13_seats_bucket", "s13_extinguisher", "s13_race_switchpanel") else "s13_race"
        sc.add_mb(mb, dae)
    # interior
    for mb in SP.interior_all():
        sc.add_mb(mb, "s1x_interior" if mb.name.startswith("s1x_") else "s13_interior")
    sc.add_mb(WM.steering_wheel_mesh("stock", "s13_steer_stock"), "s13_interior")
    # mechanicals (chassis-positioned)
    for mb in (*mech.front_suspension(D, "s13"), *mech.rear_suspension(D, "s13"), *mech.brakes(D, "s13"),
               *mech.gearboxes(D, "s13"), mech.exhaust_stock(D, "s13")):
        sc.add_mb(mb, "s13_mech")
    from . import engines as ENG
    for ob in (*ENG.engine_ka24(D, "s13"), *ENG.engine_sr20(D, "s13"), *ENG.engine_k20(D, "s13")):
        sc.add_ob(ob, "s13_engine")
    for mb in mech.turbos(D, "s13"):
        sc.add_mb(mb, "s13_engine")
    for eng in ("ka24e", "ka24de", "sr20det", "k20a"):
        for mb in mech.intakes(D, "s13", eng, ("stock", "cai", "itb")) + mech.manifolds(D, "s13", eng, ("na", "header", "turbo")):
            sc.add_mb(mb, "s13_engine")
    # shared: wheels, tires, hubcaps, aftermarket steering wheels
    for w in C.WHEELS:
        sc.add_mb(WM.wheel_mesh(w.key, w.dia, w.width, w.lugs, name=f"s1x_wheel_{w.key}"), "s1x_wheels")
    for t in C.TIRES:
        sc.add_mb(WM.tire_mesh(f"s1x_tire_{t.key}", t.radius, t.width_mm, t.aspect, t.dia, t.kind), "s1x_wheels")
    sc.add_mb(WM.hubcap_mesh(14, "s1x_hubcap_14"), "s1x_wheels")
    for kind in ("deepdish", "race"):
        sc.add_mb(WM.steering_wheel_mesh(kind, f"s1x_steer_{kind}"), "s1x_interior")

    # prop pivots (must match tools/vehicle/s13/vehicle.py)
    cx = D.STEER_CENTER[0]
    gy, gz = D.GAUGE_Y, D.GAUGE_Z
    pivots = {
        "s13_needle_tach": (cx + D.GAUGE_TACH_DX, gy + 0.004, gz),
        "s13_needle_speedo": (cx - D.GAUGE_TACH_DX, gy + 0.004, gz),
        "s13_needle_small": (cx + D.GAUGE_SMALL_DX, gy + 0.003, gz + D.GAUGE_SMALL_DZ),
        "s13_pedal_gas": (cx - 0.07, -0.86, 0.47),
        "s13_pedal_brake": (cx + 0.02, -0.86, 0.47),
        "s13_pedal_clutch": (cx + 0.12, -0.86, 0.47),
        "s13_steer_stock": D.STEER_CENTER,
        "s1x_steer_deepdish": D.STEER_CENTER,
        "s1x_steer_race": D.STEER_CENTER,
        "s13_needle_race": None,
    }
    from tools.vehicle.s13.vehicle import RACE_TACH
    pivots["s13_needle_race"] = (RACE_TACH[0], RACE_TACH[1] + 0.006, RACE_TACH[2])
    livery = {n for n, (ob, dae) in sc.objs.items() if dae in ("s13_body", "s13_body_coupe") and
              (n in ext or n in derived or n in rear)}
    livery |= {"s13_overfenders_R", "s13_sideskirts_aero", "s13_spoiler_oem"}
    return pivots, livery


DAE_FOLDER = {
    "s13_body": "vehicles/s13_240sx", "s13_body_coupe": "vehicles/s13_240sx",
    "s13_interior": "vehicles/s13_240sx", "s13_mech": "vehicles/s13_240sx",
    "s13_engine": "vehicles/s13_240sx", "s13_race": "vehicles/s13_240sx",
    "s1x_wheels": "vehicles/common/s1x_240sx", "s1x_interior": "vehicles/common/s1x_240sx",
    "s14_body": "vehicles/s14_240sx", "s14_interior": "vehicles/s14_240sx", "s14_mech": "vehicles/s14_240sx",
    "s14_engine": "vehicles/s14_240sx", "s14_race": "vehicles/s14_240sx",
}
VEHICLES = {  # --vehicle: (vehicle folder, builder, material owners written, default blend)
    "s13": ("vehicles/s13_240sx", "build_s13", ("s13", "s1x"), ".cache/build/s13_meshes.blend"),
    "s14": ("vehicles/s14_240sx", "build_s14", ("s14",), ".cache/build/s14_meshes.blend"),
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--vehicle", default="s13")
    ap.add_argument("--mod", default="mod")
    ap.add_argument("--blend", default="")
    ap.add_argument("--no-export", action="store_true")
    a = ap.parse_args(argv)
    mod = os.path.abspath(a.mod)
    veh_dir, builder, owners, blend_default = VEHICLES[a.vehicle]
    a.blend = a.blend or blend_default

    bl.reset()
    make_materials(mod)
    sc = Scene(mod)
    t0 = time.time()
    if builder == "build_s13":
        pivots, livery = build_s13(sc)
    else:
        from .build_s14 import build_s14
        pivots, livery = build_s14(sc)
    print(f"built {len(sc.objs)} meshes in {time.time() - t0:.1f}s")

    flex, props = referenced_meshes(os.path.join(mod, veh_dir))
    wanted = flex | props
    from tools.validate.run import VANILLA_MESHES
    shared = {n for n in wanted if n.startswith("s1x_")} if a.vehicle != "s13" else set()   # built with the S13
    missing = sorted(wanted - set(sc.objs) - VANILLA_MESHES - shared)
    unused = sorted(set(sc.objs) - wanted)
    for n in unused:
        ob, _ = sc.objs.pop(n)
        bpy.data.objects.remove(ob, do_unlink=True)
    print(f"referenced {len(wanted)}, exported {len(sc.objs)}, dropped {len(unused)} unused")
    if missing:
        print("MISSING meshes:", missing)

    # every watertight part must have outward normals (the game culls back faces)
    from .prims import orient_object
    nflip = sum(orient_object(ob) for ob, _ in sc.objs.values())
    print(f"flipped {nflip} inside-out closed islands")
    # props: origin at pivot (geometry is modelled around the origin), flexbodies at identity
    for n, (ob, dae) in sc.objs.items():
        if n in props:
            ob.location = Vector(pivots[n])
        finalize_uvs(ob, livery=n in livery)

    bad = _purge_unregistered()
    if bad:
        print("UNREGISTERED materials:", bad)

    used_mats = {m.name for ob, _ in sc.objs.values() for m in ob.data.materials if m}
    # glowMap swaps + damage materials are not on meshes but must be defined
    used_mats |= {n for n in MR.REGISTRY if any(n.startswith(f"{o}{b}") for o in ("s13", "s14")
                                                for b in ("_lights", "_needle_", "_gauges", "_glass", "_led_"))}
    tris = 0
    for ob, _ in sc.objs.values():
        tris += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    print(f"triangles: {tris:,}")

    if a.blend:
        os.makedirs(os.path.dirname(a.blend), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend))

    if a.no_export:
        return 0
    groups = {}
    for n, (ob, dae) in sc.objs.items():
        groups.setdefault(dae, []).append(ob)
    for dae, objs in sorted(groups.items()):
        if a.vehicle != "s13" and dae.startswith("s1x_"):
            continue                                   # shared DAEs are written by the S13 build
        path = os.path.join(mod, DAE_FOLDER[dae], f"{dae}.dae")
        for m in bpy.data.materials:
            m.use_nodes = False
        export_dae(objs, path)
        strip_dae_images(path)
        print(f"  {dae}.dae: {len(objs)} meshes, {os.path.getsize(path) / 1e6:.1f} MB")
    for owner in owners:
        p = MR.write_json(mod, owner, used_mats)
        print("  wrote", os.path.relpath(p, mod))
    return 1 if (missing or bad) else 0


if __name__ == "__main__":
    sys.exit(main())
