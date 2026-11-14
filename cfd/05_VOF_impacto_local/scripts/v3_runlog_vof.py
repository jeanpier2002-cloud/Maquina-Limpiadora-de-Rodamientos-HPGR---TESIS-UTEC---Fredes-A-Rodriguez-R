#!/usr/bin/env python3
"""
CORRIDA 2 · Actualiza las filas del VOF (V0-V4) en 00_ADMIN/run_log.csv con el costo real y el estado, leyendo
02_VOF_v3/logs/<etapa>/<caso>/{FIN,ERROR,resumen.txt,meta.json,log.interFoam.gz}. Las filas PLANIFICADO se crearon
el 24/10; aqui solo se completan (no se agregan filas). Nota fija: corrieron 4 carriles a la vez (9 procesos en 8
nucleos fisicos), asi que el costo real esta inflado frente a una corrida aislada (la referencia aislada es la tanda 1).
Uso: python -I v3_runlog_vof.py
"""
import csv
import gzip
import os
import re

B = "D:/CFD_Redosado/CORRIDA_2_desde24oct"
RL = B + "/00_ADMIN/run_log.csv"
LOGS = B + "/02_VOF_v3/logs"

filas = list(csv.DictReader(open(RL, newline="")))
cols = list(filas[0].keys())
for f in filas:
    if f["etapa"] not in ("e1", "e1od") or not f["id"].startswith("V"):
        continue
    d = f"{LOGS}/{f['etapa']}/{f['caso']}"
    if not os.path.exists(d + "/resumen.txt"):
        continue
    res = open(d + "/resumen.txt").read()
    g = lambda k: (re.search(k + r"=(\S+)", res) or [None, ""])[1]
    pared = float(g("pared_s") or 0)
    ram = re.search(r"Maximum resident set size \(kbytes\): (\d+)", res)
    t = re.search(r"^Time = (\S+)", res, flags=re.M)
    dts = []
    if os.path.exists(d + "/log.interFoam.gz"):
        with gzip.open(d + "/log.interFoam.gz", "rt", errors="ignore") as fh:
            dts = [float(ln.split()[2]) for ln in fh if ln.startswith("deltaT = ")]
    ok = os.path.exists(d + "/FIN")
    f.update(estado="EJECUTADO" if ok else ("ERROR" if os.path.exists(d + "/ERROR") else f["estado"]),
             pasos=g("pasos"), t_fin_s=t.group(1) if t else "", pared_s="%.0f" % pared, pared_h="%.3f" % (pared / 3600),
             costo_real_h="%.2f" % (pared / 3600),
             s_por_paso="%.3f" % (pared / float(g("pasos"))) if float(g("pasos") or 0) > 0 else "",
             RAM_max_MB="%.0f" % (int(ram.group(1)) / 1024) if ram else "", End=g("End"), FATAL=g("FATAL"),
             dt_medio_s="%.3g" % (sum(dts) / len(dts)) if dts else "", dt_min_s="%.3g" % min(dts) if dts else "",
             dt_max_s="%.3g" % max(dts) if dts else "")
    if "4 carriles" not in f["notas"]:
        f["notas"] += "; costo real medido con 4 carriles a la vez (9 procesos en 8 nucleos)"
tmp = RL + ".tmp"
with open(tmp, "w", newline="") as fo:
    w = csv.DictWriter(fo, fieldnames=cols)
    w.writeheader()
    w.writerows(filas)
os.replace(tmp, RL)
for f in filas:
    if f["id"].startswith("V"):
        print("%-5s %-34s %-11s est %5s h  real %5s h" % (f["id"], f["caso"], f["estado"], f["costo_estimado_h"], f["costo_real_h"]))
