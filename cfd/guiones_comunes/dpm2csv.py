#!/usr/bin/env python3
"""
Convierte archivos de muestreo DPM de Fluent (<zona>.dpm, /report/dpm-sample) a CSV
para post_kpi.py, y resume el balance de masa por zona.

Formatos verificados en F4 (Fluent 2026 R1):
  estacionario (12 col.): x y z u v w diameter t mass-flow mass frequency time name
  transitorio  (13 col.): x y z u v w diameter t parcel-mass mass n-in-parcel time flow-time name
Cada fila: (( v1 ... vn) inyeccion:indice)

CSV de salida (columnas internas de post_kpi.py):
  x y z u v w d boquilla  +  mdot (estacionario)  o  masa, t (transitorio; t = flow-time)

Uso:
  python dpm2csv.py <zona>.dpm salida.csv
  python dpm2csv.py --balance a.dpm b.dpm ... [--t0 0.020 --t1 0.035]
"""
import argparse
import csv
import os
import re


def leer_dpm(path):
    with open(path) as f:
        cab = f.readline().strip()
        cols = f.readline().strip().strip("()").split()
        filas = []
        for ln in f:
            m = re.match(r"\(\(\s*(.*?)\)\s*(\S+)\)\s*$", ln.strip())
            if not m:
                continue
            v = [float(t) for t in m.group(1).split()]
            filas.append((v, m.group(2)))
    return cab, cols, filas


def a_csv(path, salida):
    cab, cols, filas = leer_dpm(path)
    ix = {c: i for i, c in enumerate(cols)}
    trans = "flow-time" in ix
    with open(salida, "w", newline="") as f:
        w = csv.writer(f)
        if trans:
            w.writerow(["x", "y", "z", "u", "v", "w", "d", "masa", "t", "boquilla"])
        else:
            w.writerow(["x", "y", "z", "u", "v", "w", "d", "mdot", "boquilla"])
        for v, nm in filas:
            base = [v[ix[c]] for c in ("x", "y", "z", "u", "v", "w", "diameter")]
            boq = nm.split(":")[0]
            if trans:
                w.writerow(["%.9e" % q for q in base] + ["%.9e" % v[ix["parcel-mass"]], "%.9e" % v[ix["flow-time"]], boq])
            else:
                w.writerow(["%.9e" % q for q in base] + ["%.9e" % v[ix["mass-flow"]], boq])
    print(f"{salida}: {len(filas)} filas ({'transitorio' if trans else 'estacionario'})")


def balance(paths, t0, t1):
    print("zona, n_parcelas, masa_total_kg | masa_ventana_kg, mdot_ventana_kg_s  (estacionario: mdot_kg_s)")
    tot_v = 0.0
    for p in paths:
        cab, cols, filas = leer_dpm(p)
        ix = {c: i for i, c in enumerate(cols)}
        z = os.path.splitext(os.path.basename(p))[0]
        if "flow-time" in ix:
            m = [v[ix["parcel-mass"]] for v, _ in filas]
            mv = [v[ix["parcel-mass"]] for v, _ in filas if t0 <= v[ix["flow-time"]] < t1]
            tot_v += sum(mv)
            print(f"{z}, {len(filas)}, {sum(m):.6e} | {sum(mv):.6e}, {sum(mv) / (t1 - t0):.6e}")
        else:
            m = [v[ix["mass-flow"]] for v, _ in filas]
            tot_v += sum(m)
            print(f"{z}, {len(filas)}, {sum(m):.6e} kg/s")
    print(f"TOTAL ventana/estacionario: {tot_v:.6e}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("archivos", nargs="+")
    ap.add_argument("--balance", action="store_true")
    ap.add_argument("--t0", type=float, default=0.020)
    ap.add_argument("--t1", type=float, default=0.035)
    a = ap.parse_args()
    if a.balance:
        balance(a.archivos, a.t0, a.t1)
    else:
        a_csv(a.archivos[0], a.archivos[1])
