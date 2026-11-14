#!/usr/bin/env python3
"""
F5 - mapa desarrollado del agujero: la huella instantanea frente a la dosis por
vuelta. Es la figura que explica el metodo: se simula UNA posicion de la lanza,
que deja una banda acimutal estrecha, y la dosis por vuelta sale de integrar esa
banda sobre el acimut y dividir por la velocidad de giro.
"""
import argparse
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

P = argparse.ArgumentParser()
P.add_argument("--csv-dir", required=True)
P.add_argument("--salida", required=True)
P.add_argument("--caso", default="S2_seis")
A = P.parse_args()
os.makedirs(A.salida, exist_ok=True)

Z_INF, Z_SUP = 890.0, 1405.0
BOQ_Z = {"INT_1": 956.8, "INT_2": 1052.2, "INT_3": 1147.5,
         "INT_4": 1242.8, "INT_5": 1338.2, "INF_INT": 850.0}


def leer(n):
    with open(os.path.join(A.csv_dir, n)) as f:
        return list(csv.DictReader(f))


# --------------------------------------------------- datos
pts = [(float(r["z_mm"]), float(r["theta_deg"]), float(r["phi_kg_m2_s"]))
       for r in leer("F4_mapa_phi.csv") if r["caso"] == A.caso]
dz = sorted((float(r["z_mm"]), float(r["D_kg_m2_vuelta"]))
            for r in leer("F4_dosis_por_Z.csv") if r["caso"] == A.caso)
pts = np.array(pts)
dzz = np.array(dz)

fig, ax = plt.subplots(1, 3, figsize=(15.0, 6.6),
                       gridspec_kw={"width_ratios": [1.15, 1.0, 1.0]})

# ---------------------------------------- (a) huella instantanea, acimut completo
a = ax[0]
sc = a.scatter(pts[:, 1], pts[:, 0], c=pts[:, 2], s=26, marker="s",
               cmap="inferno", norm=LogNorm())
cb = fig.colorbar(sc, ax=a, pad=0.02)
cb.set_label("$\\varphi$   [kg/(m$^2\\cdot$s)]", fontsize=9)
a.axhline(Z_INF, color="k", lw=1.3)
a.axhline(Z_SUP, color="k", lw=1.3)
a.set_xlim(-180, 180)
a.set_ylim(870, 1425)
a.set_xticks([-180, -90, 0, 90, 180])
a.set_xlabel("acimut relativo a la lanza   [grados]")
a.set_ylabel("cota  Z   [mm]")
a.set_title("(a) Huella instantanea sobre el agujero desarrollado\n"
            "toda la deposicion cabe en menos de 1$\\degree$ de acimut", fontsize=10)
a.grid(alpha=.3)

# ---------------------------------------- (b) el mismo mapa, ampliado en acimut
b = ax[1]
sc2 = b.scatter(pts[:, 1], pts[:, 0], c=pts[:, 2], s=150, marker="s",
                cmap="inferno", norm=LogNorm())
for tag, z in BOQ_Z.items():
    if Z_INF - 60 <= z <= Z_SUP:
        b.annotate(tag, xy=(-0.95, z), fontsize=7.5, color="0.25", va="center")
b.axhline(Z_INF, color="k", lw=1.3)
b.axhline(Z_SUP, color="k", lw=1.3)
b.set_xlim(-1.0, 1.0)
b.set_ylim(870, 1425)
b.set_xlabel("acimut relativo a la lanza   [grados]")
b.set_title("(b) Lo mismo, ampliado\n"
            "las lineas discretas son los rayos de la tabla de inyeccion", fontsize=10)
b.grid(alpha=.3)

# ---------------------------------------- (c) dosis por vuelta, ya uniforme en acimut
c = ax[2]
# pcolormesh con shading flat necesita bordes: 2 en acimut y n+1 en Z
TH = np.array([-180.0, 180.0])
paso = dzz[1, 0] - dzz[0, 0]
Zb = np.concatenate([dzz[:, 0] - paso / 2, [dzz[-1, 0] + paso / 2]])
M = dzz[:, 1][:, None]
im = c.pcolormesh(TH, Zb, M, cmap="viridis", shading="flat")
cb2 = fig.colorbar(im, ax=c, pad=0.02)
cb2.set_label("$D(Z)$   [kg/m$^2$ por vuelta]", fontsize=9)
c.axhline(Z_INF, color="k", lw=1.3)
c.axhline(Z_SUP, color="k", lw=1.3)
c.set_xlim(-180, 180)
c.set_ylim(870, 1425)
c.set_xticks([-180, -90, 0, 90, 180])
c.set_xlabel("acimut   [grados]")
c.set_title("(c) Dosis tras una vuelta completa\n"
            "$D(Z)=\\int\\varphi\\,d\\theta/\\omega$: uniforme en acimut por construccion", fontsize=10)
c.grid(alpha=.25, color="w")

fig.suptitle("F5 - Del mapa instantaneo a la dosis por vuelta.  "
             "El agujero es axisimetrico y el distribuidor gira a 1,7 rpm, "
             "as$\\'i$ que basta simular una posicion de la lanza.", fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.93))
p = os.path.join(A.salida, "F5_mapa_desarrollado.png")
fig.savefig(p, dpi=155)
print("escrito", p)
