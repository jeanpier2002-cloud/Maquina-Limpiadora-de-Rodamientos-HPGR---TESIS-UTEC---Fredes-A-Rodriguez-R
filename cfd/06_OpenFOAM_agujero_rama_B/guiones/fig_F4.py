#!/usr/bin/env python3
"""Figuras de F4: dosis por vuelta D(Z), curva de cobertura y mapa de deposicion."""
import argparse
import csv
import math
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

P = argparse.ArgumentParser()
P.add_argument("--csv-dir", required=True)
P.add_argument("--salida", required=True)
P.add_argument("--caso", default=None, help="caso principal para el mapa")
A = P.parse_args()
os.makedirs(A.salida, exist_ok=True)

Z_INF, Z_SUP = 890.0, 1405.0
COL = {"S1r_INT3": "#1f77b4", "S2_seis": "#d62728",
       "S2_22mm": "#7f7f7f", "S2_11mm": "#2ca02c"}
ETI = {"S1r_INT3": "S1  solo INT_3", "S2_seis": "S2  seis boquillas (base 16 mm)",
       "S2_22mm": "S2  malla gruesa (22 mm)", "S2_11mm": "S2  malla fina (11 mm)"}


def leer(n):
    with open(os.path.join(A.csv_dir, n)) as f:
        return list(csv.DictReader(f))


dz = defaultdict(list)
for r in leer("F4_dosis_por_Z.csv"):
    dz[r["caso"]].append((float(r["z_mm"]), float(r["D_kg_m2_vuelta"])))
cob = defaultdict(list)
for r in leer("F4_cobertura.csv"):
    cob[r["caso"]].append((float(r["D_min_kg_m2_vuelta"]), float(r["cobertura_pct"])))
casos = sorted(dz)
principal = A.caso if A.caso in dz else (("S2_seis" in dz) and "S2_seis" or casos[-1])

fig, ax = plt.subplots(1, 3, figsize=(16.2, 5.4))

# ------------------------------------------------ (a) dosis por vuelta D(Z)
for c in casos:
    d = np.array(sorted(dz[c]))
    ax[0].plot(d[:, 1], d[:, 0], "-", lw=1.7, color=COL.get(c, None), label=ETI.get(c, c))
ax[0].axhline(Z_INF, color="k", lw=1.2)
ax[0].axhline(Z_SUP, color="k", lw=1.2)
ax[0].text(ax[0].get_xlim()[1] * .97, Z_INF - 8, "Z890 cara inferior", fontsize=7.5, ha="right", va="top")
ax[0].text(ax[0].get_xlim()[1] * .97, Z_SUP + 8, "Z1405 cara superior", fontsize=7.5, ha="right")
ax[0].set_xlabel("dosis por vuelta  D(Z)   [kg/m$^2$]")
ax[0].set_ylabel("cota  Z   [mm]")
ax[0].set_title("(a) Dosis por vuelta a lo largo del agujero\n"
                "$D(Z)=\\int\\varphi\\,d\\theta/\\omega$", fontsize=10)
ax[0].legend(fontsize=8, loc="lower right")
ax[0].grid(alpha=.3)

# ------------------------------------------------ (b) curva de cobertura
for c in casos:
    d = np.array(sorted(set(cob[c])))
    ax[1].semilogx(d[:, 0], d[:, 1], "-", lw=1.8, color=COL.get(c, None), label=ETI.get(c, c))
for x, txt in ((0.1, "0,1"), (1.0, "1"), (5.0, "5")):
    ax[1].axvline(x, ls=":", c="0.5", lw=1)
    ax[1].text(x, 3, txt, fontsize=7.5, ha="center", color="0.35")
ax[1].set_xlabel("umbral $D_{min}$   [kg/m$^2$ por vuelta]")
ax[1].set_ylabel("cobertura  [% del area del agujero]")
ax[1].set_title("(b) Cobertura frente al umbral, como curva\n"
                "el usuario no fijo $D_{min}$: se informa la curva entera", fontsize=10)
ax[1].set_ylim(0, 103)
ax[1].legend(fontsize=8, loc="lower left")
ax[1].grid(alpha=.3, which="both")

# ------------------------------------------------ (c) D(Z) por boquilla
COLB = {"INT_1": "#1f77b4", "INT_2": "#2ca02c", "INT_3": "#d62728",
        "INT_4": "#9467bd", "INT_5": "#8c564b", "INF_INT": "#ff7f0e"}
porb = defaultdict(list)
for r in leer("F4_dosis_por_Z_boquilla.csv"):
    if r["caso"] == principal:
        porb[r["boquilla"]].append((float(r["z_mm"]), float(r["D_kg_m2_vuelta"])))
for tag in ["INF_INT", "INT_1", "INT_2", "INT_3", "INT_4", "INT_5"]:
    if tag not in porb:
        continue
    d = np.array(sorted(porb[tag]))
    ax[2].plot(d[:, 1], d[:, 0], "-", lw=1.6, color=COLB[tag], label=tag)
tot = np.array(sorted(dz[principal]))
ax[2].plot(tot[:, 1], tot[:, 0], "k--", lw=1.8, label="suma")
ax[2].axhline(Z_INF, color="k", lw=1.2)
ax[2].axhline(Z_SUP, color="k", lw=1.2)
ax[2].set_xlabel("dosis por vuelta  D(Z)   [kg/m$^2$]")
ax[2].set_ylabel("cota  Z   [mm]")
ax[2].set_title("(c) Que pone cada boquilla en cada cota\n"
                "INF_INT solo aporta a los 20 mm de abajo", fontsize=10)
ax[2].legend(fontsize=7.5, ncol=2, loc="upper right")
ax[2].grid(alpha=.3)

fig.suptitle("F4 - Deposicion sobre el agujero del rodamiento   "
             "(agua a 62 $\\degree$C, abanico 50$\\degree$, Rosin-Rammler supuesta, "
             "distribuidor a 1,7 rpm)", fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.93))
p = os.path.join(A.salida, "F4_dosis_y_cobertura.png")
fig.savefig(p, dpi=155)
print("escrito", p)
