#!/usr/bin/env python3
"""
G8 - Cribado HIBRIDO de cambios de COTA de las boquillas laterales usando los impactos CFD de G3.
Una lateral movida en Z (misma R, mismo eje y misma distancia a la pared) produce la misma huella trasladada:
se desplaza la z de sus impactos en el OD y se recalculan los KPIs (misma aritmetica que post_kpi.py:
D = mdot_banda*T/A, CV sobre bandas con masa, seca D <= 1e-9). Los impactos que salen de [0,890; 1,405] se
pierden (eta baja). Supuesto: la interaccion por aire entre abanicos vecinos no cambia con el desplazamiento
(en F6, la superposicion de dos laterales vecinas dio D par/suma = 1,00000).
Los cambios de ANGULO (LAT_5, INF_EXT) no son traslaciones: requieren CFD (Caso 2/3).

Uso: python cribado_g8_cfd.py --od D:/CFD03_run/G3/G3_A_base/od.csv --t0 0.025 --t1 0.050 --salida DIR
"""
import argparse
import csv
import math
import os

import numpy as np

T_VUELTA = 2 * math.pi / 0.1780235837034216
Z0, Z1, R = 0.890, 1.405, 0.710

VARIANTES = {
    "C0_base_R05": {},
    "C1_LAT1_-5": {"lat_1_a": -0.005},
    "C1_LAT1_-10": {"lat_1_a": -0.010},
    "C1_LAT1_-12": {"lat_1_a": -0.012},
    "C2_LAT1-4_-10": {"lat_1_a": -0.010, "lat_2_a": -0.010, "lat_3_a": -0.010, "lat_4_a": -0.010},
    "C3_paso_90_desde_1090": {"lat_1_a": -0.010, "lat_2_a": 0.0 - 0.002105, "lat_3_a": 0.00579, "lat_4_a": 0.013685},
    "C3_paso_88_desde_1090": {"lat_1_a": -0.010, "lat_2_a": -0.004105, "lat_3_a": 0.00179, "lat_4_a": 0.007685},
    "C4_paso_86_desde_1090": {"lat_1_a": -0.010, "lat_2_a": -0.006105, "lat_3_a": -0.00221, "lat_4_a": 0.001685},
}


def kpis(z, m, db):
    nb = int(math.ceil((Z1 - Z0) / db - 1e-9))
    e = np.minimum(Z0 + db * np.arange(nb + 1), Z1)
    A = 2 * math.pi * R * np.diff(e)
    den = (z >= Z0) & (z <= Z1)
    ib = np.clip(np.searchsorted(e, z[den], side="right") - 1, 0, nb - 1)
    mb = np.bincount(ib, weights=m[den], minlength=nb)
    D = mb * T_VUELTA / A
    cm = D > 0
    return dict(D=(D * A).sum() / A.sum(), CV=float(np.std(D[cm]) / np.mean(D[cm])), Dmin=D.min(),
                seca=100 * A[D <= 1e-9].sum() / A.sum(), mdot=mb.sum(), perfil=(e, D))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--od", required=True)
    ap.add_argument("--t0", type=float, default=0.025)
    ap.add_argument("--t1", type=float, default=0.050)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--inyectado", type=float, default=0.908569)
    a = ap.parse_args()
    R_ = list(csv.DictReader(open(a.od)))
    t = np.array([float(r["t"]) for r in R_])
    s = (t >= a.t0) & (t < a.t1)
    z = np.array([float(r["z"]) for r in R_])[s]
    m = np.array([float(r["masa"]) for r in R_])[s] / (a.t1 - a.t0)
    b = np.array([r["boquilla"] for r in R_])[s]
    os.makedirs(a.salida, exist_ok=True)
    filas = []
    for nom, dz in VARIANTES.items():
        zz = z.copy()
        for bb, d in dz.items():
            zz[b == bb] += d
        k10, k2 = kpis(zz, m, 0.010), kpis(zz, m, 0.002)
        filas.append([nom, "%.4f" % k10["D"], "%.4f" % k10["CV"], "%.4f" % k10["Dmin"], "%.3f" % k10["seca"],
                      "%.4f" % k2["CV"], "%.4f" % k2["Dmin"], "%.3f" % k2["seca"], "%.2f" % (100 * k10["mdot"] / a.inyectado)])
        print("%-24s D %s | CV10 %s | Dmin10 %s | seca10 %s %% | CV2 %s | Dmin2 %s | seca2 %s %% | eta %s %%" % tuple(filas[-1]))
        e, D = k2["perfil"]
        with open(os.path.join(a.salida, "cribado_cfd_%s_perfil2mm.csv" % nom), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["z_centro_mm", "D_kg_m2_vuelta_ramalA"])
            w.writerows([["%.1f" % (500 * (e[i] + e[i + 1])), "%.5f" % D[i]] for i in range(len(D))])
    with open(os.path.join(a.salida, "cribado_g8_cfd_hibrido.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["variante", "D_media_10mm", "CV_10mm", "D_min_10mm", "seca_10mm_pct", "CV_2mm", "D_min_2mm",
                    "seca_2mm_pct", "eta_OD_pct"])
        w.writerows(filas)


if __name__ == "__main__":
    main()
