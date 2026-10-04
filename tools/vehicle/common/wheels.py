"""Wheels, tires and brakes as pressure-wheel parameter sets (shared S13/S14).

Split follows the BeamNG docs: hub parameters live in the wheel part, tire
parameters in the tire part (child slot of the wheel), brake parameters in the
brake part, and the actual wheel rows in the suspension's wheeldata part.
Values are scaled from the docs' known-good example (radius 0.28, width 0.135).

Wheel/tire meshes are modelled around the origin with the axle along X and the
outer face toward +X; the left wheel uses them as-is, the right one rotated 180°
about Z (same convention as vanilla).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .jb import Part

IN = 0.0254


@dataclass
class WheelDef:
    key: str            # mesh/part key, e.g. "oem15_7spoke"
    title: str
    dia: int            # rim diameter (inch)
    width: float        # rim width (inch)
    mass: float         # kg
    value: int
    lugs: int = 4
    style: str = "alloy"   # alloy / steel / race / mesh / deepdish / beadlock
    hubcap: bool = False


@dataclass
class TireDef:
    key: str            # e.g. "205_60_15_allseason"
    title: str
    width_mm: int
    aspect: int
    dia: int
    kind: str           # allseason / sport / semislick / slick / drift / dragradial / dragslick / runner
    mass: float
    value: int
    pressure: float = 32.0
    radius_override: float | None = None

    @property
    def radius(self):
        if self.radius_override:
            return self.radius_override
        return (self.dia * IN) / 2 + self.width_mm * self.aspect / 100000.0

    @property
    def tread_width(self):
        return self.width_mm / 1000.0 * (0.82 if self.kind not in ("slick", "dragslick") else 0.92)


# tire compound behaviour -------------------------------------------------------------
COMPOUND = {
    #             friction sliding  tread  softness noLoad  fullLoad slope
    "allseason":  (0.96, 0.84, 0.75, 0.55, 1.28, 0.42, 0.00019),
    "sport":      (1.04, 0.90, 0.60, 0.62, 1.30, 0.44, 0.00018),
    "semislick":  (1.14, 0.98, 0.38, 0.74, 1.34, 0.46, 0.00017),
    "slick":      (1.28, 1.08, 0.00, 0.86, 1.38, 0.50, 0.00015),
    "drift":      (0.99, 0.86, 0.55, 0.50, 1.26, 0.42, 0.00019),
    "dragradial": (1.32, 1.06, 0.30, 0.82, 1.40, 0.50, 0.00016),
    "dragslick":  (1.46, 1.16, 0.00, 0.92, 1.45, 0.55, 0.00014),
    "runner":     (0.85, 0.78, 0.40, 0.50, 1.20, 0.40, 0.00020),
}


def hub_props(w: WheelDef, num_rays=16):
    hub_r = (w.dia * IN) / 2 + 0.012
    hub_w = w.width * IN
    node_w = max(w.mass / (2 * num_rays), 0.18)
    stiff = 1.0 + 0.15 * (w.width - 6)
    return [
        {"disableMeshBreaking": False, "disableHubMeshBreaking": False, "hasTire": False},
        {"hubRadius": round(hub_r, 4)},
        {"hubWidth": round(hub_w, 4)},
        {"numRays": num_rays},
        {"hubTreadBeamSpring": int(901000 * stiff), "hubTreadBeamDamp": 6},
        {"hubPeripheryBeamSpring": int(901000 * stiff), "hubPeripheryBeamDamp": 6},
        {"hubSideBeamSpring": int(1351000 * stiff), "hubSideBeamDamp": 6},
        {"hubNodeWeight": round(node_w, 3)},
        {"hubNodeMaterial": "|NM_METAL"},
        {"hubFrictionCoef": 0.5},
        {"hubBeamDeform": 15000, "hubBeamStrength": 66000},
    ]


def tire_props(t: TireDef, axle: str, num_rays=16):
    f, sf, tread, soft, nlc, flc, slope = COMPOUND[t.kind]
    wscale = t.tread_width / 0.135
    rscale = t.radius / 0.28
    sidewall = t.radius - (t.dia * IN / 2 + 0.012)
    node_w = max(t.mass * 0.55 / (2 * num_rays), 0.08)
    pvar = f"$tirepressure_{axle}"
    lbeam = t.kind not in ("dragslick",)
    out = [
        {"hasTire": True},
        {"enableTireReinfBeams": False},
        {"enableTireLbeams": lbeam},
        {"enableTireSideReinfBeams": t.kind in ("dragslick", "dragradial", "runner")},
        {"enableTreadReinfBeams": True},
        {"enableTirePeripheryReinfBeams": True},
        {"radius": round(t.radius, 4)},
        {"tireWidth": round(t.tread_width, 4)},
        {"wheelSideBeamSpring": f"$={pvar}*{int(550 * wscale ** 0.5)}", "wheelSideBeamDamp": 20},
        {"wheelSideBeamSpringExpansion": int(281000 * wscale ** 0.5), "wheelSideBeamDampExpansion": 30},
        {"wheelSideTransitionZone": round(min(0.12, max(0.05, sidewall * 0.75)), 3), "wheelSideBeamPrecompression": 0.98},
        {"wheelReinfBeamSpring": int(15000 * wscale), "wheelReinfBeamDamp": 140},
        {"wheelReinfBeamDampCutoffHz": 500, "wheelReinfBeamPrecompression": 0.98},
        {"wheelTreadBeamSpring": int(50000 * wscale), "wheelTreadBeamDamp": 50},
        {"wheelTreadBeamDampCutoffHz": 500, "wheelTreadBeamPrecompression": 0.98},
        {"wheelTreadReinfBeamSpring": int(120000 * wscale), "wheelTreadReinfBeamDamp": 40},
        {"wheelTreadReinfBeamDampCutoffHz": 500, "wheelTreadReinfBeamPrecompression": 0.98},
        {"wheelPeripheryBeamSpring": int(35000 * wscale * rscale), "wheelPeripheryBeamDamp": 23},
        {"wheelPeripheryBeamDampCutoffHz": 500, "wheelPeripheryBeamPrecompression": 0.98},
        {"wheelPeripheryReinfBeamSpring": int(95000 * wscale * rscale), "wheelPeripheryReinfBeamDamp": 23},
        {"wheelPeripheryReinfBeamDampCutoffHz": 500, "wheelPeripheryReinfBeamPrecompression": 0.98},
        {"nodeWeight": round(node_w, 3)},
        {"nodeMaterial": "|NM_RUBBER"},
        {"triangleCollision": False},
        {"pressurePSI": pvar},
        {"dragCoef": 5},
        {"frictionCoef": f},
        {"slidingFrictionCoef": sf},
        {"treadCoef": tread},
        {"noLoadCoef": nlc},
        {"loadSensitivitySlope": slope},
        {"fullLoadCoef": flc},
        {"softnessCoef": soft},
        {"wheelSideBeamDeform": 11000, "wheelSideBeamStrength": 15000},
        {"wheelTreadBeamDeform": 10000, "wheelTreadBeamStrength": 13000},
        {"wheelPeripheryBeamDeform": 40000, "wheelPeripheryBeamStrength": 40000},
    ]
    if t.kind in ("dragslick", "dragradial"):
        out.append({"enableTireSupportBeams": True})
    return out


def wheel_part(prefix, w: WheelDef, axle: str, center_x: str, default_tire: str, axle_yz=(0.0, 0.0), mesh_prefix="s1x_wheel"):
    """Wheel (rim) part for axle 'F' or 'R'. center_x: expression for |x| of the wheel centre."""
    p = Part(f"{prefix}_wheel_{axle}_{w.key}", f"{w.title} ({'Front' if axle == 'F' else 'Rear'})",
             f"{prefix}_wheel_{axle}", value=w.value)
    p.slot(f"{prefix}_tire_{axle}_{w.dia}", default_tire, "Front Tires" if axle == "F" else "Rear Tires")
    if w.hubcap:
        p.slot(f"{prefix}_hubcap_{axle}_{w.dia}", f"{prefix}_hubcap_{axle}_{w.dia}", "Hubcaps")
    mesh = f"{mesh_prefix}_{w.key}"
    sides = ("R", "L") if axle == "F" else ("R", "L")
    for side in sides:
        tag = f"{axle}{side}"
        xexpr = f"$=-({center_x})" if side == "R" else f"$={center_x}"
        p.flexbody(mesh, [f"wheel_{tag}", f"wheelhub_{tag}"],
                   pos={"x": xexpr, "y": axle_yz[0], "z": axle_yz[1]}, rot={"x": 0, "y": 0, "z": 180 if side == "R" else 0},
                   scale={"x": 1, "y": 1, "z": 1})
    for row in hub_props(w):
        p.table("pressureWheels", ["name", "hubGroup", "group", "node1:", "node2:", "nodeS", "nodeArm:", "wheelDir"]).append(row)
    return p


def tire_part(prefix, t: TireDef, axle: str, center_x: str, axle_yz=(0.0, 0.0), mesh_prefix="s1x_tire"):
    p = Part(f"{prefix}_tire_{axle}_{t.key}", f"{t.title} ({'Front' if axle == 'F' else 'Rear'})",
             f"{prefix}_tire_{axle}_{t.dia}", value=t.value)
    p.variable(f"$tirepressure_{axle}", "psi", "Wheels", t.pressure, 0, 50 if t.kind not in ("dragslick",) else 30,
               "Tire Pressure", "Relative to atmospheric pressure",
               subCategory="Front" if axle == "F" else "Rear", stepDis=0.5)
    mesh = f"{mesh_prefix}_{t.key}"
    for side in ("R", "L"):
        tag = f"{axle}{side}"
        xexpr = f"$=-({center_x})" if side == "R" else f"$={center_x}"
        p.flexbody(mesh, [f"wheel_{tag}", f"tire_{tag}"],
                   pos={"x": xexpr, "y": axle_yz[0], "z": axle_yz[1]}, rot={"x": 0, "y": 0, "z": 180 if side == "R" else 0},
                   scale={"x": 1, "y": 1, "z": 1})
    for row in tire_props(t, axle):
        p.table("pressureWheels", ["name", "hubGroup", "group", "node1:", "node2:", "nodeS", "nodeArm:", "wheelDir"]).append(row)
    return p


@dataclass
class BrakeDef:
    key: str
    title: str
    torque_F: float
    torque_R: float
    disc_F: float
    disc_R: float
    mass_F: float
    mass_R: float
    vent_F: float = 1.0
    vent_R: float = 0.8
    type_R: str = "disc"
    pad: str = "basic"
    park: float = 1100
    value: int = 300
    abs: bool = False
    mesh_F: str = "s1x_brake_stock_F"
    mesh_R: str = "s1x_brake_stock_R"
    caliper_F: str = "s1x_caliper_stock_F"
    caliper_R: str = "s1x_caliper_stock_R"


def brake_part(prefix, b: BrakeDef, axle: str, hub_group: str):
    front = axle == "F"
    p = Part(f"{prefix}_brake_{axle}_{b.key}", f"{b.title} ({'Front' if front else 'Rear'})",
             f"{prefix}_brake_{axle}", value=b.value)
    p.slot(f"{prefix}_brakepad_{axle}", f"{prefix}_brakepad_{axle}_{b.pad}", "Brake Pads", coreSlot=True)
    disc_mesh = f"{prefix}_brake_{b.key if b.key != 'abs' else 'stock'}_{axle}"
    cal_mesh = f"{prefix}_caliper_{b.key if b.key != 'abs' else 'stock'}_{axle}"
    for side in ("R", "L"):
        tag = f"{axle}{side}"
        p.flexbody(f"{disc_mesh}_{side}", [f"wheel_{tag}", f"wheelhub_{tag}"])
    p.flexbody(cal_mesh, [hub_group])
    tq_total = b.torque_F + b.torque_R
    if front:
        torque = f"$=$brakestrength*{tq_total:.0f}*$brakebias"
    else:
        torque = f"$=$brakestrength*{tq_total:.0f}*(1-$brakebias)"
    rows = [
        {"brakeTorque": torque},
        {"brakeInputSplit": 1},
        {"brakeSplitCoef": 1},
        {"parkingTorque": 0 if front else b.park},
        {"brakeSpring": 125},
        {"enableBrakeThermals": True},
        {"brakeDiameter": b.disc_F if front else b.disc_R},
        {"brakeMass": b.mass_F if front else b.mass_R},
        {"brakeType": "vented-disc" if front or b.type_R == "vented-disc" else "disc"},
        {"rotorMaterial": "steel"},
        {"brakeVentingCoef": b.vent_F if front else b.vent_R},
        {"squealCoefNatural": 0.0, "squealCoefLowSpeed": 0.0},
        {"enableABS": b.abs},
    ]
    for row in rows:
        p.table("pressureWheels", ["name", "hubGroup", "group", "node1:", "node2:", "nodeS", "nodeArm:", "wheelDir"]).append(row)
    return p


PADS = {
    "basic": ("Stock Brake Pads", 60), "premium": ("Premium Brake Pads", 140), "sport": ("Sport Brake Pads", 220),
    "semi-race": ("Semi-Race Brake Pads", 320), "full-race": ("Race Brake Pads", 480),
}


def pad_parts(prefix):
    out = []
    for axle in ("F", "R"):
        for key, (title, value) in PADS.items():
            p = Part(f"{prefix}_brakepad_{axle}_{key}", f"{title} ({'Front' if axle == 'F' else 'Rear'})",
                     f"{prefix}_brakepad_{axle}", value=value)
            p.table("pressureWheels", ["name", "hubGroup", "group", "node1:", "node2:", "nodeS", "nodeArm:", "wheelDir"]).append(
                {"padMaterial": key})
            out.append(p)
    return out


def hubcap_part(prefix, axle, dia, center_x, axle_yz=(0.0, 0.0), mesh="s1x_hubcap"):
    p = Part(f"{prefix}_hubcap_{axle}_{dia}", f"Steel Wheel Hubcaps ({'Front' if axle == 'F' else 'Rear'})",
             f"{prefix}_hubcap_{axle}_{dia}", value=40)
    for side in ("R", "L"):
        tag = f"{axle}{side}"
        xexpr = f"$=-({center_x})" if side == "R" else f"$={center_x}"
        p.flexbody(f"{mesh}_{dia}", [f"wheel_{tag}", f"wheelhub_{tag}"],
                   pos={"x": xexpr, "y": axle_yz[0], "z": axle_yz[1]}, rot={"x": 0, "y": 0, "z": 180 if side == "R" else 0},
                   scale={"x": 1, "y": 1, "z": 1})
    return p
