#!/usr/bin/env python3
"""
CORRIDA 4 · T3b (11/11/2026, a pedido de Jean) · Masa de grasa por rodamiento con la regla de SKF.
Reemplaza el [SIN FUENTE] del llenado y de la densidad de T3 por fuentes externas. NO predice remocion.
  Volumen libre (SKF, «Determining grease quantities», web; texto leido por buscador, [VERIFICAR contra catalogo PDF]):
      V = pi/4 * B * (D^2 - d^2) - M / 7,8      [mm -> dm3; M en kg; 7,8 kg/dm3 = acero; incluye jaula metalica]
  Conversion SKF: masa de grasa [g] ~ volumen [cm3] x 0,9 (grasas estandar).
  Llenado: SKF recomienda llenar por completo el espacio libre del rodamiento (alojamiento 20-40 %).
  Evidencia HPGR (Schaeffler, Success Story 0149, 2021/05): planta de cobre de Arequipa, 12 HPGR PM8-24/17M lubricados con
      grasa, rodamientos de rodillos a rotula con jaula de laton, OD 1420 mm y > 3 t; consumo 17 bidones x 180 kg al mes
      para los 12 HPGR -> ~64 kg por rodamiento y mes (4 rodamientos por HPGR, [VERIFICAR]) -> lubricacion por purga:
      la cavidad llega llena al taller (supuesto; parte se pierde al desmontar -> escenario 50 %).
  Rodamiento SKF 241/900 ECAK30/W33: B 515, D 1420, d 900 (extremo menor del agujero conico 1:30), M 3032 kg (CLAUDE.md).
  Agujero conico: d medio = 900 + 515/60 = 908,58 mm -> segunda estimacion.
  Contraste: volumen libre medido en el STEP sin jaula (T3) = 112,864 dm3 -> jaula implicita = 112,864 - V_SKF.
Salida: 02_CAVIDAD_N1/T3b_grasa_skf.csv. Uso: python -I -B r4_t3b_grasa_skf.py
"""
import csv
import math

B4 = "D:/CFD_Redosado/CORRIDA_4_PRIMER_LAVADO"
B, D, M = 515.0, 1420.0, 3032.0
RHO_ACERO = 7.8        # kg/dm3 (SKF)
RHO_GRASA = 0.9        # kg/dm3 (conversion SKF; ficha de la grasa real [VERIFICAR])
RHO_LATON = 8.5        # kg/dm3 [VERIFICAR] (solo para el contraste de la jaula)
V_STEP = 112.864       # dm3, T3 (sin jaula)
M_EXT = (0.51, 5.10)   # kg, T3 (pelicula externa 0,1-1 mm, [SIN FUENTE])

filas = []
for nom, d in (("d nominal 900 (formula SKF tal cual)", 900.0), ("d medio 908,58 (agujero conico 1:30)", 900.0 + B / 60.0)):
    v_env = math.pi / 4.0 * B * (D ** 2 - d ** 2) * 1e-6      # dm3
    v_lib = v_env - M / RHO_ACERO
    jaula = V_STEP - v_lib
    for f in (0.5, 1.0):
        mg = f * v_lib * RHO_GRASA
        filas.append([nom, "%.2f" % v_env, "%.2f" % v_lib, "%.0f" % (100 * f), "%.1f" % mg,
                      "%.1f-%.1f" % (100 * mg / (mg + M_EXT[1]), 100 * mg / (mg + M_EXT[0])),
                      "%.1f" % jaula, "%.0f" % (jaula * RHO_LATON)])
with open(B4 + "/02_CAVIDAD_N1/T3b_grasa_skf.csv", "w", newline="", encoding="utf-8") as fo:
    w = csv.writer(fo)
    w.writerow(["caso", "V_envolvente_dm3", "V_libre_SKF_dm3", "llenado_pct", "M_grasa_cavidad_kg",
                "pct_masa_en_cavidad", "jaula_implicita_dm3", "jaula_implicita_kg_laton"])
    w.writerows(filas)
for r in filas:
    print(r)
print("Purga HPGR (Schaeffler 0149): 17 x 180 / 12 / 4 = %.1f kg por rodamiento y mes" % (17 * 180 / 12 / 4))
