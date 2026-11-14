#!/usr/bin/env python3
"""Combina la corrida A, su espejo S9 y G5_INT_base_v2 con las mascaras O7+C2.

Uso: python post_o7c2.py --nuevo D:/CFD03_run/G3/G3_A_O7_O4 \
     --g5 D:/CFD03_run/G5/G5_INT_base_v2 --salida D:/CFD03_run/G3/G3_A_O7_O4/KPI
Requiere que dpm2csv.py haya convertido od.dpm y cara_inf.dpm en ambos casos.
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = argparse.ArgumentParser()
P.add_argument("--nuevo", required=True)
P.add_argument("--g5", required=True)
P.add_argument("--salida", required=True)
a = P.parse_args()

B = json.load(open(os.path.join(HERE, "boquillas_O7_C2.json"), encoding="utf-8"))["boquillas"]
IDS = [*(f"LAT_{i}_A" for i in range(1, 6)), "INF_EXT_A", "C2_A"]
MASC = os.path.join(HERE, "K1_O7C2_mascaras.npz")
os.makedirs(a.salida, exist_ok=True)

for folder, zone in ((a.nuevo, "od"), (a.nuevo, "cara_inf"), (a.g5, "cara_inf")):
    dp = os.path.join(folder, zone + ".dpm")
    cs = os.path.join(folder, zone + ".csv")
    if not os.path.exists(cs) or (os.path.exists(dp) and os.path.getmtime(cs) < os.path.getmtime(dp)):
        if not os.path.exists(dp):
            raise SystemExit(f"Falta {dp} y tampoco existe {cs}")
        subprocess.run([sys.executable, os.path.join(HERE, "dpm2csv.py"), dp, cs], check=True)


def aporte(carpeta, zona, boq, clave):
    return f"{os.path.join(carpeta, zona + '.csv')}|{boq.lower()}|1|0.025|0.050|{clave}"


for sup in ("od", "cara_inf"):
    args = [sys.executable, os.path.join(HERE, "combinar_kpi.py"),
            "--superficie", sup, "--caso", "G3_A_O7_O4_" + sup,
            "--salida", a.salida, "--mascaras", MASC]
    for ident in IDS:
        if sup == "cara_inf" and ident not in ("LAT_5_A", "INF_EXT_A", "C2_A"):
            continue
        args += ["--aporte", aporte(a.nuevo, sup, ident, ident)]
        args += ["--aporte", aporte(a.nuevo, sup, ident, ident[:-1] + "B")]
    if sup == "cara_inf":
        args += ["--aporte", aporte(a.g5, sup, "INF_INT", "INF_INT")]
        mdot = 2 * (B["INF_EXT_A"]["mdot_kg_s"] + B["C2_A"]["mdot_kg_s"]) + B["INF_INT"]["mdot_kg_s"]
    else:
        mdot = 2 * sum(B[i]["mdot_kg_s"] for i in IDS)
    args += ["--mdot-inyectado", f"{mdot:.12g}"]
    print("EJECUTANDO:", subprocess.list2cmdline(args), flush=True)
    subprocess.run(args, check=True)
print("Hecho. Z2 es la pared proyectada de la malla L; no asignar su dosis a rodillos.")
