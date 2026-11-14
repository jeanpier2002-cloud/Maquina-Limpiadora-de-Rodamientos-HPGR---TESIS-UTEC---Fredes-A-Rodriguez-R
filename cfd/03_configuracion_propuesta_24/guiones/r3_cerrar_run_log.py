#!/usr/bin/env python3
"""
CORRIDA 3 · cierre del run_log.csv: las filas de reserva (humos de R3_04-07, solo si R3_02 no pasaba la aceptacion) pasan a
«NO NECESARIA»; a R3_00 se le anade el primer intento (fallido por el journal del kit, 0,19 h, salidas en _fallo1/) y a
cada corrida su balance de la ventana 25-50 ms (resultados/*_aceptacion.txt).
Uso: python -I -B r3_cerrar_run_log.py
"""
import csv
import os

BASE = "D:/CFD_Redosado/CORRIDA_3_O7C2"
RL = BASE + "/00_ADMIN/run_log.csv"
filas = list(csv.DictReader(open(RL, newline="")))
cols = list(filas[0])
for f in filas:
    if f["etapa"] != "fluent_R3":
        continue
    if f["estado"].startswith("RESERVA"):
        f["estado"] = "NO NECESARIA (R3_02 aceptada)"
        continue
    ac = BASE + "/03_FLUENT/resultados/%s_aceptacion.txt" % f["caso"]
    if os.path.exists(ac) and "aceptacion" not in f["notas"]:
        f["notas"] += "; aceptacion: " + open(ac, encoding="utf-8").read().strip()
    if f["id"] == "R3_00" and "intento 1 fallido" not in f["notas"]:
        f["notas"] += ("; intento 1 fallido (21:13-21:24, 0,19 h): el journal del kit no cerraba la lista de inyecciones de "
                       "/report/dpm-sample (7 lineas en blanco para 7 inyecciones) y no escribio muestras; corregido con 8")
with open(RL + ".tmp", "w", newline="") as fo:
    w = csv.DictWriter(fo, fieldnames=cols)
    w.writeheader()
    w.writerows(filas)
os.replace(RL + ".tmp", RL)
print("run_log cerrado:", sum(1 for f in filas if f["etapa"] == "fluent_R3"), "filas fluent_R3")
