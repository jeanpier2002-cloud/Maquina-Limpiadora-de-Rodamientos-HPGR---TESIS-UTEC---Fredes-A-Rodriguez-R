#!/usr/bin/env python3
"""
K1 — acceso geometrico por trazado de rayos (N1), y dimensionado de sectores.

Rayos rectos (sin arrastre ni gravedad) desde la posicion de cada parcela de la tabla de
inyeccion (abanico_*.csv de gen_abanico.py) en la direccion de su velocidad. Se intersectan con:
  cilindro : r = R (OD, la gota llega desde fuera), z en [lim]
  anillo   : plano z = z0, r en [lim]
  cono     : agujero 1:30 de la rama B (llega desde dentro)
Con el rotor girando, la huella barre todo el acimut: K1 = area de las bandas de 10 mm
alcanzadas por >= 1 rayo / area total (misma discretizacion que post_kpi.py).

Uso: python k1_rayos.py --superficie cilindro --R 0.710 --lim 0.890 1.405 \
        --tablas abanico_LAT_1.csv abanico_LAT_2.csv ... [--salida carpeta --caso nombre]
"""
import argparse
import csv
import math
import os

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--superficie", choices=["cilindro", "anillo", "cono"], required=True)
ap.add_argument("--R", type=float, default=0.710)
ap.add_argument("--z0", type=float, default=1.405)
ap.add_argument("--lim", nargs=2, type=float, required=True)
ap.add_argument("--tablas", nargs="+", required=True)
ap.add_argument("--banda-mm", type=float, default=10.0)
ap.add_argument("--salida", default=None)
ap.add_argument("--caso", default="K1")
a = ap.parse_args()


def interseca(P, U):
    """Devuelve (t, s, theta_deg) del primer impacto valido de cada rayo, o NaN."""
    n = len(P)
    t = np.full(n, np.nan)
    if a.superficie == "anillo":
        with np.errstate(divide="ignore", invalid="ignore"):
            tt = (a.z0 - P[:, 2]) / U[:, 2]
        ok = tt > 0
        H = P + tt[:, None] * U
        r = np.hypot(H[:, 0], H[:, 1])
        ok &= (r >= a.lim[0]) & (r <= a.lim[1])
        t[ok] = tt[ok]
    else:
        # |P_xy + t U_xy| = R(z)  (cono: R = 0,450 + (z - 0,890)/60; se itera en z)
        A = U[:, 0] ** 2 + U[:, 1] ** 2
        B = 2 * (P[:, 0] * U[:, 0] + P[:, 1] * U[:, 1])
        R = np.full(n, a.R)
        for _ in range(5 if a.superficie == "cono" else 1):
            C = P[:, 0] ** 2 + P[:, 1] ** 2 - R ** 2
            disc = B ** 2 - 4 * A * C
            sq = np.sqrt(np.where(disc >= 0, disc, np.nan))
            # desde fuera (cilindro): raiz menor; desde dentro (cono): raiz mayor
            tt = (-B - sq) / (2 * A) if a.superficie == "cilindro" else (-B + sq) / (2 * A)
            if a.superficie == "cono":
                zz = P[:, 2] + tt * U[:, 2]
                R = 0.450 + (np.clip(zz, 0.890, 1.405) - 0.890) / 60.0
        H = P + tt[:, None] * U
        ok = (tt > 0) & (H[:, 2] >= a.lim[0]) & (H[:, 2] <= a.lim[1])
        t[ok] = tt[ok]
    H = P + np.nan_to_num(t)[:, None] * U
    s = H[:, 2] if a.superficie != "anillo" else np.hypot(H[:, 0], H[:, 1])
    th = np.degrees(np.arctan2(H[:, 1], H[:, 0]))
    s[np.isnan(t)] = np.nan
    return t, s, th


lo, hi = a.lim
db = a.banda_mm * 1e-3
nb = int(math.ceil((hi - lo) / db - 1e-9))
bordes = np.minimum(lo + db * np.arange(nb + 1), hi)
if a.superficie == "anillo":
    A_b = math.pi * (bordes[1:] ** 2 - bordes[:-1] ** 2)
elif a.superficie == "cilindro":
    A_b = 2 * math.pi * a.R * np.diff(bordes)
else:
    rz = 0.450 + (0.5 * (bordes[1:] + bordes[:-1]) - 0.890) / 60.0
    A_b = 2 * math.pi * rz * np.diff(bordes) / math.cos(math.atan(1 / 60))
alc = np.zeros(nb, bool)
filas = []
for tb in a.tablas:
    rows = list(csv.DictReader(open(tb)))
    P = np.array([[float(r["Px_m"]), float(r["Py_m"]), float(r["Pz_m"])] for r in rows])
    U = np.array([[float(r["Ux_m_s"]), float(r["Uy_m_s"]), float(r["Uz_m_s"])] for r in rows])
    m = np.array([float(r["mDot_kg_s"]) for r in rows])
    t, s, th = interseca(P, U)
    ok = ~np.isnan(t)
    k = np.clip(np.digitize(s[ok], bordes) - 1, 0, nb - 1)
    alc[k] = True
    nombre = os.path.basename(tb).replace("abanico_", "").replace(".csv", "")
    filas.append([nombre, "%.2f" % (100 * m[ok].sum() / m.sum()),
                  "%.2f" % (1e3 * np.nanmin(s)) if ok.any() else "", "%.2f" % (1e3 * np.nanmax(s)) if ok.any() else "",
                  "%.3f" % np.nanmin(th[ok]) if ok.any() else "", "%.3f" % np.nanmax(th[ok]) if ok.any() else "",
                  "%.2f" % (1e3 * np.nanmax(t[ok] * np.linalg.norm(U[ok], axis=1))) if ok.any() else ""])
    print("%-8s llega %6s %% del caudal | s %s-%s mm | theta %s..%s grados | recorrido max %s mm" % tuple(filas[-1]))
K1 = 100 * A_b[alc].sum() / A_b.sum()
print("K1 = %.3f %% del area (%d de %d bandas de %.0f mm)" % (K1, alc.sum(), nb, a.banda_mm))
if a.salida:
    os.makedirs(a.salida, exist_ok=True)
    with open(os.path.join(a.salida, a.caso + "_K1_por_boquilla.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["boquilla", "pct_caudal_que_llega", "s_min_mm", "s_max_mm", "theta_min_deg", "theta_max_deg",
                    "recorrido_max_mm"])
        w.writerows(filas)
    with open(os.path.join(a.salida, a.caso + "_K1_bandas.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["s_centro_mm", "alcanzada"])
        w.writerows([["%.2f" % (500 * (bordes[i] + bordes[i + 1])), int(alc[i])] for i in range(nb)])
    with open(os.path.join(a.salida, a.caso + "_K1.csv"), "w", newline="") as f:
        csv.writer(f).writerows([["caso", "superficie", "K1_pct", "bandas_alcanzadas", "bandas"],
                                 [a.caso, a.superficie, "%.3f" % K1, int(alc.sum()), nb]])
