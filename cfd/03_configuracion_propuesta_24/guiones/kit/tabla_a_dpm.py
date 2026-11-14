#!/usr/bin/env python3
"""
Convierte la tabla CSV de gen_abanico.py (rama B) al archivo de inyeccion *file* de Fluent.

Formato verificado en F4 (t10): mismo formato que el archivo de muestreo DPM:
  (nombre 12)
  (x y z u v w diameter t mass-flow mass frequency time name)
  (( x y z u v w d T mdot 0 0 0) nombre)
Unidades SI. T = 300 K (sin energia: no interviene).

Uso: python tabla_a_dpm.py abanico.csv salida.dpm --nombre INT_1
"""
import argparse
import csv

ap = argparse.ArgumentParser()
ap.add_argument("csv")
ap.add_argument("salida")
ap.add_argument("--nombre", required=True)
a = ap.parse_args()

filas = list(csv.DictReader(open(a.csv)))
tot = 0.0
with open(a.salida, "w", newline="\n") as f:
    f.write(f"({a.nombre} 12)\n")
    f.write("(          x           y            z            u            v            w     diameter"
            "            t    mass-flow         mass    frequency         time         name)\n")
    for r in filas:
        md = float(r["mDot_kg_s"])
        tot += md
        f.write("(( %.9e %.9e %.9e %.9e %.9e %.9e %.9e 3.0e+02 %.9e 0.0 0.0 0.0) %s)\n" % (
            float(r["Px_m"]), float(r["Py_m"]), float(r["Pz_m"]),
            float(r["Ux_m_s"]), float(r["Uy_m_s"]), float(r["Uz_m_s"]),
            float(r["d_um"]) * 1e-6, md, a.nombre))
print(f"{a.salida}: {len(filas)} parcelas, suma mass-flow = {tot:.9g} kg/s")
