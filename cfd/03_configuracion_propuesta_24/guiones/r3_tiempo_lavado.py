#!/usr/bin/env python3
"""
CORRIDA 3 · T10 · Tiempo de lavado por superficie con el diseno O7+C2 (+ Caso 2). Copia adaptada de
v3_tiempo_lavado.py (CORRIDA 2): misma formula y mismos escenarios, con el OD y la cara inferior del CFD nuevo.

Metodo (CANDIDATO; el CFD no simula la grasa):
  T_lavado = D_req / (D / T_vuelta) ; N_vueltas = T_lavado / T_vuelta ; T_vuelta = 35,294 s (1,7 rpm, HIPOTESIS)
  Gobierna la peor celda (D_min de bandas de 10 mm, con obstaculos), no la media.
  D_req = 65 / 183 / 305 kg/m2: DATO EXTERNO PENDIENTE (mismas anclas que la Corrida 2).
  Tiempo del equipo = la superficie mas lenta (regla de Jean del 24/10: la cara inferior se incluye).
Fuentes de D: OD y cara inferior O7+C2 = el mejor valor disponible de esta tanda (A+B explicito R3_02+R3_03 si existe;
si no, R3_02 con S9); cara superior (Caso 3) y agujero NO se re-simulan (G7, como la Corrida 2); Caso Base de la
cara inferior (G7) como referencia.
Salidas: 03_FLUENT/resultados/T10_tiempo_lavado.csv, T10_tiempo_lavado_equipo.csv, figuras/T10_tiempo_lavado_O7C2.png
Uso: python -I -B r3_tiempo_lavado.py
"""
import csv
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from r3_estilo_kevin import C, ejes_coma, guardar, plt  # noqa: E402

FL = "D:/CFD_Redosado/CORRIDA_3_O7C2/03_FLUENT"
KPI = FL + "/resultados/KPI"
T = 35.294
DREQ = (65, 183, 305)


def resumen(caso):
    p = "%s/%s/%s_resumen.csv" % (KPI, caso, caso)
    if not os.path.exists(p):
        return None
    return {(r["superficie"], r["variante"]): r for r in csv.DictReader(open(p, encoding="utf-8"))}


fuente = None
for caso, nom in (("R3_02_03_AB", "Caso 2 A+B explícito (R3_02 + R3_03)"), ("R3_02_caso2", "Caso 2, ramal A con S9 (R3_02)")):
    R = resumen(caso)
    if R:
        fuente = (caso, nom, R)
        break
if fuente is None:
    raise SystemExit("no hay KPI de R3_02 todavia")
caso, nom, R = fuente
S = [("OD", "O7+C2 + Caso 2 (%s)" % caso, float(R[("od", "obst_10mm")]["D_media"]), float(R[("od", "obst_10mm")]["D_min"])),
     ("Cara inferior", "O7+C2 (%s)" % caso, float(R[("cara_inf", "obst_10mm")]["D_media"]),
      float(R[("cara_inf", "obst_10mm")]["D_min"])),
     ("Cara superior", "Caso 3 (G7; no cambia)", 21.82, 14.03),
     ("Agujero", "Base = Caso 3 (G7; no cambia)", 18.72, 11.52),
     ("Cara inferior (diseño anterior)", "Caso Base (G7)", 5.46, 2.93)]
filas = []
for sup, c, D, Dm in S:
    for Dr in DREQ:
        filas.append([sup, c, D, Dm, Dr, Dr / D, Dr / D * T / 60, Dr / Dm, Dr / Dm * T / 60])
with open(FL + "/resultados/T10_tiempo_lavado.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["superficie", "caso", "D_media", "D_min_10mm", "D_req", "vueltas_media", "min_media",
                "vueltas_peor_celda", "min_peor_celda"])
    w.writerows([[x if isinstance(x, str) else ("%.4g" % x) for x in r] for r in filas])
equipo = []
for Dr in DREQ:
    sel = [r for r in filas if r[4] == Dr and not r[0].startswith("Cara inferior (")]
    m = max(sel, key=lambda r: r[8])
    sin_inf = max([r for r in sel if r[0] != "Cara inferior"], key=lambda r: r[8])
    equipo.append(["O7+C2 + Caso 2", Dr, m[0], m[8], m[7], sin_inf[0], sin_inf[8]])
with open(FL + "/resultados/T10_tiempo_lavado_equipo.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["caso", "D_req", "superficie_que_manda", "min_equipo", "vueltas_equipo", "sin_cara_inferior_manda",
                "min_sin_cara_inferior"])
    w.writerows([[x if isinstance(x, str) else ("%.4g" % x) for x in r] for r in equipo])
fig, ax = plt.subplots()
x = np.linspace(20, 330, 200)
datos = []
for i, (sup, c, D, Dm) in enumerate(S):
    ls = ":" if sup.startswith("Cara inferior (") else "-"
    ax.plot(x, x / Dm * T / 60, color=C[i], ls=ls, label="%s (peor celda)" % sup)
    datos += [[sup, c, Dr, Dr / Dm * T / 60, Dr / D * T / 60] for Dr in DREQ]
for Dr in DREQ:
    ax.axvline(Dr, color="0.5", lw=0.8, ls=":")
ax.set_xlabel("dosis acumulada que exige la grasa, D_req (kg·m⁻²)")
ax.set_ylabel("tiempo de lavado (min)")
ax.set_xlim(20, 330)
ax.set_ylim(0, 65)
ejes_coma(ax)
ax.legend(fontsize=9, loc="upper left")
guardar(fig, FL + "/figuras", "T10_tiempo_lavado_O7C2", ["superficie", "caso", "D_req", "min_peor_celda", "min_media"], datos)
print("fuente OD y cara inferior:", nom)
for r in filas:
    print("%-32s %-40s D %6.2f Dmin %6.2f D_req %3d -> peor celda %6.1f min (%5.1f vueltas) | media %5.1f min" % (
        r[0], r[1], r[2], r[3], r[4], r[8], r[7], r[6]))
for r in equipo:
    print("equipo D_req %3d: manda %-13s %6.1f min (%5.1f vueltas); sin la cara inferior: %-13s %6.1f min" % tuple(r[1:]))
