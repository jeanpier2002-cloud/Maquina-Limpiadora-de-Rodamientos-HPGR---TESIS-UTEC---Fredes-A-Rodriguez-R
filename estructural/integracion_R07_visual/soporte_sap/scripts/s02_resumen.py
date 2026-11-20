# -*- coding: utf-8 -*-
"""Soporte superior (R07): resumen comparativo de los casos SAP2000 (resultados/*.json de s01) -> resultados/RESUMEN_CASOS.csv.
Indicadores: masa de barras, D/C maximo AISC 360-16 (y donde), frecuencias, desplazamiento horizontal del cojinete superior
(S1 operacion; S2 accidental 1 000 N), flecha vertical de vigas a mitad de luz (S1, respecto de los apoyos en columnas) y
reacciones de las bases (compresion y levantamiento maximos)."""
import csv
import glob
import json
import math
import os
import sys

R = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\soporte_sap\resultados"
filas = []
for f in sorted(glob.glob(R + r"\*.json")):
    d = json.load(open(f, encoding="utf-8"))
    nud, des = d["nudos"], d["despl"]
    def punto(x, y, z):
        return min(nud, key=lambda k: (nud[k][0] - x) ** 2 + (nud[k][1] - y) ** 2 + (nud[k][2] - z) ** 2)
    ub, lb = punto(0, 0, 3450), punto(0, 0, 2850)
    hor = lambda c, p: math.hypot(des[c][p][0], des[c][p][1])
    s2 = max(hor(c, ub) for c in des if c.startswith("S2"))
    mid = punto(0, d["yc"], d["zViga"]); ext = punto(d["xc"], d["yc"], d["zViga"])
    flecha = abs(des["S1"][mid][2] - des["S1"][ext][2])
    rz = [r[3] for c, rs in d["reacciones"].items() for r in rs]
    dis = max(d["diseno"], key=lambda r: r[1]) if d["diseno"] else ["", 0, "", ""]
    sec = {b["n"]: b["sec"] for b in d["barras"]}
    fr = d["frecuencias_Hz"]
    filas.append({"caso": d["caso"], "xc_mm": d["xc"], "columna": d["col"], "viga": d["viga"], "celosia": d["lac"],
                  "masa_barras_kg": round(d["masa_kg"], 1), "DC_max": round(dis[1], 3), "DC_barra": sec.get(dis[0], dis[0]), "DC_combo": dis[2],
                  "f1_Hz": round(fr[0], 2), "f2_Hz": round(fr[1], 2), "f3_Hz": round(fr[2], 2),
                  "cojinete_sup_S1_mm": round(hor("S1", ub), 3), "cojinete_sup_S2_max_mm": round(s2, 3),
                  "cojinete_inf_S2_max_mm": round(max(hor(c, lb) for c in des if c.startswith("S2")), 3),
                  "flecha_viga_S1_mm": round(flecha, 3), "L_sobre_flecha": round(2 * d["xc"] / max(flecha, 1e-9)),
                  "reac_compresion_max_N": round(max(rz), 0), "reac_levantamiento_max_N": round(-min(min(rz), 0), 0)})
with open(R + r"\RESUMEN_CASOS.csv", "w", newline="", encoding="utf-8") as fo:
    w = csv.DictWriter(fo, fieldnames=list(filas[0].keys())); w.writeheader(); w.writerows(filas)
for f in filas:
    print(" | ".join(f"{k}={v}" for k, v in f.items()))
