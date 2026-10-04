"""Pretty writer that emits JBeam in the layout used by vanilla BeamNG files.

Generators build parts as plain Python data:

    {"partName": {"information": {...}, "slotType": "x", "nodes": [header, {...}, row, ...], ...}}

Table sections (lists) are written one row per line. A list item that is a
string starting with ``//`` is written as a comment line, which makes the
generated files readable for people tweaking them by hand.
"""
from __future__ import annotations

import json
import math

INDENT = "    "


def fmt_num(v, places: int = 6) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if math.isinf(v):
            return '"FLT_MAX"'
        if v == int(v) and abs(v) < 1e15:
            # keep a decimal point for readability of physical values
            return f"{int(v)}" if abs(v) >= 1000 else f"{v:.1f}"
        s = f"{v:.{places}f}".rstrip("0").rstrip(".")
        if s in ("-0", ""):
            s = "0"
        return s
    raise TypeError(v)


def fmt_inline(v, places: int = 6) -> str:
    if v is None:
        return "null"
    if isinstance(v, (bool, int, float)):
        return fmt_num(v, places)
    if isinstance(v, str):
        return json.dumps(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(fmt_inline(x, places) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{json.dumps(k)}:{fmt_inline(x, places)}" for k, x in v.items()) + "}"
    raise TypeError(type(v))


def _is_table(v) -> bool:
    return isinstance(v, list) and len(v) > 0 and any(isinstance(r, (list, dict, str)) for r in v)


def _write_value(key, v, depth: int, out: list, places: int):
    pad = INDENT * depth
    k = json.dumps(key) + ":" if key is not None else ""
    if isinstance(v, dict) and v and (len(fmt_inline(v)) > 100 or any(isinstance(x, (dict, list)) and len(fmt_inline(x)) > 60 for x in v.values())):
        out.append(f"{pad}{k}{{")
        for kk, vv in v.items():
            _write_value(kk, vv, depth + 1, out, places)
        out.append(f"{pad}}},")
    elif _is_table(v) and (len(v) > 3 or len(fmt_inline(v)) > 100):
        out.append(f"{pad}{k}[")
        for row in v:
            if isinstance(row, str) and row.startswith("//"):
                out.append(f"{pad}{INDENT}{row}")
            elif isinstance(row, dict) and len(fmt_inline(row)) > 160:
                _write_value(None, row, depth + 1, out, places)
            else:
                out.append(f"{pad}{INDENT}{fmt_inline(row, places)},")
        out.append(f"{pad}],")
    else:
        out.append(f"{pad}{k}{fmt_inline(v, places)},")


def dumps(parts: dict, places: int = 6, header_comment: str | None = None) -> str:
    out = []
    if header_comment:
        for line in header_comment.strip().splitlines():
            out.append("// " + line)
    out.append("{")
    for name, part in parts.items():
        out.append(f"{json.dumps(name)}: {{")
        for k, v in part.items():
            _write_value(k, v, 1, out, places)
        out.append("},")
    out.append("}")
    return "\n".join(out) + "\n"


def dump(parts: dict, path: str, **kw):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(dumps(parts, **kw))


def dumps_json(obj, indent: int = 2) -> str:
    """Strict JSON (for .pc, info.json and materials.json)."""
    return json.dumps(obj, indent=indent, ensure_ascii=False) + "\n"
