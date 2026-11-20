# -*- coding: utf-8 -*-
"""Diagnóstico (solo lectura): distancias y solapes entre las piezas del brazo ASP-220 (BRAZO_V15B.step). Ejecutar con freecadcmd.
Sirve para saber qué piezas se tocan (se pueden pegar en SOLIDWORKS) y cuáles tienen holgura (en la máquina la llena la soldadura)."""
import os
import Part

HO = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho"
ENT = os.path.join(HO, r"01_DISENO_VIGENTE\integracion_R07_visual\planos\sw\fuente\BRAZO_V15B.step")
SAL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "geometria", "contactos_log.txt")
s = Part.Shape()
s.read(ENT)
S = list(s.Solids)
out = []
for i in range(len(S)):
    for j in range(i + 1, len(S)):
        bi, bj = S[i].BoundBox, S[j].BoundBox
        if bi.XMin > bj.XMax + 3 or bj.XMin > bi.XMax + 3 or bi.YMin > bj.YMax + 3 or bj.YMin > bi.YMax + 3 or bi.ZMin > bj.ZMax + 3 or bj.ZMin > bi.ZMax + 3:
            continue
        d = S[i].distToShape(S[j])[0]
        if d < 3.0:
            v = S[i].common(S[j]).Volume if d < 1e-6 else 0.0
            out.append("%2d-%2d distancia %.3f mm, solape %.2f mm3" % (i, j, d, v))
open(SAL, "w", encoding="utf-8").write("\n".join(out) + "\n")
