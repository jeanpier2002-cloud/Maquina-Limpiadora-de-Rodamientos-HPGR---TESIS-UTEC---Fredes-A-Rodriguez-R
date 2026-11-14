#!/usr/bin/env python3
"""
CORRIDA 2 · T5 · Figuras de convergencia al estilo de Kevin (un panel, coma decimal, sin titulo, N definido en el eje):
  CONV_<caso>_error_fino : error relativo frente a la malla mas fina vs N (log-log), con pendientes 1 y 2 de referencia;
                           todas las curvas con el mismo numero de puntos (N5, N10, N20 frente a N40).
  CONV_<caso>_teoria     : error frente a la referencia TEORICA (p0, F/b local, M por lado) vs N, con la banda del 2 %.
  CONV_<caso>_costo      : tiempo de calculo real vs N (log), con el numero de procesos.
  CONV_<caso>_orden.csv  : orden observado p = log2(|f_N - f_2N| / |f_2N - f_4N|) de cada magnitud.
caso = E1 (lamina 0,30 mm; datos de la tanda 1, solo lectura) y E1-OD (0,049 mm; datos v3) si existen.
Uso: python -I v3_figuras_conv.py
"""
import csv
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v3_estilo_kevin import C, ejes_coma, guardar, plt  # noqa: E402

B = "D:/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3"
FIG = B + "/figuras"
T1 = "D:/CFD_Redosado/CORRIDA_1_13a21oct/06_VOF"
RHO, V = 982.12, 27.4711
XLAB = "N (celdas a través del espesor e₀ de la lámina; Δ = e₀/N)"


def cargar_e1():
    m = {r["caso"]: r for r in csv.DictReader(open(T1 + "/datos/E1_metricas.csv"))}
    base = [m[f"N{n}_Co0.5_lam"] for n in (5, 10, 20, 40)]
    e0 = 0.30e-3
    mags = {"p0_Pa": ("p₀ (presión de estancamiento)", 0.5 * RHO * V ** 2), "F_loc1mm_Nm": ("F/b local (|x| < 1 mm)", RHO * V ** 2 * e0),
            "h_x2mm_um": ("espesor de la película en x = 2 mm", None), "tau_x2mm": ("τ_w en x = 2 mm", None)}
    costo = {5: (34, 1), 10: (402, 1), 20: (2766, 2), 40: (9653, 4)}   # run_log.csv de la tanda 1 (s, procesos)
    return "E1", e0, base, mags, costo


def cargar_e1od():
    p = B + "/datos/E1OD_metricas.csv"
    if not os.path.exists(p):
        return None
    m = {r["caso"]: r for r in csv.DictReader(open(p))}
    base = [m[f"OD_N{n}_Co0.5"] for n in (5, 10, 20, 40) if f"OD_N{n}_Co0.5" in m]
    if len(base) < 3:
        return None
    e0 = float(base[0]["e0_mm"]) * 1e-3
    mags = {"p0_Pa": ("p₀ (presión de estancamiento)", 0.5 * RHO * V ** 2),
            "F_loc1_Nm": ("F/b local (|x| < 0,16 mm)", RHO * V ** 2 * e0),
            "M_xr2_Nm": ("M por lado en x = 0,33 mm", 0.5 * RHO * V ** 2 * e0),
            "h_xr2_um": ("espesor de la película en x = 0,33 mm", None), "tau_xr2": ("τ_w en x = 0,33 mm", None)}
    costo = {int(r["N"]): (float(r["pared_s"]), int(float(r["np"]))) for r in base if r.get("pared_s")}
    return "E1-OD", e0, base, mags, costo


def orden(a, b, c):
    try:
        return math.log(abs((a - b) / (b - c))) / math.log(2)
    except (ValueError, ZeroDivisionError):
        return float("nan")


for datos in (cargar_e1(), cargar_e1od()):
    if not datos:
        continue
    caso, e0, base, mags, costo = datos
    tag = caso.replace("-", "")
    Ns = [int(float(r["N"])) for r in base]
    fino = base[-1]
    # A: error frente a la malla mas fina
    fig, ax = plt.subplots()
    filas, ords = [], []
    for i, (k, (lab, teo)) in enumerate(mags.items()):
        v = np.array([float(r[k]) for r in base])
        if caso == "E1-OD" and k == "p0_Pa":
            # p0 de N40 (Co 0,5) queda +4 % sobre la teoria (posible limite capilar; ver INFORME_E1_OD_v3 §4):
            # se juzga solo frente a la teoria (figura B), no frente a la malla mas fina
            ords.append([lab, k, orden(*v[0:3]), orden(*v[1:4]) if len(v) >= 4 else float("nan")])
            continue
        err = np.abs(v[:-1] - v[-1]) / abs(v[-1])
        ax.loglog(Ns[:-1], err, "o-", color=C[i], label=lab)
        filas += [[lab, n, x, e] for n, x, e in zip(Ns, v, list(err) + [0.0])]
        p1 = orden(*v[0:3]) if len(v) >= 3 else float("nan")   # noqa: E501
        p2 = orden(*v[1:4]) if len(v) >= 4 else float("nan")
        ords.append([lab, k, p1, p2])
    x0 = np.array([Ns[0], Ns[-2]], dtype=float)
    for pend, ls in ((1, "--"), (2, ":")):
        ax.loglog(x0, 0.05 * (x0 / x0[0]) ** (-pend), color="0.35", ls=ls, lw=1.2, label="pendiente %d" % pend)
    ejes_coma(ax, x=False)
    ax.set_xticks(Ns[:-1]); ax.set_xticklabels([str(n) for n in Ns[:-1]])
    ax.set_xlabel(XLAB, fontsize=11)
    ax.set_ylabel("error relativo frente a la malla más fina (N%d)" % Ns[-1], fontsize=11)
    ax.legend(fontsize=8.5)
    guardar(fig, FIG, f"CONV_{tag}_error_fino", ["magnitud", "N", "valor", "error_rel_fino"], filas)
    with open(f"{FIG}/CONV_{tag}_orden.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["magnitud", "clave", "orden_5-10-20", "orden_10-20-40"])
        w.writerows([[a, b, "%.2f" % c, "%.2f" % d] for a, b, c, d in ords])
    # B: error frente a la teoria
    fig, ax = plt.subplots()
    filas = []
    for i, (k, (lab, teo)) in enumerate(mags.items()):
        if teo is None:
            continue
        v = np.array([float(r[k]) for r in base])
        e = (v / teo - 1) * 100
        ax.semilogx(Ns, e, "o-", color=C[i], label=lab + " (teórica)")
        filas += [[lab, n, x, teo, y] for n, x, y in zip(Ns, v, e)]
    ax.axhspan(-2, 2, color="0.85", alpha=0.6, lw=0, label="±2 % (criterio de ingeniero)")
    ax.axhline(0, color="0.3", lw=0.8)
    ejes_coma(ax, x=False)
    ax.set_xticks(Ns); ax.set_xticklabels([str(n) for n in Ns])
    ax.set_xlabel(XLAB, fontsize=11)
    ax.set_ylabel("diferencia con la referencia teórica (%)", fontsize=11)
    ax.legend(fontsize=8.5)
    guardar(fig, FIG, f"CONV_{tag}_teoria", ["magnitud", "N", "valor", "teoria", "dif_pct"], filas)
    # C: costo
    if costo:
        fig, ax = plt.subplots()
        n_ = sorted(costo)
        h = [costo[n][0] / 3600 for n in n_]
        ax.semilogy(n_, h, "o-", color=C[0])
        for n, hh in zip(n_, h):
            ax.annotate("%d proc." % costo[n][1], (n, hh), textcoords="offset points", xytext=(6, -12), fontsize=10)
        ejes_coma(ax, x=False)
        ax.set_xticks(n_); ax.set_xticklabels([str(n) for n in n_])
        ax.set_xlabel(XLAB, fontsize=11)
        ax.set_ylabel("tiempo de cálculo (h)", fontsize=11)
        guardar(fig, FIG, f"CONV_{tag}_costo", ["N", "pared_s", "procesos"], [[n, costo[n][0], costo[n][1]] for n in n_])
    for o in ords:
        print(caso, "%-42s p(5-10-20) %5.2f   p(10-20-40) %5.2f" % (o[0], o[2], o[3]))
