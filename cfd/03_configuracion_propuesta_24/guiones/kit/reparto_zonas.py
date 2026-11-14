#!/usr/bin/env python3
"""Agrega por Z1/Z2/Z3 las bandas de 2 mm producidas por combinar_kpi.py.

Uso: python reparto_zonas.py KPI/G3_A_O7_O4_cara_inf_bandas_2mm.csv KPI/zonas.csv
La columna area_mojable_m2 de combinar_kpi ya excluye contacto PAD.
"""
import csv
import math
import sys

if len(sys.argv) != 3:
    raise SystemExit(__doc__)
src, dst = sys.argv[1:]
ZONES = (("Z1_aro_interior", .4501, .5215),
         ("Z2_ventana_proyectada", .5215, .6175),
         ("Z3_aro_exterior_sin_PAD", .6175, .7100))
with open(src, newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
out = []
for name, lo, hi in ZONES:
    parts = []
    for r in rows:
        c = float(r["s_centro_mm"]) / 1000
        b0, b1 = c - .001, min(c + .001, .710)
        x0, x1 = max(lo, b0), min(hi, b1)
        if x1 <= x0:
            continue
        frac = (x1 * x1 - x0 * x0) / (b1 * b1 - b0 * b0)
        area = float(r["area_mojable_m2"]) * frac
        parts.append((area, float(r["D_obst_media_theta"]), float(r["J_obst"])))
    area = sum(p[0] for p in parts)
    ds = [p[1] for p in parts if p[1] > 0]
    dmean = sum(p[0] * p[1] for p in parts) / area
    jmean = sum(p[0] * p[2] for p in parts) / area
    cv = math.sqrt(sum((x - sum(ds)/len(ds))**2 for x in ds)/len(ds)) / (sum(ds)/len(ds)) if len(ds)>1 else float("nan")
    dry = 100 * sum(p[0] for p in parts if p[1] <= 1e-9) / area
    out.append((name, f"{lo:.4f}", f"{hi:.4f}", f"{area:.8g}", f"{dmean:.8g}",
                f"{jmean:.8g}", f"{cv:.8g}", f"{min(p[1] for p in parts):.8g}", f"{dry:.8g}"))
with open(dst, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(("zona", "r_min_m", "r_max_m", "area_mojable_m2", "D_media_kg_m2_vuelta",
                "J_media_Ns_m2_vuelta", "CV_bandas", "D_min_bandas", "seca_pct"))
    w.writerows(out)
print(dst)
