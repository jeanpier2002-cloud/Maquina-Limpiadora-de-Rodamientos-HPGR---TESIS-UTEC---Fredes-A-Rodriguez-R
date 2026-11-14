#!/usr/bin/env python3
"""Figuras de F2: verificacion de la huella, diametros que llegan, y masa suspendida."""
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

ETIQ = {
    "V1_ico_absorbe":  "V1  aire congelado, 300 um",
    "V2_aco_absorbe":  "V2  aire acoplado, 300 um",
    "V3_ico_adhiere":  "V3  congelado, pared adhiere",
    "V4_ico_rebota":   "V4  congelado, pared rebota",
    "V5_ico_RR":       "V5  congelado, Rosin-Rammler",
    "V6_aco_RR":       "V6  acoplado, RR (minpp = 1)",
    "V7_aco_RR_minpp": "V7  acoplado, RR (minpp = 1e-6)",
}
COL = {"V1_ico_absorbe": "#1f77b4", "V2_aco_absorbe": "#d62728",
       "V5_ico_RR": "#ff7f0e", "V6_aco_RR": "#9467bd", "V7_aco_RR_minpp": "#2ca02c"}


def leer(nombre):
    with open(os.path.join(A.csv_dir, nombre)) as f:
        return list(csv.DictReader(f))


# =========================================================== figura 1
fig, ax = plt.subplots(1, 3, figsize=(15.5, 4.7))

# --- (a) huella acumulada frente a la prediccion analitica -----------------
ac = defaultdict(list)
for r in leer("F2_huella_acumulada.csv"):
    ac[r["variante"]].append((float(r["x_mm"]), float(r["fraccion_masa_acumulada"]),
                              float(r["prediccion_uniforme_por_angulo"])))
d = np.array(sorted(ac["V1_ico_absorbe"]))
ax[0].plot(d[:, 0], d[:, 2], "k--", lw=2,
           label="prediccion analitica\n$F(x)=(\\arctan(x/Y)+25\\degree)/50\\degree$")
for v in ["V1_ico_absorbe", "V2_aco_absorbe", "V7_aco_RR_minpp"]:
    if v in ac:
        d = np.array(sorted(ac[v]))
        ax[0].plot(d[:, 0], d[:, 1], "-", color=COL[v], lw=1.5, label=ETIQ[v])
ax[0].set_xlabel("posicion a lo largo del abanico  [mm]")
ax[0].set_ylabel("fraccion acumulada de la masa depositada")
ax[0].set_title("(a) La huella sale donde la geometria manda\n"
                "desviacion maxima 0,016 = 1/60 = la discretizacion en rayos", fontsize=9.5)
ax[0].legend(fontsize=7.5, loc="upper left")
ax[0].grid(alpha=.3)

# --- (b) perfil de la huella por bins, contra el analitico -----------------
MDOT = 0.149244074  # kg/s
BIN = 10.0          # mm
h = defaultdict(list)
for r in leer("F2_huella.csv"):
    h[r["variante"]].append((float(r["x_mm"]), float(r["mdot_bin_kg_s"])))
Y, SEMI = 147.8, np.radians(25.0)
xx = np.linspace(-68.9, 68.9, 400)
ax[1].plot(xx, Y / (2 * SEMI * (Y ** 2 + xx ** 2)) * MDOT * 1e3 * BIN, "k--", lw=2.2,
           label="analitico: masa uniforme\npor unidad de angulo")
for v in ["V1_ico_absorbe", "V2_aco_absorbe", "V7_aco_RR_minpp", "V5_ico_RR"]:
    if v not in h:
        continue
    d = np.array(sorted(h[v]))
    ax[1].plot(d[:, 0], d[:, 1] * 1e3, "-o", ms=3.5, color=COL[v], lw=1.4, label=ETIQ[v])
for s_ in (-68.92, 68.92):
    ax[1].axvline(s_, ls=":", c="k", lw=1)
ax[1].annotate("el zigzag no es ruido: son 4 o 5\nde los 60 rayos por bin de 10 mm",
               xy=(-15, 13.0), xytext=(-66, 14.6), fontsize=7.5,
               arrowprops=dict(arrowstyle="->", lw=.8))
ax[1].set_xlabel("posicion a lo largo del abanico  [mm]\n(= vertical; en la pared del agujero es la cota Z)")
ax[1].set_ylabel("caudal depositado por bin de 10 mm  [g/s]")
ax[1].set_title("(b) Perfil de la huella a 143,3 mm\n"
                "la resolucion la limitan los 60 rayos, no la malla", fontsize=9.5)
ax[1].legend(fontsize=7, loc="lower center")
ax[1].grid(alpha=.3)
ax[1].set_ylim(6.5, 16)

# --- (c) diametros que llegan ---------------------------------------------
d2 = defaultdict(list)
for r in leer("F2_diametros_impacto.csv"):
    d2[r["variante"]].append((float(r["d_um"]), float(r["fraccion_de_masa"])))
for v in ["V5_ico_RR", "V6_aco_RR", "V7_aco_RR_minpp"]:
    if v in d2:
        d = np.array(sorted(d2[v]))
        ax[2].plot(d[:, 0], d[:, 1], "-o", ms=3, color=COL[v], lw=1.5, label=ETIQ[v])
ax[2].axvline(374.7, ls="--", c="grey", lw=1.2)
ax[2].annotate("corte silencioso en 375 um\npor minParticlesPerParcel = 1",
               xy=(374.7, 0.045), xytext=(415, 0.062), fontsize=7.5,
               arrowprops=dict(arrowstyle="->", lw=.8))
ax[2].axvline(630.2, ls=":", c="k", lw=1.2)
ax[2].text(575, 0.004, "maximo de\nla tabla\n630 um", fontsize=7.5)
ax[2].axvline(72.5, ls="-.", c="#ff7f0e", lw=1.2)
ax[2].annotate("con aire congelado nada\npor debajo de 72 um llega",
               xy=(72.5, 0.008), xytext=(130, 0.022), fontsize=7.5, color="#b35900",
               arrowprops=dict(arrowstyle="->", lw=.8, color="#b35900"))
ax[2].set_xlabel("diametro de la gota que llega a la pared  [$\\mu$m]")
ax[2].set_ylabel("fraccion de la masa depositada")
ax[2].set_title("(c) Que parte de la Rosin-Rammler llega de verdad", fontsize=9.5)
ax[2].legend(fontsize=7.5, loc="upper right", framealpha=.95)
ax[2].grid(alpha=.3)

fig.suptitle("F2 piloto - una boquilla H3/8U-5020 contra placa plana a 143,3 mm   "
             "(9,1177 L/min | 27,11 m/s | abanico 50$\\degree$ | malla 55 500 celdas)",
             fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.93))
p1 = os.path.join(A.salida, "F2_verificacion_huella.png")
fig.savefig(p1, dpi=155)
print("escrito", p1)

# =========================================================== figura 2
fig2, ax2 = plt.subplots(figsize=(7.6, 4.8))
serie = defaultdict(list)
for r in leer("F2_masa_en_vuelo.csv"):
    serie[r["variante"]].append((float(r["t_s"]), float(r["masa_kg"])))
for v in ["V1_ico_absorbe", "V2_aco_absorbe", "V5_ico_RR", "V6_aco_RR", "V7_aco_RR_minpp"]:
    if v not in serie:
        continue
    s = np.array(sorted(serie[v]))
    ax2.plot(s[:, 0] * 1e3, s[:, 1] * 1e6, lw=1.8, color=COL[v], label=ETIQ[v])
ax2.annotate("aire congelado + gotas finas:\nnunca alcanza regimen,\nlas finas quedan flotando",
             xy=(44, 1215), xytext=(11, 1080), fontsize=8.5, color="#b35900",
             arrowprops=dict(arrowstyle="->", lw=1, color="#b35900"))
ax2.set_xlabel("tiempo  [ms]")
ax2.set_ylabel("masa de agua suspendida en el dominio  [mg]")
ax2.set_title("El criterio que decide el solver:\nsolo el aire acoplado llega a regimen estacionario", fontsize=10)
ax2.legend(fontsize=8, loc="lower right", framealpha=.75)
ax2.set_ylim(0, 1450)
ax2.grid(alpha=.3)
fig2.tight_layout()
p2 = os.path.join(A.salida, "F2_masa_en_vuelo.png")
fig2.savefig(p2, dpi=155)
print("escrito", p2)
