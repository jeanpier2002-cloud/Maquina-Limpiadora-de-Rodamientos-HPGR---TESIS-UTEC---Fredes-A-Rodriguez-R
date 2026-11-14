#!/usr/bin/env python3
"""
CORRIDA 2 · T1 · Numero de Froude por fenomeno y cotas analiticas del efecto de la gravedad (PROMPT_CORRIDA_2 §2.1-2.2).

Fr = v / sqrt(g*L)  (forma que uso Kevin; la ficha de la tanda 1 daba Fr^2 = v^2/(gL)).
Lectura directa del efecto: a lo largo de L la gravedad cambia v^2 como mucho en 2gL, es decir
dv^2/v^2 <= 2/Fr^2 (balance de energia mecanica, sin perdidas). Con Fr >> 1 el cambio es despreciable.
Cotas de §2.2.1: velocidad ganada en la ventana simulada dw = g*t; caida durante el vuelo 1/2 g t^2.

Uso: python -I v3_froude.py   -> ../datos/v3_froude.csv y v3_cotas_gravedad.csv (y tabla en pantalla)
"""
import csv
import math
import os

BASE = "D:/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3"
os.makedirs(BASE + "/datos", exist_ok=True)
g = 9.81
RHO, MU, SIGMA = 982.12, 4.5227e-4, 0.0662          # TABLA_PARAMETROS_v2 (tanda 1)
V = 27.4711                                          # m/s, velocidad de E1/E2 (E2_LAT3A.md l. 17)
OMEGA = 1.7 * 2 * math.pi / 60                       # 1,7 rpm (CLAUDE.md, HIPOTESIS de operacion)

# (fenomeno, v [m/s], L [m], fuente de v, fuente de L)
FILAS = [
    ("Chorro en vuelo, LAT -> OD", V, 0.13035, "E1/E2 (27,47 m/s)", "TABLA_MAESTRA_22: 130,35 mm"),
    ("Chorro en vuelo, SUP -> cara superior", V, 0.189, "E1/E2", "PROMPT §A: ~189 mm"),
    ("Chorro en vuelo, INT -> agujero", V, 0.148, "E1/E2", "PROMPT §A: ~148 mm"),
    ("Lamina, L = espesor e0 (E1)", V, 0.30e-3, "E1/E2", "E1: e0 = 0,30 mm"),
    ("Lamina, L = espesor en el OD (E1-OD)", V, 0.049e-3, "E1/E2", "e_OD = 0,049 mm (lamina intacta)"),
    ("Dominio de E1 (impacto y pelicula cercana)", V, 0.020, "E1/E2", "E1: dominio de 20 mm"),
    ("Pelicula junto al impacto, alto de huella", 26.6, 0.1216, "u_f de E1 (NUMEROS_v2 l. 13)",
     "alto de huella 121,6 mm (2*130,35*tan 25)"),
    ("Pelicula que escurre lejos del impacto (u = 1 m/s)", 1.0, 0.515, "[CALCULO, orden de magnitud]",
     "ancho del rodamiento 515 mm (CLAUDE.md)"),
    ("Pelicula que escurre lejos del impacto (u = 0,1 m/s)", 0.1, 0.515, "[CALCULO, orden de magnitud]",
     "ancho del rodamiento 515 mm"),
    ("Gotas de INF_EXT llegando rasantes a la cara inferior", 4.4, 0.26, "K6: v_n 4,4 m/s (G7)",
     "ancho radial de la cara inferior (1420-900)/2 = 260 mm"),
    ("Gotas de INF_INT llegando a la cara inferior", 9.7, 0.26, "K6: v_n 9,7 m/s (G5)", "260 mm"),
    ("Drenaje y goteo bajo la cara inferior", 0.1, 2.6e-3, "[CALCULO, orden de magnitud]",
     "longitud capilar sqrt(sigma/rho g) = 2,6 mm"),
    ("Rotor a 1,7 rpm, L = diametro exterior", OMEGA * 0.71, 1.42, "omega*R, R = 0,71 m", "OD 1420 mm"),
    ("Rotor a 1,7 rpm, L = radio exterior", OMEGA * 0.71, 0.71, "omega*R", "R = 710 mm"),
]

out = []
for fen, v, L, fv, fL in FILAS:
    fr = v / math.sqrt(g * L)
    out.append(dict(fenomeno=fen, v_m_s="%.4g" % v, L_m="%.4g" % L, Fr="%.3g" % fr, Fr2="%.3g" % fr ** 2,
                    cambio_max_v2_pct="%.3g" % (200.0 / fr ** 2), fuente_v=fv, fuente_L=fL))
with open(BASE + "/datos/v3_froude.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)
for r in out:
    print("%-55s v %-8s L %-9s Fr %-8s Fr2 %-8s 2/Fr2 %s %%" % (r["fenomeno"], r["v_m_s"], r["L_m"], r["Fr"],
                                                                r["Fr2"], r["cambio_max_v2_pct"]))

# Cotas analiticas (§2.2.1)
t_vuelo = 0.13035 / V
cotas = [
    ("Velocidad ganada en la ventana de E1 (1,2 ms)", g * 1.2e-3, "m/s", 100 * g * 1.2e-3 / V, "% de v"),
    ("Velocidad ganada en 10 ms (ventana de E2)", g * 10e-3, "m/s", 100 * g * 10e-3 / V, "% de v"),
    ("Tiempo de vuelo LAT -> OD (130,35 mm)", t_vuelo * 1e3, "ms", float("nan"), ""),
    ("Caida durante el vuelo, 1/2 g t^2", 0.5 * g * t_vuelo ** 2 * 1e3, "mm",
     100 * 0.5 * g * t_vuelo ** 2 / 0.1216, "% del alto de huella 121,6 mm"),
    ("Desvio angular del chorro al llegar, atan(g t / v)", math.degrees(math.atan(g * t_vuelo / V)), "grados",
     float("nan"), ""),
    ("Gravedad a lo largo de la pared en el dominio de E1 (20 mm), 2gL/u_f^2", 2 * g * 0.020 / 26.6 ** 2 * 100,
     "% de u_f^2", float("nan"), "cota de V4 (gravedad en el plano)"),
    ("Bond de la lamina e0 = 0,30 mm, rho g e^2/sigma", RHO * g * 0.30e-3 ** 2 / SIGMA, "-", float("nan"),
     "la gravedad no deforma la lamina"),
    ("Bond de la lamina e_OD = 0,049 mm", RHO * g * 0.049e-3 ** 2 / SIGMA, "-", float("nan"), ""),
]
with open(BASE + "/datos/v3_cotas_gravedad.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cota", "valor", "unidad", "relativo", "relativo_a"])
    for c in cotas:
        w.writerow([c[0], "%.4g" % c[1], c[2], "" if math.isnan(c[3]) else "%.3g" % c[3], c[4]])
print()
for c in cotas:
    print("%-75s %.4g %s %s" % (c[0], c[1], c[2], "" if math.isnan(c[3]) else "(%.3g %s)" % (c[3], c[4])))
