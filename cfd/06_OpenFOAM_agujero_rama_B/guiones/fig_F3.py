#!/usr/bin/env python3
"""Figura de F3: seccion del dominio en el plano del abanico y cobertura geometrica."""
import argparse
import csv
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

P = argparse.ArgumentParser()
P.add_argument("--csv-dir", required=True)
P.add_argument("--salida", required=True)
A = P.parse_args()
os.makedirs(A.salida, exist_ok=True)

Z_INF, Z_SUP = 890.0, 1405.0
R_INF = 450.0
R_SUP = R_INF + (Z_SUP - Z_INF) / 60.0
SEMI = math.radians(25.0)

BOQ = [
    ("INT_1", 306.70, 956.822, (0.0, 1.0)),
    ("INT_2", 306.70, 1052.162, (0.0, 1.0)),
    ("INT_3", 306.70, 1147.502, (0.0, 1.0)),
    ("INT_4", 306.70, 1242.842, (0.0, 1.0)),
    ("INT_5", 306.70, 1338.182, (0.0, 1.0)),
    ("INF_INT", 400.00, 850.000, (0.9063077870366499, 0.42261826174069944)),
]
COL = {"INT_1": "#1f77b4", "INT_2": "#2ca02c", "INT_3": "#d62728",
       "INT_4": "#9467bd", "INT_5": "#8c564b", "INF_INT": "#ff7f0e"}


def r_pared(z):
    return R_INF + (z - Z_INF) / 60.0


def impacto(y0, z0, ey, ez):
    """avanza el rayo hasta cortar la pared conica; devuelve (y, z) o None"""
    t = 0.0
    for _ in range(40000):
        t += 0.25
        y, z = y0 + ey * t, z0 + ez * t
        if y >= r_pared(z):
            return y, z
        if z < 700 or z > 1600 or y > 700:
            return None
    return None


fig, ax = plt.subplots(1, 2, figsize=(13.2, 7.4),
                       gridspec_kw={"width_ratios": [1.45, 1]})

# ------------------------------------------------- (a) seccion en el plano y-z
a = ax[0]
# pared conica
a.plot([r_pared(Z_INF), r_pared(Z_SUP)], [Z_INF, Z_SUP], "k-", lw=3, zorder=5)
a.add_patch(Rectangle((r_pared(Z_INF), Z_INF), 120, Z_SUP - Z_INF,
                      facecolor="0.82", edgecolor="none", zorder=1))
a.text(495, 1150, "aro interior\ndel rodamiento", fontsize=8.5, rotation=90,
       va="center", ha="center", color="0.3")
# caras del rodamiento
for z in (Z_INF, Z_SUP):
    a.plot([r_pared(z), 500], [z, z], "k-", lw=2, zorder=5)
# lanza
a.add_patch(Rectangle((233.3, 812.7), 33.4, 1445 - 812.7,
                      facecolor="0.55", edgecolor="k", lw=.5, zorder=4))
a.text(250, 1420, "lanza\nDN25", fontsize=8, ha="center", va="top", color="w", zorder=6)
# caja del dominio
a.add_patch(Rectangle((0, 790), 500, 655, fill=False, ec="tab:blue", ls="--", lw=1.3, zorder=3))
a.text(20, 1420, "caja del dominio\n(contornos abiertos)", fontsize=8, color="tab:blue")

# abanicos
for tag, y0, z0, (ey, ez) in BOQ:
    c = COL[tag]
    a.plot([y0], [z0], "o", ms=5, color=c, zorder=7)
    for s in (-1, 0, 1):
        al = s * SEMI
        # rotar el eje dentro del plano
        ry = ey * math.cos(al) - ez * math.sin(al)
        rz = ey * math.sin(al) + ez * math.cos(al)
        p = impacto(y0, z0, ry, rz)
        if p is None:
            p = (y0 + ry * 250, z0 + rz * 250)
            a.plot([y0, p[0]], [z0, p[1]], "-", color=c, lw=.9, alpha=.35, zorder=6)
        else:
            a.plot([y0, p[0]], [z0, p[1]], "-", color=c, lw=1.1, alpha=.8, zorder=6)
    a.text(y0 + 10, z0 - 14, tag, fontsize=7.5, ha="left", va="top", color=c,
           zorder=9, bbox=dict(fc="white", ec="none", alpha=.75, pad=.8))

a.set_xlim(0, 560)
a.set_ylim(760, 1470)
a.set_xlabel("radio  r  [mm]")
a.set_ylabel("cota  Z  [mm]")
a.set_title("(a) Seccion del dominio en el plano del abanico (radial-vertical)\n"
            "agujero conico 1:30: R450 en Z890 -> R458,58 en Z1405", fontsize=10)
a.grid(alpha=.3)
a.set_aspect("equal")

# ------------------------------------------------- (b) cobertura en la cota Z
b = ax[1]
cob = {}
with open(os.path.join(A.csv_dir, "cobertura_geometrica.csv")) as f:
    for r in csv.DictReader(f):
        if r["z_min_mm"]:
            cob[r["tag"]] = (float(r["z_min_mm"]), float(r["z_max_mm"]),
                             float(r["porcentaje_del_abanico_en_el_agujero"]))
orden = ["INF_INT", "INT_1", "INT_2", "INT_3", "INT_4", "INT_5"]
for i, tag in enumerate(orden):
    if tag not in cob:
        continue
    z0, z1, frac = cob[tag]
    b.barh(i, z1 - z0, left=z0, height=0.62, color=COL[tag], alpha=.85)
    b.text(z1 + 6, i, "%.0f mm\n%.1f %% del abanico" % (z1 - z0, frac),
           fontsize=7.5, va="center")
b.axvline(Z_INF, color="k", ls="-", lw=1.5)
b.axvline(Z_SUP, color="k", ls="-", lw=1.5)
b.text(Z_INF - 6, 5.6, "Z890\ncara inferior", fontsize=7.5, ha="right")
b.text(Z_SUP + 6, 5.6, "Z1405\ncara superior", fontsize=7.5, ha="left")
b.set_yticks(range(len(orden)))
b.set_yticklabels(orden, fontsize=9)
b.set_xlabel("cota  Z  [mm]")
b.set_xlim(820, 1520)
b.set_ylim(-0.7, 6.1)
b.set_title("(b) Tramo del agujero que alcanza cada abanico\n"
            "las cinco INT cubren el 99,99 % de la altura; INF_INT solo 20 mm", fontsize=10)
b.grid(alpha=.3, axis="x")

fig.suptitle("F3 - Dominio de aire del agujero del rodamiento SKF 241/900  "
             "(geometria R05, eje vertical)", fontsize=11.5)
fig.tight_layout(rect=(0, 0, 1, 0.94))
p = os.path.join(A.salida, "F3_dominio_y_cobertura.png")
fig.savefig(p, dpi=155)
print("escrito", p)
