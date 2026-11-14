#!/usr/bin/env python3
"""
CORRIDA 3 · T3 · Mascaras N1 de obstaculos (PAD, topes, vigas) para el Caso 2 (LAT_1_A/B a -4 grados).

1. Prueba de fidelidad: rayos_r05.py (copia del kit, sin cambios) sobre abanico_LAT_1_A.csv de G3_A_base_v3
   (LAT_1 horizontal, SOLO LECTURA) debe reproducir las matrices LAT_1_A__*__libre/obst de K1_O7C2_mascaras.npz.
2. Mascaras nuevas: rayos_r05.py --dphi 0.5 sobre abanico_LAT_1_A.csv (caso2_A) y abanico_LAT_1_B.csv (caso2_B)
   generados en T2 con el mismo generador.
3. Ensamblado: K1_O7C2_Caso2_mascaras.npz = K1_O7C2_mascaras.npz del kit con LAT_1_A/B sustituidas (misma
   convencion de claves <boq>__<sup>__libre/obst y edges__<sup>, como ensamblar_mascaras.ps1 del kit).
   Se comprueba que las demas claves quedan identicas.
Salidas: 01_ENTRADA/mascaras/ (npz, reparto y K1 de rayos_r05, T3_log.txt)
Uso: python -I -B r3_t3_mascaras.py
"""
import os
import subprocess
import sys

import numpy as np

BASE = "D:/CFD_Redosado/CORRIDA_3_O7C2"
SC = BASE + "/03_FLUENT/scripts/kit"
OUT = BASE + "/01_ENTRADA/mascaras"
KIT_NPZ = SC + "/K1_O7C2_mascaras.npz"
G3_LAT1 = "D:/CFD03_run/G3/G3_A_base_v3/abanico_LAT_1_A.csv"
os.makedirs(OUT, exist_ok=True)
log = []


def rayos(tablas, caso):
    cmd = [sys.executable, "-I", "-B", SC + "/rayos_r05.py", "--tablas", *tablas, "--salida", OUT, "--caso", caso,
           "--dphi", "0.5"]
    log.append("CMD " + subprocess.list2cmdline(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    log.append(r.stdout.strip())
    if r.returncode:
        raise SystemExit(r.stderr)
    return np.load(OUT + "/%s_mascaras.npz" % caso)


K = np.load(KIT_NPZ)
# 1. fidelidad
F = rayos([G3_LAT1], "T3_fidelidad_LAT1_horizontal")
for sup in ("od", "sup", "cara_inf", "agujero"):
    for t in ("libre", "obst"):
        k = "LAT_1_A__%s__%s" % (sup, t)
        a, b = F[k], K[k]
        d = np.abs(a - b).max() / max(np.abs(b).max(), 1e-300)
        log.append("fidelidad %-26s max|dif|/max = %.3e  (suma %.6e frente a %.6e)" % (k, d, a.sum(), b.sum()))
# 2. Caso 2
NA = rayos([BASE + "/01_ENTRADA/inyecciones/caso2_A/abanico_LAT_1_A.csv"], "T3_LAT1_A_m4")
NB = rayos([BASE + "/01_ENTRADA/inyecciones/caso2_B/abanico_LAT_1_B.csv"], "T3_LAT1_B_m4")
# 3. ensamblado
nuevo = {}
for k in K.files:
    if k.startswith("LAT_1_A__"):
        nuevo[k] = NA[k]
    elif k.startswith("LAT_1_B__"):
        nuevo[k] = NB[k]
    else:
        nuevo[k] = K[k]
for k in ("od", "sup", "cara_inf", "agujero"):
    assert np.array_equal(NA["edges__" + k], K["edges__" + k]), "bordes distintos en " + k
dst = OUT + "/K1_O7C2_Caso2_mascaras.npz"
np.savez_compressed(dst, **nuevo)
Z = np.load(dst)
iguales = sum(np.array_equal(Z[k], K[k]) for k in K.files if not k.startswith(("LAT_1_A__", "LAT_1_B__")))
otras = sum(1 for k in K.files if not k.startswith(("LAT_1_A__", "LAT_1_B__")))
log.append("ensamblado %s: %d claves; %d/%d claves ajenas a LAT_1 identicas al kit" % (dst, len(Z.files), iguales, otras))
for sup in ("od", "cara_inf"):
    for lado, N in (("A", NA), ("B", NB)):
        k = "LAT_1_%s__%s__" % (lado, sup)
        log.append("LAT_1_%s -4 grados %-8s: masa libre %.4e (kit horizontal %.4e) | obst/libre %.4f (kit %.4f)" % (
            lado, sup, N[k + "libre"].sum(), K[k + "libre"].sum(),
            N[k + "obst"].sum() / max(N[k + "libre"].sum(), 1e-300), K[k + "obst"].sum() / max(K[k + "libre"].sum(), 1e-300)))
open(OUT + "/T3_log.txt", "w", encoding="utf-8").write("\n".join(log) + "\n")
print("\n".join(log))
