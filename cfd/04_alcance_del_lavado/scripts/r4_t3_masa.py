#!/usr/bin/env python3
"""
CORRIDA 4 · T3 · Reparto de la masa de grasa: cavidad frente a superficies externas (M9). Escenarios PARAMETRICOS [SIN FUENTE].
NO predice remocion: solo dimensiona que significa «casi toda la grasa».
  V_libre = integral_0^515 pi (r_oi^2 - r_io^2) dx  -  V_rodillos (2 x 23, volumen medido con FreeCAD en step_medicion.json).
  Sin jaula (no esta en el STEP): V_libre es COTA SUPERIOR del volumen que puede ocupar la grasa.
  M_cav = f_llenado x V_libre x rho_grasa, f = 30 / 50 / 100 % [SIN FUENTE]; rho = 0,9 g/cm3 [SIN FUENTE] (las fichas SKF
  LGEV2/LGHP2/LGMT2 de METRICA_GRASA/papers no traen densidad).
  M_ext = S_ref,1 x e x rho, S_ref,1 = 5,6625 m2 (prompt; T1 mide 5,638 m2), e = 0,1 / 0,5 / 1 mm [SIN FUENTE].
Salida: 06_REDACCION/../04_PALANCAS? -> 02_CAVIDAD_N1/T3_reparto_masa.csv. Uso: python -I -B r4_t3_masa.py
"""
import csv
import json
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import r4_t2_cavidad_n1 as T  # noqa: E402

R = json.load(open(T.OUT + "/step_medicion.json"))
x = np.linspace(0, T.LB, 20601)
anillo = np.pi * (T.r_oi(x) ** 2 - T.r_io(x) ** 2)
V_entre = float(((anillo[1:] + anillo[:-1]) * 0.5 * np.diff(x)).sum())     # mm3
V_rod = sum(s["vol_mm3"] for s in R["solidos"] if s["i"] in (2, 3))
V_libre = V_entre - V_rod
RHO = 0.9e-6        # kg/mm3 (0,9 g/cm3) [SIN FUENTE]
S_EXT = 5.6625e6    # mm2
filas = []
for f in (0.30, 0.50, 1.00):
    Mc = f * V_libre * RHO
    for e in (0.1, 0.5, 1.0):
        Me = S_EXT * e * RHO
        filas.append(["%.2f" % f, "%.1f" % e, "%.3f" % (V_libre * 1e-6), "%.2f" % Mc, "%.2f" % Me, "%.1f" % (100 * Mc / (Mc + Me))])
with open(T.OUT + "/T3_reparto_masa.csv", "w", newline="", encoding="utf-8") as fo:
    w = csv.writer(fo)
    w.writerow(["f_llenado", "espesor_ext_mm", "V_libre_dm3", "M_cavidad_kg", "M_externa_kg", "pct_masa_en_cavidad"])
    w.writerows(filas)
print("V entre aros %.2f dm3 | V rodillos %.2f dm3 | V libre (sin jaula) %.2f dm3" % (V_entre * 1e-6, V_rod * 1e-6, V_libre * 1e-6))
for r in filas:
    print(r)
