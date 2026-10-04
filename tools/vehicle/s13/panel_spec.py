"""S13 hatch panel outlines (left side, x>0; mirrored for the right side).

Views (see tools/model/panels.py):
  side  -> (y, z) polygons extruded along x
  plan  -> (x, y) polygons extruded along z
These outlines are shared by the mesh builder (panel cuts) and by the JBeam
generator (which panel nodes/flexbody groups belong to).
"""
ARCH_F = (-1.240, 0.305)
ARCH_R = (1.235, 0.305)
ARCH_RADIUS = 0.348

WINDSHIELD = [(-0.648, -0.772), (-0.40, -0.786), (0.0, -0.792), (0.40, -0.786), (0.648, -0.772),
              (0.515, -0.168), (0.0, -0.150), (-0.515, -0.168)]
WINDSHIELD_Z = (0.84, 1.45)

DOOR = [(-0.618, 0.200), (-0.640, 0.40), (-0.664, 0.62), (-0.673, 0.84), (-0.660, 0.868), (-0.140, 1.208),
        (0.530, 1.222), (0.582, 1.200), (0.604, 0.880), (0.590, 0.600), (0.570, 0.200)]
DOOR_GLASS = [(-0.598, 0.880), (-0.160, 1.168), (0.495, 1.182), (0.548, 1.150), (0.556, 0.896)]
QUARTER_GLASS = [(0.705, 0.905), (0.705, 1.168), (1.10, 1.112), (1.45, 1.036), (1.70, 0.978),
                 (1.55, 0.955), (1.20, 0.935)]
SIDE_X = (0.35, 1.25)

HATCH = [(-0.494, 0.818), (0.494, 0.818), (0.503, 1.20), (0.515, 1.60), (0.560, 1.84), (0.660, 1.96),
         (0.700, 2.10), (0.705, 2.32), (-0.705, 2.32), (-0.700, 2.10), (-0.660, 1.96), (-0.560, 1.84),
         (-0.515, 1.60), (-0.503, 1.20)]
HATCH_Z = (0.905, 1.50)
HATCH_GLASS = [(-0.462, 0.868), (0.462, 0.868), (0.470, 1.40), (0.462, 1.70), (0.400, 1.848), (0.0, 1.872),
               (-0.400, 1.848), (-0.462, 1.70), (-0.470, 1.40)]
HATCH_GLASS_Z = (0.95, 1.50)

HOOD = [(-0.355, -2.30), (0.355, -2.30), (0.365, -1.848), (0.686, -1.848), (0.705, -1.55), (0.712, -1.10),
        (0.712, -0.866), (-0.712, -0.866), (-0.712, -1.10), (-0.705, -1.55), (-0.686, -1.848), (-0.365, -1.848)]
HOOD_Z = (0.555, 1.10)
POPUP = [(0.374, -2.125), (0.672, -2.125), (0.672, -1.857), (0.374, -1.857)]
POPUP_Z = (0.575, 1.10)

def _sill_edge(y0, y1, n=14):
    """Bumper bottom edge just above the rocker line (keeps the floor pan out of the bumper covers; the floor is the
    separate underbody mesh)."""
    from .body_spec import Z_SILL
    from tools.model.shape import Guide
    g = Guide(Z_SILL)
    import numpy as _np
    return [(float(y), float(g(float(y))) - 0.006) for y in _np.linspace(y0, y1, n)]


BUMPER_F = [(-2.40, 0.23), (-2.40, 0.492), (-2.15, 0.490), (-1.90, 0.483), (-1.70, 0.476), (-1.62, 0.470),
            (-1.55, 0.40), (-1.50, 0.16)] + _sill_edge(-1.50, -2.30)[1:]
BUMPER_R = [(2.40, 0.268), (2.40, 0.535), (2.05, 0.535), (1.85, 0.525), (1.70, 0.500), (1.62, 0.430),
            (1.555, 0.16)] + _sill_edge(1.555, 2.30)[1:][::-1][::-1]
BUMPER_X = (-1.25, 1.25)

FENDER = [(-2.30, 0.0), (-2.30, 0.95), (-0.80, 0.95), (-0.69, 0.88), (-0.673, 0.84), (-0.664, 0.62),
          (-0.640, 0.40), (-0.622, 0.200), (-0.92, 0.200), (-1.20, 0.0)]
FENDER_X = (0.62, 1.25)

# tail light bar on the rear face (front view: x, z), cut through y in [2.15, 2.40]
TAILLIGHT = [(-0.735, 0.640), (0.735, 0.640), (0.745, 0.860), (-0.745, 0.860)]
TAIL_Y = (2.17, 2.40)

# ---------------------------------------------------------------------------
# coupe / convertible (rear half only; everything ahead of the B-pillar is shared with the hatch)
# ---------------------------------------------------------------------------
# small opera-style quarter window behind the door, rear edge raked parallel to the C-pillar
COUPE_QUARTER_GLASS = [(0.705, 0.918), (0.705, 1.172), (0.80, 1.180), (0.875, 1.158), (1.075, 0.932), (0.95, 0.920)]
# rear window on the top surface between the C-pillars (plan view)
REAR_WINDOW = [(-0.470, 0.935), (0.470, 0.935), (0.482, 1.20), (0.478, 1.45), (0.452, 1.555), (0.360, 1.592),
               (0.0, 1.600), (-0.360, 1.592), (-0.452, 1.555), (-0.478, 1.45), (-0.482, 1.20)]
REAR_WINDOW_Z = (0.90, 1.40)
# trunk lid: deck + the rear face between the tail lamps (front view T-shape, extruded along y)
TRUNK_Y = (1.648, 2.40)
TRUNK_STEM_X = 0.296
TRUNK_DECK_Z = 0.818
TRUNK_STEM_Z = 0.648
TRUNK = [(-0.708, TRUNK_DECK_Z), (-TRUNK_STEM_X, TRUNK_DECK_Z), (-TRUNK_STEM_X, TRUNK_STEM_Z),
         (TRUNK_STEM_X, TRUNK_STEM_Z), (TRUNK_STEM_X, TRUNK_DECK_Z), (0.708, TRUNK_DECK_Z), (0.708, 1.20),
         (-0.708, 1.20)]
# coupe tail lamps (front view, left side; mirrored): outer wrap-around units on the rear panel
COUPE_TAIL = [(0.304, 0.636), (0.770, 0.636), (0.776, 0.802), (0.304, 0.802)]
COUPE_TAIL_Y = (2.12, 2.40)
COUPE_TAIL_ZONES = [  # (x0, x1, z0, z1, material) left lamp; the right lamp mirrors x and swaps the signal side
    (0.30, 0.80, 0.63, 0.712, "s13_taillight"),
    (0.47, 0.80, 0.712, 0.81, "signal"),
    (0.30, 0.47, 0.712, 0.81, "s13_reverselight"),
]

# convertible: everything above the beltline from just behind the windshield header to the deck is the top
CONV_TOP_Y = (-0.085, 1.600)
CONV_QUARTER_GLASS = [(0.640, 0.925), (0.640, 1.168), (0.80, 1.176), (0.860, 1.160), (1.045, 0.940), (0.93, 0.928)]
CONV_REAR_WINDOW = [(-0.420, 1.110), (0.420, 1.110), (0.430, 1.40), (0.400, 1.505), (0.300, 1.535), (0.0, 1.540),
                    (-0.300, 1.535), (-0.400, 1.505), (-0.430, 1.40)]
CONV_TONNEAU_Y = (1.18, 1.600)
