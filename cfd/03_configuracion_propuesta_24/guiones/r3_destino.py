#!/usr/bin/env python3
"""
CORRIDA 3 · T7 · Destino del caudal de cada boquilla en una corrida: fraccion de su caudal inyectado que sale por
cada muestra DPM (od, cara_inf, abierto_*) en la ventana [t0, t1) — p. ej. cuanto de la boquilla C2 pasa bajo el aro
y entra al agujero (abierto_agujero; N1 predijo ~17 %) y cuanto escapa por los costados del sector (abierto_lateral;
R3_10 solo si > 2 % del caudal). Misma aritmetica que procesar_caso.py (masa en la ventana / duracion).
Uso: python -I -B r3_destino.py <carpeta del caso> --salida <csv> [--t0 0.025 --t1 0.050]
"""
import argparse
import csv
import glob
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "post_cfd03"))
from lector_impactos import leer  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("carpeta")
ap.add_argument("--salida", required=True)
ap.add_argument("--t0", type=float, default=0.025)
ap.add_argument("--t1", type=float, default=0.050)
a = ap.parse_args()
C = a.carpeta.rstrip("/\\")
tag = os.path.basename(C)
jou = open(os.path.join(C, tag + ".jou")).read()
iny = {}
for t in re.findall(r'"([^"]+\.dpm)"', jou):
    s = 0.0
    for ln in open(t):
        m = re.match(r"\(\(\s*(.*?)\)\s*(\S+)\)\s*$", ln.strip())
        if m:
            s += float(m.group(1).split()[8])
    iny[os.path.splitext(os.path.basename(t))[0].lower()] = s
zonas = [os.path.splitext(os.path.basename(p))[0] for p in sorted(glob.glob(os.path.join(C, "*.csv")))]
zonas = [z for z in zonas if z in ("od", "cara_inf") or z.startswith("abierto_")]
tab = {b: {} for b in iny}
for z in zonas:
    R = leer(os.path.join(C, z + ".csv"), ["masa", "t"], texto=("boquilla",), filtro_t=(a.t0, a.t1))
    if "boquilla" not in R or not len(R["boquilla"]):
        continue
    bq = np.array([str(x).lower() for x in R["boquilla"]], dtype=object)
    for b in iny:
        tab[b][z] = R["masa"][bq == b].sum() / (a.t1 - a.t0)
with open(a.salida, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["boquilla", "inyectado_kg_s"] + ["pct_" + z for z in zonas] + ["pct_total"])
    for b, m in iny.items():
        pc = [100 * tab[b].get(z, 0.0) / m for z in zonas]
        w.writerow([b, "%.6f" % m] + ["%.3f" % p for p in pc] + ["%.3f" % sum(pc)])
        print("%-10s " % b + " ".join("%s %.2f" % (z.replace("abierto_", "ab_"), p) for z, p in zip(zonas, pc)) +
              " | total %.2f %%" % sum(pc))
