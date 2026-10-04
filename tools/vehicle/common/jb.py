"""Tiny DSL for building JBeam parts in Python.

Example:
    p = Part("s13_hood", "Stock Hood", "s13_hood", value=300)
    p.nodes_props(group="s13_hood", nodeWeight=1.2, collision=True, selfCollision=True, nodeMaterial="|NM_METAL")
    p.node("h1l", 0.3, -1.9, 0.6)
    p.beams_props(beamSpring=1001000, beamDamp=40, beamDeform=9000, beamStrength="FLT_MAX")
    p.beam("h1l", "h1r")
    ...
    p.build() -> dict ready for writer.dumps({name: dict})
"""
from __future__ import annotations

import math
from collections import OrderedDict

AUTHOR = "S13/S14 240SX mod"

NODE_HEADER = ["id", "posX", "posY", "posZ"]
BEAM_HEADER = ["id1:", "id2:"]
TRI_HEADER = ["id1:", "id2:", "id3:"]
TORSION_HEADER = ["id1:", "id2:", "id3:", "id4:"]
SLOT_HEADER = ["type", "default", "description"]
VAR_HEADER = ["name", "type", "unit", "category", "default", "min", "max", "title", "description"]
FLEX_HEADER = ["mesh", "[group]:", "nonFlexMaterials"]
PROP_HEADER = ["func", "mesh", "idRef:", "idX:", "idY:", "baseRotation", "rotation", "translation", "min", "max", "offset", "multiplier"]
PT_HEADER = ["type", "name", "inputName", "inputIndex"]
CAM_HEADER = ["type", "x", "y", "z", "fov", "id1:", "id2:", "id3:", "id4:", "id5:", "id6:"]
PW_HEADER = ["name", "hubGroup", "group", "node1:", "node2:", "nodeS", "nodeArm:", "wheelDir"]


def r3(v, n=4):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return round(float(v), n)
    return v


class Part:
    def __init__(self, name, title, slot_type, value=100, authors=AUTHOR, aux=False):
        self.name = name
        self.d = OrderedDict()
        info = {"authors": authors, "name": title, "value": value}
        if aux:
            info["isAuxiliary"] = True
        self.d["information"] = info
        self.d["slotType"] = slot_type
        self._tables = {}
        self.node_names = []
        self.node_pos = {}

    # -- generic --------------------------------------------------------
    def set(self, key, value):
        self.d[key] = value
        return self

    def table(self, key, header):
        if key not in self._tables:
            self._tables[key] = [header]
        return self._tables[key]

    def row(self, key, header, row):
        self.table(key, header).append(row)

    def comment(self, key, header, text):
        self.table(key, header).append("//" + text)

    # -- slots / variables ----------------------------------------------
    def slot(self, slot_type, default, description, **opts):
        r = [slot_type, default, description]
        if opts:
            r.append(opts)
        self.row("slots", SLOT_HEADER, r)

    def variable(self, name, unit, category, default, vmin, vmax, title, desc, **opts):
        r = [name, "range", unit, category, default, vmin, vmax, title, desc]
        if opts:
            r.append(opts)
        self.row("variables", VAR_HEADER, r)

    # -- nodes ------------------------------------------------------------
    def nodes_props(self, **props):
        self.table("nodes", NODE_HEADER).append(dict(props))

    def node(self, name, x, y, z, **inline):
        r = [name, r3(x), r3(y), r3(z)]
        if inline:
            r.append(inline)
        self.row("nodes", NODE_HEADER, r)
        self.node_names.append(name)
        self.node_pos[name] = (x, y, z)

    def node_lr(self, name, x, y, z, **inline):
        """Left (x>0) and right (x<0) pair: names <name>l / <name>r."""
        self.node(name + "l", abs(x), y, z, **inline)
        self.node(name + "r", -abs(x), y, z, **inline)

    # -- beams ------------------------------------------------------------
    def beams_props(self, **props):
        self.table("beams", BEAM_HEADER).append(dict(props))

    def beam(self, a, b, **inline):
        r = [a, b]
        if inline:
            r.append(inline)
        self.row("beams", BEAM_HEADER, r)

    def beams(self, pairs, **inline):
        for a, b in pairs:
            self.beam(a, b, **inline)

    def chain(self, names, closed=False, **inline):
        for a, b in zip(names, names[1:]):
            self.beam(a, b, **inline)
        if closed and len(names) > 2:
            self.beam(names[-1], names[0], **inline)

    def beam_comment(self, text):
        self.comment("beams", BEAM_HEADER, text)

    # -- triangles ---------------------------------------------------------
    def tris_props(self, **props):
        self.table("triangles", TRI_HEADER).append(dict(props))

    def tri(self, a, b, c, **inline):
        r = [a, b, c]
        if inline:
            r.append(inline)
        self.row("triangles", TRI_HEADER, r)

    def quad(self, a, b, c, d, **inline):
        """Two triangles for quad a-b-c-d (counter-clockwise seen from outside)."""
        self.tri(a, b, c, **inline)
        self.tri(a, c, d, **inline)

    # -- misc sections ----------------------------------------------------
    def torsionbar(self, a, b, c, d, **inline):
        r = [a, b, c, d]
        if inline:
            r.append(inline)
        self.row("torsionbars", TORSION_HEADER, r)

    def torsion_props(self, **props):
        self.table("torsionbars", TORSION_HEADER).append(dict(props))

    def flexbody(self, mesh, groups, **opts):
        r = [mesh, list(groups)]
        if opts:
            r += [[], opts]
        self.row("flexbodies", FLEX_HEADER, r)

    def flex_props(self, **props):
        self.table("flexbodies", FLEX_HEADER).append(dict(props))

    def prop(self, func, mesh, ref, idx, idy, base_rot, rot, trans, vmin, vmax, offset=0, mult=1, **opts):
        r = [func, mesh, ref, idx, idy, base_rot, rot, trans, vmin, vmax, offset, mult]
        if opts:
            r.append(opts)
        self.row("props", PROP_HEADER, r)

    def props_props(self, **props):
        self.table("props", PROP_HEADER).append(dict(props))

    def powertrain(self, typ, name, inp, idx, **opts):
        r = [typ, name, inp, idx]
        if opts:
            r.append(opts)
        self.row("powertrain", PT_HEADER, r)

    def controller(self, filename, **opts):
        self.row("controller", ["fileName"], [filename, opts] if opts else [filename])

    def hydros_props(self, **props):
        self.table("hydros", BEAM_HEADER).append(dict(props))

    def hydro(self, a, b, **inline):
        r = [a, b]
        if inline:
            r.append(inline)
        self.row("hydros", BEAM_HEADER, r)

    def pw_props(self, **props):
        self.table("pressureWheels", PW_HEADER).append(dict(props))

    def pw(self, *row):
        self.row("pressureWheels", PW_HEADER, list(row))

    def scale_springs(self, factor, sections=("beams", "hydros")):
        """Scale every numeric beamSpring/beamDamp modifier (and inline row values) in the given sections.
        Used for lightweight panel variants: same frequency with lighter nodes."""
        for sec in sections:
            for row in self._tables.get(sec, []):
                d = row if isinstance(row, dict) else (row[-1] if isinstance(row, list) and row and isinstance(row[-1], dict) else None)
                if not d:
                    continue
                for k in ("beamSpring", "beamDamp"):
                    v = d.get(k)
                    if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
                        d[k] = int(round(v * factor)) if k == "beamSpring" else round(v * factor, 2)
        return self

    def build(self):
        out = OrderedDict((k, v) for k, v in self.d.items() if not k.startswith("_"))
        # keep a stable, vanilla-like section order
        order = ["slots", "variables", "controller", "powertrain", "flexbodies", "props", "nodes", "beams",
                 "hydros", "torsionbars", "triangles", "pressureWheels"]
        for k in order:
            if k in self._tables:
                t = self._tables[k]
                out[k] = t
        for k, t in self._tables.items():
            if k not in out:
                out[k] = t
        return out


def merge(*parts):
    out = OrderedDict()
    for p in parts:
        out[p.name] = p.build()
    return out


def dist(a, b):
    return math.dist(a, b)
