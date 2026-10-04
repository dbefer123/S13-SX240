"""Offline approximation of BeamNG's JBeam part-tree loader.

It is used only for validation. Behaviour mirrored from the game (as documented
at documentation.beamng.com and observed in the official modding template):

* parts are found by name across all .jbeam files of a vehicle folder;
* the root is the part whose slotType is ``main``;
* ``slots`` / ``slots2`` choose children: config value if present (``""`` = empty),
  otherwise the slot default; children are processed depth-first after the parent;
* table sections start with a header row; dict rows are modifiers that persist
  ("leak") until changed, across parts; an inline trailing dict on a row
  overrides properties for that row only;
* ``$var`` / ``"$=expr"`` values are evaluated against the variable set
  (variable defaults from all used parts, overridden by slot variables and the
  config ``vars``);
* ``nodeOffset`` / ``nodeMove`` from slot options apply to the whole subtree;
* dict sections merge key by key; ``$+key`` adds and ``$*key`` multiplies.
"""
from __future__ import annotations

import glob
import math
import os
import re
from dataclasses import dataclass, field

import numpy as np

from .parser import load

TABLE_SECTIONS = {
    "nodes", "beams", "triangles", "quads", "torsionbars", "hydros", "torsionHydros",
    "rails", "slidenodes", "pressureWheels", "flexbodies", "props", "refNodes",
    "camerasInternal", "powertrain", "controller", "variables", "slots", "slots2",
    "energyStorage", "mirrors", "sounds", "rotators", "thrusters", "triggers",
    "triggerEventLinks", "cameraExternalPositions", "events",
}

NODE_REF_SECTIONS = {
    "beams": 2, "triangles": 3, "quads": 4, "torsionbars": 4, "hydros": 2,
    "torsionHydros": 4,
}


class ResolveError(Exception):
    pass


# ---------------------------------------------------------------------------
# expression evaluation
# ---------------------------------------------------------------------------
_VAR_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_\.]*)")


def _lua_to_py(expr: str) -> str:
    e = expr
    e = e.replace("~=", "!=")
    e = re.sub(r"\bnil\b", "None", e)
    e = e.replace("..", " + ")
    e = re.sub(r"\bmath\.", "", e)
    e = _VAR_RE.sub(lambda m: f"__v({m.group(1)!r})", e)
    return e


_SAFE = {
    "min": min, "max": max, "abs": abs, "floor": math.floor, "ceil": math.ceil,
    "sqrt": math.sqrt, "pi": math.pi, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "atan": math.atan, "pow": pow, "huge": math.inf, "clamp": lambda v, a, b: max(a, min(b, v)),
    "round": round, "tostring": str, "tonumber": float, "concat": lambda a, sep="": sep.join(map(str, a)),
}


def evaluate(value, variables: dict, components: dict | None = None):
    """Evaluate a jbeam value that may contain "$var" or "$=expr" strings."""
    if isinstance(value, str):
        if value.startswith("$="):
            def __v(name):
                if name.startswith("components."):
                    cur = components or {}
                    for p in name.split(".")[1:]:
                        if not isinstance(cur, dict) or p not in cur:
                            return None
                        cur = cur[p]
                    return cur
                key = "$" + name
                if key not in variables:
                    raise ResolveError(f"undefined variable {key} in {value!r}")
                return variables[key]
            env = dict(_SAFE)
            env["__v"] = __v
            try:
                return eval(_lua_to_py(value[2:]), {"__builtins__": {}}, env)
            except ResolveError:
                raise
            except Exception as ex:  # pragma: no cover - reported to caller
                raise ResolveError(f"cannot evaluate {value!r}: {ex}") from ex
        if value.startswith("$") and not value.startswith("$+") and not value.startswith("$*"):
            if value in variables:
                return variables[value]
            if re.fullmatch(r"\$[A-Za-z_][A-Za-z0-9_]*", value):
                raise ResolveError(f"undefined variable {value}")
        return value
    if isinstance(value, list):
        return [evaluate(v, variables, components) for v in value]
    if isinstance(value, dict):
        return {k: evaluate(v, variables, components) for k, v in value.items()}
    return value


# ---------------------------------------------------------------------------
# part database
# ---------------------------------------------------------------------------
class PartDB:
    def __init__(self, *dirs: str):
        self.parts: dict[str, dict] = {}
        self.part_file: dict[str, str] = {}
        self.duplicates: list[tuple[str, str, str]] = []
        for d in dirs:
            for path in sorted(glob.glob(os.path.join(d, "**", "*.jbeam"), recursive=True)):
                data = load(path)
                for name, part in data.items():
                    if name in self.parts:
                        self.duplicates.append((name, self.part_file[name], path))
                    self.parts[name] = part
                    self.part_file[name] = path

    def slot_types(self, part: dict) -> list[str]:
        st = part.get("slotType")
        return st if isinstance(st, list) else [st]

    def main_part(self) -> str:
        mains = [n for n, p in self.parts.items() if "main" in self.slot_types(p)]
        if len(mains) != 1:
            raise ResolveError(f"expected exactly one main part, found {mains}")
        return mains[0]

    def parts_for_slot(self, allow: list[str], deny: list[str] = ()) -> list[str]:
        out = []
        for n, p in self.parts.items():
            st = self.slot_types(p)
            if any(t in allow for t in st) and not any(t in deny for t in st):
                out.append(n)
        return out


def iter_slots(part: dict):
    """Yield (slotName, allowTypes, denyTypes, default, description, options)."""
    for sec in ("slots", "slots2"):
        rows = part.get(sec)
        if not rows:
            continue
        header = rows[0]
        for row in rows[1:]:
            if not isinstance(row, list):
                continue
            opts = row[-1] if row and isinstance(row[-1], dict) else {}
            vals = row[:-1] if opts else row
            if sec == "slots":
                name, default = vals[0], vals[1] if len(vals) > 1 else ""
                desc = vals[2] if len(vals) > 2 else name
                yield name, [name], [], default, desc, opts
            else:
                name, allow, deny = vals[0], vals[1], vals[2]
                default = vals[3] if len(vals) > 3 else ""
                desc = vals[4] if len(vals) > 4 else name
                yield name, list(allow), list(deny), default, desc, opts


@dataclass
class TreeNode:
    slot: str
    part: str
    path: str
    offset: dict = field(default_factory=dict)  # accumulated nodeOffset / nodeMove
    slot_vars: dict = field(default_factory=dict)
    children: list = field(default_factory=list)


@dataclass
class Resolved:
    tree: TreeNode
    order: list            # TreeNode in processing order
    variables: dict
    var_defs: dict         # name -> (part, row)
    nodes: dict            # name -> dict(pos=np.array, props..., part=...)
    tables: dict           # section -> list of (row dict, part)
    dicts: dict            # merged dict sections
    errors: list
    warnings: list
    unused_config_slots: list


def build_tree(db: PartDB, config_parts: dict, main: str | None = None):
    errors, warnings = [], []
    main = main or config_parts.get("main") or db.main_part()
    if main not in db.parts:
        raise ResolveError(f"main part {main!r} not found")
    used_slots = set()
    root = TreeNode("main", main, main)

    def rec(node: TreeNode, offset: dict, svars: dict, depth: int):
        if depth > 40:
            raise ResolveError("slot recursion too deep")
        part = db.parts[node.part]
        for name, allow, deny, default, desc, opts in iter_slots(part):
            chosen = config_parts.get(name, default) if name in config_parts else default
            if name in config_parts:
                used_slots.add(name)
            if not chosen:
                if opts.get("coreSlot"):
                    errors.append(f"core slot {name!r} in {node.part} is empty")
                continue
            if chosen not in db.parts:
                errors.append(f"slot {name!r} in {node.part}: part {chosen!r} does not exist")
                continue
            st = db.slot_types(db.parts[chosen])
            if not any(t in allow for t in st) or any(t in deny for t in st):
                errors.append(f"slot {name!r} in {node.part}: part {chosen!r} has slotType {st}, allowed {allow}")
                continue
            off = dict(offset)
            for k in ("nodeOffset", "nodeMove"):
                if k in opts:
                    off[k] = opts[k]  # child slot overwrites parent value (docs)
            nv = dict(svars)
            nv.update(opts.get("variables", {}))
            child = TreeNode(name, chosen, node.path + "/" + name, off, nv)
            node.children.append(child)
            rec(child, off, nv, depth + 1)

    rec(root, {}, {}, 0)
    unused = [k for k in config_parts if k not in used_slots and k != "main"]
    return root, errors, warnings, unused


def _flatten(node: TreeNode):
    yield node
    for c in node.children:
        yield from _flatten(c)


def _apply_offset(pos, offset: dict, variables: dict):
    x, y, z = pos
    no = offset.get("nodeOffset")
    if no:
        no = evaluate(no, variables)
        ox, oy, oz = float(no.get("x", 0)), float(no.get("y", 0)), float(no.get("z", 0))
        if x > 0:
            x += ox
        elif x < 0:
            x -= ox
        y += oy
        z += oz
    nm = offset.get("nodeMove")
    if nm:
        nm = evaluate(nm, variables)
        x += float(nm.get("x", 0)); y += float(nm.get("y", 0)); z += float(nm.get("z", 0))
    return np.array([x, y, z], dtype=float)


def resolve(db: PartDB, config: dict, main: str | None = None) -> Resolved:
    config_parts = config.get("parts", {})
    config_vars = config.get("vars", {})
    root, errors, warnings, unused = build_tree(db, config_parts, main)
    order = list(_flatten(root))

    # ---- variables: defaults from every used part, then slot vars, then config
    variables, var_defs = {}, {}
    for tn in order:
        rows = db.parts[tn.part].get("variables") or []
        for row in rows[1:]:
            if isinstance(row, list) and row and isinstance(row[0], str) and row[0].startswith("$"):
                name, default = row[0], row[4] if len(row) > 4 else 0
                vmin = row[5] if len(row) > 5 else None
                vmax = row[6] if len(row) > 6 else None
                if name in var_defs and var_defs[name][0] != tn.part:
                    warnings.append(f"variable {name} defined in {var_defs[name][0]} and {tn.part}")
                var_defs[name] = (tn.part, row)
                variables[name] = default
                if isinstance(default, (int, float)) and isinstance(vmin, (int, float)) and isinstance(vmax, (int, float)):
                    lo, hi = min(vmin, vmax), max(vmin, vmax)
                    if not (lo - 1e-9 <= default <= hi + 1e-9):
                        warnings.append(f"variable {name} default {default} outside [{vmin},{vmax}]")
    for tn in order:
        for k, v in tn.slot_vars.items():
            variables[k] = v
    for k, v in config_vars.items():
        if k not in variables:
            warnings.append(f"config var {k} is not defined by any used part")
        variables[k] = v
    # resolve variables that are themselves expressions
    for _ in range(3):
        for k, v in list(variables.items()):
            if isinstance(v, str) and v.startswith("$"):
                try:
                    variables[k] = evaluate(v, variables)
                except ResolveError:
                    pass

    nodes: dict = {}
    tables: dict = {}
    dicts: dict = {}
    components: dict = {}
    state: dict = {}  # per-section leaking modifiers

    # components first (they can be referenced anywhere)
    def deep_merge(dst, src):
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                deep_merge(dst[k], v)
            else:
                dst[k] = v
    for tn in order:
        comp = db.parts[tn.part].get("components")
        if isinstance(comp, dict):
            deep_merge(components, comp)

    for tn in order:
        part = db.parts[tn.part]
        for sec, val in part.items():
            if sec in ("information", "slotType", "slots", "slots2", "variables", "components"):
                continue
            if isinstance(val, list) and val and isinstance(val[0], list) and sec in TABLE_SECTIONS:
                header = val[0]
                props = state.setdefault(sec, {})
                for row in val[1:]:
                    if isinstance(row, dict):
                        try:
                            props.update(evaluate(row, variables, components))
                        except ResolveError as ex:
                            errors.append(f"{tn.part}.{sec}: {ex}")
                        continue
                    if isinstance(row, str):
                        if row.startswith("$="):
                            try:
                                row = evaluate(row, variables, components)
                            except ResolveError as ex:
                                errors.append(f"{tn.part}.{sec}: {ex}")
                                continue
                        else:
                            continue
                    if not isinstance(row, list):
                        continue
                    inline = row[-1] if row and isinstance(row[-1], dict) else None
                    vals = row[:-1] if inline is not None else row
                    try:
                        vals = evaluate(vals, variables, components)
                        inline = evaluate(inline, variables, components) if inline else None
                    except ResolveError as ex:
                        errors.append(f"{tn.part}.{sec}: {ex}")
                        continue
                    rec = dict(props)
                    for i, h in enumerate(header):
                        if i < len(vals):
                            rec[h] = vals[i]
                    if inline:
                        rec.update(inline)
                    rec["__part"] = tn.part
                    rec["__treenode"] = tn
                    if sec == "nodes":
                        try:
                            pos = (float(vals[1]), float(vals[2]), float(vals[3]))
                        except (TypeError, ValueError, IndexError):
                            errors.append(f"{tn.part}: bad node row {row}")
                            continue
                        rec["pos"] = _apply_offset(pos, tn.offset, variables)
                        name = vals[0]
                        if name in nodes:
                            warnings.append(f"node {name} redefined in {tn.part} (first in {nodes[name]['__part']})")
                        nodes[name] = rec
                    else:
                        tables.setdefault(sec, []).append(rec)
            elif isinstance(val, dict):
                try:
                    ev = evaluate(val, variables, components)
                except ResolveError as ex:
                    errors.append(f"{tn.part}.{sec}: {ex}")
                    continue
                dst = dicts.setdefault(sec, {})
                for k, v in ev.items():
                    if k.startswith("$+"):
                        kk = k[2:]
                        dst[kk] = dst.get(kk, 0) + v
                    elif k.startswith("$*"):
                        kk = k[2:]
                        dst[kk] = dst.get(kk, 1) * v
                    elif isinstance(v, dict) and isinstance(dst.get(k), dict) and sec not in ("information",):
                        deep_merge(dst[k], v)
                    else:
                        dst[k] = v
            else:
                dicts.setdefault("__globals", {})[sec] = val

    dicts["__components"] = components
    return Resolved(root, order, variables, var_defs, nodes, tables, dicts, errors, warnings, unused)
