#!/usr/bin/env python3
"""Figura de S3: como cambian los indicadores con cada parametro supuesto."""
import argparse
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

P = argparse.ArgumentParser()
P.add_argument("--csv-dir", required=True)
P.add_argument("--salida", required=True)
A = P.parse_args()
os.makedirs(A.salida, exist_ok=True)

Z_INF, Z_SUP = 890.0, 1405.0
BASE = "S2_seis"
GRUPOS = [
    ("angulo del abanico", ["S3_ang40", BASE, "S3_ang55"],
     ["40$\\degree$", "50$\\degree$ (base)", "55$\\degree$"],
     ["#7f7f7f", "#d62728", "#1f77b4"]),
    ("tamano de gota (Rosin-Rammler)", ["S3_RR150", BASE, "S3_RR500"],
     ["$\\lambda$=150 $\\mu$m (D32 177)", "$\\lambda$=300 $\\mu$m (D32 354, base)",
      "$\\lambda$=500 $\\mu$m (D32 584)"],
     ["#2ca02c", "#d62728", "#8c564b"]),
    ("angulo fuera del plano (el unico SIN DATO)", [BASE, "S3_fuera5"],
     ["2$\\degree$ (base)", "5$\\degree$"], ["#d62728", "#ff7f0e"]),
]


def leer(n):
    with open(os.path.join(A.csv_dir, n)) as f:
        return list(csv.DictReader(f))


dz = defaultdict(list)
for r in leer("F4_dosis_por_Z.csv"):
    dz[r["caso"]].append((float(r["z_mm"]), float(r["D_kg_m2_vuelta"])))
cob = defaultdict(list)
for r in leer("F4_cobertura.csv"):
    cob[r["caso"]].append((float(r["D_min_kg_m2_vuelta"]), float(r["cobertura_pct"])))

fig, ax = plt.subplots(2, 3, figsize=(15.5, 9.2))
for j, (titulo, casos, etiq, cols) in enumerate(GRUPOS):
    for c, e, col in zip(casos, etiq, cols):
        if c not in dz:
            continue
        d = np.array(sorted(dz[c]))
        ax[0, j].plot(d[:, 1], d[:, 0], "-", lw=1.7, color=col, label=e)
        k = np.array(sorted(set(cob[c])))
        ax[1, j].semilogx(k[:, 0], k[:, 1], "-", lw=1.8, color=col, label=e)
    ax[0, j].axhline(Z_INF, color="k", lw=1)
    ax[0, j].axhline(Z_SUP, color="k", lw=1)
    ax[0, j].set_xlabel("dosis por vuelta  D(Z)  [kg/m$^2$]")
    ax[0, j].set_ylabel("cota Z  [mm]" if j == 0 else "")
    ax[0, j].set_title(titulo, fontsize=10)
    ax[0, j].legend(fontsize=7.5, loc="lower right")
    ax[0, j].grid(alpha=.3)
    ax[1, j].set_xlabel("umbral $D_{min}$  [kg/m$^2$ por vuelta]")
    ax[1, j].set_ylabel("cobertura  [%]" if j == 0 else "")
    ax[1, j].set_ylim(0, 103)
    ax[1, j].legend(fontsize=7.5, loc="lower left")
    ax[1, j].grid(alpha=.3, which="both")

fig.suptitle("F4 / S3 - sensibilidad de la dosis y la cobertura a los tres supuestos del modelo\n"
             "arriba: dosis por vuelta    abajo: curva de cobertura", fontsize=11.5)
fig.tight_layout(rect=(0, 0, 1, 0.93))
p = os.path.join(A.salida, "F4_S3_sensibilidades.png")
fig.savefig(p, dpi=150)
print("escrito", p)
