#!/usr/bin/env python3
# v3 (CORRIDA 2, 24/10/2026): copia de CORRIDA_1_13a21oct/06_VOF/scripts/run_log.py con rutas cambiadas a 02_VOF_v3 y /home/piermoto/vof3 (sed); sin otros cambios.
"""Construye 06_VOF/run_log.csv a partir de logs/e1 y logs/e2 (resumen.txt, meta.json, log.interFoam.gz).
Columnas: etapa, caso, malla, celdas, dx_min_m, maxCo, modelo, np, pasos, t_fin_s, dt_medio_s, dt_min_s,
dt_max_s, Co_max_ultimo, alphaCo_max_ultimo, pared_s, pared_h, s_por_paso, RAM_max_MB, End, FATAL.
Uso: python run_log.py
"""
import csv
import glob
import gzip
import json
import os
import re

import numpy as np

BASE = "D:/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3"
filas = []
for et in ("e1", "e2"):
    for d in sorted(glob.glob(f"{BASE}/logs/{et}/*/")):
        caso = os.path.basename(d.rstrip("/\\"))
        if not os.path.exists(d + "resumen.txt") or not os.path.exists(d + "meta.json"):
            continue
        meta = json.load(open(d + "meta.json"))
        res = open(d + "resumen.txt").read()
        g = lambda k: (re.search(k + r"=(\S+)", res) or [None, ""])[1]
        ram = re.search(r"Maximum resident set size \(kbytes\): (\d+)", res)
        dts, cos, acos, ts = [], [], [], []
        if os.path.exists(d + "log.interFoam.gz"):
            with gzip.open(d + "log.interFoam.gz", "rt", errors="ignore") as f:
                for ln in f:
                    if ln.startswith("deltaT = "):
                        dts.append(float(ln.split()[2]))
                    elif ln.startswith("Courant Number mean"):
                        cos.append(float(ln.split()[-1]))
                    elif ln.startswith("Interface Courant Number"):
                        acos.append(float(ln.split()[-1]))
                    elif ln.startswith("Time = "):
                        ts.append(float(ln.split()[2]))
        dts = np.array(dts)
        if et == "e1":
            m = meta["malla"]
            malla, celdas, dx = f"N{meta['N']}", m["celdas"], min(m["dx_min"], m["dy_min"])
            modelo = meta["modelo"]
        else:
            m = meta["info"]
            malla, celdas, dx = meta["malla"], m["celdas"], min(m["dr_pared"], m["dy_min"], m["dz"])
            modelo = "laminar"
        pared = float(g("pared_s") or "nan")
        pasos = int(g("pasos") or 0)
        filas.append(dict(etapa=et, caso=caso, malla=malla, celdas=celdas, dx_min_m=f"{dx:.4g}", maxCo=meta["co"],
                          modelo=modelo, np=g("np"), pasos=pasos, t_fin_s=f"{ts[-1]:.6g}" if ts else "",
                          dt_medio_s=f"{dts.mean():.4g}" if len(dts) else "",
                          dt_min_s=f"{dts[len(dts)//10:].min():.4g}" if len(dts) > 10 else "",
                          dt_max_s=f"{dts.max():.4g}" if len(dts) else "",
                          Co_max_ultimo=f"{cos[-1]:.3g}" if cos else "", alphaCo_max_ultimo=f"{acos[-1]:.3g}" if acos else "",
                          pared_s=pared, pared_h=f"{pared / 3600:.3f}", s_por_paso=f"{pared / max(pasos, 1):.4g}",
                          RAM_max_MB=f"{int(ram[1]) / 1024:.0f}" if ram else "", End=g("End"), FATAL=g("FATAL")))
with open(f"{BASE}/run_log.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(filas[0]))
    w.writeheader()
    w.writerows(filas)
for r in filas:
    print(r["etapa"], r["caso"], r["celdas"], r["pasos"], r["t_fin_s"], r["dt_medio_s"], r["pared_h"], r["End"], r["FATAL"])
