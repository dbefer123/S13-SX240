"""S14 retarget and configuration checks (no bpy needed)."""
from __future__ import annotations

import numpy as np

from tools.vehicle.s13 import dims as D13
from tools.vehicle.s14 import dims as D14
from tools.vehicle.s14.warp import KX, S13_Y, S14_Y, warp, warp_points, wy


def test_warp_maps_anchors():
    for a, b in zip(S13_Y, S14_Y):
        assert abs(wy(a) - b) < 1e-9
    assert abs(warp(1.0, 0.0, 0.5)[0] - KX) < 1e-12


def test_warp_preserves_orientation():
    """Strictly increasing in y (and x scaled by a positive factor), so warped meshes keep their winding."""
    ys = np.linspace(-2.6, 2.6, 2001)
    w = np.array([wy(float(y)) for y in ys])
    assert np.all(np.diff(w) > 0)
    assert KX > 0


def test_vectorised_warp_matches_scalar():
    rng = np.random.default_rng(0)
    pts = rng.uniform([-0.9, -2.6, 0.0], [0.9, 2.6, 1.4], (500, 3))
    a = warp_points(pts)
    b = np.array([warp(*p) for p in pts])
    assert np.allclose(a, b)


def test_s14_wheelbase_and_hard_points():
    assert abs((D14.AXLE_R_Y - D14.AXLE_F_Y) - 2.525) < 0.002
    assert abs(D14.GAUGE_Y - wy(D13.GAUGE_Y)) < 1e-3


def test_s14_configs_resolve_to_s14_parts():
    from tools.vehicle.s14 import configs as C14
    cfgs = C14.configs()
    assert len(cfgs) == 9
    for c in cfgs:
        for slot, part in c.parts.items():
            assert not slot.startswith("s13_") and not str(part).startswith("s13_"), (c.key if hasattr(c, "key") else c, slot)
