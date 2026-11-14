#!/usr/bin/env python3
"""
CORRIDA 4 · T7 · Insumos TECNICOS (no costos) para el analisis costo-beneficio de Jean.
Programas de 10 / 15 / 20 / 30 / 45 / 60 min con N vueltas enteras (N = techo(t/T_vuelta), T_vuelta 35,294 s, HIPOTESIS).
  Volumen bombeado Q*t, Q = 221,07 L/min (C8; con recirculacion NO es consumo; volumen del tanque DATO EXTERNO PENDIENTE).
  Energia de bomba al eje P_eje*t, P_eje = 3,446 kW (C8, eta_b 0,55); eta del motor [VERIFICAR] -> se da el limite inferior.
  Fase de calentamiento D-058 (36 kW, 23 min, 13,8 kWh): con y sin (Jean considera el calentador fuera de su alcance).
  Arranque en frio del tanque (primer ciclo del dia, no esta en D-058): 46,8 kWh / 1,30 h con 858 kg y 36 kW, sin perdidas.
  Vueltas del motorreductor = N.
  Beneficio tecnico: M3 (fraccion de S_acc con meta de dosis) de cada superficie a esas N (T4), lecturas media theta y celdas.
Salida: 06_REDACCION/INSUMOS_COSTO_BENEFICIO.csv. Uso: python -I -B r4_t7_insumos.py
"""
import csv
import math

B4 = "D:/CFD_Redosado/CORRIDA_4_PRIMER_LAVADO"
T = 35.294
Q = 221.07
PE = 3.446
M3 = list(csv.DictReader(open(B4 + "/03_DOSIS_TIEMPO/M3_curvas.csv", encoding="utf-8")))
idx = {(r["superficie"], r["zona"], r["lectura"], int(r["D_req"]), int(r["N_vueltas"])): float(r["M3_S_acc"]) for r in M3}
filas = []
for tmin in (10, 15, 20, 30, 45, 60):
    N = int(math.ceil(tmin * 60 / T - 1e-9))
    tr = N * T / 60
    fila = [tmin, N, "%.2f" % tr, "%.0f" % (Q * tr), "%.3f" % (PE * tr / 60), "%.2f" % (tr + 23), "%.3f" % (PE * tr / 60 + 13.8)]
    for sup in ("OD", "Cara inferior", "Cara superior", "Agujero"):
        for Dr in (65, 183, 305):
            for lec in ("media_theta", "celdas"):
                fila.append("%.1f" % (100 * idx[(sup, "total", lec, Dr, min(N, 204))]))
    filas.append(fila)
cab = ["programa_min", "N_vueltas", "t_real_min", "volumen_bombeado_L", "E_bomba_eje_kWh_lim_inf",
       "t_ciclo_con_fase_D058_min", "E_con_fase_D058_kWh_lim_inf"]
for sup in ("OD", "cara_inf", "cara_sup", "agujero"):
    for Dr in (65, 183, 305):
        for lec in ("media_theta", "celdas"):
            cab.append("M3pct_%s_D%d_%s" % (sup, Dr, lec))
with open(B4 + "/06_REDACCION/INSUMOS_COSTO_BENEFICIO.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["# CORRIDA 4 · T7 · valores TECNICOS (no costos). CANDIDATO. Fuentes: C8 (Q, P_eje), D-058/R07 (fase), T4 (M3)."])
    w.writerow(["# Arranque en frio del tanque (1er ciclo del dia): 46,8 kWh y 1,30 h con 858 kg y 36 kW sin perdidas "
                "(32,7 kWh / 0,91 h con 600 kg); masa del tanque [VERIFICAR]. Eta del motor [VERIFICAR]: energia electrica >= eje."])
    w.writerow(cab)
    w.writerows(filas)
for r in filas:
    print(r[:7], "| cara inf 183 media/celdas:", r[7 + 3 * 2 + 2], r[7 + 3 * 2 + 3])
