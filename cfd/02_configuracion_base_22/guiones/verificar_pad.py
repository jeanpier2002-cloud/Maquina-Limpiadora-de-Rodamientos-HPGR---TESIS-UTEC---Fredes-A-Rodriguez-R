#!/usr/bin/env python3
"""
G5 - Verificacion con CFD del metodo de sombras por rayos (G2 §4): corrida G5_PAD_base (PAD 1 en la malla, ramal A
en theta = 0 sobre el PAD) frente a G3_A_base (misma malla sin PAD, mismas tablas de 150 rayos).

Compara, por boquilla:
  - masa que el CFD atrapa en la pared 'pad' vs fraccion que los rayos (rayos_r05.trazar, phi = 0, con obstaculos)
    mandan al PAD 1 (cap + liner + base);
  - masa en la cara inferior dentro de |theta| <= 12 grados por tramos de r (sombra: r < 638 mm) con y sin PAD.
Uso: python verificar_pad.py --pad D:/CFD03_run/G5/G5_PAD_base --libre D:/CFD03_run/G3/G3_A_base --salida DIR
"""
import argparse
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rayos_r05 import trazar  # noqa: E402


def leer(p, t0, t1):
    if not os.path.exists(p):
        return None
    R = list(csv.DictReader(open(p)))
    t = np.array([float(r["t"]) for r in R]); s = (t >= t0) & (t < t1)
    d = {k: np.array([float(r[k]) for r in R])[s] for k in ("x", "y", "z")}
    d["m"] = np.array([float(r["masa"]) for r in R])[s] / (t1 - t0)
    d["b"] = np.array([r["boquilla"] for r in R])[s]
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pad", required=True)
    ap.add_argument("--libre", required=True)
    ap.add_argument("--t0", type=float, default=0.025)
    ap.add_argument("--t1", type=float, default=0.050)
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)
    pad = leer(os.path.join(a.pad, "pad.csv"), a.t0, a.t1)
    ciP = leer(os.path.join(a.pad, "cara_inf.csv"), a.t0, a.t1)
    ciL = leer(os.path.join(a.libre, "cara_inf.csv"), a.t0, a.t1)
    odP = leer(os.path.join(a.pad, "od.csv"), a.t0, a.t1)
    odL = leer(os.path.join(a.libre, "od.csv"), a.t0, a.t1)
    filas = []
    tabs = sorted(f for f in os.listdir(a.pad) if f.startswith("abanico_") and f.endswith(".csv"))
    for tb in tabs:
        ident = tb[8:-4]; b = ident.lower()
        R = list(csv.DictReader(open(os.path.join(a.pad, tb))))
        P = np.array([[float(r["Px_m"]), float(r["Py_m"]), float(r["Pz_m"])] for r in R])
        U = np.array([[float(r["Ux_m_s"]), float(r["Uy_m_s"]), float(r["Uz_m_s"])] for r in R])
        m = np.array([float(r["mDot_kg_s"]) for r in R])
        dest, _, H = trazar(P, U, obst=True)
        f_pad_r = 100 * m[np.isin(dest, ["PAD_1", "PAD_1_base"])].sum() / m.sum()
        f_ci_r = 100 * m[dest == "cara_inf"].sum() / m.sum()
        f_od_r = 100 * m[dest == "od"].sum() / m.sum()
        destL, _, _ = trazar(P, U, obst=False)
        f_ciL_r = 100 * m[destL == "cara_inf"].sum() / m.sum()
        mp = pad["m"][pad["b"] == b].sum() if pad is not None else 0.0

        def ci(d):
            if d is None:
                return 0.0, 0.0, 0.0
            s = d["b"] == b
            r = np.hypot(d["x"][s], d["y"][s]); mm = d["m"][s]
            return mm[r < 0.638].sum(), mm[(r >= 0.638) & (r <= 0.688)].sum(), mm[r > 0.688].sum()
        cP, cL = ci(ciP), ci(ciL)
        oP = odP["m"][odP["b"] == b].sum() if odP is not None else 0.0
        oL = odL["m"][odL["b"] == b].sum() if odL is not None else 0.0
        fila = [ident, "%.6f" % m.sum(), "%.2f" % f_pad_r, "%.2f" % (100 * mp / m.sum()),
                "%.2f" % f_ciL_r, "%.2f" % f_ci_r, "%.2f" % (100 * sum(cL) / m.sum()), "%.2f" % (100 * sum(cP) / m.sum()),
                "%.3f" % (100 * cL[0] / m.sum()), "%.3f" % (100 * cP[0] / m.sum()),
                "%.2f" % (100 * oL / m.sum()), "%.2f" % (100 * oP / m.sum()), "%.2f" % f_od_r]
        filas.append(fila)
        print("%-10s PAD: rayos %s %% / CFD %s %% | cara_inf: rayos libre %s -> PAD %s %% ; CFD libre %s -> PAD %s %% "
              "(r<638: %s -> %s %%) | OD CFD %s -> %s %% (rayos PAD %s %%)" % tuple(fila[:1] + fila[2:]))
    with open(os.path.join(a.salida, "G5_verificacion_PAD.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["boquilla", "mdot_kg_s", "PAD_rayos_pct", "PAD_CFD_pct", "cara_inf_rayos_libre_pct",
                    "cara_inf_rayos_PAD_pct", "cara_inf_CFD_libre_pct", "cara_inf_CFD_PAD_pct", "cara_inf_r638_CFD_libre_pct",
                    "cara_inf_r638_CFD_PAD_pct", "OD_CFD_libre_pct", "OD_CFD_PAD_pct", "OD_rayos_PAD_pct"])
        w.writerows(filas)


if __name__ == "__main__":
    main()
