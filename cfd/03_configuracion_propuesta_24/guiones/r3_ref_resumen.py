#!/usr/bin/env python3
"""
CORRIDA 3 · T7 · Resumen de KPI de las referencias con el MISMO formato que r3_post.py (<tag>_resumen.csv), para
compararlas fila a fila: Caso Base (CB) y Caso 2 del diseno anterior (C2), ambos S9 con mascaras de 22 boquillas,
de CFD03/06_RESULTADOS/G8/comparacion/{CB,C2} (SOLO LECTURA: se leen indicadores y bandas; no se recalcula nada).
Anade las zonas Z1/Z2/Z3 (reparto_zonas.py del kit sobre las bandas de 2 mm) y el OD bajo/alto (misma funcion que
r3_post.py sobre las bandas de 10 y 2 mm).
Salida: 03_FLUENT/resultados/KPI/REF_CB/REF_CB_resumen.csv y REF_C2/REF_C2_resumen.csv
Uso: python -I -B r3_ref_resumen.py
"""
import csv
import math
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
FL = "D:/CFD_Redosado/CORRIDA_3_O7C2/03_FLUENT"
REF = "G:/Mi unidad/Semestre X/TESIS II/Sistema de aspersión/CFD03_ANSYS_COMPLETO/06_RESULTADOS/G8/comparacion"


def kpi_tramo(filas, lo, hi, col="D_obst_media_theta"):     # copia de r3_post.py
    sel = [r for r in filas if lo <= float(r["s_centro_mm"]) < hi and float(r["area_mojable_m2"]) > 0]
    A = sum(float(r["area_mojable_m2"]) for r in sel)
    D = [float(r[col]) for r in sel]
    W = [float(r["area_mojable_m2"]) for r in sel]
    Dm = sum(d * w for d, w in zip(D, W)) / A
    pos = [d for d in D if d > 0]
    mu = sum(pos) / len(pos)
    cv = math.sqrt(sum((d - mu) ** 2 for d in pos) / len(pos)) / mu if len(pos) > 1 else float("nan")
    seca = 100 * sum(w for d, w in zip(D, W) if d <= 1e-9) / A
    return dict(D_media=Dm, CV=cv, D_min=min(D), D_max=max(D), seca_pct=seca, n_bandas=len(sel))


for ref in ("CB", "C2"):
    tag = "REF_" + ref
    out = os.path.join(FL, "resultados", "KPI", tag)
    os.makedirs(out, exist_ok=True)
    filas = []
    for sup in ("od", "cara_inf"):
        ind = {r["variante"]: r for r in csv.DictReader(open("%s/%s/G7_%s_indicadores.csv" % (REF, ref, sup), encoding="utf-8"))}
        for var in ("obst_10mm", "obst_2mm", "libre_10mm"):
            v = ind[var]
            filas.append([sup, var] + [v.get(c, "") for c in ("D_media", "CV", "D_min", "D_min_celdas", "seca_pct",
                                                               "seca_celdas_pct", "J_media", "eta_pct", "cob5_pct")])
    zon = os.path.join(out, tag + "_zonas.csv")
    subprocess.run([sys.executable, "-I", os.path.join(AQUI, "kit", "reparto_zonas.py"),
                    "%s/%s/G7_cara_inf_bandas_2mm.csv" % (REF, ref), zon], check=True, capture_output=True)
    for row in csv.DictReader(open(zon, encoding="utf-8")):
        filas.append(["cara_inf_" + row["zona"], "obst_2mm", row["D_media_kg_m2_vuelta"], row["CV_bandas"],
                      row["D_min_bandas"], "", row["seca_pct"], "", row["J_media_Ns_m2_vuelta"], "", ""])
    for res in ("10mm", "2mm"):
        B = list(csv.DictReader(open("%s/%s/G7_od_bandas_%s.csv" % (REF, ref, res), encoding="utf-8")))
        for nombre, lo, hi in (("OD_bajo_z890-1000", 890, 1000), ("OD_alto_z1000-1405", 1000, 1406),
                               ("OD_completo", 890, 1406)):
            k = kpi_tramo(B, lo, hi)
            filas.append([nombre, "obst_" + res, "%.6g" % k["D_media"], "%.6g" % k["CV"], "%.6g" % k["D_min"], "",
                          "%.6g" % k["seca_pct"], "", "", "", ""])
    with open(os.path.join(out, tag + "_resumen.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["superficie", "variante", "D_media", "CV", "D_min", "D_min_celdas", "seca_pct", "seca_celdas_pct",
                    "J_media", "eta_pct", "cob5_pct"])
        w.writerows(filas)
    print(tag, "->", out)
