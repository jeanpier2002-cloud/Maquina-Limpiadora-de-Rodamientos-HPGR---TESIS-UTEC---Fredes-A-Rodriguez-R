# -*- coding: utf-8 -*-
"""Cargas del brazo A en el sistema del STEP del brazo (x = X − 300,75; y = Z − 1740; z = −Y; mm y N), para SOLIDWORKS.
Chorros: reacción F = m_dot · v opuesta a cada chorro (boquillas O7+C2, LAT_1 con −4° del Caso 2), como en r07_reaccion_chorros_U.py.
Accidental: 1 000 N a Z1400 en el eje del brazo (R03 y B1), fuera del plano (tangencial, ±z) y en el plano (radial hacia afuera, +x)."""
import csv
import json
import math
from pathlib import Path

HO = Path(r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho")
BOQ = HO / "01_DISENO_VIGENTE/cfd/CFD_ANSYS/02_ANALISIS/cara_inferior/alternativas_2026-10-07/PAQUETE_JEAN_O7_C2/boquillas_O7_C2.json"
SAL = Path(__file__).resolve().parents[1] / "geometria" / "cargas_brazo_A.csv"
X0, Z0 = 300.75, 1740.0
X_ARM = 599.39


def rot(X, Y, Z):
    return (X, Z, -Y)


def a_step(X, Y, Z):
    return (X - X0, Z - Z0, -Y)


d = json.loads(BOQ.read_text(encoding="utf-8"))
filas = []
for k, x in d["boquillas"].items():
    if x["ramal"] != "A":
        continue
    e = list(x["eje"])
    if k.startswith("LAT_1"):
        a = math.radians(4.0)
        e = [-math.cos(a), 0.0, -math.sin(a)]
    F = x["mdot_kg_s"] * x["v_m_s"]
    R = [-F * c for c in e]
    p = [v * 1000 for v in x["vertice_m"]]
    filas.append(["CHORRO_" + k, *a_step(*p), *rot(*R)])
filas.append(["ACC_FUERA_PLANO", X_ARM, 1400.0 - Z0, 0.0, 0.0, 0.0, 1000.0])
filas.append(["ACC_EN_PLANO", X_ARM, 1400.0 - Z0, 0.0, 1000.0, 0.0, 0.0])
with SAL.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["nombre", "x_mm", "y_mm", "z_mm", "Fx_N", "Fy_N", "Fz_N"])
    for r in filas:
        w.writerow([r[0]] + ["%.4f" % v for v in r[1:]])
for r in filas:
    print("%-20s (%.1f; %.1f; %.1f) F (%.3f; %.3f; %.3f)" % tuple(r))
s = [sum(r[i] for r in filas if r[0].startswith("CHORRO")) for i in (4, 5, 6)]
print("suma de chorros (N, ejes del STEP):", [round(v, 3) for v in s])
