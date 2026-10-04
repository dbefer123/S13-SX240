"""Inspect soft / zero-energy modes of a structure (debug helper)."""
import numpy as np
from . import physics as P


def soft_modes(res, names=None, k=10, top=6):
    names = names or list(res.nodes.keys())
    beams = P.beam_list(res)
    names, K, C, m = P.stiffness_matrices(res, beams, names)
    Kd = K.toarray()
    scale = np.max(np.abs(Kd))
    w, V = np.linalg.eigh(Kd / scale)
    out = []
    for i in range(min(k, len(w))):
        v = V[:, i].reshape(-1, 3)
        mag = np.linalg.norm(v, axis=1)
        # remove rigid-body-ish uniform motion by looking at the largest movers
        idx = np.argsort(-mag)[:top]
        out.append((w[i], [(names[j], round(float(mag[j]), 3)) for j in idx]))
    return out
