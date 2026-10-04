"""S13 -> S14 coordinate warp.

The S14 shares the S13's architecture (MacPherson/multilink, same engines, same hard-point
layout), so its chassis is the S13 coupe's under a smooth warp: overhangs and wheelbase are
stretched piecewise-linearly through the bumper faces and axles, and the car is 1.2 %
wider (the published front track 1465 -> 1480 mm).  Everything that is generated from S13
coordinates (unibody nodes, suspension hard points, interior, race hardware and their meshes)
goes through `warp` so physics and visuals stay consistent.
"""
from __future__ import annotations

import numpy as np

S13_Y = (-2.250, -1.240, 1.235, 2.255)    # front face, front axle, rear axle, rear face
S14_Y = (-2.255, -1.265, 1.260, 2.305)
KX = 1.012


def wy(y: float) -> float:
    ys, ts = S13_Y, S14_Y
    if y <= ys[0]:
        return ts[0] + (y - ys[0]) * (ts[1] - ts[0]) / (ys[1] - ys[0])
    if y >= ys[-1]:
        return ts[-1] + (y - ys[-1]) * (ts[-1] - ts[-2]) / (ys[-1] - ys[-2])
    return float(np.interp(y, ys, ts))


def warp(x: float, y: float, z: float):
    return (x * KX, wy(y), z)


def warp_points(co):
    """Vectorised warp of an (n, 3) array."""
    co = np.asarray(co, float).copy()
    co[:, 0] *= KX
    ys, ts = np.asarray(S13_Y), np.asarray(S14_Y)
    y = co[:, 1]
    out = np.interp(y, ys, ts)
    lo, hi = y < ys[0], y > ys[-1]
    out[lo] = ts[0] + (y[lo] - ys[0]) * (ts[1] - ts[0]) / (ys[1] - ys[0])
    out[hi] = ts[-1] + (y[hi] - ys[-1]) * (ts[-1] - ts[-2]) / (ys[-1] - ys[-2])
    co[:, 1] = out
    return co


def warp_object(ob):
    """Warp a Blender mesh object's vertices in place (object transform must be identity)."""
    me = ob.data
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    co = warp_points(co.reshape(n, 3)).reshape(-1)
    me.vertices.foreach_set("co", co)
    me.update()
