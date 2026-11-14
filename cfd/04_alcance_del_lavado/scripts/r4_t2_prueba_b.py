#!/usr/bin/env python3
"""
CORRIDA 4 · T2 prueba (b): marcha + biseccion de r4_t2_cavidad_n1 frente a la solucion analitica rayo-cilindro finito
(superficie lateral + tapas), con la variante cilindro (rho 68 mm) del rodillo 0 de la hilera superior, sin aros.
Salida: 02_CAVIDAD_N1/prueba_b_cilindro.csv. Uso: python -I -B r4_t2_prueba_b.py
"""
import csv
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import r4_t2_cavidad_n1 as T  # noqa: E402

rng = np.random.default_rng(20261111)
c1, a, eo, et = T.ejes_rodillo(0, 0, 0.0)
R, L = T.RHO_CIL, T.L_ROD
n = 4000
# rayos desde una esfera de 400 mm alrededor del centro del rodillo, apuntando a puntos aleatorios del cilindro
cen = c1 + 0.5 * L * a
d0 = rng.normal(size=(n, 3)); d0 /= np.linalg.norm(d0, axis=1, keepdims=True)
P = cen + 400 * d0
tgt = c1 + rng.uniform(-10, L + 10, n)[:, None] * a + (rng.uniform(0, 1.2 * R, n)[:, None]) * (
    np.cos(rng.uniform(0, 2 * np.pi, n))[:, None] * eo + np.sin(rng.uniform(0, 2 * np.pi, n))[:, None] * et)
U = tgt - P; U /= np.linalg.norm(U, axis=1, keepdims=True)


def analitico(P, U):
    t = np.full(len(P), np.inf)
    w = P - c1
    ws, us = w @ a, U @ a
    wp = w - ws[:, None] * a; up = U - us[:, None] * a
    A_ = (up * up).sum(1); B_ = 2 * (wp * up).sum(1); C_ = (wp * wp).sum(1) - R * R
    D = B_ * B_ - 4 * A_ * C_
    ok = (D >= 0) & (A_ > 1e-12)
    t1 = np.where(ok, (-B_ - np.sqrt(np.where(ok, D, 0))) / (2 * np.where(A_ > 1e-12, A_, 1)), np.inf)
    s1 = ws + t1 * us
    t = np.where(ok & (t1 > 0) & (s1 >= 0) & (s1 <= L), t1, t)
    for s0 in (0.0, L):
        with np.errstate(divide="ignore", invalid="ignore"):
            tc = (s0 - ws) / us
        Q = P + np.where(np.isfinite(tc), tc, 0)[:, None] * U - c1
        rr = np.linalg.norm(Q - (Q @ a)[:, None] * a, axis=1)
        val = np.isfinite(tc) & (tc > 0) & (rr <= R)
        t = np.where(val & (tc < t), tc, t)
    return t


# marcha solo contra el rodillo 0 (variante cilindro): se reutiliza la logica de T.marchar con un «solido» propio
def solido_c(Q):
    w = Q - c1
    s = w @ a
    d2 = (w * w).sum(1) - s * s
    return ((s >= 0) & (s <= L) & (d2 <= R * R)).astype(int)


def marchar(P, U, h=1.0, nmax=900, nbis=12):
    n = len(P); t = np.zeros(n); vivo = np.ones(n, bool); tpre = np.zeros(n); hit = np.zeros(n, bool)
    for _ in range(nmax):
        idx = np.where(vivo)[0]
        if not len(idx):
            break
        tn = t[idx] + h
        g = solido_c(P[idx] + tn[:, None] * U[idx]) > 0
        tpre[idx] = t[idx]; t[idx] = tn
        hit[idx[g]] = True; vivo[idx[g]] = False
    sel = np.where(hit)[0]
    lo, hi = tpre[sel].copy(), t[sel].copy()
    for _ in range(nbis):
        mid = 0.5 * (lo + hi)
        g = solido_c(P[sel] + mid[:, None] * U[sel]) > 0
        hi = np.where(g, mid, hi); lo = np.where(g, lo, mid)
    out = np.full(n, np.inf); out[sel] = hi
    return out


ta = analitico(P, U)
tm = marchar(P, U)
both = np.isfinite(ta) & np.isfinite(tm)
mis = np.isfinite(ta) ^ np.isfinite(tm)
err = np.abs(ta[both] - tm[both])
# los desacuerdos de deteccion solo pueden ser rayos rasantes que cruzan el cilindro en menos de 1 mm (paso de marcha)
print("rayos %d | impactan (analitico) %d | ambos %d | discrepancia de deteccion %d" % (n, np.isfinite(ta).sum(), both.sum(), mis.sum()))
print("error |t_marcha - t_analitico|: max %.4f mm, medio %.5f mm" % (err.max(), err.mean()))
os.makedirs(T.OUT, exist_ok=True)
with open(T.OUT + "/prueba_b_cilindro.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["n_rayos", "impactan_analitico", "ambos", "discrepancia_deteccion", "err_max_mm", "err_medio_mm"])
    w.writerow([n, int(np.isfinite(ta).sum()), int(both.sum()), int(mis.sum()), "%.5f" % err.max(), "%.6f" % err.mean()])
