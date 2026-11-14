#!/usr/bin/env python3
"""
CORRIDA 4 · T4b · Diagnostico geometrico de sombras parciales en E1 (no cambia S_acc; se informa aparte).
Factor de sombra por celda f = D_celda(obst) / D_libre(banda) (mapa *_mapa10mm.npz y bandas de r4_t1).
Clases fijadas aqui sin mirar D_req: f < 0,25 (sombra fuerte), 0,25-0,5, 0,5-0,75, >= 0,75 (casi libre).
Salidas: 03_DOSIS_TIEMPO/T4b_sombras.csv, figuras/T4b_mapa_cara_inf.png (+csv). Uso: python -I -B r4_t4b_sombras.py
"""
import csv
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from r4_estilo_kevin import guardar, plt  # noqa: E402
from r4_t4_cumplimiento import MAPAS, OUT, FIG, SUPS, T, leer  # noqa: E402


def main():
    F = leer(OUT + "/dosis_por_banda_unificada.csv")
    filas = []
    for sup in SUPS:
        Z = np.load(MAPAS[sup])
        D, A = Z["D"], Z["A"]
        sel = [r for r in F if r["superficie"] == sup]
        Dl = np.array([float(r["D1_libre"]) for r in sel])
        f = np.where(Dl[:, None] > 0, D / np.where(Dl[:, None] > 0, Dl[:, None], 1), 0)
        ok = A > 0
        At = A[ok].sum()
        cl = [(0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 99)]
        fr = [100 * A[ok & (f >= a) & (f < b)].sum() / At for a, b in cl]
        lo = ok & (f < 0.5)
        Dm_lo = (D[lo] * A[lo]).sum() / A[lo].sum() if lo.any() else float("nan")
        filas.append([sup, "%.4f" % At] + ["%.2f" % x for x in fr] + ["%.3f" % Dm_lo])
        print(sup, ["%.2f" % x for x in fr], "D medio en f<0,5: %.3f" % Dm_lo)
    with open(OUT + "/T4b_sombras.csv", "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo)
        w.writerow(["superficie", "S_acc_m2", "pct_f_lt_0.25", "pct_f_0.25_0.5", "pct_f_0.5_0.75", "pct_f_ge_0.75",
                    "D_medio_en_f_lt_0.5"])
        w.writerows(filas)
    # mapa polar de la cara inferior: N de vueltas que necesita cada celda para D_req = 183 (lectura por celdas)
    Z = np.load(MAPAS["Cara inferior"])
    D, A, e, th = Z["D"], Z["A"], Z["edges"], Z["th"]
    tmin = np.where(D > 0, 183.0 / np.where(D > 0, D, 1) * T / 60, np.nan)
    tmin[A <= 0] = np.nan
    fig = plt.figure(figsize=(6.4, 6.0))
    ax = fig.add_subplot(projection="polar")
    TH, R = np.meshgrid(np.radians(np.append(th - 0.25, 360 - 0.25)), e * 1e3)
    vals = np.ma.masked_invalid(tmin)
    pc = ax.pcolormesh(TH, R, vals, cmap="viridis_r", vmin=0, vmax=120, shading="flat")
    ax.set_ylim(400, 712)
    ax.set_rorigin(0)
    ax.set_yticks([450, 521.5, 617.5, 710])
    ax.set_yticklabels(["450", "521,5", "617,5", "710"], fontsize=8)
    ax.grid(alpha=0.3)
    cb = fig.colorbar(pc, ax=ax, shrink=0.75, pad=0.1)
    cb.set_label("minutos para D_req = 183 kg·m⁻² (celda)")
    cb.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: ("%g" % v).replace(".", ",")))
    datos = []
    for b in range(D.shape[0]):
        for k in range(0, D.shape[1], 4):
            datos.append(["%.1f" % (0.5e3 * (e[b] + e[b + 1])), "%.2f" % th[k], "%.4f" % D[b, k],
                          "" if not np.isfinite(tmin[b, k]) else "%.2f" % tmin[b, k]])
    guardar(fig, FIG, "T4b_mapa_cara_inf", ["r_mm", "theta_grados", "D_kg_m2_vuelta", "min_para_183"], datos)
    # M3 de la cara inferior con la lectura por celdas (complementaria), tres bandas
    from r4_estilo_kevin import C, ejes_coma
    M = [r for r in csv.DictReader(open(OUT + "/M3_curvas.csv", encoding="utf-8"))
         if r["superficie"] == "Cara inferior" and r["zona"] == "total" and r["lectura"] == "celdas"]
    fig, ax = plt.subplots()
    datos = []
    for i, Dr in enumerate((65, 183, 305)):
        s = [r for r in M if int(r["D_req"]) == Dr]
        t = np.array([float(r["t_min"]) for r in s]); y = 100 * np.array([float(r["M3_S_acc"]) for r in s])
        ax.plot(t, y, color=C[i], label="D_req %d · celdas" % Dr)
        k = np.where(y >= 95 - 1e-9)[0]
        if len(k):
            ax.plot([t[k[0]]], [y[k[0]]], "o", color=C[i])
            ax.annotate(("%.1f" % t[k[0]]).replace(".", ","), (t[k[0]], y[k[0]]), textcoords="offset points",
                        xytext=(4, -14), color=C[i], fontsize=11)
        datos += [[Dr, r["N_vueltas"], r["t_min"], "%.4f" % v] for r, v in zip(s, y)]
    for tm in (15, 30, 60):
        ax.axvline(tm, color="0.55", lw=0.8, ls=":")
    ax.axhline(95, color="0.3", lw=0.8, ls="-.")
    ax.set_xlim(0, 125); ax.set_ylim(0, 102)
    ax.set_xlabel("tiempo de programa (min)")
    ax.set_ylabel("área accesible con meta de dosis (%)")
    ejes_coma(ax)
    ax.legend(fontsize=10, loc="lower right")
    guardar(fig, FIG, "T4b_M3_cara_inf_celdas", ["D_req", "N", "t_min", "M3_acc_celdas_pct"], datos)


if __name__ == "__main__":
    main()
