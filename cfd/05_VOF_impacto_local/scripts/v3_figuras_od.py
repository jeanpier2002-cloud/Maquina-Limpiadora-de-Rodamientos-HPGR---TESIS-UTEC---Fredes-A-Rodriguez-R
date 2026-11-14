#!/usr/bin/env python3
"""
CORRIDA 2 · T3/T2/T5 · Figuras de E1-OD (un panel cada una, coma decimal, sin titulo):
  OD_M_x        : empuje de la pelicula por lado M(x)/M0 frente a x/e0 (mallas N10-N40), con M0 = rho v^2 e0/2 (teorica)
  OD_tau_x      : esfuerzo cortante en la pared tau_w(x) para N5-N40 (ventana 0,3-0,5 ms*S)
  OD_dt         : cambio relativo frente a Co 0,25 en N20 (Co 0,5 y 1)
  OD_gravedad   : cambio relativo con gravedad frente al caso sin gravedad, por magnitud
Lee 02_VOF_v3/datos/E1OD_*.csv (v3_e1od_post.py). Uso: python -I v3_figuras_od.py
"""
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v3_estilo_kevin import C, ejes_coma, guardar, plt  # noqa: E402

B = "D:/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3"
D, FIG = B + "/datos", B + "/figuras"
E0 = 0.049e-3


def leer(n):
    p = f"{D}/{n}"
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.exists(p) else []


# M(x)
M = leer("E1OD_M_lineas.csv")
if M:
    fig, ax = plt.subplots()
    filas = []
    for i, n in enumerate((10, 20, 40)):
        R = sorted([r for r in M if r["caso"] == f"OD_N{n}_Co0.5" and r["ventana"] == "v1" and r["lado"] == "+"],
                   key=lambda r: float(r["x_mm"]))
        if not R:
            continue
        x = [float(r["x_mm"]) * 1e-3 / E0 for r in R]
        y = [float(r["M_sobre_M0"]) for r in R]
        ax.plot(x, y, "o-", color=C[i], label=f"N{n}")
        filas += [[f"N{n}", r["x_mm"], xx, r["M_agua_Nm"], yy, r["q_sobre_q0"]] for r, xx, yy in zip(R, x, y)]
    ax.axhline(1, color="0.3", ls="--", lw=1.2, label="M₀ = ρv²e₀/2 = 18,2 N/m (teórica, sin viscosidad)")
    # en la ventana 0,3-0,5 ms*S el frente de la pelicula esta hacia x/e0 ~ 20-35 (como x = 10 mm en E1/B4)
    ax.axvspan(20, 35, color="0.88", lw=0, label="frente de la película (no estacionario)")
    ax.set_xlabel("distancia al eje del impacto, x/e₀ (−)")
    ax.set_ylabel("M(x) / M₀ (−)")
    ax.set_ylim(0, 1.15)
    ejes_coma(ax)
    ax.legend(fontsize=9)
    guardar(fig, FIG, "OD_M_x", ["malla", "x_mm", "x_sobre_e0", "M_Nm", "M_sobre_M0", "q_sobre_q0"], filas)

# tau_w(x)
P = leer("E1OD_perfiles_pared.csv")
if P:
    fig, ax = plt.subplots()
    filas = []
    for i, n in enumerate((5, 10, 20, 40)):
        R = [r for r in P if r["caso"] == f"OD_N{n}_Co0.5"]
        if not R:
            continue
        x = np.array([float(r["x_m"]) for r in R]); t = np.array([float(r["tau_w_Pa"]) for r in R])
        o = np.argsort(x)
        sel = x[o] / E0 <= 12
        ax.plot(x[o][sel] / E0, t[o][sel] / 1e3, color=C[i], label=f"N{n}")
        filas += [[f"N{n}", xx, tt] for xx, tt in zip(x[o][sel], t[o][sel])]
    ax.set_xlabel("distancia al eje del impacto, x/e₀ (−)")
    ax.set_ylabel("esfuerzo cortante en la pared τ_w (kPa)")
    ejes_coma(ax)
    ax.legend(fontsize=10)
    guardar(fig, FIG, "OD_tau_x", ["malla", "x_m", "tau_w_Pa"], filas)

# dt
T = leer("E1OD_dt.csv")
if T:
    fig, ax = plt.subplots()
    claves = [("dp0", "p₀"), ("dF_loc1", "F/b local"), ("dtau_xr2", "τ_w (x = 0,33 mm)"), ("dh_xr2", "espesor (x = 0,33 mm)"),
              ("dM_xr2", "M (x = 0,33 mm)")]
    co = [float(r["Co"]) for r in T]
    filas = []
    for i, (k, lab) in enumerate(claves):
        y = [100 * float(r[k]) for r in T]
        ax.plot(co, y, "o-", color=C[i], label=lab)
        filas += [[lab, c, yy] for c, yy in zip(co, y)]
    ax.axhline(0, color="0.3", lw=0.8)
    ax.set_xlabel("número de Courant máximo (−), N20")
    ax.set_ylabel("cambio frente a Co = 0,25 (%)")
    ax.set_xscale("log")
    ejes_coma(ax)
    ax.set_xticks(co); ax.set_xticklabels([("%g" % c).replace(".", ",") for c in co])
    ax.legend(fontsize=9)
    guardar(fig, FIG, "OD_dt", ["magnitud", "Co", "cambio_pct"], filas)

# gravedad
G = leer("E1OD_gravedad.csv")
if G:
    casos = []
    for r in G:   # solo los casos con gravedad (el control y la asimetria entre lados van en el texto)
        c = r["caso_gravedad"]
        if c not in casos and "control" not in c and "lado" not in c:
            casos.append(c)
    mags = [("p0_Pa", "p₀"), ("F_loc1_Nm", "F/b local"), ("tau_xr2", "τ_w"), ("h_xr2_um", "espesor"),
            ("M_xr2_Nm", "M")]
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    w = 0.8 / max(len(casos), 1)
    filas = []
    for i, c in enumerate(casos):
        y = []
        for k, _ in mags:
            v = [float(r["cambio_rel"]) for r in G if r["caso_gravedad"] == c and r["magnitud"] == k]
            y.append(100 * v[0] if v else np.nan)
        ax.bar(np.arange(len(mags)) + (i - (len(casos) - 1) / 2) * w, y, width=w, color=C[i], label=c)
        filas += [[c, k, yy] for (k, _), yy in zip(mags, y)]
    ax.axhline(0, color="0.3", lw=0.8)
    ax.set_xticks(range(len(mags))); ax.set_xticklabels([l for _, l in mags], fontsize=10)
    ax.set_ylabel("cambio por la gravedad (%)")
    ax.set_xlabel("magnitud (τ_w, espesor y M en x = 0,33 mm)", fontsize=11)
    ejes_coma(ax, x=False)
    ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
    guardar(fig, FIG, "OD_gravedad", ["caso", "magnitud", "cambio_pct"], filas)
