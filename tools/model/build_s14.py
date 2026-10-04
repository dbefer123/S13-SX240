"""S14 mesh library (requires bpy).

    * the S14 exterior (tools/model/s14_exterior.py) and meshes that must follow the S14 skin
      (underbody, wheel wells, engine bay, carpet, door cards, headliner, cabin trim, side skirts)
      are generated with the S14 spec / dims;
    * suspension, brakes, drivetrain and engines come straight from the shared generators with
      the S14 hard points (they match the catalogue JBeam built with the same dims);
    * everything else that was laid out in S13 coordinates (interior, mirrors, exhaust, race
      hardware) is generated as for the S13 and moved with the S13 -> S14 warp, exactly like
      its retargeted JBeam.
Every object and material is re-prefixed s13_ -> s14_.
"""
from __future__ import annotations

import contextlib
import time

from . import materials as MR, mech, wheels_mesh as WM
from tools.vehicle.s13 import dims as D13
from tools.vehicle.s13 import race as R13
from tools.vehicle.s14 import body_spec as B14, dims as D14
from tools.vehicle.s14 import vehicle as V14
from tools.vehicle.s14.warp import KX, warp, warp_object, wy


@contextlib.contextmanager
def patched(module, **kw):
    old = {k: getattr(module, k) for k in kw}
    for k, v in kw.items():
        setattr(module, k, v)
    try:
        yield
    finally:
        for k, v in old.items():
            setattr(module, k, v)


def s14ify(ob, do_warp=False, name=None):
    if do_warp:
        warp_object(ob)
    nn = name or ob.name.replace("s13_", "s14_")
    ob.name = nn
    ob.data.name = nn
    me = ob.data
    for i, m in enumerate(me.materials):
        if m and m.name.startswith("s13_"):
            new = "s14_" + m.name[4:]
            if new in MR.REGISTRY:
                me.materials[i] = MR.blender_material(new)
    return ob


_S14SPEC = []


def cowl14(x, y):
    """S14 windshield / cowl top at S13-coordinate (x, y): the S14 skin seen through the warp."""
    from .shape import top_z
    if not _S14SPEC:
        _S14SPEC.append(B14.s14_spec())
    return top_z(_S14SPEC[0], wy(y), min(abs(x) * KX, 0.66))


def build_s14(sc):
    from . import s14_exterior as EXT, s13_parts as SP, s13_details as DET, s13_race as RM, s13_coupe as CP
    from . import engines as ENG
    S14SPEC = B14.s14_spec()
    t0 = time.time()
    ext = EXT.build_exterior()
    rename = {"s14_quarterglass_L": "s14_quarterglass_coupe_L", "s14_quarterglass_R": "s14_quarterglass_coupe_R"}
    body = {}
    for name, ob in list(ext.items()):
        body[rename.get(name, name)] = sc.add_ob(s14ify(ob, name=rename.get(name, name)), "s14_body")
    for mb in EXT.trunk_spoilers():
        body[mb.name] = sc.add_mb(mb, "s14_body")
    for name, ob in EXT.body_kits(body).items():
        body[name] = sc.add_ob(s14ify(ob, name=name), "s14_body")
    print(f"  S14 exterior {time.time() - t0:.1f}s")

    # race / lightweight variants of the S14 panels
    from tools.vehicle.s13 import panel_spec as PS13
    from tools.vehicle.s14 import panel_spec as PS14
    with patched(PS13, ARCH_F=PS14.ARCH_F, ARCH_R=PS14.ARCH_R):
        for side, sg in (("L", 1), ("R", -1)):
            body[f"s14_fender_wide_{side}"] = sc.add_ob(
                RM.widen_fender(body[f"s14_fender_{side}"], f"s14_fender_wide_{side}", sg, 0.050), "s14_body")
    for side in ("L", "R"):
        body[f"s14_doorglass_poly_{side}"] = sc.add_ob(
            RM.recolor_copy(body[f"s14_doorglass_{side}"], f"s14_doorglass_poly_{side}", "s14_glass_poly"), "s14_body")
    body["s14_hood_carbon"] = sc.add_ob(RM.recolor_copy(body["s14_hood_zenki"], "s14_hood_carbon", {"s14_paint": "s1x_carbon"}),
                                        "s14_body")
    with patched(RM, SPEC=S14SPEC):
        vh = RM.vented_hood(body["s14_hood_zenki"])
    body["s14_hood_vented"] = sc.add_ob(s14ify(vh, name="s14_hood_vented"), "s14_body")
    body["s14_trunk_carbon"] = sc.add_ob(RM.recolor_copy(body["s14_trunk"], "s14_trunk_carbon", {"s14_paint": "s1x_carbon"}),
                                         "s14_body")

    # meshes that follow the S14 skin
    with patched(SP, SPEC=S14SPEC, D=D14):
        for mb in (SP.underbody(), SP.wheelwells(), SP.enginebay(), SP.carpet(), *SP.doorcards()):
            sc.add_ob(s14ify(mb.to_object()), "s14_body" if mb.name in ("s13_underbody", "s13_wheelwells", "s13_enginebay")
                      else "s14_interior")
    with patched(CP, SPEC=S14SPEC):
        sc.add_ob(s14ify(CP.headliner_coupe().to_object()), "s14_interior")
    with patched(DET, SPEC=S14SPEC):
        sc.add_ob(s14ify(DET.sun_visors_and_belts().to_object()), "s14_interior")
        sk = s14ify(DET.side_skirts().to_object())
        sc.add_ob(sk, "s14_body")
        body[sk.name] = sk
    sc.add_ob(s14ify(CP.parcel_shelf().to_object(), do_warp=True), "s14_interior")

    # S13-coordinate meshes moved with the warp
    for mb in (SP.radiator(), SP.fueltank()):
        sc.add_ob(s14ify(mb.to_object(), do_warp=True), "s14_body")
    for mb in DET.mirrors():
        sc.add_ob(s14ify(mb.to_object(), do_warp=True), "s14_interior" if mb.name == "s13_mirror_int" else "s14_body")
    props = {"s13_needle_tach", "s13_needle_speedo", "s13_needle_small", "s13_pedal_gas", "s13_pedal_brake",
             "s13_pedal_clutch", "s13_needle_race"}
    from . import s14_interior as INT14
    with patched(SP, COWL_TOP=cowl14):
        own = {mb.name: mb for mb in INT14.all_meshes()}       # S14 dash and cluster (S13 coordinates)
    for mb in SP.interior_all():
        if mb.name.startswith("s1x_"):
            sc.add_mb(mb, "s1x_interior")              # shared (exported by the S13 build), kept for previews
            continue
        if mb.name in ("s13_doorcard_L", "s13_doorcard_R", "s13_carpet", "s13_headliner") or mb.name in own:
            mb.bm.free()
            continue
        sc.add_ob(s14ify(mb.to_object(), do_warp=mb.name not in props), "s14_interior")
    for mb in own.values():
        sc.add_ob(s14ify(mb.to_object(), do_warp=True), "s14_interior")
    sc.add_ob(s14ify(WM.steering_wheel_mesh("stock_s14", "s13_steer_stock").to_object()), "s14_interior")
    saved = dict(R13.WING)
    R13.WING.update(V14.WING_S14)
    try:
        with patched(SP, COWL_TOP=cowl14):
            race_meshes = RM.race_all()
        for mb in race_meshes:
            if mb.name in ("s13_tubeframe", "s13_tube_floor", "s13_wheeliebar", "s13_wheeliebar_wheel", "s13_parachute",
                           "s13_wing_wicker", "s13_bumper_F_race", "s13_bumper_R_race"):
                mb.bm.free()
                continue
            dae = "s14_interior" if mb.name in ("s13_dash_race", "s13_race_tach", "s13_needle_race", "s13_seat_race",
                                                "s13_seats_bucket", "s13_extinguisher", "s13_race_switchpanel") else "s14_race"
            ob = s14ify(mb.to_object(), do_warp=mb.name not in props)
            sc.add_ob(ob, dae)
            if ob.name in ("s14_overfenders_R",):
                body[ob.name] = ob
    finally:
        R13.WING.clear()
        R13.WING.update(saved)
    sc.add_ob(s14ify(mech.exhaust_stock(D13, "s13").to_object(), do_warp=True), "s14_mech")
    ex = RM.exhaust_race()
    sc.add_ob(s14ify(ex.to_object(), do_warp=True), "s14_mech")

    # chassis-positioned mechanicals and engines, built with the S14 hard points
    for mb in (*mech.front_suspension(D14, "s14"), *mech.rear_suspension(D14, "s14"), *mech.brakes(D14, "s14"),
               *mech.gearboxes(D14, "s14")):
        sc.add_ob(s14ify(mb.to_object()), "s14_mech")
    for ob in (*ENG.engine_ka24(D14, "s14"), *ENG.engine_sr20(D14, "s14"), *ENG.engine_k20(D14, "s14")):
        sc.add_ob(s14ify(ob), "s14_engine")
    for mb in mech.turbos(D14, "s14"):
        sc.add_ob(s14ify(mb.to_object()), "s14_engine")
    for eng in ("ka24e", "ka24de", "sr20det", "k20a"):
        for mb in mech.intakes(D14, "s14", eng, ("stock", "cai", "itb")) + mech.manifolds(D14, "s14", eng, ("na", "header", "turbo")):
            sc.add_ob(s14ify(mb.to_object()), "s14_engine")

    # shared wheels / tires / steering wheels: kept in the .blend for previews, exported by the S13 build only
    from tools.vehicle.s13 import catalog as C
    for w in C.WHEELS:
        sc.add_mb(WM.wheel_mesh(w.key, w.dia, w.width, w.lugs, name=f"s1x_wheel_{w.key}"), "s1x_wheels")
    for t in C.TIRES:
        sc.add_mb(WM.tire_mesh(f"s1x_tire_{t.key}", t.radius, t.width_mm, t.aspect, t.dia, t.kind), "s1x_wheels")
    sc.add_mb(WM.hubcap_mesh(14, "s1x_hubcap_14"), "s1x_wheels")
    for kind in ("deepdish", "race"):
        sc.add_mb(WM.steering_wheel_mesh(kind, f"s1x_steer_{kind}"), "s1x_interior")

    # prop pivots: the S13 pivots under the warp (the props' JBeam positions are warped the same way)
    cx = D13.STEER_CENTER[0]
    gy, gz = D13.GAUGE_Y, D13.GAUGE_Z
    from tools.vehicle.s13.vehicle import RACE_TACH
    p13 = {
        "s14_needle_tach": (cx + D13.GAUGE_TACH_DX, gy + 0.004, gz),
        "s14_needle_speedo": (cx - D13.GAUGE_TACH_DX, gy + 0.004, gz),
        "s14_needle_small": (cx + D13.GAUGE_SMALL_DX, gy + 0.003, gz + D13.GAUGE_SMALL_DZ),
        "s14_pedal_gas": (cx - 0.07, -0.86, 0.47),
        "s14_pedal_brake": (cx + 0.02, -0.86, 0.47),
        "s14_pedal_clutch": (cx + 0.12, -0.86, 0.47),
        "s14_steer_stock": D13.STEER_CENTER,
        "s1x_steer_deepdish": D13.STEER_CENTER,
        "s1x_steer_race": D13.STEER_CENTER,
        "s14_needle_race": (RACE_TACH[0], RACE_TACH[1] + 0.006, RACE_TACH[2]),
    }
    pivots = {k: warp(*v) for k, v in p13.items()}
    livery = set(body) | {n for n in sc.objs if n.startswith("s14_trunkspoiler")}
    return pivots, livery
