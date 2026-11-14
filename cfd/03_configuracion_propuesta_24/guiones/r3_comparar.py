#!/usr/bin/env python3
"""
CORRIDA 3 · T7 · Comparaciones obligatorias (PROMPT_CORRIDA_3 §4 T7) a partir de los KPI de r3_post.py:
  R3_01 (kit, LAT_1 horizontal) frente al Caso Base (G3_A_base_v3, S9: CFD03/06_RESULTADOS/G8/comparacion/CB);
  R3_02 (Caso 2) frente a R3_01 (OD) y frente a G8_C2_OD (Caso 2 sobre el diseno anterior, S9: .../comparacion/C2);
  R3_03 (ramal B) frente a R3_02 (diferencia A<->B); A+B explicito (R3_02 + R3_03) como valor final del Caso 2;
  todo frente a la prediccion N1 (05_VERIF_PREVIA/PREDICCION_N1_O7C2.csv): tabla «N1 / estimado / CFD».
Comprobaciones: franja sin deposito del OD (R3_01 si, R3_02 no), zona seca de la cara inferior = 0 %,
D media de Z3 >= 15,8 (criterio D-047, HIPOTESIS), CV de la cara completa y de Z3 por separado (CV <= 0,4),
fraccion de cada boquilla a abierto_agujero y abierto_lateral (r3_destino.py).
Salidas: 03_FLUENT/resultados/T7_comparacion.csv (formato largo) y T7_N1_vs_CFD.csv; texto en pantalla.
Uso: python -I -B r3_comparar.py
"""
import csv
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")   # la consola de Windows (cp1252) no imprime la barra de D̄

BASE = "D:/CFD_Redosado/CORRIDA_3_O7C2"
FL = BASE + "/03_FLUENT"
KPI = FL + "/resultados/KPI"
REF = "G:/Mi unidad/Semestre X/TESIS II/Sistema de aspersión/CFD03_ANSYS_COMPLETO/06_RESULTADOS/G8/comparacion"
N1 = BASE + "/05_VERIF_PREVIA/PREDICCION_N1_O7C2.csv"
CASOS = [("Base (G3_A_base_v3, S9)", "REF_CB"), ("Caso 2 diseño anterior (G8_C2_OD, S9)", "REF_C2"),
         ("R3_01 kit, LAT_1 horizontal (S9)", "R3_01_kit"), ("R3_02 Caso 2, ramal A (S9)", "R3_02_caso2"),
         ("R3_03 Caso 2, ramal B (S9)", "R3_03_B_caso2"), ("Caso 2 A+B explícito (R3_02 + R3_03)", "R3_02_03_AB")]


def leer_ind(path):
    if not os.path.exists(path):
        return None
    return {r["variante"]: r for r in csv.DictReader(open(path, encoding="utf-8"))}


def kpis(clave):
    """Diccionario {(superficie, variante): fila} con las columnas de combinar_kpi; zonas y tramos si existen."""
    out = {}
    if clave.startswith("REF:"):
        d = REF + "/" + clave[4:]
        for sup in ("od", "cara_inf"):
            I = leer_ind("%s/G7_%s_indicadores.csv" % (d, sup))
            if I:
                for v, r in I.items():
                    out[(sup, v)] = r
        return out
    p = "%s/%s/%s_resumen.csv" % (KPI, clave, clave)
    if not os.path.exists(p):
        return None
    for r in csv.DictReader(open(p, encoding="utf-8")):
        out[(r["superficie"], r["variante"])] = r
    return out


def g(K, sup, var, col):
    try:
        return float(K[(sup, var)][col])
    except (KeyError, TypeError, ValueError):
        return None


def f(v, nd=3):
    return "—" if v is None else ("%.*f" % (nd, v)).replace(".", ",")


FILAS = [("OD", "D̄ 10 mm", "od", "obst_10mm", "D_media", 2), ("OD", "CV 10 mm", "od", "obst_10mm", "CV", 3),
         ("OD", "D_min 10 mm", "od", "obst_10mm", "D_min", 2), ("OD", "zona seca 10 mm %", "od", "obst_10mm", "seca_pct", 2),
         ("OD", "zona seca 2 mm %", "od", "obst_2mm", "seca_pct", 2), ("OD", "η %", "od", "obst_10mm", "eta_pct", 1),
         ("OD bajo z 890-1000", "D̄", "OD_bajo_z890-1000", "obst_10mm", "D_media", 2),
         ("OD bajo z 890-1000", "D_min", "OD_bajo_z890-1000", "obst_10mm", "D_min", 2),
         ("OD alto z 1000-1405", "D̄", "OD_alto_z1000-1405", "obst_10mm", "D_media", 2),
         ("OD alto z 1000-1405", "CV", "OD_alto_z1000-1405", "obst_10mm", "CV", 3),
         ("OD alto z 1000-1405", "D_min", "OD_alto_z1000-1405", "obst_10mm", "D_min", 2),
         ("Cara inferior", "D̄ 10 mm", "cara_inf", "obst_10mm", "D_media", 2),
         ("Cara inferior", "CV 10 mm", "cara_inf", "obst_10mm", "CV", 3),
         ("Cara inferior", "D_min 10 mm", "cara_inf", "obst_10mm", "D_min", 2),
         ("Cara inferior", "zona seca 10 mm %", "cara_inf", "obst_10mm", "seca_pct", 2),
         ("Cara inferior", "zona seca 2 mm %", "cara_inf", "obst_2mm", "seca_pct", 2),
         ("Cara inferior", "η % (INF_EXT+C2+INF_INT)", "cara_inf", "obst_10mm", "eta_pct", 1),
         ("Z1 r 450-521", "D̄", "cara_inf_Z1_aro_interior", "obst_2mm", "D_media", 2),
         ("Z2 r 521-617 (pared proyectada)", "D̄", "cara_inf_Z2_ventana_proyectada", "obst_2mm", "D_media", 2),
         ("Z3 r 617-710", "D̄ (D-047: ≥ 15,8)", "cara_inf_Z3_aro_exterior_sin_PAD", "obst_2mm", "D_media", 2),
         ("Z3 r 617-710", "CV (D-047: ≤ 0,4)", "cara_inf_Z3_aro_exterior_sin_PAD", "obst_2mm", "CV", 3),
         ("Z3 r 617-710", "D_min 2 mm", "cara_inf_Z3_aro_exterior_sin_PAD", "obst_2mm", "D_min", 2)]

K = {c: kpis(c) for _, c in CASOS}
largo = []
print("%-34s %-26s" % ("superficie", "kpi") + "".join(" %12s" % c[:12] for _, c in CASOS))
for supn, lab, sup, var, col, nd in FILAS:
    vals = [g(K[c], sup, var, col) if K[c] else None for _, c in CASOS]
    print("%-34s %-26s" % (supn, lab) + "".join(" %12s" % f(v, nd) for v in vals))
    for (nom, c), v in zip(CASOS, vals):
        largo.append([supn, lab, nom, "" if v is None else "%.6g" % v])
os.makedirs(FL + "/resultados", exist_ok=True)
with open(FL + "/resultados/T7_comparacion.csv", "w", newline="", encoding="utf-8") as fo:
    w = csv.writer(fo)
    w.writerow(["superficie", "kpi", "caso", "valor"])
    w.writerows(largo)
# franjas sin deposito del OD
for _, c in CASOS[2:]:
    p = "%s/%s/%s_od_franja.csv" % (KPI, c, c)
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding="utf-8")):
            print("franja OD %-16s %-20s %s bandas de 2 mm: z %s" % (c, r["columna"], r["bandas_2mm_sin_deposito"], r["tramos_z_mm"]))
# destino por boquilla
for _, c in CASOS[2:5]:
    p = "%s/resultados/destino_%s.csv" % (FL, c)
    if os.path.exists(p):
        print("destino %s:" % c)
        for r in csv.DictReader(open(p, encoding="utf-8")):
            print("   %-10s agujero %6s %% | lateral %6s %% | od %6s %% | cara_inf %6s %% | inferior %6s %% | total %s %%" % (
                r["boquilla"], r.get("pct_abierto_agujero", "—"), r.get("pct_abierto_lateral", "—"), r.get("pct_od", "—"),
                r.get("pct_cara_inf", "—"), r.get("pct_abierto_inferior", "—"), r["pct_total"]))
# N1 / estimado / CFD
mapa = {  # (superficie N1, caso N1, magnitud) -> (clave de caso CFD, sup, var, col)
    ("cara_inferior", "O7+C2 (kit)", "D_media_A+B"): ("cara_inf", "obst_10mm", "D_media"),
    ("cara_inferior", "O7+C2 (kit)", "CV"): ("cara_inf", "obst_10mm", "CV"),
    ("cara_inferior", "O7+C2 (kit)", "D_min_10mm"): ("cara_inf", "obst_10mm", "D_min"),
    ("cara_inferior", "O7+C2 (kit)", "zona_seca_10mm_pct"): ("cara_inf", "obst_10mm", "seca_pct"),
    ("cara_inferior", "O7+C2 (kit)", "D_min_2mm"): ("cara_inf", "obst_2mm", "D_min"),
    ("cara_inferior", "O7+C2 (kit)", "Z1_D_media"): ("cara_inf_Z1_aro_interior", "obst_2mm", "D_media"),
    ("cara_inferior", "O7+C2 (kit)", "Z2_D_media"): ("cara_inf_Z2_ventana_proyectada", "obst_2mm", "D_media"),
    ("cara_inferior", "O7+C2 (kit)", "Z3_D_media"): ("cara_inf_Z3_aro_exterior_sin_PAD", "obst_2mm", "D_media"),
    ("OD", "O7+C2 + Caso 2", "D_media_A+B"): ("od", "obst_10mm", "D_media"),
    ("OD", "O7+C2 + Caso 2", "CV"): ("od", "obst_10mm", "CV"),
    ("OD", "O7+C2 + Caso 2", "D_min_10mm"): ("od", "obst_10mm", "D_min"),
    ("OD", "O7+C2 + Caso 2", "zona_seca_2mm"): ("od", "obst_2mm", "seca_pct"),
}
n1 = []
for r in csv.DictReader(open(N1, encoding="utf-8")):
    k = (r["superficie"], r["caso"], r["magnitud"])
    if k in mapa:
        sup, var, col = mapa[k]
        cfd = {c: g(K[c], sup, var, col) if K[c] else None for c in ("R3_01_kit", "R3_02_caso2", "R3_02_03_AB")}
        n1.append([r["superficie"], r["caso"], r["magnitud"], r["valor_N1"], r["estimado_CFD"]] +
                  ["" if cfd[c] is None else "%.4g" % cfd[c] for c in ("R3_01_kit", "R3_02_caso2", "R3_02_03_AB")])
with open(FL + "/resultados/T7_N1_vs_CFD.csv", "w", newline="", encoding="utf-8") as fo:
    w = csv.writer(fo)
    w.writerow(["superficie", "caso_N1", "magnitud", "N1", "estimado_CFD_calibrado", "CFD_R3_01_S9", "CFD_R3_02_S9",
                "CFD_Caso2_AB"])
    w.writerows(n1)
print("N1 / estimado / CFD:")
for r in n1:
    print("   " + " | ".join(r))
# INFORME_R3_comparacion.md (traspaso a la siguiente sesion; Jean recibe lo mismo en el PDF)
md = ["# INFORME_R3_comparacion — T7 (generado por r3_comparar.py; no editar a mano)", "",
      "Fuentes: `resultados/KPI/<caso>/<caso>_resumen.csv` (r3_post.py), `KPI/REF_*` (r3_ref_resumen.py), "
      "`05_VERIF_PREVIA/PREDICCION_N1_O7C2.csv`, `resultados/destino_*.csv`. Con obstaculos; ventana 25-50 ms.", "",
      "| superficie | kpi | " + " | ".join(c for _, c in CASOS) + " |", "|---|---|" + "---|" * len(CASOS)]
for supn, lab, sup, var, col, nd in FILAS:
    md.append("| %s | %s | " % (supn, lab) + " | ".join(f(g(K[c], sup, var, col) if K[c] else None, nd) for _, c in CASOS) + " |")
md += ["", "## N1 / estimado / CFD", "", "| superficie | caso N1 | magnitud | N1 | estimado | R3_01 S9 | R3_02 S9 | Caso 2 A+B |",
       "|---|---|---|---|---|---|---|---|"] + ["| " + " | ".join(r) + " |" for r in n1]
for _, c in CASOS[2:]:
    p = "%s/%s/%s_od_franja.csv" % (KPI, c, c)
    if os.path.exists(p):
        md += [""] + ["- franja sin deposito del OD, %s, %s: %s bandas de 2 mm, z %s" % (
            c, r["columna"], r["bandas_2mm_sin_deposito"], r["tramos_z_mm"]) for r in csv.DictReader(open(p, encoding="utf-8"))]
open(FL + "/resultados/INFORME_R3_comparacion.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
