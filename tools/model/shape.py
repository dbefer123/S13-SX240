"""Parametric car-body loft (pure numpy, no Blender dependency).

A body is described by *guide curves*: functions of the longitudinal coordinate
``y`` (BeamNG frame: +X left, +Y rear, +Z up) traced from orthographic
blueprints and scaled to published dimensions.

Half cross-section at station y, from the underbody centreline to the roof
centreline (right side, x>0 here; mirrored later):

    under   : flat floor from the centreline to the rocker corner
    corner  : radius r_floor turning up into the rocker
    lower   : rocker (w_max*w_sill_k, z_sill) bulging out to the shoulder crease (w_max, z_sh)
    upper   : crease -> start of the top edge radius, leaning inward by `lean`
    edge    : radius r_top rolling the side over into the top surface (ends at z_belt)
    ledge   : short flat from the edge to the glass base (w_belt) - window sill / fender top
    glass   : glass base -> roof rail (w_rail, z_rail); inside the greenhouse only.
              Outside the greenhouse the "rail" point lies on the hood/deck crown.
    top     : rail -> centreline (crowned, z_top at x=0)

Every segment has a fixed number of samples, so feature lines stay on grid rows.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.interpolate import PchipInterpolator

SEG_COUNTS = {"under": 8, "corner": 5, "lower": 12, "upper": 8, "edge": 6, "ledge": 3, "glass": 12, "top": 18}
SEG_ORDER = ["under", "corner", "lower", "upper", "edge", "ledge", "glass", "top"]


class Guide:
    """Monotone cubic interpolation through (y, value) control points; clamped outside."""

    def __init__(self, pts):
        pts = sorted(pts)
        self.y = np.array([p[0] for p in pts], float)
        self.v = np.array([p[1] for p in pts], float)
        self.f = PchipInterpolator(self.y, self.v, extrapolate=False) if len(pts) > 1 else None

    def __call__(self, y):
        if self.f is None:
            return np.full_like(np.asarray(y, float), self.v[0])
        y = np.asarray(y, float)
        return self.f(np.clip(y, self.y[0], self.y[-1]))


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


@dataclass
class BodySpec:
    name: str
    y_front: float
    y_rear: float
    guides: dict
    gh_start: float           # greenhouse (windshield base)
    gh_end: float             # greenhouse end (hatch glass bottom / rear window base)
    gh_blend: float = 0.06    # blend length at the greenhouse ends
    r_floor: float = 0.05
    top_power: float = 2.2
    glass_bulge: float = 0.010
    lower_power: float = 0.55
    cap_front: float = 0.02   # edge radius of the flat front face (bumper face)
    cap_rear: float = 0.02
    cap_steps: int = 6
    extra: dict = field(default_factory=dict)

    def g(self, name, y, default=None):
        if name not in self.guides:
            return default
        return float(self.guides[name](y))

    def keypoints(self, y: float):
        g = self.g
        z_bot, z_top = g("z_bot", y), g("z_top", y)
        z_sill = float(np.clip(g("z_sill", y), z_bot, z_top))
        z_sh = float(np.clip(g("z_sh", y), z_sill + 1e-3, z_top))
        z_belt = float(np.clip(g("z_belt", y), z_sh + 1e-3, z_top))
        w_max = g("w_max", y)
        w_sill = min(g("w_sill_k", y, 0.96) * w_max, w_max)
        lean = g("lean", y, 0.015)
        r_top = min(g("r_top", y, 0.03), max(z_belt - z_sh, 1e-3) * 0.9)
        x_edge = w_max - lean - r_top          # where the top-edge radius ends (horizontal tangent)
        w_belt = min(g("w_belt", y, x_edge), x_edge - 0.002)
        # crown point used as "rail" outside the greenhouse
        w_rail_out = 0.92 * w_belt
        z_rail_out = z_top - (z_top - z_belt) * 0.92 ** self.top_power
        gh = smoothstep(self.gh_start - self.gh_blend, self.gh_start, y) * \
            (1 - smoothstep(self.gh_end, self.gh_end + self.gh_blend, y))
        if gh > 0:
            w_rail_in = min(g("w_rail", y), w_belt)
            z_rail_in = float(np.clip(g("z_rail", y), z_belt, z_top))
        else:
            w_rail_in, z_rail_in = w_rail_out, z_rail_out
        w_rail = w_rail_out + (w_rail_in - w_rail_out) * gh
        z_rail = z_rail_out + (z_rail_in - z_rail_out) * gh
        z_rail = min(z_rail, z_top - 1e-4)
        return dict(z_bot=z_bot, z_top=z_top, z_sill=z_sill, z_sh=z_sh, z_belt=z_belt, z_rail=z_rail,
                    w_max=w_max, w_sill=w_sill, w_belt=w_belt, w_rail=w_rail, lean=lean, r_top=r_top,
                    x_edge=x_edge, gh=gh)

    def section(self, y: float, counts=SEG_COUNTS):
        k = self.keypoints(y)
        pts, tags = [], []

        def add(seg, xs, zs):
            for i, (x, z) in enumerate(zip(xs, zs)):
                if i == 0 and pts:
                    continue
                pts.append((float(x), float(z))); tags.append(seg)

        # under + floor corner
        r = min(self.r_floor, k["w_sill"] * 0.5, max(k["z_sill"] - k["z_bot"], 0.0) + 0.02)
        x_under_end = max(k["w_sill"] - r, 0.0)
        u = np.linspace(0, 1, counts["under"] + 1)
        add("under", x_under_end * u, np.full_like(u, k["z_bot"]))
        a = np.linspace(0, np.pi / 2, counts["corner"] + 1)
        zc = k["z_bot"] + min(r, max(k["z_sill"] - k["z_bot"], 1e-4))
        add("corner", x_under_end + r * np.sin(a), zc - (zc - k["z_bot"]) * np.cos(a))
        x0, z0 = pts[-1]
        z0 = max(z0, k["z_bot"])
        # lower body side up to the crease
        u = np.linspace(0, 1, counts["lower"] + 1)
        xs = x0 + (k["w_max"] - x0) * np.sin(np.pi / 2 * u) ** self.lower_power
        zs = z0 + (k["z_sh"] - z0) * u
        add("lower", xs, zs)
        # upper side: lean inward up to where the edge radius starts
        z_r0 = k["z_belt"] - k["r_top"]
        u = np.linspace(0, 1, counts["upper"] + 1)
        xs = k["w_max"] - k["lean"] * u ** 1.4
        zs = k["z_sh"] + (max(z_r0, k["z_sh"]) - k["z_sh"]) * u
        add("upper", xs, zs)
        # top edge radius (quarter circle from vertical to horizontal)
        a = np.linspace(0, np.pi / 2, counts["edge"] + 1)
        cx, cz = k["w_max"] - k["lean"] - k["r_top"], max(z_r0, k["z_sh"])
        add("edge", cx + k["r_top"] * np.cos(a), cz + k["r_top"] * np.sin(a))
        xe, ze = pts[-1]
        # ledge to the glass base
        u = np.linspace(0, 1, counts["ledge"] + 1)
        add("ledge", xe + (k["w_belt"] - xe) * u, ze + (k["z_belt"] - ze) * u)
        # glass / pillar
        u = np.linspace(0, 1, counts["glass"] + 1)
        dx, dz = k["w_rail"] - k["w_belt"], k["z_rail"] - k["z_belt"]
        L = np.hypot(dx, dz)
        bul = self.glass_bulge * min(1.0, L / 0.2) * k["gh"]
        nx, nz = (dz / L, -dx / L) if L > 1e-6 else (0.0, 0.0)
        add("glass", k["w_belt"] + dx * u + nx * bul * np.sin(np.pi * u),
            k["z_belt"] + dz * u + nz * bul * np.sin(np.pi * u))
        # crowned top to the centreline
        u = np.linspace(0, 1, counts["top"] + 1)
        add("top", k["w_rail"] * (1 - u), k["z_top"] - (k["z_top"] - k["z_rail"]) * (1 - u) ** self.top_power)
        return np.array(pts), tags

    def stations(self, n_mid=120, n_end=24, ends=0.30, extra=()):
        a = np.linspace(0, np.pi / 2, n_end, endpoint=False)
        front = self.y_front + ends * (1 - np.cos(a))
        rear = self.y_rear - ends * (1 - np.cos(a))
        mid = np.linspace(self.y_front + ends, self.y_rear - ends, n_mid)
        ys = np.concatenate([front, mid, rear, [self.y_rear], list(extra)])
        ys = np.unique(np.round(ys, 5))
        return ys

    def _cap_rows(self, y_face, sign, r):
        """Rows closing a flat end face: the face section shrinks toward the
        centreline while moving outward by r*sin(theta) -> rounded edge of radius r."""
        p, tags = self.section(float(y_face))
        k = self.keypoints(float(y_face))
        zc = 0.5 * (k["z_bot"] + k["z_top"])
        rows, ys = [], []
        n = self.cap_steps
        for i in range(1, n + 1):
            th = (np.pi / 2) * i / n
            # first shrink by the edge radius (rounded rim), then collapse the flat face
            ring = r * (1 - np.cos(th))
            q = p.copy()
            # inset every point toward the face centre by `ring` (approximate offset)
            cx = np.zeros(len(q)); cz = np.full(len(q), zc)
            d = np.hypot(q[:, 0] - cx, q[:, 1] - cz) + 1e-9
            f = np.clip(1 - ring / d, 0, 1)
            q[:, 0] = cx + (q[:, 0] - cx) * f
            q[:, 1] = cz + (q[:, 1] - cz) * f
            rows.append(q); ys.append(y_face + sign * r * np.sin(th))
        # flat face: shrink to the centre in a few more rows
        last = rows[-1]
        for i in range(1, 5):
            f = 1 - i / 4
            q = last.copy()
            q[:, 0] = last[:, 0] * f
            q[:, 1] = zc + (last[:, 1] - zc) * f
            rows.append(q); ys.append(ys[-1] + sign * 0.002 * (1 - f))
        return rows, ys, tags

    def grid(self, ys=None, caps=True):
        """(Y, X, Z, tags) arrays shaped (n_stations, n_section); x>=0 side."""
        ys = self.stations() if ys is None else ys
        rows, tags, yy = [], None, []
        for y in ys:
            p, tags = self.section(float(y))
            rows.append(p); yy.append(float(y))
        if caps:
            fr, fy, _ = self._cap_rows(ys[0], -1, self.cap_front)
            rr, ry, _ = self._cap_rows(ys[-1], +1, self.cap_rear)
            rows = fr[::-1] + rows + rr
            yy = fy[::-1] + yy + ry
        P = np.array(rows)
        X, Z = P[:, :, 0], P[:, :, 1]
        Y = np.repeat(np.asarray(yy)[:, None], X.shape[1], axis=1)
        return Y, X, Z, tags

    def surface_point(self, y, seg, u):
        """Point on the section at segment `seg`, fraction u in [0,1] (x>=0 side)."""
        p, tags = self.section(float(y))
        idx = [i for i, t in enumerate(tags) if t == seg]
        if not idx:
            raise KeyError(seg)
        i0 = max(idx[0] - 1, 0)
        seg_pts = p[[i0] + idx]
        s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(seg_pts, axis=0), axis=1))])
        t = u * s[-1]
        x = np.interp(t, s, seg_pts[:, 0]); z = np.interp(t, s, seg_pts[:, 1])
        return x, z
