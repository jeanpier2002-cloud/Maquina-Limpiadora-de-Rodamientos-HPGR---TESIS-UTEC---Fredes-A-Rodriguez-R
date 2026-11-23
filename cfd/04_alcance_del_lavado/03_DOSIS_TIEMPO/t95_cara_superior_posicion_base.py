#!/usr/bin/env python3
"""
t95 de la cara superior con la boquilla SUP_2 en su posicion base (configuracion del informe).

T4_t95_tabla.csv usa para la cara superior el mapa del Caso 3 (SUP_2 desplazada 15 mm), que no se
incorporo al diseno. El informe (Seccion 7.2.2.6 y Tabla A6.10) usa la posicion base; este guion
reproduce esas cifras a partir de las bandas de 10 mm de la cara superior de la configuracion base
(G7_sup_bandas_10mm_posicion_base.csv).

t95 = menor numero entero de vueltas N para el que el 95 % del area mojable cumple N*D >= D_req,
por 35,294 s por vuelta (1,7 rpm).

Uso: python t95_cara_superior_posicion_base.py  ->  t95_cara_superior_posicion_base.csv
"""
import csv
from pathlib import Path

aqui = Path(__file__).resolve().parent
filas = list(csv.DictReader(open(aqui / "G7_sup_bandas_10mm_posicion_base.csv", encoding="utf-8-sig")))
D = [float(f["D_obst_media_theta"]) for f in filas]
A = [float(f["area_mojable_m2"]) for f in filas]
T_vuelta = 60.0 / 1.7

salida = []
for D_req in (65, 183, 305):
    for N in range(1, 1000):
        if sum(a for d, a in zip(D, A) if N * d >= D_req) >= 0.95 * sum(A) - 1e-12:
            salida.append(dict(D_req_kg_m2=D_req, vueltas=N, t95_min=round(N * T_vuelta / 60.0, 2)))
            break

with open(aqui / "t95_cara_superior_posicion_base.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(salida[0]))
    w.writeheader()
    w.writerows(salida)
print("D_min por vuelta = %.3f kg/m2" % min(D))
for s in salida:
    print("D_req %3d kg/m2: %2d vueltas, t95 = %.2f min" % (s["D_req_kg_m2"], s["vueltas"], s["t95_min"]))
