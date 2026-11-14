#!/usr/bin/env python3
"""
G7 - Caso Base COMPLETO de las 22 boquillas de R05: KPIs por superficie (libre y con obstaculos R05) y
balance global frente a la red de 22 (202,59 L/min).

Aportes por superficie (CSV de impactos de dpm2csv.py en D:/CFD03_run/<fase>/<caso>/<zona>.csv):
  OD       : ramal A (G3) + ramal B (G4, explicito; si falta, A x 2 por S9)
  cara_inf : INF_EXT A (G3) + INF_EXT B (G4) + INF_INT (sector G5_INT); LAT_5 incluido por si deposita
  sup      : SUP_1-2 ramal A (G6_ESUP_base) x 2 (S9, verificado en G4 sobre el OD)
  agujero  : INT_1-5 + INF_INT (F5_red22; si falta, F5 de CFD02 escalado por boquilla a la red de 22)
Mascaras de obstaculos: 06_RESULTADOS/G1_G2_rayos/K1_22boq_mascaras.npz (rayos_r05.py).
Uso: python caso_base_22.py --casos casos_G7.json --salida 06_RESULTADOS/G7
casos_G7.json: {"G3": ["D:/CFD03_run/G3/G3_A_base", t0, t1], "G4": [...], "INT": [...], "ESUP": [...], "F5": [...]}
"""
import argparse
import csv
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
MASC = os.path.join(RAIZ, "06_RESULTADOS", "G1_G2_rayos", "K1_22boq_v2_mascaras.npz")   # v2: INF con 1200 rayos (S17)
B22 = json.load(open(os.path.join(RAIZ, "03_GEOMETRIA", "boquillas_22.json")))["boquillas"]
F5_Q = {"int_1": 9.13621, "int_2": 9.1436, "int_3": 9.1523, "int_4": 9.16194, "int_5": 9.17216, "inf_int": 9.11767}


def ap(caso, zona, boqs, fac, masc):
    c, t0, t1 = caso
    return "%s/%s.csv|%s|%s|%s|%s|%s" % (c, zona, ",".join(boqs), fac, t0, t1, ",".join(masc))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--casos", required=True)
    p.add_argument("--salida", required=True)
    a = p.parse_args()
    C = json.load(open(a.casos))
    os.makedirs(a.salida, exist_ok=True)
    LATA = ["lat_%d_a" % i for i in range(1, 6)] + ["inf_ext_a"]
    LATB = ["lat_%d_b" % i for i in range(1, 6)] + ["inf_ext_b"]
    mA = [b.upper() for b in LATA]
    mB = [b.upper() for b in LATB]
    iny = {k: v["mdot_kg_s"] for k, v in B22.items()}
    tareas, iny_sup = {}, {}
    # Ramal B = ramal A (S9, verificado en G4 con el par de 150 rayos G4_B_base / G3_A_base). Se usa la corrida del
    # ramal A con INF_EXT a 1200 rayos (G3_A_base_v2) para A y para B; las mascaras de B son las propias de B
    # (identicas a las de A por simetria). G4 (150 rayos) no se mezcla en el Caso Base: su cara inferior no convergio.
    # OD. Si se da "G4" (ramal B explicito con la MISMA discretizacion S18), se usa: promedia dos realizaciones del
    # flujo acoplado (A y B son geometricamente identicos; su diferencia es ruido de corrida, G4_S9_A_vs_B_S18).
    LATB = [b.replace("_a", "_b") for b in LATA]
    if "G4" in C:
        tareas["od"] = ([ap(C["G3"], "od", [b], 1, [b.upper()]) for b in LATA] +
                        [ap(C["G4"], "od", [b], 1, [b.upper()]) for b in LATB])
    else:
        tareas["od"] = ([ap(C["G3"], "od", [b], 1, [b.upper()]) for b in LATA] +
                        [ap(C["G3"], "od", [b], 1, [b.upper().replace("_A", "_B")]) for b in LATA])
    iny_sup["od"] = 2 * sum(B22[b.upper()]["mdot_kg_s"] for b in LATA)
    # cara inferior: INF_EXT A + B y INF_INT (LAT_5 no llega; se incluye por si deposita)
    ci = []
    for b in ("inf_ext_a", "lat_5_a"):
        ci += [ap(C["G3"], "cara_inf", [b], 1, [b.upper()])]
        ci += ([ap(C["G4"], "cara_inf", [b.replace("_a", "_b")], 1, [b.upper().replace("_A", "_B")])] if "G4" in C
               else [ap(C["G3"], "cara_inf", [b], 1, [b.upper().replace("_A", "_B")])])
    if "INT" in C:
        ci += [ap(C["INT"], "cara_inf", ["inf_int"], 1, ["INF_INT"])]
    tareas["cara_inf"] = ci
    iny_sup["cara_inf"] = 2 * B22["INF_EXT_A"]["mdot_kg_s"] + B22["INF_INT"]["mdot_kg_s"]
    # cara superior (S9)
    if "ESUP" in C:
        tareas["sup"] = [ap(C["ESUP"], "sup", [b], 2, [b.upper()]) for b in ("sup_1_a", "sup_2_a")]
        iny_sup["sup"] = 2 * (B22["SUP_1_A"]["mdot_kg_s"] + B22["SUP_2_A"]["mdot_kg_s"])
    # agujero (lanza completa, incluida INF_INT)
    if "F5" in C:
        tareas["agujero"] = [ap(C["F5"], "pared_agujero", [b], 1, [b.upper()]) for b in F5_Q]
    elif "F5_CFD02" in C:
        tareas["agujero"] = [ap(C["F5_CFD02"], "pared_agujero", [b], "%.6f" % (B22[b.upper()]["q_Lmin"] / F5_Q[b]),
                                [b.upper()]) for b in F5_Q]
    iny_sup["agujero"] = sum(B22[b.upper()]["mdot_kg_s"] for b in F5_Q)
    for sup, aps in tareas.items():
        cmd = [sys.executable, os.path.join(AQUI, "combinar_kpi.py"), "--superficie", sup, "--caso", "G7_" + sup,
               "--salida", a.salida, "--mascaras", MASC, "--mdot-inyectado", "%.6f" % iny_sup[sup]] + \
              sum([["--aporte", x] for x in aps], [])
        r = subprocess.run(cmd, capture_output=True, text=True)
        print("== %s\n%s%s" % (sup, r.stdout, r.stderr[-800:]))


if __name__ == "__main__":
    main()
