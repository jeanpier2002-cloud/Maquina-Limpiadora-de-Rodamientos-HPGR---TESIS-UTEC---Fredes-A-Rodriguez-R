#!/usr/bin/env python3
"""
CORRIDA 3 · T6 · Post-proceso de KPI (K2-K6) de OD y cara inferior. Copia de post_o7c2.py del kit con
(PROMPT_CORRIDA_3 §4 T6):
  (a) dos modos de ramal B: S9 (espejo de la corrida A, como el kit) o A+B explicito (--b: corrida del ramal B,
      como caso_base_22.py/G7 hizo con G4 para el Caso Base);
  (b) INF_INT de G5_INT_base_v2 con la ventana de la base, 0,070-0,100 s (el kit usaba 0,025-0,050; F5 del analisis);
  (c) mascaras elegibles (--mascaras: las del kit para LAT_1 horizontal, K1_O7C2_Caso2_mascaras.npz para el Caso 2);
  (d) las 7 inyecciones del ramal entran en ambas superficies (las que no llegan aportan 0; el kit omitia LAT_1-4
      en la cara inferior). El caudal inyectado de referencia (eta) es el del kit: OD = 2 x 7 boquillas;
      cara inferior = 2 x (INF_EXT + boquilla C2) + INF_INT.
Despues: reparto_zonas.py (Z1/Z2/Z3) sobre las bandas de 2 mm de la cara inferior y KPI del OD bajo/alto
(z 890-1000 y 1000-1405 mm) sobre las bandas de 10 mm; franja sin deposito del OD en bandas de 2 mm.
combinar_kpi.py, reparto_zonas.py y dpm2csv.py son las copias sin cambios del kit.

Uso: python -I -B r3_post.py --a <corrida A> [--b <corrida B>] --mascaras <npz> --salida <dir> --tag <nombre>
     [--g5 D:/CFD03_run/G5/G5_INT_base_v2] [--ventana 0.025 0.050] [--ventana-int 0.070 0.100]
Salidas en <salida>: <tag>_{od,cara_inf}_{indicadores,bandas_10mm,bandas_2mm,aportes,mapa10mm}, <tag>_zonas.csv,
<tag>_od_alto_bajo.csv, <tag>_od_franja.csv, <tag>_resumen.csv
"""
import argparse
import csv
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = argparse.ArgumentParser()
P.add_argument("--a", required=True)
P.add_argument("--b", default=None)
P.add_argument("--g5", default="D:/CFD03_run/G5/G5_INT_base_v2")
P.add_argument("--mascaras", required=True)
P.add_argument("--salida", required=True)
P.add_argument("--tag", required=True)
P.add_argument("--ventana", nargs=2, type=float, default=[0.025, 0.050])
P.add_argument("--ventana-int", nargs=2, type=float, default=[0.070, 0.100])
P.add_argument("--sufijo-a", default="A", help="ramal de la corrida --a (A, o B si se quiere espejar una corrida B)")
a = P.parse_args()

B = json.load(open(os.path.join(HERE, "boquillas_O7_C2.json"), encoding="utf-8"))["boquillas"]
BASE7 = ["LAT_1", "LAT_2", "LAT_3", "LAT_4", "LAT_5", "INF_EXT", "C2"]
os.makedirs(a.salida, exist_ok=True)
carpetas = [(a.a, "od"), (a.a, "cara_inf"), (a.g5, "cara_inf")] + ([(a.b, "od"), (a.b, "cara_inf")] if a.b else [])
for folder, zone in carpetas:
    dp = os.path.join(folder, zone + ".dpm")
    cs = os.path.join(folder, zone + ".csv")
    if not os.path.exists(cs) or (os.path.exists(dp) and os.path.getmtime(cs) < os.path.getmtime(dp)):
        if not os.path.exists(dp):
            raise SystemExit(f"Falta {dp} y tampoco existe {cs}")
        subprocess.run([sys.executable, "-I", os.path.join(HERE, "dpm2csv.py"), dp, cs], check=True)


def aporte(carpeta, zona, boq, clave, t0, t1):
    return f"{os.path.join(carpeta, zona + '.csv')}|{boq.lower()}|1|{t0}|{t1}|{clave}"


t0, t1 = a.ventana
sa = a.sufijo_a
sb = "B" if sa == "A" else "A"
res = {}
for sup in ("od", "cara_inf"):
    caso = "%s_%s" % (a.tag, sup)
    args = [sys.executable, "-I", os.path.join(HERE, "combinar_kpi.py"), "--superficie", sup, "--caso", caso,
            "--salida", a.salida, "--mascaras", a.mascaras]
    for n in BASE7:
        ia, ib = "%s_%s" % (n, sa), "%s_%s" % (n, sb)
        args += ["--aporte", aporte(a.a, sup, ia, ia, t0, t1)]
        if a.b:
            args += ["--aporte", aporte(a.b, sup, ib, ib, t0, t1)]
        else:
            args += ["--aporte", aporte(a.a, sup, ia, ib, t0, t1)]      # S9: la corrida A con la mascara de B
    if sup == "cara_inf":
        args += ["--aporte", aporte(a.g5, sup, "INF_INT", "INF_INT", *a.ventana_int)]
        mdot = 2 * (B["INF_EXT_A"]["mdot_kg_s"] + B["C2_A"]["mdot_kg_s"]) + B["INF_INT"]["mdot_kg_s"]
    else:
        mdot = 2 * sum(B["%s_A" % n]["mdot_kg_s"] for n in BASE7)
    args += ["--mdot-inyectado", f"{mdot:.12g}"]
    print("EJECUTANDO:", subprocess.list2cmdline(args), flush=True)
    r = subprocess.run(args, capture_output=True, text=True)
    print(r.stdout + r.stderr, flush=True)
    if r.returncode:
        raise SystemExit("combinar_kpi fallo en " + sup)
    res[sup] = {row["variante"]: row for row in csv.DictReader(open(os.path.join(a.salida, caso + "_indicadores.csv")))}

# zonas de la cara inferior (reparto_zonas.py del kit, bandas de 2 mm)
zon = os.path.join(a.salida, a.tag + "_zonas.csv")
subprocess.run([sys.executable, "-I", os.path.join(HERE, "reparto_zonas.py"),
                os.path.join(a.salida, a.tag + "_cara_inf_bandas_2mm.csv"), zon], check=True)


def kpi_tramo(filas, lo, hi, col="D_obst_media_theta"):
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


b10 = list(csv.DictReader(open(os.path.join(a.salida, a.tag + "_od_bandas_10mm.csv"))))
b2 = list(csv.DictReader(open(os.path.join(a.salida, a.tag + "_od_bandas_2mm.csv"))))
tramos = []
for nombre, lo, hi in (("OD_bajo_z890-1000", 890, 1000), ("OD_alto_z1000-1405", 1000, 1406), ("OD_completo", 890, 1406)):
    for res_mm, F in (("10mm", b10), ("2mm", b2)):
        k = kpi_tramo(F, lo, hi)
        tramos.append([nombre, res_mm] + ["%.6g" % k[c] for c in ("D_media", "CV", "D_min", "D_max", "seca_pct")] + [k["n_bandas"]])
with open(os.path.join(a.salida, a.tag + "_od_alto_bajo.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["tramo", "bandas", "D_media", "CV", "D_min", "D_max", "seca_pct", "n_bandas"])
    w.writerows(tramos)
# franja sin deposito del OD (bandas de 2 mm, libre y con obstaculos)
secas = []
for col in ("D_libre", "D_obst_media_theta"):
    z = [float(r["s_centro_mm"]) for r in b2 if float(r[col]) <= 1e-9 and float(r["area_mojable_m2"]) > 0]
    tr, ini, prev = [], None, None
    for zz in z:
        if ini is None:
            ini = prev = zz
        elif zz - prev > 2.01:
            tr.append((ini, prev)); ini = prev = zz
        else:
            prev = zz
    if ini is not None:
        tr.append((ini, prev))
    secas.append([col, len(z), " ; ".join("%.0f-%.0f" % (x - 1, y + 1) for x, y in tr) or "ninguna"])
with open(os.path.join(a.salida, a.tag + "_od_franja.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["columna", "bandas_2mm_sin_deposito", "tramos_z_mm"])
    w.writerows(secas)
# resumen
filas = []
for sup in ("od", "cara_inf"):
    for var in ("obst_10mm", "obst_2mm", "libre_10mm"):
        v = res[sup][var]
        filas.append([sup, var] + [v.get(c, "") for c in ("D_media", "CV", "D_min", "D_min_celdas", "seca_pct",
                                                           "seca_celdas_pct", "J_media", "eta_pct", "cob5_pct")])
for row in csv.DictReader(open(zon, encoding="utf-8")):
    filas.append(["cara_inf_" + row["zona"], "obst_2mm", row["D_media_kg_m2_vuelta"], row["CV_bandas"],
                  row["D_min_bandas"], "", row["seca_pct"], "", row["J_media_Ns_m2_vuelta"], "", ""])
for t in tramos:   # t = [tramo, bandas, D_media, CV, D_min, D_max, seca_pct, n_bandas]
    filas.append([t[0], "obst_" + t[1], t[2], t[3], t[4], "", t[6], "", "", "", ""])
with open(os.path.join(a.salida, a.tag + "_resumen.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["superficie", "variante", "D_media", "CV", "D_min", "D_min_celdas", "seca_pct", "seca_celdas_pct",
                "J_media", "eta_pct", "cob5_pct"])
    w.writerows(filas)
for s in secas:
    print("franja sin deposito OD (%s): %s bandas de 2 mm; z %s" % tuple(s))
print("Hecho %s (%s). Z2 es la pared proyectada de la malla L; no asignar su dosis a rodillos." % (
    a.tag, "A+B explicito" if a.b else "S9"))
