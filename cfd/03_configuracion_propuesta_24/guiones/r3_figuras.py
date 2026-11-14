#!/usr/bin/env python3
"""
CORRIDA 3 · T6/T7 · Figuras de resultados (estilo de la Corrida 2: un panel por figura, coma decimal, CSV al lado):
  R3F1  OD: dosis por banda de 10 mm (con obstaculos) frente a z — Caso Base, Caso 2 del diseno anterior, R3_01, R3_02
  R3F2  OD: franja entre z 1000 y 1070 mm, bandas de 2 mm (sin obstaculos: la franja es geometrica) — R3_01 frente a R3_02
  R3F3  Cara inferior: dosis por banda de 10 mm (con obstaculos) frente a r — Caso Base frente a O7+C2, con Z1/Z2/Z3
        y la linea de 15,8 kg/m2 (criterio D-047 para Z3, HIPOTESIS)
  R3F4  Cara inferior: aporte de cada boquilla por banda de 10 mm (O7+C2, sin obstaculos) — INF_EXT, boquilla C2, INF_INT
Entradas: KPI de r3_post.py (03_FLUENT/resultados/KPI/<caso>/) y, para el Caso Base y el Caso 2 anterior, las bandas S9
de CFD03/06_RESULTADOS/G8/comparacion/{CB,C2} (SOLO LECTURA). Se dibuja lo que exista.
Uso: python -I -B r3_figuras.py
"""
import csv
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from r3_estilo_kevin import C, ejes_coma, guardar, plt  # noqa: E402

FL = "D:/CFD_Redosado/CORRIDA_3_O7C2/03_FLUENT"
KPI = FL + "/resultados/KPI"
FIG = FL + "/figuras"
REF = "G:/Mi unidad/Semestre X/TESIS II/Sistema de aspersión/CFD03_ANSYS_COMPLETO/06_RESULTADOS/G8/comparacion"


def bandas(clave, sup, res="10mm"):
    if clave.startswith("REF:"):
        p = "%s/%s/G7_%s_bandas_%s.csv" % (REF, clave[4:], sup, res)
    else:
        p = "%s/%s/%s_%s_bandas_%s.csv" % (KPI, clave, clave, sup, res)
    if not os.path.exists(p):
        return None
    return list(csv.DictReader(open(p, encoding="utf-8")))


def mejor_o7c2():
    for c, n in (("R3_02_03_AB", "O7+C2 + Caso 2, A+B explícito"), ("R3_02_caso2", "O7+C2 + Caso 2, ramal A (S9)"),
                 ("R3_01_kit", "O7+C2 kit (S9)")):
        if os.path.exists("%s/%s/%s_resumen.csv" % (KPI, c, c)):
            return c, n
    return None, None


# R3F1
fig, ax = plt.subplots(figsize=(6.4, 5.4))
datos = []
for i, (c, n, ls) in enumerate((("REF:CB", "Caso Base (S9)", ":"), ("REF:C2", "Caso 2, diseño anterior (S9)", "--"),
                                 ("R3_01_kit", "O7+C2 kit, LAT_1 horizontal", "-"), ("R3_02_caso2", "O7+C2 + Caso 2", "-"))):
    B = bandas(c, "od")
    if not B:
        continue
    z = [float(r["s_centro_mm"]) for r in B]
    D = [float(r["D_obst_media_theta"]) for r in B]
    ax.plot(D, z, ls=ls, color=C[i], label=n, lw=1.8 if ls == "-" else 1.4)
    datos += [[n, zz, dd] for zz, dd in zip(z, D)]
ax.set_xlabel("dosis por vuelta D (kg·m⁻²·vuelta⁻¹)")
ax.set_ylabel("altura en el OD, z (mm)")
ax.set_xscale("log")
ejes_coma(ax)
ax.legend(fontsize=9, loc="lower left")
if datos:
    guardar(fig, FIG, "R3F1_OD_dosis_z", ["caso", "z_mm", "D_obst_10mm"], datos)
else:
    plt.close(fig)

# R3F2
fig, ax = plt.subplots()
datos = []
for i, (c, n) in enumerate((("R3_01_kit", "O7+C2 kit, LAT_1 horizontal"), ("R3_02_caso2", "O7+C2 + Caso 2 (LAT_1 a −4°)"))):
    B = bandas(c, "od", "2mm")
    if not B:
        continue
    sel = [r for r in B if 1000 <= float(r["s_centro_mm"]) <= 1070]
    z = [float(r["s_centro_mm"]) for r in sel]
    D = [float(r["D_libre"]) for r in sel]
    ax.step(z, D, where="mid", color=C[i + 2], label=n)
    datos += [[n, zz, dd] for zz, dd in zip(z, D)]
ax.set_xlabel("altura en el OD, z (mm)")
ax.set_ylabel("D por banda de 2 mm (kg·m⁻²·vuelta⁻¹)")
ejes_coma(ax)
ax.legend(fontsize=9)
if datos:
    guardar(fig, FIG, "R3F2_OD_franja_2mm", ["caso", "z_mm", "D_libre_2mm"], datos)
else:
    plt.close(fig)

# R3F3
c3, n3 = mejor_o7c2()
fig, ax = plt.subplots()
datos = []
for i, (c, n) in enumerate((("REF:CB", "Caso Base (S9)"), (c3, n3))):
    if not c:
        continue
    B = bandas(c, "cara_inf")
    if not B:
        continue
    r = [float(x["s_centro_mm"]) for x in B]
    D = [float(x["D_obst_media_theta"]) for x in B]
    ax.plot(r, D, "o-" if i else "s--", ms=3.5, color=C[i], label=n)
    datos += [[n, rr, dd] for rr, dd in zip(r, D)]
for lo, hi, z in ((450.1, 521.5, "Z1"), (521.5, 617.5, "Z2"), (617.5, 710, "Z3")):
    ax.axvspan(lo, hi, color="0.92" if z != "Z2" else "0.97", zorder=0)
    ax.text(0.5 * (lo + hi), 0.97, z, transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=11)
ax.axhline(15.8, color="0.3", lw=1, ls=":")
ax.text(530, 14.6, "15,8 (D-047, Z3)", fontsize=9, color="0.3")
ax.set_xlabel("radio en la cara inferior, r (mm)")
ax.set_ylabel("D por banda de 10 mm (kg·m⁻²·vuelta⁻¹)")
ejes_coma(ax)
ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5, 0.9))
if datos:
    guardar(fig, FIG, "R3F3_cara_inf_dosis_r", ["caso", "r_mm", "D_obst_10mm"], datos)
else:
    plt.close(fig)

# R3F4: aportes por boquilla (sin obstaculos) a partir de combinar_kpi con una sola boquilla por aporte no se guarda
# por banda; se reconstruye con los CSV de impactos solo si existe <caso>_cara_inf_aportes_bandas.csv (r3_aportes.py).
p = "%s/%s/%s_cara_inf_aportes_bandas.csv" % (KPI, c3, c3) if c3 else ""
if p and os.path.exists(p):
    A = list(csv.DictReader(open(p, encoding="utf-8")))
    cols = [k for k in A[0] if k not in ("s_centro_mm",) and any(float(x[k]) > 0 for x in A)]   # sin columnas nulas
    fig, ax = plt.subplots()
    r = [float(x["s_centro_mm"]) for x in A]
    for i, k in enumerate(cols):
        ax.plot(r, [float(x[k]) for x in A], color=C[i], label=k, ls="--" if k == "total" else "-")
    ax.set_xlabel("radio en la cara inferior, r (mm)")
    ax.set_ylabel("D sin obstáculos (kg·m⁻²·vuelta⁻¹)")
    ejes_coma(ax)
    ax.legend(fontsize=9)
    guardar(fig, FIG, "R3F4_cara_inf_aportes", ["s_centro_mm"] + cols, [[x["s_centro_mm"]] + [x[k] for k in cols] for x in A])
