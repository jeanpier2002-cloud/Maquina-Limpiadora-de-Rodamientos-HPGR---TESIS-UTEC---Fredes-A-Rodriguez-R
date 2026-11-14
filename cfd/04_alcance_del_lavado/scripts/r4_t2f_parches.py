#!/usr/bin/env python3
"""
CORRIDA 4 · T2f · Sensibilidad del N1 de cavidad al tamano del parche (sin nuevo trazado): se agrupan los parches de la
union (OR) de 2 x 2 (flanco: 10 mm x 20 grados; pistas: 10 mm x 1 grado) y se recalcula el gate (rodillos + pistas).
Parche nativo: flanco 5 mm x 10 grados; extremos 10 mm x 30 grados (no se agrupan); pistas 5 mm x 0,5 grados.
Un parche grueso se cuenta visible si cualquiera de sus subparches lo es -> el gate crece con el tamano del parche.
Uso: python -I -B r4_t2f_parches.py --tag d2400=d2400_SUP_1_A+...   Salida: 02_CAVIDAD_N1/<nombre>_parches.csv
"""
import argparse
import csv
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from r4_t2b_post import OUT, cargar  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--tag", default="base")
a = ap.parse_args()
Z = cargar(a.tag)
nombre = a.tag.split("=", 1)[0]
U = {k: Z[k].any(axis=0) for k in ("U_fl", "U_end", "U_out", "U_in")}
A_FL, A_END, A_OUT, A_IN, XC = Z["A_FL"], Z["A_END"], Z["A_OUT"], Z["A_IN"], Z["XC"]
XR = Z["X_RES"]
pista_in = (XC > XR[0]) & (XC < XR[1])


def gate(fac):
    """fac = 1 (nativo) o 2 (2 x 2)."""
    num = den = 0.0
    Ufl = U["U_fl"]                                   # (2, 23, NS, NPSI)
    ns, npsi = Ufl.shape[2], Ufl.shape[3]
    for f in range(2):
        for k in range(23):
            u = Ufl[f, k]
            if fac > 1:
                ns2 = ns // fac * fac
                g = u[:ns2].reshape(ns2 // fac, fac, npsi // fac, fac).any(axis=(1, 3))
                gg = np.repeat(np.repeat(g, fac, 0), fac, 1)
                u = np.vstack([gg, u[ns2:]])
            num += (u * A_FL[:, None]).sum(); den += A_FL.sum() * npsi
    Ue = U["U_end"]
    num += (Ue * A_END[None, None, None, :, None]).sum(); den += A_END.sum() * Ue.shape[-1] * Ue.shape[0] * Ue.shape[1] * Ue.shape[2]
    for UU, AA, msk in ((U["U_out"], A_OUT, np.ones(len(XC), bool)), (U["U_in"], A_IN, pista_in)):
        u = UU.copy()
        if fac > 1:
            nx = u.shape[0] // fac * fac
            g = u[:nx].reshape(nx // fac, fac, u.shape[1] // fac, fac).any(axis=(1, 3))
            u[:nx] = np.repeat(np.repeat(g, fac, 0), fac, 1)
        num += (u[msk] * AA[msk][:, None]).sum(); den += AA[msk].sum() * u.shape[1]
    return num / den


filas = [[nombre, "nativo (flanco 5 mm x 10°, pistas 5 mm x 0,5°)", "%.5f" % gate(1)],
         [nombre, "2x2 (flanco 10 mm x 20°, pistas 10 mm x 1°)", "%.5f" % gate(2)]]
with open(OUT + "/%s_parches.csv" % nombre, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["tag", "parche", "gate_rodillos_mas_pistas"]); w.writerows(filas)
for r in filas:
    print(r)
