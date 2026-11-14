#!/usr/bin/env python3
"""
CORRIDA 4 · T5 · Palancas fisicas legitimas, cuantificadas con datos existentes o declaradas «no modelables».
  L1 duracion -> t95 de T4 (03_DOSIS_TIEMPO/M4_tX.csv).
  L2 temperatura -> factor sobre tau_y: 2^((62 - T)/b), b = 34-78 C (Cyriac, Tabla 3 del articulo E; fila->grasa [VERIFICAR]).
     No cambia la dosis. T del lavado: 46-51 C (sin fase, R07 §d), 59,5 C (con fase D-058), 62 C (D-007); cotas 15 y 30 C.
     Costo de la fase (D-058): +23 min y 36 kW x 23 min = 13,8 kWh (R07: 34 min con 24 kW, 18 con 48 kW).
     Arranque en frio del tanque: m c_p (62-15) / P, m = 600 / 858 kg (R07; volumen [VERIFICAR]), c_p 4,18 kJ/kg/K [CALCULO].
  L5 pausas (remojo con el rodamiento mojado por el rocio, SIN inmersion) -> Davis y DeWeese 1995, Tabla 2 (p. 488),
     transcrita a mano de la imagen: solo tendencia (sin replicas) -> «no modelable» para esta maquina.
  L8 presion (DESCARTADA 24/10): solo escalas t ~ p^-0,5 (dosis por vuelta ~ caudal ~ p^0,5) y potencia ~ p^1,5.
Salidas: 04_PALANCAS/L2_temperatura.csv, L5_davis_tabla2.csv, L5_efecto_remojo.csv, T5_palancas.csv
Uso: python -I -B r4_t5_palancas.py
"""
import csv
import os

B4 = "D:/CFD_Redosado/CORRIDA_4_PRIMER_LAVADO"
OUT = B4 + "/04_PALANCAS"
os.makedirs(OUT, exist_ok=True)

# ---------------- L2
esc = [("cota 15 °C (rodamiento frío, sin intercambio)", 15.0), ("cota 30 °C", 30.0),
       ("sin fase de calentamiento, baño a 46 °C (R07)", 46.0), ("sin fase de calentamiento, baño a 51 °C (R07)", 51.0),
       ("con fase D-058 (baño 59,5 °C, R07)", 59.5), ("punto de cálculo 62 °C (D-007)", 62.0)]
l2 = []
for nom, T in esc:
    f34 = 2 ** ((62 - T) / 34.0); f78 = 2 ** ((62 - T) / 78.0)
    l2.append([nom, "%.1f" % T, "%.3f" % f78, "%.3f" % f34])
with open(OUT + "/L2_temperatura.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["escenario", "T_C", "factor_tau_y_b78", "factor_tau_y_b34"]); w.writerows(l2)
cp = 4.18
arr = []
for m in (600.0, 858.0):
    E = m * cp * (62 - 15) / 3600.0          # kWh
    for P in (24.0, 36.0, 48.0):
        arr.append([m, P, "%.1f" % E, "%.2f" % (E / P)])
with open(OUT + "/L2_arranque_frio_tanque.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["masa_agua_kg_VERIFICAR", "potencia_kW", "energia_kWh_sin_perdidas", "horas_sin_perdidas"])
    w.writerows(arr)

# ---------------- L5: Davis y DeWeese 1995, Tabla 2 (p. 488), transcripcion manual
# run, panel, T_F, soak_min, conc_pct, p_psi, residuo_pct, osee, tension_psi
TAB2 = [(16, 17, 140, 10, 30, 675, 0, 441, 8743), (2, 3, 72, 2, 30, 675, 0, 425, 8584), (8, 5, 72, 10, 30, 675, 0, 360, 8568),
        (7, 12, 140, 10, 10, 675, 0, 476, 8554), (12, 8, 140, 2, 30, 675, 0, 484, 8512), (11, 16, 72, 2, 10, 675, 0, 293, 8277),
        (15, 4, 72, 10, 10, 675, 0, 444, 7939), (4, 9, 140, 2, 10, 675, 0, 408, 7391), (6, 10, 140, 10, 30, 75, 15, 481, 7038),
        (10, 15, 72, 2, 30, 75, 25, 290, 4478), (3, 7, 140, 2, 30, 75, 30, 407, 4476), (13, 11, 140, 10, 10, 75, 20, 417, 4349),
        (5, 13, 72, 10, 10, 75, 40, 283, 2420), (9, 14, 140, 2, 10, 75, 40, 299, 1518), (14, 6, 72, 10, 30, 75, 40, 441, 1153),
        (1, 2, 72, 2, 10, 75, 95, 445, 871)]
with open(OUT + "/L5_davis_tabla2.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["run", "panel", "T_F", "soak_min", "conc_pct", "p_psi", "residuo_luz_negra_pct", "osee_delta_cV", "adhesion_psi"])
    w.writerows(TAB2)
ef = []
for p in (75, 675):
    for T in (72, 140):
        for c in (10, 30):
            r2 = [r for r in TAB2 if r[5] == p and r[2] == T and r[4] == c and r[3] == 2][0][6]
            r10 = [r for r in TAB2 if r[5] == p and r[2] == T and r[4] == c and r[3] == 10][0][6]
            ef.append([p, T, c, r2, r10, r10 - r2])
with open(OUT + "/L5_efecto_remojo.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["p_psi", "T_F", "conc_pct", "residuo_soak2", "residuo_soak10", "delta_puntos"]); w.writerows(ef)
d75 = [e[5] for e in ef if e[0] == 75]
efT = []
for s in (2, 10):
    for c in (10, 30):
        r72 = [r for r in TAB2 if r[5] == 75 and r[2] == 72 and r[4] == c and r[3] == s][0][6]
        r140 = [r for r in TAB2 if r[5] == 75 and r[2] == 140 and r[4] == c and r[3] == s][0][6]
        efT.append(r140 - r72)
print("L5 (75 psi) efecto soak 2->10 min por par:", d75, "media %.2f puntos" % (sum(d75) / len(d75)))
print("L2 lit. (75 psi) efecto 72->140 F por par:", efT, "media %.2f puntos" % (sum(efT) / len(efT)))

# ---------------- L8 (descartada): escalas
l8 = []
for p in (3.0, 4.0, 5.0, 6.0):
    l8.append([p, "%.3f" % ((p / 4.0) ** -0.5), "%.3f" % ((p / 4.0) ** 1.5)])
with open(OUT + "/L8_escalas_presion.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["p_bar", "t_rel_a_4bar", "potencia_rel_a_4bar"]); w.writerows(l8)

# ---------------- tabla resumen de palancas (texto corto; las cifras salen de los CSV)
T5 = [
    ["L1", "Duración (vueltas)", "CUANTIFICADA (T4)", "t95 por superficie y D_req: ver 03_DOSIS_TIEMPO/T4_t95_tabla.csv",
     "tiempo, agua y energía (T7)"],
    ["L2", "Temperatura del baño / fase de calentamiento (D-058)", "CUANTIFICADA como factor sobre τ_y; no cambia la dosis",
     "sin fase 1,10-1,39; con fase 1,02-1,05; 15 °C 1,52-2,61 (L2_temperatura.csv)",
     "+23 min y ≈ 13,8 kWh por ciclo con 36 kW; arranque en frío del tanque ≈ 1,3 h con 858 kg y 36 kW (sin pérdidas)"],
    ["L3", "Pose de boquillas hacia la ventana", "CUANTIFICADA en N1 (T2c)",
     "ventana sup.: sin ganancia al converger (mejor 31,3 % frente a 30,7 % de la pose tipo SUP_1, 600 rayos); ventana inf.: una boquilla "
     "por dentro (r 540 mm, 75°, 40° tang.) ve 18,7 % (flanco de la hilera inf. 18,4 %) frente a 0,4 % por fuera (T2c_pose_denso.csv)",
     "[INTERFAZ ISMAEL]: espacio bajo la cara inferior entre la lanza y las bases de PAD"],
    ["L4", "Zona que manda", "CUANTIFICADA (T4/T4b)", "cara inferior: sombras de bases de PAD y topes (≈ 14 % del área con f < 0,5)",
     "cavidad: la hilera inferior (flanco 0,35 % visible) manda; reposición propuesta en L3 (solo N1)"],
    ["L5", "Pausas entre pasadas (rodamiento mojado por el rocío, sin inmersión)", "NO MODELABLE (solo tendencia de literatura)",
     "Davis y DeWeese, Tabla 2, 75 psi: remojo 10 frente a 2 min, Δresiduo = %s puntos (media %.1f; sin réplicas; un par inverso)" % (
         d75, sum(d75) / len(d75)), "tiempo de ciclo; requiere ensayo"],
    ["L6", "Química del desengrasante", "NO MODELABLE (fuera de alcance)", "—", "ensayo futuro (ASTM D4049 o gravimétrico)"],
    ["L7", "Velocidad del rotor", "A primer orden no cambia la dosis acumulada por tiempo", "D·N/t constante si el caudal no cambia",
     "la intensidad por pasada no se modela"],
    ["L8", "Presión / caudal", "DESCARTADA por Jean (24/10)", "t ∝ p^-0,5; potencia ∝ p^1,5 (L8_escalas_presion.csv)", "no se explora"],
]
with open(OUT + "/T5_palancas.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["id", "palanca", "estado", "efecto", "costo_o_nota"]); w.writerows(T5)
for r in l2:
    print(r)
for r in arr:
    print(r)
