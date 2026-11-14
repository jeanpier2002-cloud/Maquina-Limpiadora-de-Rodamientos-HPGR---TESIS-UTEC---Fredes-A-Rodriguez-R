#!/usr/bin/env python3
"""
Post-proceso del caso puente F5 y tabla comparativa rama B (OpenFOAM, S2_seis) vs Fluent.

1) Balance por zona en la ventana [t0, t1) con los archivos de muestreo (dpm2csv.leer_dpm).
2) pared_agujero.dpm -> CSV -> post_kpi.py (cono, transitorio, bandas de 10 mm).
3) Tabla F5_puente.csv con los criterios de PROMPT_MAESTRO_ANSYS.md §4.2 (objetivo de trabajo):
   |dD| <= 5 %, |dCV| <= 0,03, zona seca 0 % en ambos, curvas C(Dmin) superpuestas en 1-20.

Uso: python post_f5.py --run D:/CFD02_run/F5 --caso F5_base_v1 --salida <06_RESULTADOS/F5>
"""
import argparse
import csv
import glob
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from dpm2csv import a_csv, leer_dpm  # noqa: E402

RAMA_B = os.path.join(HERE, "..", "02_ENTRADAS", "de_rama_B")
MDOT_INY = 0.14954763 + 0.149668594 + 0.149811002 + 0.149968796 + 0.150136084 + 0.149244155  # tablas F5

ap = argparse.ArgumentParser()
ap.add_argument("--run", required=True)
ap.add_argument("--caso", required=True)
ap.add_argument("--salida", required=True)
ap.add_argument("--t0", type=float, default=0.020)
ap.add_argument("--t1", type=float, default=0.035)
ap.add_argument("--ref", default="S2_seis")
a = ap.parse_args()
os.makedirs(a.salida, exist_ok=True)

# 1) balance en la ventana
zonas = ["pared_agujero", "cara_inf_rodamiento", "cara_sup_rodamiento", "lanza", "abierto_inferior",
         "abierto_superior", "lateral_abierto", "nucleo_abierto"]
bal = []
tot = 0.0
for z in zonas:
    p = os.path.join(a.run, z + ".dpm")
    cab, cols, filas = leer_dpm(p)
    ix = {c: i for i, c in enumerate(cols)}
    m = sum(v[ix["parcel-mass"]] for v, _ in filas if a.t0 <= v[ix["flow-time"]] < a.t1)
    mt = sum(v[ix["parcel-mass"]] for v, _ in filas)
    bal.append([z, len(filas), "%.6e" % mt, "%.6e" % (m / (a.t1 - a.t0))])
    tot += m / (a.t1 - a.t0)
err = 100 * (tot - MDOT_INY) / MDOT_INY
bal.append(["TOTAL_salidas_ventana", "", "", "%.6e" % tot])
bal.append(["inyectado", "", "%.6e" % (MDOT_INY * a.t1), "%.6e" % MDOT_INY])
bal.append(["error_balance_ventana_pct", "", "", "%.4f" % err])
with open(os.path.join(a.salida, a.caso + "_balance.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["zona", "n_parcelas_total", "masa_total_kg", "mdot_ventana_kg_s"])
    w.writerows(bal)
print("balance en la ventana: salidas %.6f kg/s vs inyectado %.6f kg/s -> %.3f %%" % (tot, MDOT_INY, err))

# 2) KPIs sobre la pared del agujero
csvp = os.path.join(a.salida, a.caso + "_impactos_pared_agujero.csv")
a_csv(os.path.join(a.run, "pared_agujero.dpm"), csvp)
subprocess.check_call([sys.executable, os.path.join(HERE, "post_kpi.py"), "--entrada", csvp, "--caso", a.caso,
                       "--salida", a.salida, "--superficie", "cono", "--lim", "0.890", "1.405",
                       "--modo", "transitorio", "--t-estable", str(a.t0), "--t-fin", str(a.t1),
                       "--mdot-inyectado", "%.9f" % MDOT_INY])

# 3) comparacion
fl = next(csv.DictReader(open(os.path.join(a.salida, a.caso + "_indicadores.csv"))))
rb = [r for r in csv.DictReader(open(os.path.join(RAMA_B, "F4_indicadores.csv"))) if r["caso"] == a.ref][0]
cobB = [(float(r["D_min_kg_m2_vuelta"]), float(r["cobertura_pct"]))
        for r in csv.DictReader(open(os.path.join(RAMA_B, "F4_cobertura.csv"))) if r["caso"] == a.ref]
cobF = [(float(r["D_min_kg_m2_vuelta"]), float(r["cobertura_pct"]))
        for r in csv.DictReader(open(os.path.join(a.salida, a.caso + "_cobertura.csv")))]
cobB.sort(); cobF.sort()   # la tabla de la rama B trae umbrales extra al final sin ordenar
u = np.logspace(0, np.log10(20), 40)
cB = np.interp(u, [c[0] for c in cobB], [c[1] for c in cobB])
cF = np.interp(u, [c[0] for c in cobF], [c[1] for c in cobF])
dcob = float(np.abs(cB - cF).max())

Db, Df = float(rb["dosis_media_kg_m2_vuelta"]), float(fl["K2_D_media_kg_m2_vuelta"])
CVb, CVf = float(rb["CV_de_Dz"]), float(fl["K3_CV"])
Sb, Sf = float(rb["area_seca_pct"]), float(fl["K4_zona_seca_pct"])
filas = [
    ["mdot_depositado_kg_s", rb["mdot_depositado_kg_s"], fl["mdot_depositado_kg_s"],
     "%.2f %%" % (100 * (float(fl["mdot_depositado_kg_s"]) / float(rb["mdot_depositado_kg_s"]) - 1)), "-", "-"],
    ["K2_D_media_kg_m2_vuelta", "%.4f" % Db, "%.4f" % Df, "%.2f %%" % (100 * (Df / Db - 1)), "|dD| <= 5 %",
     "SI" if abs(Df / Db - 1) <= 0.05 else "NO"],
    ["K3_CV", "%.4f" % CVb, "%.4f" % CVf, "%.4f" % (CVf - CVb), "|dCV| <= 0,03", "SI" if abs(CVf - CVb) <= 0.03 else "NO"],
    ["K4_zona_seca_pct", "%.3f" % Sb, "%.3f" % Sf, "%.3f" % (Sf - Sb), "0 % en ambos", "SI" if Sb == 0 and Sf == 0 else "NO"],
    ["K2_D_min", rb["dosis_min_kg_m2_vuelta"], fl["K2_D_min"], "%.4f" % (float(fl["K2_D_min"]) - float(rb["dosis_min_kg_m2_vuelta"])), "-", "-"],
    ["K2_D_max", rb["dosis_max_kg_m2_vuelta"], fl["K2_D_max"], "%.4f" % (float(fl["K2_D_max"]) - float(rb["dosis_max_kg_m2_vuelta"])), "-", "-"],
    ["K4_C(Dmin)_max_dif_1a20_pp", "", "", "%.2f" % dcob, "curvas superpuestas (<= 2 pp, objetivo de trabajo)", "SI" if dcob <= 2 else "NO"],
    ["K6_vn_medio_m_s (rama B: |U| medio)", rb["v_impacto_media"], fl["K6_vn_medio_m_s"], "-", "no comparable 1:1", "-"],
    ["balance_ventana_pct", "~1e-8 (rama B)", "%.3f" % err, "-", "< 1 %", "SI" if abs(err) < 1 else "NO"],
]
with open(os.path.join(a.salida, "F5_puente.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["indicador", "rama_B_" + a.ref, "Fluent_" + a.caso, "diferencia", "criterio", "cumple"])
    w.writerows(filas)
for r in filas:
    print(" | ".join(r))
# perfiles D(z) lado a lado
dB = {round(float(r["z_mm"]), 2): float(r["D_kg_m2_vuelta"]) for r in csv.DictReader(open(os.path.join(RAMA_B, "F4_dosis_por_Z.csv"))) if r["caso"] == a.ref}
dF = [(float(r["s_centro_mm"]), float(r["D_kg_m2_vuelta"])) for r in csv.DictReader(open(os.path.join(a.salida, a.caso + "_dosis_por_banda.csv")))]
with open(os.path.join(a.salida, "F5_perfil_Dz.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["z_mm", "D_rama_B", "D_Fluent", "dif_rel_pct"])
    for z, d in dF:
        b = dB.get(round(z, 2), float("nan"))
        w.writerow(["%.2f" % z, "%.4f" % b, "%.4f" % d, "%.2f" % (100 * (d / b - 1) if b > 0 else float("nan"))])
e = np.array([[dB.get(round(z, 2), np.nan), d] for z, d in dF])
ok = e[:, 0] > 0
rmse = float(np.sqrt(np.mean(((e[ok, 1] - e[ok, 0]) / e[ok, 0].mean()) ** 2)))
print("RMSE relativo del perfil D(z) Fluent vs rama B: %.2f %% de la media" % (100 * rmse))
