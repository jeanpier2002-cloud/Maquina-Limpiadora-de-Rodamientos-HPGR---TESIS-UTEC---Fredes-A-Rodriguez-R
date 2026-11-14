#!/usr/bin/env python3
"""
CORRIDA 3 · T3 · Complemento de la prueba de fidelidad: compara la MASCARA que usa combinar_kpi.py
(cociente obst/libre agregado a bandas de 10 mm, funcion mascara()) y la marginal en z (suma en theta), entre
el kit y la reproduccion de LAT_1_A horizontal. Las matrices crudas difieren celda a celda cuando un rayo cae
justo en un borde de 0,5 grados (rotor en pasos de 0,5 grados y LAT_1 apuntando a theta = 0).
Uso: python -I -B r3_t3_fidelidad_cociente.py  (anade lineas a 01_ENTRADA/mascaras/T3_log.txt)
"""
import sys

import numpy as np

BASE = "D:/CFD_Redosado/CORRIDA_3_O7C2"
sys.path.insert(0, BASE + "/03_FLUENT/scripts/kit")
from combinar_kpi import bandas, mascara  # noqa: E402

K = np.load(BASE + "/03_FLUENT/scripts/kit/K1_O7C2_mascaras.npz")
F = np.load(BASE + "/01_ENTRADA/mascaras/T3_fidelidad_LAT1_horizontal_mascaras.npz")
N = np.load(BASE + "/01_ENTRADA/mascaras/K1_O7C2_Caso2_mascaras.npz")
out = []
for sup in ("od",):
    e = bandas(sup, 0.010)
    mk, mf = mascara(K, ["LAT_1_A"], sup, e), mascara(F, ["LAT_1_A"], sup, e)
    mn = mascara(N, ["LAT_1_A"], sup, e)
    out.append("cociente %s LAT_1_A: max|kit - reproduccion| = %.3e ; min/max kit %.4f/%.4f ; Caso 2 min/max %.4f/%.4f" % (
        sup, np.nanmax(np.abs(mk - mf)), np.nanmin(mk), np.nanmax(mk), np.nanmin(mn), np.nanmax(mn)))
    k = "LAT_1_A__%s__libre" % sup
    zk, zf = K[k].sum(1), F[k].sum(1)
    out.append("marginal en z (suma en theta) %s: max|dif|/max = %.3e" % (k, np.abs(zk - zf).max() / zk.max()))
open(BASE + "/01_ENTRADA/mascaras/T3_log.txt", "a", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
