"""S14 hard points: the S13 points under the S13 -> S14 warp (tools/vehicle/s14/warp.py).

Same names as tools/vehicle/s13/dims.py so the shared generators (suspension, powertrain,
mechanical meshes, interior) take either module.
"""
from tools.vehicle.s13 import dims as D13
from . import body_spec as B
from .warp import KX, warp, wy

AXLE_F_Y, AXLE_R_Y, AXLE_Z = B.AXLE_F_Y, B.AXLE_R_Y, B.AXLE_Z
WHEELBASE = B.WHEELBASE
TRACK_F = round(D13.TRACK_F * KX, 4)
TRACK_R = round(D13.TRACK_R * KX, 4)

_POINTS = ["FH1", "FH2", "FH3", "FH5", "FH6", "FS1", "FX1", "FX2", "FU1", "FU2",
           "RH1", "RH2", "RH3", "RH4", "RH5", "RX1", "RX2", "RX3", "RX4", "RX5", "RS1",
           "SEAT_H_POINT", "EYE", "STEER_CENTER"]
for _n in _POINTS:
    globals()[_n] = tuple(round(v, 4) for v in warp(*getattr(D13, _n)))

RACK_Y = round(wy(D13.RACK_Y), 4)
RACK_Z = D13.RACK_Z
RACK_X = round(D13.RACK_X * KX, 4)
ENGINE_FRONT_Y = round(wy(D13.ENGINE_FRONT_Y), 4)
ENGINE_REAR_Y = round(wy(D13.ENGINE_REAR_Y), 4)
CRANK_Z = D13.CRANK_Z
TRANS_REAR_Y = round(wy(D13.TRANS_REAR_Y), 4)
DIFF_Y = round(wy(D13.DIFF_Y), 4)
DIFF_Z = D13.DIFF_Z
DRIVER_X = round(D13.DRIVER_X * KX, 4)

GAUGE_Y = round(wy(D13.GAUGE_Y), 4)
GAUGE_Z = D13.GAUGE_Z
GAUGE_W, GAUGE_H = D13.GAUGE_W, D13.GAUGE_H
GAUGE_TACH_DX = D13.GAUGE_TACH_DX
GAUGE_SMALL_DX = D13.GAUGE_SMALL_DX
GAUGE_SMALL_DZ = D13.GAUGE_SMALL_DZ
GAUGE_R_MAIN = D13.GAUGE_R_MAIN
GAUGE_R_SMALL = D13.GAUGE_R_SMALL
