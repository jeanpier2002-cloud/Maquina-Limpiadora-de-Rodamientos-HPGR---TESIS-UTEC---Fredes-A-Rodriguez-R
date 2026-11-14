#!/usr/bin/env python3
"""
Dosis por vuelta por RAYOS (N1: sin gravedad ni arrastre) sobre una superficie, para cribar variantes de
rediseno (G8) antes de simularlas en Fluent. Misma definicion de bandas y de D que post_kpi.py:
  D(b) = mdot_banda * T_vuelta / A_banda ; CV sobre bandas con masa ; zona seca D <= 1e-9.
Sin obstaculos (sector libre). Las tablas son abanico_*.csv de gen_abanico.py.

Uso: python dosis_rayos.py --superficie od --tablas a.csv b.csv ... [--banda-mm 10] [--csv salida.csv]
"""
import argparse
import csv
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rayos_r05 import trazar, SUPS  # noqa: E402

T_VUELTA = 2 * math.pi / 0.1780235837034216


def dosis(tablas, sup, banda_mm, factor=1.0):
    lo, hi = SUPS[sup][1]
    db = banda_mm / 1000.0
    nb = int(math.ceil((hi - lo) / db - 1e-9))
    e = np.minimum(lo + db * np.arange(nb + 1), hi)
    if sup == "od":
        A = 2 * math.pi * 0.710 * np.diff(e)
    elif sup == "agujero":
        A = 2 * math.pi * (0.450 + (0.5 * (e[:-1] + e[1:]) - 0.890) / 60) * np.diff(e) / math.cos(math.atan(1 / 60))
    else:
        A = math.pi * (e[1:] ** 2 - e[:-1] ** 2)
    mb = np.zeros(nb)
    for tb in tablas:
        R = list(csv.DictReader(open(tb)))
        P = np.array([[float(r["Px_m"]), float(r["Py_m"]), float(r["Pz_m"])] for r in R])
        U = np.array([[float(r["Ux_m_s"]), float(r["Uy_m_s"]), float(r["Uz_m_s"])] for r in R])
        m = np.array([float(r["mDot_kg_s"]) for r in R]) * factor
        dest, t, H = trazar(P, U, obst=False)
        s = dest == sup
        sc = H[s, 2] if SUPS[sup][0] == "z" else np.hypot(H[s, 0], H[s, 1])
        ib = np.clip(np.searchsorted(e, sc, side="right") - 1, 0, nb - 1)
        np.add.at(mb, ib, m[s])
    D = mb * T_VUELTA / A
    cm = D > 0
    return dict(e=e, D=D, A=A, D_media=(D * A).sum() / A.sum(), CV=float(np.std(D[cm]) / np.mean(D[cm])),
                seca=100 * A[D <= 1e-9].sum() / A.sum(), D_min=D.min(), D_max=D.max(), mdot=mb.sum())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--superficie", default="od", choices=list(SUPS))
    ap.add_argument("--tablas", nargs="+", required=True)
    ap.add_argument("--banda-mm", type=float, default=10.0)
    ap.add_argument("--factor", type=float, default=1.0)
    ap.add_argument("--csv", default=None)
    a = ap.parse_args()
    r = dosis(a.tablas, a.superficie, a.banda_mm, a.factor)
    print("rayos %s %g mm: D %.4f | CV %.4f | seca %.3f %% | Dmin %.4f | Dmax %.4f | mdot %.6f"
          % (a.superficie, a.banda_mm, r["D_media"], r["CV"], r["seca"], r["D_min"], r["D_max"], r["mdot"]))
    if a.csv:
        with open(a.csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["s_centro_mm", "D_kg_m2_vuelta"])
            w.writerows([["%.2f" % (500 * (r["e"][k] + r["e"][k + 1])), "%.6f" % r["D"][k]] for k in range(len(r["D"]))])
