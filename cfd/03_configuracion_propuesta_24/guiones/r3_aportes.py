#!/usr/bin/env python3
"""
CORRIDA 3 · T6 · Aporte de cada boquilla a la dosis de la cara inferior por banda de 10 mm, sin obstaculos, con la
misma aritmetica de combinar_kpi.py (se importan sus funciones: leer, bandas, area_banda, T_VUELTA):
  D_n(b) = mdot_n,banda * T_vuelta / A_banda
Ramal B: S9 (la corrida A cuenta dos veces) o explicito (--b). INF_INT de G5_INT_base_v2 con ventana 0,070-0,100 s.
Salida: <salida>/<tag>_cara_inf_aportes_bandas.csv (columnas INF_EXT, boquilla C2, LAT_5, INF_INT, total)
Uso: python -I -B r3_aportes.py --a <corrida A> [--b <corrida B>] --salida <dir> --tag <nombre>
"""
import argparse
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit"))
from combinar_kpi import T_VUELTA, area_banda, bandas, leer  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--a", required=True)
ap.add_argument("--b", default=None)
ap.add_argument("--g5", default="D:/CFD03_run/G5/G5_INT_base_v2")
ap.add_argument("--salida", required=True)
ap.add_argument("--tag", required=True)
a = ap.parse_args()
e = bandas("cara_inf", 0.010)
nb = len(e) - 1
Ab = np.array([area_banda("cara_inf", e[k], e[k + 1]) for k in range(nb)])


def D(path, boq, t0, t1, fac=1.0):
    s, m, _ = leer(path, [boq], t0, t1, "cara_inf")
    ok = (s >= e[0]) & (s <= e[-1])
    ib = np.clip(np.searchsorted(e, s[ok], side="right") - 1, 0, nb - 1)
    return fac * np.bincount(ib, weights=m[ok], minlength=nb) * T_VUELTA / Ab


ca = os.path.join(a.a, "cara_inf.csv")
cb = os.path.join(a.b, "cara_inf.csv") if a.b else None
col = {}
for nom, n in (("INF_EXT", "inf_ext"), ("boquilla C2", "c2"), ("LAT_5", "lat_5")):
    col[nom] = D(ca, n + "_a", 0.025, 0.050) + (D(cb, n + "_b", 0.025, 0.050) if cb else D(ca, n + "_a", 0.025, 0.050))
col["INF_INT"] = D(os.path.join(a.g5, "cara_inf.csv"), "inf_int", 0.070, 0.100)
col["total"] = sum(col.values())
os.makedirs(a.salida, exist_ok=True)
with open(os.path.join(a.salida, a.tag + "_cara_inf_aportes_bandas.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["s_centro_mm"] + list(col))
    for k in range(nb):
        w.writerow(["%.1f" % (500 * (e[k] + e[k + 1]))] + ["%.5f" % col[c][k] for c in col])
for c, v in col.items():
    print("%-12s D media (area) %.3f kg/m2/vuelta" % (c, (v * Ab).sum() / Ab.sum()))
