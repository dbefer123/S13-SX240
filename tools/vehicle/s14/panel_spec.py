"""S14 panel outlines (left side, x>0; mirrored for the right side), traced from the
dimensioned S14 drawing.  Same view conventions as tools/vehicle/s13/panel_spec.py:
  side  -> (y, z) polygons extruded along x
  plan  -> (x, y) polygons extruded along z
  front -> (x, z) polygons extruded along y
"""
import numpy as np

from tools.model.shape import Guide
from . import body_spec as B

ARCH_F = (B.AXLE_F_Y, 0.305)
ARCH_R = (B.AXLE_R_Y, 0.305)
ARCH_RADIUS = 0.352

_BELT = Guide(B.Z_BELT)
_SILL = Guide(B.Z_SILL)


def belt_line(y0, y1, dz=0.004, n=16):
    return [(float(y), float(_BELT(float(y))) + dz) for y in np.linspace(y0, y1, n)]


def sill_line(y0, y1, dz=-0.006, n=14):
    return [(float(y), float(_SILL(float(y))) + dz) for y in np.linspace(y0, y1, n)]


# --- glass -------------------------------------------------------------------------
WINDSHIELD = [(-0.665, -0.772), (-0.40, -0.787), (0.0, -0.793), (0.40, -0.787), (0.665, -0.772),
              (0.548, -0.150), (0.0, -0.122), (-0.548, -0.150)]
WINDSHIELD_Z = (0.84, 1.45)
# frameless door glass: A-pillar -> roof rail -> slanted B-pillar
DOOR_GLASS = [(-0.640, 0.884), (-0.420, 1.035), (-0.160, 1.180), (0.150, 1.200), (0.420, 1.200), (0.500, 1.186),
              (0.452, 0.898)]
# black B-pillar applique between the door glass and the quarter window
B_PILLAR = [(0.468, 0.898), (0.516, 1.192), (0.612, 1.198), (0.566, 0.898)]
QUARTER_GLASS = [(0.580, 0.898), (0.626, 1.190), (0.760, 1.186), (0.860, 1.164), (0.975, 1.132), (1.215, 0.904),
                 (0.950, 0.896)]
SIDE_X = (0.35, 1.25)
REAR_WINDOW = [(-0.470, 0.975), (0.470, 0.975), (0.530, 1.20), (0.560, 1.45), (0.565, 1.60), (0.500, 1.652),
               (0.0, 1.664), (-0.500, 1.652), (-0.565, 1.60), (-0.560, 1.45), (-0.530, 1.20)]
REAR_WINDOW_Z = (0.90, 1.40)

# --- doors ---------------------------------------------------------------------------
DOOR = ([(-0.655, 0.195), (-0.680, 0.40), (-0.695, 0.62), (-0.703, 0.840)] + belt_line(-0.703, 0.535)
        + [(0.548, 0.70), (0.540, 0.45), (0.525, 0.195)])

# --- front end ---------------------------------------------------------------------
HOOD = [(-0.692, -0.880), (0.692, -0.880), (0.693, -1.55), (0.690, -1.90), (0.684, -2.05), (0.660, -2.40),
        (-0.660, -2.40), (-0.684, -2.05), (-0.690, -1.90), (-0.693, -1.55)]
HOOD_Z = (0.652, 1.10)
# grille / header panel between the headlamps (front view)
GRILLE = [(-0.255, 0.590), (0.255, 0.590), (0.268, 0.650), (-0.268, 0.650)]
GRILLE_Y = (-2.40, -2.00)
HEADLIGHT_Y = (-2.40, -1.86)
HEADLIGHTS = {  # front view (x, z), left lamp; the outer end is shared so one fender fits both
    "zenki": [(0.290, 0.612), (0.400, 0.594), (0.600, 0.591), (0.740, 0.603), (0.786, 0.630), (0.778, 0.680),
              (0.722, 0.704), (0.560, 0.701), (0.410, 0.686), (0.318, 0.658)],
    "kouki": [(0.262, 0.590), (0.400, 0.598), (0.600, 0.594), (0.740, 0.603), (0.786, 0.630), (0.778, 0.680),
              (0.722, 0.704), (0.580, 0.700), (0.430, 0.672), (0.300, 0.622)],
}
BUMPER_F = [(-2.40, 0.33), (-2.40, 0.585), (-2.15, 0.582), (-2.00, 0.562), (-1.80, 0.505), (-1.68, 0.468),
            (-1.62, 0.410), (-1.58, 0.17)] + sill_line(-1.58, -2.30)[1:]
BUMPER_X = (-1.25, 1.25)
FENDER = [(-2.30, 0.0), (-2.30, 0.98), (-0.84, 0.98), (-0.718, 0.880), (-0.705, 0.84), (-0.695, 0.62),
          (-0.680, 0.40), (-0.662, 0.197), (-0.94, 0.197), (-1.24, 0.0)]
FENDER_X = (0.62, 1.25)

# --- rear end ------------------------------------------------------------------------
BUMPER_R = [(2.40, 0.40), (2.40, 0.622), (2.18, 0.622), (2.02, 0.612), (1.86, 0.585), (1.72, 0.540), (1.66, 0.470),
            (1.60, 0.17)] + sill_line(1.60, 2.30)[1:]
# trunk lid: deck + the rear face between the outer lamps, down to the lamp bottoms (front view, along y)
TRUNK = [(-0.600, 0.742), (0.600, 0.742), (0.600, 0.870), (0.680, 0.900), (0.680, 1.30), (-0.680, 1.30),
         (-0.680, 0.900), (-0.600, 0.870)]
TRUNK_Y = (1.700, 2.40)
# tail lamps (front view, left side; mirrored): outer units on the quarters, middle + inner units on the trunk lid
TAIL_OUTER = [(0.628, 0.752), (0.790, 0.752), (0.796, 0.862), (0.628, 0.866)]
TAIL_MIDDLE = [(0.300, 0.756), (0.588, 0.756), (0.588, 0.860), (0.300, 0.860)]
TAIL_INNER = [(0.185, 0.756), (0.285, 0.756), (0.285, 0.860), (0.185, 0.860)]
TAIL_Y = (1.95, 2.40)
# lamp colour zones per facelift: (lamp, x0, x1, z0, z1, material key) on the left lamp
TAIL_ZONES = {
    "zenki": [("outer", 0.60, 0.82, 0.805, 0.87, "signal"), ("outer", 0.60, 0.82, 0.74, 0.805, "tail"),
              ("middle", 0.38, 0.60, 0.74, 0.87, "tail"), ("middle", 0.29, 0.38, 0.74, 0.87, "reverse"),
              ("inner", 0.17, 0.29, 0.74, 0.87, "tail")],
    "kouki": [("outer", 0.60, 0.82, 0.74, 0.87, "tail"),
              ("middle", 0.47, 0.60, 0.74, 0.87, "tail"), ("middle", 0.29, 0.47, 0.815, 0.87, "signal"),
              ("middle", 0.29, 0.47, 0.74, 0.815, "reverse"), ("inner", 0.17, 0.29, 0.74, 0.87, "tail")],
}
