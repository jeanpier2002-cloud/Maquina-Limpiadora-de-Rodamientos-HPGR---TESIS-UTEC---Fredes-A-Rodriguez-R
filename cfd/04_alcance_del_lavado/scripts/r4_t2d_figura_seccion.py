#!/usr/bin/env python3
"""
CORRIDA 4 · T2d · Figura del corte meridiano del rodamiento (perfiles medidos del STEP) con la ventana, los rodillos de
cada hilera (en el plano de su eje) y rayos de ejemplo de SUP_1_A y SUP_2_A (plano central del abanico, rotor en phi = 0 y
phi = medio paso), trazados con r4_t2_cavidad_n1 (N1: rectos, sin rebote). Un panel.
Salida: 02_CAVIDAD_N1/figuras/T2_seccion_rayos.png (+csv). Uso: python -I -B r4_t2d_figura_seccion.py
"""
import json
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import r4_t2_cavidad_n1 as T  # noqa: E402
from r4_estilo_kevin import C, guardar, plt  # noqa: E402

B = json.load(open(T.JSON_BOQ, encoding="utf-8"))["boquillas"]
fig, ax = plt.subplots(figsize=(6.4, 6.4))
x = np.linspace(0, T.LB, 1031)
Z = T.Z_TOP * 1000 - x
# aros (relleno gris)
ax.fill_betweenx(Z, T.r_oi(x), 710, color="0.82", lw=0, label="aros (perfil medido del STEP)")
ri_bore = 450.0 + (T.LB - x) / 60.0
ax.fill_betweenx(Z, ri_bore, T.r_io(x), color="0.82", lw=0)
# rodillos en el plano de su eje
s = np.linspace(0, T.L_ROD, 200)
rh = T.rho_s(s)
for f, (x1, ax_) in enumerate(((T.X1_T, T.AX), (T.X1_B, -T.AX))):
    eo = np.array([-T.AR if f == 0 else T.AR, T.AX])
    xs = x1 + s * ax_; rs = T.R1 + s * T.AR
    P1 = np.column_stack([xs + rh * eo[0], rs + rh * eo[1]]); P2 = np.column_stack([xs - rh * eo[0], rs - rh * eo[1]])
    poly = np.vstack([P1, P2[::-1]])
    ax.fill(poly[:, 1], T.Z_TOP * 1000 - poly[:, 0], fc=C[1] if f == 0 else C[2], alpha=0.35, lw=1.0,
            ec=C[1] if f == 0 else C[2], label="rodillo hilera superior (plano θ = 0)" if f == 0 else "rodillo hilera inferior (plano θ = ½ paso)")
# ventana
for zf in (T.Z_TOP * 1000, T.Z_BOT * 1000):
    ax.plot([T.W_IN, T.W_OUT], [zf, zf], color=C[3], lw=3, solid_capstyle="butt")
ax.text(569.5, T.Z_TOP * 1000 + 6, "ventana", color=C[3], ha="center", fontsize=10)
# rayos de ejemplo
datos = []
for nb, col in (("SUP_1_A", C[0]), ("SUP_2_A", C[4])):
    P0, D0, m0 = T.abanico(B[nb], 21, n_fuera=1, ang_fuera=0.0)
    for fase, ls in ((0.0, "-"), (T.PASO / 2, "--")):
        dest, tt, H = T.RR.trazar(P0, D0, obst=False)
        rH = np.hypot(H[:, 0], H[:, 1]) * 1000
        w_ = (dest == "sup") & (rH >= T.W_IN) & (rH <= T.W_OUT)
        Pb, Ub = T.a_marco_rodamiento(H[w_], D0[w_]); Pb = Pb - Ub
        cod, tc = T.marchar(Pb, Ub, -fase, False, True)
        Q = Pb + tc[:, None] * Ub
        V = np.array(B[nb]["vertice_m"]) * 1000
        for q, c_ in zip(Q, cod):
            rq = math.hypot(q[1], q[2]); zq = T.Z_TOP * 1000 - q[0]
            ax.plot([math.hypot(V[0], V[1]), rq], [V[2], zq], color=col, lw=0.8, ls=ls, alpha=0.9)
            datos.append([nb, "%.3f" % fase, "%.1f" % rq, "%.1f" % zq, int(c_)])
    ax.plot([math.hypot(B[nb]["vertice_m"][0], B[nb]["vertice_m"][1]) * 1000], [B[nb]["vertice_m"][2] * 1000], "v", color=col,
            ms=9, label="%s" % nb)
ax.set_xlim(440, 1000); ax.set_ylim(860, 1610)
ax.set_aspect("equal")
ax.set_xlabel("radio (mm)")
ax.set_ylabel("altura z (mm)")
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: ("%g" % v).replace(".", ",")))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: ("%g" % v).replace(".", ",")))
ax.plot([], [], color="0.3", ls="-", lw=0.8, label="rayo con el rotor en θ = 0")
ax.plot([], [], color="0.3", ls="--", lw=0.8, label="rayo con el rotor en θ = ½ paso")
ax.legend(fontsize=7.5, loc="lower right", framealpha=0.9, frameon=True)
guardar(fig, T.OUT + "/figuras", "T2_seccion_rayos", ["boquilla", "fase_deg", "r_impacto_mm", "z_impacto_mm", "codigo"], datos)
