"""Pop-up headlamp pod geometry shared by the mesh builder and the JBeam (pure math).

The pod is defined raised (lens vertical, lid on top, hinge at the rear) and
rotated closed about the hinge axis by POPUP_ANGLE.  All points are for the
left side (x > 0); mirror x for the right side.
"""
from __future__ import annotations

import math

from tools.model.shape import top_z
from . import body_spec as B

SPEC = B.hatch_spec()
POPUP_ANGLE = 45.0          # degrees of rotation when raised
X0, X1 = 0.395, 0.652       # pod inner/outer x
HINGE_Y = -1.857
FRONT_Y = -2.105            # lid front edge (closed)
LENS_H = 0.115


def hinge():
    xm = (X0 + X1) / 2
    hz = min(top_z(SPEC, HINGE_Y, x) for x in (X0, xm, X1)) - 0.012
    return HINGE_Y, hz


def closed(y, z, th=None):
    """Map a raised-pose (y, z) point to the closed pose."""
    th = math.radians(POPUP_ANGLE) if th is None else th
    hy, hz = hinge()
    fwd, up = -(y - hy), z - hz
    c, s = math.cos(th), math.sin(th)
    fwd2, up2 = fwd * c + up * s, -fwd * s + up * c
    return hy - fwd2, hz + up2


def raised_profile():
    """Side profile of the pod in the raised pose: [(y, z)] front-top, front-bottom, rear-bottom, hinge."""
    hy, hz = hinge()
    xm = (X0 + X1) / 2
    fz = min(top_z(SPEC, FRONT_Y, x) for x in (X0, xm, X1 + 0.02)) - 0.022
    L = math.hypot(FRONT_Y - hy, fz - hz)
    a_closed = math.atan2(fz - hz, -(FRONT_Y - hy))
    a_up = a_closed + math.radians(POPUP_ANGLE)
    Fy, Fz = hy - L * math.cos(a_up), hz + L * math.sin(a_up)
    return [(Fy, Fz), (Fy, Fz - LENS_H), (hy - 0.03, Fz - LENS_H), (hy, hz)]


def lens_center_closed():
    """(x, y, z) of the lens centre in the closed (spawn) pose, left side."""
    prof = raised_profile()
    (Fy, Fz) = prof[0]
    y, z = closed(Fy - 0.006, Fz - LENS_H / 2)
    return (X0 + X1) / 2, y, z
