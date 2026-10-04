"""Physics sanity analyses on a resolved JBeam vehicle.

* mass, centre of gravity, axle load split;
* explicit-integration stability: the largest natural frequency of the beam
  network, omega_max, from the generalised eigenproblem K v = w^2 M v.  BeamNG
  steps physics at 2000 Hz; symplectic-Euler-type integrators go unstable when
  omega*dt approaches 2, so we keep a margin and compare with values measured
  on the official template's known-good parts;
* truss rigidity: zero-energy modes of the stiffness matrix (rigid-body modes +
  mechanisms) for a sub-structure.
"""
from __future__ import annotations

import math

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

DT = 1.0 / 2000.0


def _num(v, default=0.0):
    if v is None:
        return default
    if v == "FLT_MAX":
        return 1e30
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def node_mass(n: dict) -> float:
    return _num(n.get("nodeWeight"), 25.0)  # BeamNG default nodeWeight is 25 kg


def mass_props(nodes: dict, extra_points=()):
    """Return total mass, CoG (x,y,z) from nodes plus (mass, pos) extra points."""
    ms, ps = [], []
    for n in nodes.values():
        ms.append(node_mass(n)); ps.append(n["pos"])
    for m, p in extra_points:
        ms.append(m); ps.append(np.asarray(p, float))
    ms = np.asarray(ms); ps = np.asarray(ps)
    tot = ms.sum()
    cog = (ms[:, None] * ps).sum(0) / tot
    return tot, cog


def beam_list(res, include_types=("|NORMAL", "NORMAL", None, "|SUPPORT", "SUPPORT", "|BOUNDED", "BOUNDED", "|ANISOTROPIC", "ANISOTROPIC", "|LBEAM")):
    out = []
    for sec in ("beams", "hydros"):
        for b in res.tables.get(sec, []):
            a, c = b.get("id1:"), b.get("id2:")
            if a not in res.nodes or c not in res.nodes:
                continue
            t = b.get("beamType", "|NORMAL")
            k = _num(b.get("beamSpring"), 4300000.0)
            if t in ("|BOUNDED", "BOUNDED"):
                k = max(k, _num(b.get("beamLimitSpring"), 0.0))
            d = _num(b.get("beamDamp"), 580.0)
            out.append((a, c, k, d, t, b))
    return out


def stiffness_matrices(res, beams, node_names=None):
    names = node_names or list(res.nodes.keys())
    idx = {n: i for i, n in enumerate(names)}
    N = len(names)
    rows, cols, vals = [], [], []
    drows, dcols, dvals = [], [], []
    for a, c, k, d, t, b in beams:
        if a not in idx or c not in idx:
            continue
        pa, pc = res.nodes[a]["pos"], res.nodes[c]["pos"]
        e = pc - pa
        L = np.linalg.norm(e)
        if L < 1e-6:
            continue
        e = e / L
        kk = np.outer(e, e)
        ia, ic = 3 * idx[a], 3 * idx[c]
        for (r0, c0, s) in ((ia, ia, 1), (ic, ic, 1), (ia, ic, -1), (ic, ia, -1)):
            for i in range(3):
                for j in range(3):
                    rows.append(r0 + i); cols.append(c0 + j); vals.append(s * k * kk[i, j])
                    drows.append(r0 + i); dcols.append(c0 + j); dvals.append(s * d * kk[i, j])
    K = sp.csr_matrix((vals, (rows, cols)), shape=(3 * N, 3 * N))
    C = sp.csr_matrix((dvals, (drows, dcols)), shape=(3 * N, 3 * N))
    m = np.repeat([node_mass(res.nodes[n]) for n in names], 3)
    return names, K, C, m


def stability(res, beams=None, names=None):
    """omega_max*dt and the worst nodes (by row-sum bound)."""
    beams = beams if beams is not None else beam_list(res)
    names, K, C, m = stiffness_matrices(res, beams, names)
    if K.shape[0] == 0:
        return {"omega_dt": 0.0, "damp_dt": 0.0, "worst": []}
    Minv_sqrt = sp.diags(1.0 / np.sqrt(m))
    A = Minv_sqrt @ K @ Minv_sqrt
    try:
        lam = spla.eigsh(A, k=1, which="LA", return_eigenvectors=False, tol=1e-4, maxiter=5000)[0]
    except Exception:
        lam = float(np.max(np.abs(A).sum(axis=1)))
    omega = math.sqrt(max(lam, 0.0))
    # damping: largest eigenvalue of M^-1/2 C M^-1/2
    Ad = Minv_sqrt @ C @ Minv_sqrt
    try:
        dmax = float(spla.eigsh(Ad, k=1, which="LA", return_eigenvectors=False, tol=1e-4, maxiter=5000)[0])
    except Exception:
        dmax = float(np.max(np.abs(Ad).sum(axis=1)))
    # per-node Gershgorin bound to find culprits
    rs = np.asarray(np.abs(A).sum(axis=1)).ravel().reshape(-1, 3).max(axis=1)
    order = np.argsort(-rs)[:8]
    worst = [(names[i], math.sqrt(rs[i]) * DT) for i in order]
    return {"omega_dt": omega * DT, "damp_dt": dmax * DT, "worst": worst}


def rigidity_modes(res, names, beams=None, tol=1e-6):
    """Number of near-zero stiffness modes of the sub-structure made by `names`."""
    beams = beams if beams is not None else beam_list(res)
    names, K, C, m = stiffness_matrices(res, beams, names)
    Kd = K.toarray()
    scale = np.max(np.abs(Kd)) or 1.0
    w = np.linalg.eigvalsh(Kd / scale)
    nz = int(np.sum(w < tol))
    return nz, w[:12]
