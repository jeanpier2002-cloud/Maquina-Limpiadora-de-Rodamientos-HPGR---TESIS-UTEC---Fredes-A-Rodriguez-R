#!/usr/bin/env python3
"""
CORRIDA 4 · T4c · Resumen descriptivo de M6 (intensidad C1, SIN pasa/no pasa) a partir de 03_DOSIS_TIEMPO/M6_intensidad.csv.
Por superficie: J (impulso normal por vuelta y area, N s m-2 vuelta-1 = Pa s por vuelta) minimo, mediana y maximo de las bandas
de 10 mm; cociente min/mediana; vueltas para acumular el impulso por area del ciclo de Davis y DeWeese a 75 psi (262-419 Pa s,
U7_anclas_conversion.csv, momento ideal: cota superior de esa referencia) en la banda de menor J. Las unidades concilian
(Pa s acumulados), pero la referencia es un chorro distinto: [TRANSFERENCIA - VERIFICAR APLICABILIDAD]. No es criterio.
Salida: 03_DOSIS_TIEMPO/M6_resumen.csv. Uso: python -I -B r4_t4c_m6_resumen.py
"""
import csv
import statistics as st
B4 = "D:/CFD_Redosado/CORRIDA_4_PRIMER_LAVADO"
M = list(csv.DictReader(open(B4 + "/03_DOSIS_TIEMPO/M6_intensidad.csv", encoding="utf-8")))
out = []
for s in ("OD", "Agujero", "Cara superior", "Cara inferior"):
    J = [float(r["J_Ns_m2_vuelta"]) for r in M if r["superficie"] == s]
    jm, jmed, jM = min(J), st.median(J), max(J)
    out.append([s, "%.1f" % jm, "%.1f" % jmed, "%.1f" % jM, "%.3f" % (jm / jmed), "%.1f" % (262 / jm), "%.1f" % (419 / jm)])
with open(B4 + "/03_DOSIS_TIEMPO/M6_resumen.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["superficie", "J_min", "J_mediana", "J_max", "min_sobre_mediana", "vueltas_262_Pa_s_banda_min", "vueltas_419_Pa_s_banda_min"])
    w.writerows(out)
for r in out:
    print(r)
