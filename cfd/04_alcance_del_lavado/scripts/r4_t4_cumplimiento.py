#!/usr/bin/env python3
"""
CORRIDA 4 · T4 · Curvas de cumplimiento de dosis frente al tiempo de programa (M3, M4, M5; M6 descriptiva).
CANDIDATO / DATO EXTERNO PENDIENTE (D_req). El CFD mide dosis, NO limpieza.

Preregistro (CRITERIO_PREREGISTRADO.md v1, hash 20cab8a5...):
  M3(N) = fraccion de area (S_ref y S_acc) cuyas bandas cumplen N*D1(b) >= D_req, D_req in {65, 183, 305} kg/m2.
  Lecturas por banda de 10 mm: «media_theta» (D_obst_media_theta, optimista) y «peor_celda» (D_obst_min_celda, conservadora).
  Lectura complementaria declarada antes de calcular (ESTADO 01:06): «celdas» = celdas 10 mm x 0,5 grados del mapa *_mapa10mm.npz.
  M4: t_X = primer N entero con M3 >= X %, X = 90 / 95 / 99 (meta supuesta 95 %). Tambien valor continuo (cuantil).
  M5: t = D_req*T_vuelta/D_min (D_min = peor banda de 10 mm de la media theta, formula de T10).
  N = 0..204 vueltas (120 min), T_vuelta = 35,294 s. S_ref = area_banda; S_acc = area_mojable (sin PAD/topes).
Entradas: 03_DOSIS_TIEMPO/dosis_por_banda_unificada.csv (+ _2mm) de r4_t1 y los mapas de celdas (rutas abajo).
Salidas (03_DOSIS_TIEMPO/): M3_curvas.csv, M4_tX.csv, M5_peor_banda.csv, M6_intensidad.csv, T4_t95_tabla.csv,
  figuras T4_M3_<sup>.png (+csv) y T4_t95_tabla.png. Uso: python -I -B r4_t4_cumplimiento.py
"""
import csv
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from r4_estilo_kevin import C, ejes_coma, guardar, plt  # noqa: E402

B4 = "D:/CFD_Redosado/CORRIDA_4_PRIMER_LAVADO"
OUT = B4 + "/03_DOSIS_TIEMPO"
FIG = OUT + "/figuras"
K3 = "D:/CFD_Redosado/CORRIDA_3_O7C2/03_FLUENT/resultados/KPI/R3_02_03_AB/R3_02_03_AB_"
G = "G:/Mi unidad/Semestre X/TESIS II/Sistema de aspersión/CFD03_ANSYS_COMPLETO/06_RESULTADOS"
MAPAS = {"OD": K3 + "od_mapa10mm.npz", "Cara inferior": K3 + "cara_inf_mapa10mm.npz",
         "Cara superior": G + "/G8/comparacion/C3/G7_sup_mapa10mm.npz", "Agujero": G + "/G7/G7_agujero_mapa10mm.npz"}
T = 35.294
DREQ = (65, 183, 305)
NMAX = 204
N = np.arange(NMAX + 1)
XS = (90, 95, 99)
SUPS = ("OD", "Cara inferior", "Cara superior", "Agujero")
LECT = ("media_theta", "peor_celda", "celdas")


def leer(ruta):
    F = list(csv.DictReader(open(ruta, encoding="utf-8")))
    for r in F:
        for c in ("s_centro_mm", "area_banda_m2", "area_mojable_m2", "D1_media_theta", "D1_peor_celda", "J_obst"):
            r[c] = float(r[c])
    return F


def grupos(F):
    """Superficie completa y sus zonas; para las caras tambien 'aros sin ventana' (Z1+Z3)."""
    g = {}
    for s in SUPS:
        sel = [r for r in F if r["superficie"] == s]
        g[(s, "total")] = sel
        for z in sorted({r["zona"] for r in sel}):
            if s != "Agujero":
                g[(s, z)] = [r for r in sel if r["zona"] == z]
        if s in ("Cara inferior", "Cara superior"):
            g[(s, "Z1+Z3_aros_sin_ventana")] = [r for r in sel if not r["zona"].startswith("Z2")]
    return g


def elementos(sel, lect, sup, zona):
    """Devuelve (D, A_acc, S_ref) por elemento (banda o celda)."""
    Sref = sum(r["area_banda_m2"] for r in sel)
    if lect != "celdas":
        col = "D1_media_theta" if lect == "media_theta" else "D1_peor_celda"
        D = np.array([r[col] for r in sel]); A = np.array([r["area_mojable_m2"] for r in sel])
        return D, A, Sref
    Z = np.load(MAPAS[sup])
    e = Z["edges"]; sc = 0.5 * (e[:-1] + e[1:]) * 1e3
    keep = np.zeros(len(sc), bool)
    s_sel = {round(r["s_centro_mm"], 2) for r in sel}
    for k, s in enumerate(sc):
        keep[k] = round(s, 2) in s_sel
    D = Z["D"][keep].ravel(); A = Z["A"][keep].ravel()
    return D, A, Sref


def m3(D, A, Sref, Dr):
    ok = A > 0
    D, A = D[ok], A[ok]
    Sacc = A.sum()
    cum = np.array([(A * (n * D >= Dr - 1e-12)).sum() for n in N])
    return cum / Sacc, cum / Sref, Sacc


def t_cont(D, A, frac_obj, Dr):
    """Cuantil continuo de N_req = D_req/D ponderado por area (fraccion objetivo sobre el area de D, A)."""
    ok = A > 0
    D, A = D[ok], A[ok]
    with np.errstate(divide="ignore"):
        nreq = np.where(D > 0, Dr / D, np.inf)
    o = np.argsort(nreq)
    c = np.cumsum(A[o]) / A.sum()
    k = np.searchsorted(c, frac_obj - 1e-12)
    return float(nreq[o][k]) if k < len(c) else float("inf")


def primer(curva, X):
    k = np.where(curva >= X / 100.0 - 1e-12)[0]
    return int(N[k[0]]) if len(k) else None


def fmt_min(n):
    return "no alcanzada en 120 min" if n is None else ("%.1f" % (n * T / 60)).replace(".", ",")


def main():
    os.makedirs(FIG, exist_ok=True)
    F10 = leer(OUT + "/dosis_por_banda_unificada.csv")
    F2 = leer(OUT + "/dosis_por_banda_unificada_2mm.csv")
    G10, G2 = grupos(F10), grupos(F2)
    curvas, tx = [], []
    CURV = {}
    for (sup, zona), sel in G10.items():
        for lect in LECT:
            D, A, Sref = elementos(sel, lect, sup, zona)
            for Dr in DREQ:
                ca, cr, Sacc = m3(D, A, Sref, Dr)
                CURV[(sup, zona, lect, Dr)] = (ca, cr)
                for n in N:
                    curvas.append([sup, zona, lect, Dr, int(n), "%.3f" % (n * T / 60), "%.5f" % ca[n], "%.5f" % cr[n]])
                for X in XS:
                    na, nr = primer(ca, X), primer(cr, X)
                    tca = t_cont(D, A, X / 100.0, Dr)
                    fr = X / 100.0 * Sref / Sacc          # fraccion de S_acc que equivale a X % de S_ref
                    tcr = t_cont(D, A, fr, Dr) if fr <= 1 + 1e-12 else float("inf")
                    tx.append([sup, zona, lect, "10mm", Dr, X, "%.4f" % Sref, "%.4f" % Sacc,
                               "" if na is None else na, "" if na is None else "%.2f" % (na * T / 60),
                               "%.3f" % tca if math.isfinite(tca) else "inf",
                               "" if nr is None else nr, "" if nr is None else "%.2f" % (nr * T / 60),
                               "%.3f" % tcr if math.isfinite(tcr) else "inf"])
    # bandas de 2 mm (complementaria; solo las dos lecturas por banda)
    for (sup, zona), sel in G2.items():
        for lect in ("media_theta", "peor_celda"):
            D, A, Sref = elementos(sel, lect, sup, zona)
            for Dr in DREQ:
                ca, cr, Sacc = m3(D, A, Sref, Dr)
                for X in XS:
                    na, nr = primer(ca, X), primer(cr, X)
                    tx.append([sup, zona, lect, "2mm", Dr, X, "%.4f" % Sref, "%.4f" % Sacc,
                               "" if na is None else na, "" if na is None else "%.2f" % (na * T / 60), "",
                               "" if nr is None else nr, "" if nr is None else "%.2f" % (nr * T / 60), ""])
    with open(OUT + "/M3_curvas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["superficie", "zona", "lectura", "D_req", "N_vueltas", "t_min", "M3_S_acc", "M3_S_ref"])
        w.writerows(curvas)
    with open(OUT + "/M4_tX.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["superficie", "zona", "lectura", "bandas", "D_req", "X_pct", "S_ref_m2", "S_acc_m2", "N_X_acc",
                    "t_X_acc_min", "N_X_acc_continuo", "N_X_ref", "t_X_ref_min", "N_X_ref_continuo"])
        w.writerows(tx)
    # M5 (formula T10: peor banda de la media theta)
    m5 = []
    for (sup, zona), sel in G10.items():
        sel2 = [r for r in sel if r["area_mojable_m2"] > 0]
        Dmin = min(r["D1_media_theta"] for r in sel2)
        Dc = min(r["D1_peor_celda"] for r in sel2)
        for Dr in DREQ:
            m5.append([sup, zona, Dr, "%.4f" % Dmin, "%.3f" % (Dr / Dmin), "%.2f" % (Dr / Dmin * T / 60),
                       "%.4f" % Dc, "%.2f" % (Dr / Dc * T / 60)])
    with open(OUT + "/M5_peor_banda.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["superficie", "zona", "D_req", "D_min_banda_media_theta", "vueltas_M5", "min_M5",
                    "D_min_celda", "min_peor_celda_absoluta"])
        w.writerows(m5)
    # M6 descriptiva: J por banda frente a la mediana de su superficie; impulso acumulado frente al ciclo Davis 75 psi
    m6 = []
    for sup in SUPS:
        sel = [r for r in F10 if r["superficie"] == sup and r["area_mojable_m2"] > 0]
        J = np.array([r["J_obst"] for r in sel])
        med = float(np.median(J))
        for r in sel:
            m6.append([sup, r["zona"], "%.1f" % r["s_centro_mm"], "%.4g" % r["J_obst"], "%.3f" % (r["J_obst"] / med),
                       "%.1f" % (262 / r["J_obst"]) if r["J_obst"] > 0 else "inf",
                       "%.1f" % (419 / r["J_obst"]) if r["J_obst"] > 0 else "inf"])
    with open(OUT + "/M6_intensidad.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["superficie", "zona", "s_centro_mm", "J_Ns_m2_vuelta", "J_sobre_mediana",
                    "vueltas_para_262_Pa_s", "vueltas_para_419_Pa_s"])
        w.writerows(m6)
    # tabla t95: superficie x D_req (S_acc; media theta / peor celda / celdas) + M1 clase
    tab = []
    idx = {(r[0], r[1], r[2], r[3], r[4], r[5]): r for r in tx}
    for sup in SUPS:
        zonas = ["total"] + sorted({k[1] for k in G10 if k[0] == sup and k[1] != "total"})
        for zona in zonas:
            for Dr in DREQ:
                fila = [sup, zona, Dr]
                for lect in LECT:
                    r = idx[(sup, zona, lect, "10mm", Dr, 95)]
                    fila += [r[8], r[9] if r[9] else "no alcanzada", r[11], r[12] if r[12] else "no alcanzada"]
                tab.append(fila)
    with open(OUT + "/T4_t95_tabla.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["superficie", "zona", "D_req"] + sum([["N95_acc_" + l, "t95_acc_min_" + l, "N95_ref_" + l,
                                                           "t95_ref_min_" + l] for l in LECT], []))
        w.writerows(tab)
    # figuras M3(t): una por superficie (total), tres bandas; trazo continuo media theta, discontinuo peor celda
    for sup in SUPS:
        fig, ax = plt.subplots()
        datos = []
        tmin = N * T / 60
        for i, Dr in enumerate(DREQ):
            ca, _ = CURV[(sup, "total", "media_theta", Dr)]
            cp, _ = CURV[(sup, "total", "peor_celda", Dr)]
            ax.plot(tmin, 100 * ca, color=C[i], ls="-", label="D_req %d · media θ" % Dr)
            ax.plot(tmin, 100 * cp, color=C[i], ls="--", lw=1.6, label="D_req %d · peor celda" % Dr)
            n95 = primer(ca, 95)
            if n95 is not None:
                ax.plot([n95 * T / 60], [100 * ca[n95]], "o", color=C[i])
                ax.annotate(("%.1f" % (n95 * T / 60)).replace(".", ","), (n95 * T / 60, 100 * ca[n95]),
                            textcoords="offset points", xytext=(4, -14), color=C[i], fontsize=11)
            for n in N:
                datos.append([sup, Dr, int(n), "%.3f" % tmin[n], "%.4f" % (100 * ca[n]), "%.4f" % (100 * cp[n])])
        for tm in (15, 30, 60):
            ax.axvline(tm, color="0.55", lw=0.8, ls=":")
        ax.axhline(95, color="0.3", lw=0.8, ls="-.")
        ax.set_xlim(0, 65 if sup != "Cara inferior" else 125)
        ax.set_ylim(0, 102)
        ax.set_xlabel("tiempo de programa (min)")
        ax.set_ylabel("área accesible con meta de dosis (%)")
        ejes_coma(ax)
        ax.legend(fontsize=8.5, loc="lower right", ncol=1)
        nombre = "T4_M3_" + {"OD": "OD", "Cara inferior": "cara_inf", "Cara superior": "cara_sup", "Agujero": "agujero"}[sup]
        guardar(fig, FIG, nombre, ["superficie", "D_req", "N", "t_min", "M3_acc_media_theta_pct", "M3_acc_peor_celda_pct"], datos)
    # impresion resumida
    print("\n t95 sobre S_acc (min) — media θ | peor celda | celdas   [S_ref entre corchetes]")
    for f_ in tab:
        print("%-14s %-24s %3d : %8s | %14s | %10s   [%s | %s | %s]" % (
            f_[0], f_[1], f_[2], f_[4], f_[8], f_[12], f_[6], f_[10], f_[14]))


if __name__ == "__main__":
    main()
