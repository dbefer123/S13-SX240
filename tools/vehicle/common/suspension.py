"""Front MacPherson strut and rear multilink suspensions (shared S13/S14).

The MacPherson strut is modelled the robust way: a lower A-arm (transverse link
+ tension rod) and a short virtual upper link set perpendicular to the strut
axis, plus the spring/damper/bump-stop beams between the knuckle (fh2) and the
strut top on the body (fs1).  Steering uses tie-rod hydros from fixed rack-end
nodes to the steering arm, the pattern used by vanilla cars.

Node names (left side; right mirrors with 'r'):
  fh1 lower ball joint, fh2 knuckle top (strut bottom), fh3 steering arm,
  fh5 caliper arm, fh6 hub helper, fw1l / fw1ll axle inner / outer,
  fx1 lower arm inner, fx2 tension rod mount, fu1/fu2 virtual upper link pivots,
  rk1 rack end (inner tie rod).
  Rear: rh1 lower, rh2 upper, rh3 toe link, rh4 shock bottom, rh5 caliper arm,
  rw1l / rw1ll axle, rx1/rx2 lower arm inner, rx3 upper arm inner, rx4 toe link
  inner, rx5 traction rod mount.
"""
from __future__ import annotations

from .jb import Part

HUB = dict(collision=True, selfCollision=False, nodeMaterial="|NM_METAL", frictionCoef=0.5)


def _L(n):
    return n + "l"


def _R(n):
    return n + "r"


def _both(p, name, pos, w, **inline):
    x, y, z = pos
    p.node(name + "l", abs(x), y, z, nodeWeight=w, **inline)
    p.node(name + "r", -abs(x), y, z, nodeWeight=w, **inline)


def _beam_both(p, a, b, **inline):
    p.beam(a + "l", b + "l", **inline)
    p.beam(a + "r", b + "r", **inline)


def _side(p, pairs, side, **inline):
    for a, b in pairs:
        p.beam(a + side, b + side, **inline)


# ---------------------------------------------------------------------------
# front
# ---------------------------------------------------------------------------
def front_suspension(prefix, D, body_links, value=900, title="MacPherson Strut Front Suspension",
                     default_wheel=None, default_spring=None, default_brake=None, default_steer=None):
    """body_links: dict pivot -> list of body node base names (without l/r) or centre names (ending in '!')."""
    p = Part(f"{prefix}_suspension_F", title, f"{prefix}_suspension_F", value=value)
    cx = f"{D.TRACK_F / 2:.4f}+$trackoffset_F"
    p.slot(f"{prefix}_brake_F", default_brake or f"{prefix}_brake_F_stock", "Front Brakes")
    p.slot(f"{prefix}_wheel_F", default_wheel, "Front Wheels")
    p.slot(f"{prefix}_wheeldata_F", f"{prefix}_wheeldata_F", "Front Spindles", coreSlot=True)
    p.slot(f"{prefix}_spring_F", default_spring or f"{prefix}_spring_F_stock", "Front Struts")
    p.slot(f"{prefix}_swaybar_F", f"{prefix}_swaybar_F_stock", "Front Sway Bar")
    p.slot(f"{prefix}_steering", default_steer or f"{prefix}_steering_stock", "Steering Rack")
    p.variable("$camber_F", "", "Wheel Alignment", 1.0, 0.97, 1.03, "Camber Adjust", "Adjusts the front camber",
               subCategory="Front")
    p.variable("$trackoffset_F", "+m", "Wheels", 0.0, -0.02, 0.06, "Wheel Spacer", "Spacing of the wheel from the hub",
               stepDis=0.001, subCategory="Front")
    p.flexbody(f"{prefix}_lowerarm_F", [f"{prefix}_lowerarm_F", f"{prefix}_fsubframe"])
    p.flexbody(f"{prefix}_knuckle_F", [f"{prefix}_hub_F"])
    p.flexbody(f"{prefix}_fsubframe", [f"{prefix}_fsubframe"])
    p.nodes_props(**HUB)
    # hub
    p.nodes_props(group=[f"{prefix}_hub_F", f"{prefix}_lowerarm_F"])
    _both(p, "fh1", D.FH1, 4.2)
    p.nodes_props(group=[f"{prefix}_hub_F", f"{prefix}_strut_F"])
    _both(p, "fh2", D.FH2, 3.6)
    p.nodes_props(group=[f"{prefix}_hub_F", f"{prefix}_tierod_F"])
    _both(p, "fh3", D.FH3, 3.8)
    p.nodes_props(group=f"{prefix}_hub_F")
    _both(p, "fh5", D.FH5, 3.2)
    _both(p, "fh6", D.FH6, 1.0)
    # axle nodes (wheel hub)
    xc = D.TRACK_F / 2
    p.nodes_props(group="")
    for side, s in (("l", 1), ("r", -1)):
        tag = "FL" if s > 0 else "FR"
        p.nodes_props(group=f"wheelhub_{tag}")
        xi = f"$={s}*({xc - 0.045:.4f}+$trackoffset_F)"
        xo = f"$={s}*({xc + 0.045:.4f}+$trackoffset_F)"
        p.row("nodes", ["id", "posX", "posY", "posZ"], [f"fw1{side}", xi, D.AXLE_F_Y, D.AXLE_Z, {"nodeWeight": 3.0}])
        p.row("nodes", ["id", "posX", "posY", "posZ"], [f"fw1{side}{side}", xo, D.AXLE_F_Y, D.AXLE_Z, {"nodeWeight": 3.0}])
    # chassis pivots
    p.nodes_props(group=[f"{prefix}_fsubframe", f"{prefix}_lowerarm_F"])
    _both(p, "fx1", D.FX1, 3.0)
    _both(p, "fx2", D.FX2, 2.6)
    p.nodes_props(group=f"{prefix}_fsubframe", collision=False, selfCollision=False)
    _both(p, "fu1", D.FU1, 2.0)
    _both(p, "fu2", D.FU2, 2.0)
    p.nodes_props(group="", collision=True, selfCollision=True)

    p.beams_props(deformLimitExpansion=1.2)
    p.beams_props(beamPrecompression=1.0, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beam_comment("knuckle")
    p.beams_props(beamDeform=50000, beamStrength=350000, beamSpring=6001000, beamDamp=100)
    hub = [("fh1", "fh2"), ("fh1", "fh3"), ("fh2", "fh3"), ("fh1", "fh5"), ("fh2", "fh5"), ("fh3", "fh5")]
    for a, b in hub:
        _beam_both(p, a, b)
    p.beams_props(beamSpring=2001000, beamDamp=40)
    for a in ("fh1", "fh2", "fh3", "fh5"):
        _beam_both(p, "fh6", a)
    p.beam_comment("hub to axle (breakable)")
    p.beams_props(beamSpring=8001000, beamDamp=100, beamDeform=50000, beamStrength=155000, optional=True)
    for side, tag in (("l", "FL"), ("r", "FR")):
        p.beams_props(breakGroup=f"wheel_{tag}")
        p.beam(f"fh1{side}", f"fw1{side}", name=f"axle_{tag}")
        for a in ("fh2", "fh3", "fh5"):
            p.beam(a + side, f"fw1{side}")
        for a in ("fh1", "fh2", "fh3", "fh5"):
            p.beam(a + side, f"fw1{side}{side}")
    p.beams_props(breakGroup="", optional=False)
    p.beam_comment("lower A-arm (transverse link + tension rod) and virtual upper link")
    p.beams_props(beamSpring=6001000, beamDamp=500, beamDeform=45000, beamStrength=375000)
    for a, b in (("fx1", "fh1"), ("fx2", "fh1"), ("fu2", "fh2")):
        _beam_both(p, a, b, dampCutoffHz=500)
    p.beam_comment("pivots to chassis")
    p.beams_props(beamSpring=4001000, beamDamp=150, beamDeform=40000, beamStrength="FLT_MAX")
    for piv, links in body_links.items():
        for b in links:
            if b.endswith("!"):
                for side in ("l", "r"):
                    p.beam(piv + side, b[:-1])
            else:
                _beam_both(p, piv, b)
    p.beam_comment("anti-invert / travel limiters")
    p.beams_props(beamPrecompression=1, beamType="|SUPPORT", beamLongBound=2.0, beamDeform=50000, beamStrength=250000,
                  beamSpring=2501000, beamDamp=100)
    for a, b in (("fh1", "fu1"), ("fh1", "fu2"), ("fh2", "fx1"), ("fh2", "fx2")):
        _beam_both(p, a, b, beamPrecompression=0.65)
    p.beams_props(beamPrecompression=1.0, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    # camber adjust: precompress the upper link beams
    p.beam_comment("camber adjust")
    p.beams_props(beamSpring=3001000, beamDamp=100, beamDeform=40000, beamStrength=300000)
    for side in ("l", "r"):
        p.beam(f"fu1{side}", f"fh2{side}", beamPrecompression="$camber_F", beamPrecompressionTime=0.5)
    p.beams_props(beamPrecompression=1.0)
    p.tris_props(dragCoef=0, triangleType="NONCOLLIDABLE")
    for side in ("l", "r"):
        p.tri(f"fh1{side}", f"fh2{side}", f"fh5{side}")
        p.tri(f"fh1{side}", f"fh3{side}", f"fh2{side}")
    p.tris_props(triangleType="NORMALTYPE")
    p.d["_center_x"] = cx
    return p


def wheeldata_front(prefix, D, torque_nodes=None):
    p = Part(f"{prefix}_wheeldata_F", "Front Spindles", f"{prefix}_wheeldata_F", value=100)
    p.pw_props(selfCollision=False, collision=True)
    for side, tag, s, wd in (("r", "FR", -1, 1), ("l", "FL", 1, -1)):
        p.pw_props(hubcapBreakGroup=f"hubcap_{tag}", hubcapGroup=f"hubcap_{tag}", axleBeams=[f"axle_{tag}"])
        p.pw(tag, f"wheel_{tag}", f"tire_{tag}", f"fw1{side}{side}", f"fw1{side}", 9999, f"fh5{side}", wd,
             {"torqueCoupling:": f"fh6{side}", "torqueArm:": f"fh5{side}", "steerAxisUp:": f"fh2{side}",
              "steerAxisDown:": f"fh1{side}"})
    p.pw_props(selfCollision=True)
    p.pw_props(axleBeams=[], disableMeshBreaking=False, disableTriangleBreaking=False)
    p.pw_props(hubcapBreakGroup="", hubcapGroup="", enableHubcaps=False)
    p.pw_props(enableTireLbeams=False, enableTireSideReinfBeams=False, enableTireReinfBeams=False,
               enableTreadReinfBeams=False, enableTirePeripheryReinfBeams=False, enableTireSupportBeams=False)
    p.pw_props(loadSensitivitySlope="", noLoadCoef=1, fullLoadCoef=0, softnessCoef=0.5)
    return p


def struts_front(prefix, key, title, spring, bump, rebound, height_def, height_min, height_max, value, static_load,
                 mesh=None, travel_c=0.075, travel_d=0.095, adjustable=False):
    p = Part(f"{prefix}_spring_F_{key}", title, f"{prefix}_spring_F", value=value)
    mesh = mesh or f"{prefix}_strut_F"
    p.flexbody(f"{mesh}_{key}" if key != "stock" else mesh, [f"{prefix}_strut_F", f"{prefix}_shocktop_F"])
    cat = "Suspension"
    p.variable("$springheight_F", "+m", cat, height_def, height_min, height_max, "Spring Height",
               "Raise or lower the front ride height", stepDis=0.002, subCategory="Front")
    if adjustable:
        p.variable("$spring_F", "N/m", cat, spring, spring * 0.5, spring * 2.0, "Spring Rate", "Front spring stiffness",
                   stepDis=500, subCategory="Front")
        p.variable("$damp_bump_F", "N/m/s", cat, bump, bump * 0.4, bump * 2.5, "Bump Damping", "Damper rate in compression",
                   stepDis=50, subCategory="Front")
        p.variable("$damp_rebound_F", "N/m/s", cat, rebound, rebound * 0.4, rebound * 2.5, "Rebound Damping",
                   "Damper rate in extension", stepDis=50, subCategory="Front")
        k, cb, cr = "$spring_F", "$damp_bump_F", "$damp_rebound_F"
        pre = f"$=({static_load:.0f}/$spring_F) + $springheight_F"
    else:
        k, cb, cr = spring, bump, rebound
        pre = f"$={static_load / spring:.4f} + $springheight_F"
    p.beams_props(beamType="|NORMAL", beamDeform=12000, beamStrength=140000)
    p.beams_props(beamSpring=k, beamDamp=0)
    for s in ("l", "r"):
        p.beam(f"fh2{s}", f"fs1{s}", precompressionRange=pre)
    p.beams_props(beamPrecompression=1.0, beamType="|BOUNDED", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamLimitSpring=0, beamLimitDamp=0, beamSpring=250, beamDamp=cb)
    for s in ("l", "r"):
        p.beam(f"fh2{s}", f"fs1{s}", beamDampRebound=cr, beamDampVelocitySplit=0.2,
               beamDampFast=f"$={cb}/3" if isinstance(cb, str) else round(cb / 3), beamDampReboundFast=f"$={cr}/3" if isinstance(cr, str) else round(cr / 3),
               dampCutoffHz=500, soundFile="event:>Vehicle>Suspension>car_modn_sml_01>spring_compress_01",
               colorFactor=0.8, attackFactor=10, volumeFactor=1.8, decayMode=1, decayFactor=10, pitchFactor=0.7, maxStress=13)
    p.beams_props(beamSpring=0, beamDamp=0, beamLimitSpring=201000, beamLimitDamp=5000)
    for s in ("l", "r"):
        p.beam(f"fh2{s}", f"fs1{s}", longBoundRange=travel_d, shortBoundRange=travel_c, boundZone=0.03,
               beamLimitDampRebound=0, dampCutoffHz=500)
    p.beams_props(beamLimitSpring=0, beamLimitDamp=0)
    p.beams_props(beamPrecompression=1.0, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    return p


def swaybar_front(prefix, key, title, rate, value, adjustable=False, lever=0.20):
    p = Part(f"{prefix}_swaybar_F_{key}", title, f"{prefix}_swaybar_F", value=value)
    if adjustable:
        p.variable("$arb_spring_F", "N/m", "Suspension", rate, rate * 0.3, rate * 2.5, "Anti-Roll Spring Rate",
                   "Stiffness of the front anti-roll bar at the end links", stepDis=500, subCategory="Front")
        r = "$arb_spring_F"
        spring = f"$=$arb_spring_F*{lever}*{lever}"
    else:
        spring = round(rate * lever * lever, 1)
    p.flexbody(f"{prefix}_swaybar_F", [f"{prefix}_lowerarm_F", f"{prefix}_fsubframe"])
    p.torsion_props(spring=spring, damp=10, deform=8000, strength=9999999)
    p.torsionbar("fh1l", "fx1l", "fx1r", "fh1r")
    return p


def steering(prefix, D, key, title, lock_deg, wheel_angle_deg, value, body_links):
    """Rack ends rk1 are fixed to the crossmember; tie-rod hydros change length to steer."""
    import math
    p = Part(f"{prefix}_steering_{key}", title, f"{prefix}_steering", value=value)
    p.flexbody(f"{prefix}_steering_rack", [f"{prefix}_fsubframe"])
    p.flexbody(f"{prefix}_tierod_F", [f"{prefix}_tierod_F", f"{prefix}_fsubframe"])
    p.variable("$toe_F", "", "Wheel Alignment", 0.999, 0.98, 1.02, "Toe Adjust", "Adjusts the front toe angle",
               subCategory="Front")
    p.nodes_props(**HUB)
    p.nodes_props(group=[f"{prefix}_fsubframe", f"{prefix}_tierod_F"], collision=False, selfCollision=False)
    _both(p, "rk1", (D.RACK_X, D.RACK_Y, D.RACK_Z), 3.6)
    p.nodes_props(group="", collision=True, selfCollision=True)
    p.beams_props(beamPrecompression=1.0, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamSpring=4001000, beamDamp=150, beamDeform=40000, beamStrength="FLT_MAX")
    for b in body_links:
        if b.endswith("!"):
            for s in ("l", "r"):
                p.beam("rk1" + s, b[:-1])
        else:
            _beam_both(p, "rk1", b)
    p.beam("rk1l", "rk1r")
    arm = math.dist(D.FH3[:2], (D.FH1[0], D.FH1[1]))
    tie = math.dist((D.RACK_X, D.RACK_Y, D.RACK_Z), D.FH3)
    factor = arm * math.sin(math.radians(wheel_angle_deg)) / tie
    p.hydros_props(beamPrecompression=1.0, beamType="|NORMAL", beamLongBound=1, beamShortBound=1)
    p.hydros_props(beamSpring=6001000, beamDamp=60, beamDeform=40000, beamStrength=140000)
    p.hydro("rk1l", "fh3l", factor=round(factor, 4), steeringWheelLock=lock_deg, inRate=1.6, outRate=1.6,
            beamPrecompression="$toe_F", beamPrecompressionTime=0.5)
    p.hydro("rk1r", "fh3r", factor=-round(factor, 4), steeringWheelLock=lock_deg, inRate=1.6, outRate=1.6,
            beamPrecompression="$toe_F", beamPrecompressionTime=0.5)
    p.set("input", {"FFBcoef": "$=$ffbstrength*15"})
    return p


# ---------------------------------------------------------------------------
# rear
# ---------------------------------------------------------------------------
def rear_suspension(prefix, D, body_links, value=1100, title="Multilink Rear Suspension", default_wheel=None,
                    default_spring=None, default_brake=None, default_diff=None):
    p = Part(f"{prefix}_suspension_R", title, f"{prefix}_suspension_R", value=value)
    p.slot(f"{prefix}_brake_R", default_brake or f"{prefix}_brake_R_stock", "Rear Brakes")
    p.slot(f"{prefix}_wheel_R", default_wheel, "Rear Wheels")
    p.slot(f"{prefix}_wheeldata_R", f"{prefix}_wheeldata_R", "Rear Spindles", coreSlot=True)
    p.slot(f"{prefix}_spring_R", default_spring or f"{prefix}_spring_R_stock", "Rear Shocks/Springs")
    p.slot(f"{prefix}_swaybar_R", f"{prefix}_swaybar_R_stock", "Rear Sway Bar")
    p.slot(f"{prefix}_differential_R", default_diff or f"{prefix}_differential_R_open", "Rear Differential")
    p.variable("$camber_R", "", "Wheel Alignment", 0.985, 0.95, 1.03, "Camber Adjust", "Adjusts the rear camber",
               subCategory="Rear")
    p.variable("$toe_R", "", "Wheel Alignment", 0.998, 0.98, 1.02, "Toe Adjust", "Adjusts the rear toe angle",
               subCategory="Rear")
    p.variable("$trackoffset_R", "+m", "Wheels", 0.0, -0.02, 0.08, "Wheel Spacer", "Spacing of the wheel from the hub",
               stepDis=0.001, subCategory="Rear")
    p.flexbody(f"{prefix}_rsubframe", [f"{prefix}_rsubframe"])
    p.flexbody(f"{prefix}_rearlinks", [f"{prefix}_hub_R", f"{prefix}_rsubframe"])
    p.flexbody(f"{prefix}_knuckle_R", [f"{prefix}_hub_R"])
    p.nodes_props(**HUB)
    p.nodes_props(group=f"{prefix}_hub_R")
    _both(p, "rh1", D.RH1, 4.4)
    _both(p, "rh2", D.RH2, 4.0)
    _both(p, "rh3", D.RH3, 3.6)
    p.nodes_props(group=[f"{prefix}_hub_R", f"{prefix}_shockbottom_R"])
    _both(p, "rh4", D.RH4, 3.6)
    p.nodes_props(group=f"{prefix}_hub_R")
    _both(p, "rh5", D.RH5, 3.8)
    xc = D.TRACK_R / 2
    p.nodes_props(group="")
    for side, s in (("l", 1), ("r", -1)):
        tag = "RL" if s > 0 else "RR"
        p.nodes_props(group=f"wheelhub_{tag}")
        xi = f"$={s}*({xc - 0.045:.4f}+$trackoffset_R)"
        xo = f"$={s}*({xc + 0.045:.4f}+$trackoffset_R)"
        p.row("nodes", ["id", "posX", "posY", "posZ"], [f"rw1{side}", xi, D.AXLE_R_Y, D.AXLE_Z, {"nodeWeight": 3.0}])
        p.row("nodes", ["id", "posX", "posY", "posZ"], [f"rw1{side}{side}", xo, D.AXLE_R_Y, D.AXLE_Z, {"nodeWeight": 3.0}])
    p.nodes_props(group=f"{prefix}_rsubframe")
    _both(p, "rx1", D.RX1, 3.4)
    _both(p, "rx2", D.RX2, 3.4)
    _both(p, "rx3", D.RX3, 4.2)
    _both(p, "rx4", D.RX4, 2.6)
    _both(p, "rx5", D.RX5, 2.4)
    p.nodes_props(group="")
    p.beams_props(deformLimitExpansion=1.2)
    p.beams_props(beamPrecompression=1.0, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.beam_comment("upright")
    p.beams_props(beamSpring=5001000, beamDamp=100, beamDeform=50000, beamStrength=350000)
    for a, b in (("rh1", "rh2"), ("rh1", "rh3"), ("rh2", "rh3"), ("rh1", "rh5"), ("rh2", "rh5"), ("rh3", "rh5"),
                 ("rh4", "rh1"), ("rh4", "rh2"), ("rh4", "rh5"), ("rh4", "rh3")):
        _beam_both(p, a, b)
    p.beam_comment("upright to axle (breakable)")
    p.beams_props(beamSpring=8001000, beamDamp=100, beamDeform=55000, beamStrength=155000, optional=True)
    for side, tag in (("l", "RL"), ("r", "RR")):
        p.beams_props(breakGroup=f"wheel_{tag}")
        p.beam(f"rh1{side}", f"rw1{side}", name=f"axle_{tag}")
        for a in ("rh2", "rh3", "rh5"):
            p.beam(a + side, f"rw1{side}")
        for a in ("rh1", "rh2", "rh3", "rh5"):
            p.beam(a + side, f"rw1{side}{side}")
    p.beams_props(breakGroup="", optional=False)
    p.beam_comment("links: lower A-arm, upper link (camber), toe link, traction rod")
    p.beams_props(beamSpring=6001000, beamDamp=400, beamDeform=45000, beamStrength=375000)
    for a, b in (("rx1", "rh1"), ("rx2", "rh1")):
        _beam_both(p, a, b, dampCutoffHz=500)
    for s in ("l", "r"):
        p.beam(f"rx3{s}", f"rh2{s}", beamPrecompression="$camber_R", beamPrecompressionTime=0.5, dampCutoffHz=500)
        p.beam(f"rx4{s}", f"rh3{s}", beamPrecompression="$toe_R", beamPrecompressionTime=0.5, dampCutoffHz=500)
        p.beam(f"rx5{s}", f"rh5{s}", dampCutoffHz=500)
    p.beam_comment("subframe (rigid) + mounts")
    p.beams_props(beamSpring=4501000, beamDamp=150, beamDeform=60000, beamStrength="FLT_MAX")
    sub = [("rx1", "rx2"), ("rx1", "rx3"), ("rx2", "rx3"), ("rx2", "rx4"), ("rx3", "rx4"), ("rx1", "rx4")]
    for a, b in sub:
        _beam_both(p, a, b)
    for a, b in (("rx1l", "rx1r"), ("rx2l", "rx2r"), ("rx3l", "rx3r"), ("rx1l", "rx2r"), ("rx2l", "rx1r"),
                 ("rx3l", "rx1r"), ("rx3r", "rx1l"), ("rx3l", "rx2r"), ("rx3r", "rx2l")):
        p.beam(a, b)
    p.beams_props(beamSpring=3001000, beamDamp=150, beamDeform=40000, beamStrength="FLT_MAX")
    for piv, links in body_links.items():
        for b in links:
            if b.endswith("!"):
                for s in ("l", "r"):
                    p.beam(piv + s, b[:-1])
            else:
                _beam_both(p, piv, b)
    p.beam_comment("anti-invert")
    p.beams_props(beamPrecompression=1, beamType="|SUPPORT", beamLongBound=2.0, beamDeform=50000, beamStrength=250000,
                  beamSpring=2501000, beamDamp=100)
    for a, b in (("rh1", "rx3"), ("rh2", "rx1"), ("rh2", "rx2")):
        _beam_both(p, a, b, beamPrecompression=0.65)
    p.beams_props(beamPrecompression=1.0, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    p.tris_props(dragCoef=0, triangleType="NONCOLLIDABLE")
    for s in ("l", "r"):
        p.tri(f"rh1{s}", f"rh2{s}", f"rh5{s}")
        p.tri(f"rh1{s}", f"rh3{s}", f"rh2{s}")
    p.tris_props(triangleType="NORMALTYPE")
    p.d["_center_x"] = f"{D.TRACK_R / 2:.4f}+$trackoffset_R"
    return p


def wheeldata_rear(prefix, torque_coupling="dh1", torque_arm="dh2l", torque_arm2="dh2r"):
    p = Part(f"{prefix}_wheeldata_R", "Rear Spindles", f"{prefix}_wheeldata_R", value=100)
    p.pw_props(selfCollision=False, collision=True)
    for side, tag, s, wd in (("r", "RR", -1, 1), ("l", "RL", 1, -1)):
        p.pw_props(hubcapBreakGroup=f"hubcap_{tag}", hubcapGroup=f"hubcap_{tag}", axleBeams=[f"axle_{tag}"])
        p.pw(tag, f"wheel_{tag}", f"tire_{tag}", f"rw1{side}{side}", f"rw1{side}", 9999, f"rh5{side}", wd,
             {"torqueCoupling:": torque_coupling, "torqueArm:": torque_arm, "torqueArm2:": torque_arm2})
    p.pw_props(selfCollision=True)
    p.pw_props(axleBeams=[], disableMeshBreaking=False, disableTriangleBreaking=False)
    p.pw_props(hubcapBreakGroup="", hubcapGroup="", enableHubcaps=False)
    p.pw_props(enableTireLbeams=False, enableTireSideReinfBeams=False, enableTireReinfBeams=False,
               enableTreadReinfBeams=False, enableTirePeripheryReinfBeams=False, enableTireSupportBeams=False)
    p.pw_props(loadSensitivitySlope="", noLoadCoef=1, fullLoadCoef=0, softnessCoef=0.5)
    p.powertrain("shaft", "wheelaxleRL", "differential_R", 1,
                 connectedWheel="RL", breakTriggerBeam="axle_RL", uiName="Rear Left Axle", friction=2)
    p.powertrain("shaft", "wheelaxleRR", "differential_R", 2,
                 connectedWheel="RR", breakTriggerBeam="axle_RR", uiName="Rear Right Axle", friction=2)
    return p


def shocks_rear(prefix, key, title, spring, bump, rebound, height_def, height_min, height_max, value, static_load,
                mesh=None, travel_c=0.08, travel_d=0.10, adjustable=False):
    p = Part(f"{prefix}_spring_R_{key}", title, f"{prefix}_spring_R", value=value)
    mesh = mesh or f"{prefix}_shock_R"
    p.flexbody(f"{mesh}_{key}" if key != "stock" else mesh, [f"{prefix}_shockbottom_R", f"{prefix}_shocktop_R"])
    cat = "Suspension"
    p.variable("$springheight_R", "+m", cat, height_def, height_min, height_max, "Spring Height",
               "Raise or lower the rear ride height", stepDis=0.002, subCategory="Rear")
    if adjustable:
        p.variable("$spring_R", "N/m", cat, spring, spring * 0.5, spring * 2.0, "Spring Rate", "Rear spring stiffness",
                   stepDis=500, subCategory="Rear")
        p.variable("$damp_bump_R", "N/m/s", cat, bump, bump * 0.4, bump * 2.5, "Bump Damping", "Damper rate in compression",
                   stepDis=50, subCategory="Rear")
        p.variable("$damp_rebound_R", "N/m/s", cat, rebound, rebound * 0.4, rebound * 2.5, "Rebound Damping",
                   "Damper rate in extension", stepDis=50, subCategory="Rear")
        k, cb, cr = "$spring_R", "$damp_bump_R", "$damp_rebound_R"
        pre = f"$=({static_load:.0f}/$spring_R) + $springheight_R"
    else:
        k, cb, cr = spring, bump, rebound
        pre = f"$={static_load / spring:.4f} + $springheight_R"
    p.beams_props(beamType="|NORMAL", beamDeform=12000, beamStrength=140000)
    p.beams_props(beamSpring=k, beamDamp=0)
    for s in ("l", "r"):
        p.beam(f"rh4{s}", f"rt1{s}", precompressionRange=pre)
    p.beams_props(beamPrecompression=1.0, beamType="|BOUNDED", beamLongBound=1.0, beamShortBound=1.0)
    p.beams_props(beamLimitSpring=0, beamLimitDamp=0, beamSpring=250, beamDamp=cb)
    for s in ("l", "r"):
        p.beam(f"rh4{s}", f"rt1{s}", beamDampRebound=cr, beamDampVelocitySplit=0.2,
               beamDampFast=f"$={cb}/3" if isinstance(cb, str) else round(cb / 3),
               beamDampReboundFast=f"$={cr}/3" if isinstance(cr, str) else round(cr / 3),
               dampCutoffHz=500, soundFile="event:>Vehicle>Suspension>car_modn_sml_01>spring_compress_01",
               colorFactor=0.8, attackFactor=10, volumeFactor=2.0, decayMode=1, decayFactor=10, pitchFactor=0.5, maxStress=13)
    p.beams_props(beamSpring=0, beamDamp=0, beamLimitSpring=251000, beamLimitDamp=5000)
    for s in ("l", "r"):
        p.beam(f"rh4{s}", f"rt1{s}", longBoundRange=travel_d, shortBoundRange=travel_c, boundZone=0.03,
               beamLimitDampRebound=0, dampCutoffHz=500)
    p.beams_props(beamLimitSpring=0, beamLimitDamp=0)
    p.beams_props(beamPrecompression=1.0, beamType="|NORMAL", beamLongBound=1.0, beamShortBound=1.0)
    return p


def swaybar_rear(prefix, key, title, rate, value, adjustable=False, lever=0.18):
    p = Part(f"{prefix}_swaybar_R_{key}", title, f"{prefix}_swaybar_R", value=value)
    if adjustable:
        p.variable("$arb_spring_R", "N/m", "Suspension", rate, rate * 0.3, rate * 2.5, "Anti-Roll Spring Rate",
                   "Stiffness of the rear anti-roll bar at the end links", stepDis=500, subCategory="Rear")
        spring = f"$=$arb_spring_R*{lever}*{lever}"
    else:
        spring = round(rate * lever * lever, 1)
    p.flexbody(f"{prefix}_swaybar_R", [f"{prefix}_hub_R", f"{prefix}_rsubframe"])
    p.torsion_props(spring=spring, damp=10, deform=8000, strength=9999999)
    p.torsionbar("rh1l", "rx1l", "rx1r", "rh1r")
    return p
