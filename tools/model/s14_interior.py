"""S14 dash (requires bpy).

Laid out in S13 coordinates like the rest of the shared interior and moved onto the S14 with the
S13 -> S14 warp (tools/vehicle/s14/warp.py), so it lines up with the warped gauge needles, column and
seats.  Mesh names use the s13_ prefix; build_s14.s14ify renames them.

The S14 dash differs from the S13's: a rounder, lower top with a softer nose, a hooded cluster that
blends into it, a centre stack carrying the two centre vents, hazard switch, radio and three-dial climate
control, round outboard vents, defroster and speaker grilles on the top, and a glovebox with a handle.
"""
from __future__ import annotations

import math

from . import s13_parts as SP
from .prims import MeshBuilder
from tools.vehicle.s13 import dims as D

M_INT, M_INT2, M_LIGHT = "s13_interior_plastic", "s13_interior_trim", "s13_interior_plastic_light"


def _wall(x):
    return 0.70 - 0.03 * math.cos(x * 2.0)


def normal(x):
    """Passenger / centre section: rounded top, a large-radius nose and a face receding toward the knees."""
    return [(-0.80, 0.86), (-0.72, 0.878), (-0.64, 0.893), (-0.57, 0.902), (-0.515, 0.902), (-0.485, 0.893),
            (-0.463, 0.877), (-0.449, 0.856), (-0.441, 0.832), (-0.438, 0.805), (-0.440, 0.775), (-0.446, 0.745),
            (-0.452, _wall(x)), (-0.50, 0.615), (-0.62, 0.565), (-0.80, 0.55)]


def cluster(x):
    """Binnacle around the column: hood rising out of the top, gauge recess, lower bezel."""
    gy, gz, gh = D.GAUGE_Y, D.GAUGE_Z, D.GAUGE_H
    return [(-0.80, 0.86), (-0.72, 0.886), (-0.64, 0.922), (-0.57, 0.956), (-0.505, 0.987), (-0.465, 1.004),
            (-0.446, 1.006), (-0.437, 0.999), (-0.443, 0.994), (gy - 0.002, gz + gh / 2 + 0.006),
            (gy - 0.002, gz - gh / 2 - 0.006), (-0.455, 0.842), (-0.452, _wall(x)), (-0.50, 0.615), (-0.62, 0.565),
            (-0.80, 0.55)]


def _face_y(prof, z):
    """y of the dash face (the descending part of a profile) at height z."""
    pts = prof[7:14]                 # (index 0 is the lip under the cowl added by dash_loft)
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if min(z0, z1) <= z <= max(z0, z1) and abs(z1 - z0) > 1e-9:
            return y0 + (y1 - y0) * (z - z0) / (z1 - z0)
    return pts[-1][0]


def _vent_round(mb, c, r):
    """Round adjustable vent facing the cabin: bezel ring, dark barrel and three vanes."""
    x, y, z = c
    mb.cylinder((x, y - 0.018, z), (x, y + 0.004, z), r + 0.008, M_LIGHT, segs=28)
    mb.cylinder((x, y - 0.02, z), (x, y + 0.006, z), r, "s1x_dark", segs=24)
    for k in (-1, 0, 1):
        mb.box((x, y + 0.004, z + k * r * 0.45), (2 * r * math.sqrt(1 - (0.45 * k) ** 2) * 0.92, 0.004, 0.004), M_LIGHT)


def _vent_rect(mb, c, w, h):
    x, y, z = c
    mb.rbox((x, y - 0.004, z), (w + 0.012, 0.014, h + 0.012), 0.008, M_LIGHT)
    mb.rbox((x, y + 0.002, z), (w, 0.012, h), 0.006, "s1x_dark")
    for k in range(4):
        mb.box((x, y + 0.008, z - h * 0.33 + k * h * 0.22), (w - 0.008, 0.004, 0.003), M_LIGHT)
    mb.box((x, y + 0.010, z), (0.004, 0.003, h - 0.008), M_LIGHT)          # vertical fin / thumb wheel


def dash_s14():
    mb = MeshBuilder("s13_dash")
    prof = SP.dash_loft(mb, normal, cluster, M_INT, ramp=0.06)
    # --- centre stack: protrudes from the face and runs down to the console ----------------------------------
    sy = -0.428                                      # stack face plane
    mb.rbox((0.0, sy - 0.045, 0.6325), (0.30, 0.09, 0.385), 0.03, M_INT)
    mb.rbox((0.0, sy, 0.69), (0.26, 0.008, 0.25), 0.01, M_INT2)          # face plate
    for s in (1, -1):                                 # twin centre vents with the hazard switch between
        _vent_rect(mb, (s * 0.068, sy, 0.772), 0.105, 0.048)
    mb.rbox((0.0, sy + 0.006, 0.772), (0.018, 0.01, 0.018), 0.004, "s1x_fire_red")
    SP.textured_quad(mb, (0.0, sy + 0.0055, 0.698), 0.20, 0.058, "s13_radio")
    SP.textured_quad(mb, (0.0, sy + 0.0055, 0.612), 0.22, 0.070, "s13_hvac")
    for kx in (0.07, 0.0, -0.07):                    # fan / temperature / mode dials over the printed scales
        mb.cylinder((kx, sy + 0.005, 0.612), (kx, sy + 0.018, 0.612), 0.017, "s1x_dark", segs=20)
        mb.box((kx, sy + 0.0185, 0.612 + 0.009), (0.003, 0.001, 0.010), M_LIGHT)
    mb.rbox((0.0, sy, 0.535), (0.16, 0.012, 0.035), 0.006, "s1x_dark")   # coin tray
    # --- outboard round vents ---------------------------------------------------------------------------------
    for x in (0.63, -0.63):
        p = prof(x)
        y = _face_y(p, 0.79)
        _vent_round(mb, (x, y + 0.004, 0.79), 0.036)
    # --- glovebox lid with handle ---------------------------------------------------------------------------
    gy = _face_y(prof(-0.38), 0.735)
    mb.rbox((-0.38, gy + 0.003, 0.735), (0.32, 0.008, 0.09), 0.014, M_INT2)
    mb.rbox((-0.38, gy + 0.008, 0.772), (0.08, 0.008, 0.014), 0.004, "s1x_dark")
    # --- defroster slot and speaker grilles on the top --------------------------------------------------------
    def surf(x, y):
        pts = prof(x)[:6]
        for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
            if y0 <= y <= y1:
                return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
        return pts[-1][1]
    for x0, x1 in ((-0.62, 0.03),):
        xm, w = (x0 + x1) / 2, x1 - x0
        mb.box((xm, -0.70, surf(xm, -0.70) + 0.0015), (w, 0.030, 0.003), "s1x_dark")
    for x in (-0.60, 0.60):
        z = min(surf(x, -0.665), SP.COWL_TOP(x, -0.665) - 0.016)
        mb.cylinder((x, -0.665, z - 0.002), (x, -0.665, z + 0.0018), 0.034, "s1x_dark", segs=24)
    SP.column_shroud(mb)
    return mb


def gauges_s14():
    """S14 cluster face: as the S13's, with a chrome-ringed bezel."""
    mb = SP.gauges()
    cx = D.STEER_CENTER[0]
    gy, gz, w, h = D.GAUGE_Y, D.GAUGE_Z, D.GAUGE_W, D.GAUGE_H
    mb.rbox((cx, gy + 0.004, gz + h / 2 + 0.003), (w + 0.01, 0.006, 0.004), 0.0015, "s1x_chrome")
    return mb


def all_meshes():
    return [dash_s14(), gauges_s14()]

