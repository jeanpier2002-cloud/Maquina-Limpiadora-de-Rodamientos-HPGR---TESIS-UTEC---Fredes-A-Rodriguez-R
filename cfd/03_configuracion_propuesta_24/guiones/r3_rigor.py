#!/usr/bin/env python3
"""
CORRIDA 3 · T9 · Rigor numerico pedido por Kevin Redosado sobre el caso nuevo (Caso 2, ramal A + S9, con mascaras):
  1. Malla con Courant de gota constante: R3_04 (gruesa, 202 616) / R3_02 (base, 430 560) / R3_05 (fina, 846 960).
     Error frente a la malla mas fina, cambio entre las dos mas finas (objetivo inicial del proyecto < 5 %; criterio
     de ingeniero de Kevin 2 %), orden observado p y GCI (Celik et al. 2008: funcion gci() de r3_gci.py, copia sin
     cambios de CFD03/05_SCRIPTS/gci.py; h = N^(-1/3)), con el costo real de cada corrida (run_log.csv).
  2. Numero de parcelas: R3_06 (x0,5) / R3_02 (x1) / R3_07 (x2). Mismas tablas; razon de refinamiento 2 en N
     (p observado con h = N^(-1/2), la escala del ruido de muestreo; solo orientativo).
  3. Ruido A<->B: R3_03 (ramal B explicito) frente a R3_02 (ramal A), mismo post-proceso S9 de cada uno.
KPI usados (PROMPT §6/T9): D media, CV y zona seca (10 mm y 2 mm) del OD y de la cara inferior, D media de Z3. D_min
se tabula pero NO se usa como criterio (ruidoso: ~18 % entre realizaciones en la base).
Entradas: 03_FLUENT/resultados/KPI/<caso>/<caso>_resumen.csv (r3_post.py) y 00_ADMIN/run_log.csv.
Salidas: 03_FLUENT/resultados/T9_malla.csv, T9_particulas.csv, T9_ruido_AB.csv y figuras (un panel por KPI, coma
decimal, valores escritos en los puntos) en 03_FLUENT/figuras/T9_*.png (+ .csv).
Uso: python -I -B r3_rigor.py
"""
import csv
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from r3_estilo_kevin import C, ejes_coma, guardar, plt  # noqa: E402
from r3_gci import gci  # noqa: E402

BASE = "D:/CFD_Redosado/CORRIDA_3_O7C2"
FL = BASE + "/03_FLUENT"
KPI = FL + "/resultados/KPI"
FIG = FL + "/figuras"
CELDAS = {"R3_04_gruesa": 202616, "R3_02_caso2": 430560, "R3_05_fina": 846960}
NPAR = {"R3_06_np050": 0.5, "R3_02_caso2": 1.0, "R3_07_np200": 2.0}
# (superficie, variante, columna, etiqueta, modo) ; modo rel = % ; abs = diferencia absoluta
MAG = [("od", "obst_10mm", "D_media", "OD: D̄ (kg·m⁻²·vuelta⁻¹)", "rel"),
       ("od", "obst_10mm", "CV", "OD: CV (−)", "abs"),
       ("od", "obst_10mm", "D_min", "OD: D_min 10 mm (no es criterio)", "rel"),
       ("od", "obst_2mm", "seca_pct", "OD: zona seca 2 mm (%)", "abs"),
       ("cara_inf", "obst_10mm", "D_media", "Cara inferior: D̄ (kg·m⁻²·vuelta⁻¹)", "rel"),
       ("cara_inf", "obst_10mm", "CV", "Cara inferior: CV (−)", "abs"),
       ("cara_inf", "obst_10mm", "D_min", "Cara inferior: D_min 10 mm (no es criterio)", "rel"),
       ("cara_inf", "obst_2mm", "seca_pct", "Cara inferior: zona seca 2 mm (%)", "abs"),
       ("cara_inf_Z3_aro_exterior_sin_PAD", "obst_2mm", "D_media", "Z3: D̄ (kg·m⁻²·vuelta⁻¹)", "rel"),
       ("cara_inf_Z3_aro_exterior_sin_PAD", "obst_2mm", "CV", "Z3: CV (−)", "abs")]


def resumen(caso):
    p = "%s/%s/%s_resumen.csv" % (KPI, caso, caso)
    if not os.path.exists(p):
        return None
    return {(r["superficie"], r["variante"]): r for r in csv.DictReader(open(p, encoding="utf-8"))}


def costo(caso):
    for r in csv.DictReader(open(BASE + "/00_ADMIN/run_log.csv", newline="")):
        if r["caso"] == caso and r["etapa"] == "fluent_R3":
            return r["costo_real_h"]
    return ""


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def dif(a, b, modo):
    if math.isnan(a) or math.isnan(b):
        return float("nan")
    return (a / b - 1) * 100 if modo == "rel" and b else a - b


def estudio(casos, nombre, hfun, etiqueta_x, xs):
    R = {c: resumen(c) for c in casos}
    faltan = [c for c in casos if R[c] is None]
    filas = []
    for sup, var, col, lab, modo in MAG:
        v = [num(R[c][(sup, var)][col]) if R[c] and (sup, var) in R[c] else float("nan") for c in casos]
        g = dict(tipo="", p=float("nan"), ext=float("nan"), gci=float("nan"))
        if not any(math.isnan(x) for x in v):
            h3, h2, h1 = (hfun(c) for c in casos)
            g = gci(v[2], v[1], v[0], h2 / h1, h3 / h2)
        e = [dif(x, v[2], modo) for x in v]       # error frente al nivel mas fino
        cambio = dif(v[2], v[1], modo)             # entre los dos mas finos
        filas.append([lab, modo] + ["%.5g" % x for x in v] + ["%.3g" % x for x in e[:2]] +
                     ["%.3g" % cambio, ("sí" if abs(cambio) < 5 else "no") if modo == "rel" and not math.isnan(cambio) else "",
                      ("sí" if abs(cambio) < 2 else "no") if modo == "rel" and not math.isnan(cambio) else "",
                      g["tipo"], "%.3g" % g["p"], "%.5g" % g["ext"],
                      "%.3g" % (100 * g["gci"]) if g["gci"] == g["gci"] else ""])
        if not any(math.isnan(x) for x in v):
            fig, ax = plt.subplots()
            if modo == "rel" and v[2]:
                # banda de +-2 % alrededor del nivel mas fino (criterio de ingeniero de Kevin) y eje de +-5 % como minimo,
                # para no exagerar cambios de decimas de por ciento
                ax.axhspan(0.98 * v[2], 1.02 * v[2], color="0.9", zorder=0, label="±2 % del nivel más fino")
                lo, hi = min(min(v), 0.95 * v[2]), max(max(v), 1.05 * v[2])
                ax.set_ylim(lo - 0.02 * abs(hi - lo), hi + 0.08 * abs(hi - lo))
                ax.legend(fontsize=10, loc="lower right")
            ax.plot(xs, v, "o-", color=C[0])
            for x, y in zip(xs, v):
                ax.annotate(("%.4g" % y).replace(".", ","), (x, y), textcoords="offset points", xytext=(0, 8),
                            ha="center", fontsize=11)
            ax.set_xlabel(etiqueta_x)
            ax.set_ylabel(lab)
            ax.set_xscale("log")
            ax.set_xticks(xs)
            ejes_coma(ax)
            guardar(fig, FIG, "T9_%s_%s_%s_%s" % (nombre, sup, var, col),
                    ["caso", etiqueta_x, col], [[c, x, y] for c, x, y in zip(casos, xs, v)])
    cab = ["kpi", "modo"] + casos + ["err_vs_%s_%s" % (casos[2], casos[0]), "err_vs_%s_%s" % (casos[2], casos[1]),
                                    "cambio_dos_mas_finos", "menor_5pct", "menor_2pct", "convergencia", "p_observado",
                                    "extrapolado", "GCI_fino_pct"]
    with open(FL + "/resultados/T9_%s.csv" % nombre, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cab)
        w.writerows(filas)
        w.writerow(["costo_real_h", ""] + [costo(c) for c in casos])
    print("T9 %s: %s%s" % (nombre, ", ".join(casos), (" | FALTAN: " + ", ".join(faltan)) if faltan else ""))
    for fl in filas:
        print("  " + " | ".join(fl))


estudio(["R3_04_gruesa", "R3_02_caso2", "R3_05_fina"], "malla", lambda c: CELDAS[c] ** (-1 / 3), "celdas",
        [CELDAS[c] for c in ("R3_04_gruesa", "R3_02_caso2", "R3_05_fina")])
estudio(["R3_06_np050", "R3_02_caso2", "R3_07_np200"], "particulas", lambda c: NPAR[c] ** (-1 / 2),
        "parcelas (× base)", [0.5, 1.0, 2.0])
# ruido A<->B
a, b = resumen("R3_02_caso2"), resumen("R3_03_B_caso2")
if a and b:
    filas = []
    for sup, var, col, lab, modo in MAG:
        va, vb = num(a[(sup, var)][col]), num(b[(sup, var)][col])
        filas.append([lab, "%.5g" % va, "%.5g" % vb, "%.3g" % dif(vb, va, modo), "%" if modo == "rel" else "abs"])
    with open(FL + "/resultados/T9_ruido_AB.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kpi", "A_S9 (R3_02)", "B_S9 (R3_03)", "B_menos_A", "unidad"])
        w.writerows(filas)
    print("T9 ruido A<->B:")
    for fl in filas:
        print("  " + " | ".join(fl))
