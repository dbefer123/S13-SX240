"""Shared S13 hard points (BeamNG frame: +X left, +Y rear, +Z up; metres).

Node names ending in 'l' are on the left (x>0); the mirror ends in 'r'.
"""
from .body_spec import AXLE_F_Y, AXLE_R_Y, AXLE_Z, TRACK_F, TRACK_R, WHEELBASE  # noqa: F401

# --- front suspension (MacPherson strut, front-steer rack) ------------------
FH1 = (0.655, AXLE_F_Y + 0.010, 0.155)    # lower ball joint
FH2 = (0.640, AXLE_F_Y - 0.010, 0.470)    # strut-to-knuckle mount (upper hub node)
FH3 = (0.615, AXLE_F_Y - 0.135, 0.235)    # outer tie-rod end (steering arm ahead of axle)
FH5 = (0.640, AXLE_F_Y + 0.140, 0.330)    # caliper / brake reaction arm
FH6 = (0.660, AXLE_F_Y + 0.010, 0.315)    # hub centre helper (flexbody help)
FS1 = (0.5707, AXLE_F_Y - 0.0317, 0.7515)  # strut top (body), 45 mm below the hood skin
FX1 = (0.300, AXLE_F_Y + 0.020, 0.175)    # lower arm inner pivot (crossmember)
FX2 = (0.390, AXLE_F_Y - 0.360, 0.205)    # tension (TC) rod body mount
FU1 = (0.360, AXLE_F_Y - 0.180, 0.405)    # virtual upper link pivot, front
FU2 = (0.360, AXLE_F_Y + 0.160, 0.405)    # virtual upper link pivot, rear
RACK_Y = AXLE_F_Y - 0.145
RACK_Z = 0.235
RACK_X = 0.280                             # inner tie-rod (rack end) half width

# --- rear suspension (multilink) --------------------------------------------
RH1 = (0.665, AXLE_R_Y + 0.000, 0.160)    # lower arm outer
RH2 = (0.655, AXLE_R_Y + 0.010, 0.470)    # upper arm outer
RH3 = (0.640, AXLE_R_Y + 0.150, 0.220)    # toe link outer
RH4 = (0.620, AXLE_R_Y - 0.020, 0.250)    # shock lower mount
RH5 = (0.645, AXLE_R_Y - 0.140, 0.320)    # caliper / brake reaction arm
RX1 = (0.290, AXLE_R_Y - 0.090, 0.200)    # lower arm inner front (subframe)
RX2 = (0.290, AXLE_R_Y + 0.090, 0.200)    # lower arm inner rear (subframe)
RX3 = (0.390, AXLE_R_Y + 0.000, 0.420)    # upper arm inner (subframe)
RX4 = (0.300, AXLE_R_Y + 0.160, 0.220)    # toe link inner (subframe)
RX5 = (0.420, AXLE_R_Y - 0.320, 0.230)    # traction rod body mount
RS1 = (0.565, AXLE_R_Y + 0.020, 0.790)    # shock tower (body)

# --- powertrain ---------------------------------------------------------------
ENGINE_FRONT_Y = -1.70
ENGINE_REAR_Y = -0.93
CRANK_Z = 0.400
TRANS_REAR_Y = -0.25
DIFF_Y = AXLE_R_Y + 0.010
DIFF_Z = 0.305

# --- cabin --------------------------------------------------------------------
DRIVER_X = 0.365                           # LHD: driver on +X
SEAT_H_POINT = (0.365, 0.12, 0.40)
EYE = (0.365, 0.21, 1.080)
STEER_CENTER = (0.365, -0.385, 0.880)

# instrument cluster (shared by the gauge mesh/texture and the needle props)
GAUGE_Y = STEER_CENTER[1] - 0.21      # face plane
GAUGE_Z = 0.955                       # face centre height
GAUGE_W, GAUGE_H = 0.44, 0.15         # face size
GAUGE_TACH_DX = 0.075                 # main dial centres at +-dx from the column (tach on the driver's left, +x)
GAUGE_SMALL_DX = 0.175                # temp (left) / fuel (right) dial centres
GAUGE_SMALL_DZ = -0.02
GAUGE_R_MAIN = 0.060
GAUGE_R_SMALL = 0.030
