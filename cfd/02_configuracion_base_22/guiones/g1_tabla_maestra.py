#!/usr/bin/env python3
"""
G1 - Tabla maestra de las 22 boquillas de R05.

Fuentes (todas copias con hash en 03_GEOMETRIA/R05_copia/):
  - Geometria: 03_GEOMETRIA/R05_extraccion/r05_extraccion.json, MEDIDA sobre los solidos BOQUILLA_nn de
    R05_GEOMETRICO_DETALLADO.FCStd con 05_SCRIPTS/g1_extraer_r05.py (punta, eje, salida del orificio, ranura).
  - Caudal y presion por toma: resultados_22.json (red de 22, ../Calculos_R05_22boquillas, CANDIDATO).
  - Velocidad de salida: v = Cv*sqrt(2*p/rho), Cv = 0,95 SUPUESTO (I4; 27,1135 m/s a 4 bar, igual que CFD02).
  - CFD02: comandos de gen_abanico.py en las cabeceras de las tablas de F7/F5 (q = 9,11767 L/min en F7;
    red de la rama B en F5).

Salida: 03_GEOMETRIA/tabla_maestra_22_boquillas.csv y boquillas_22.json (parametros de inyeccion).
"""
import csv
import json
import math
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
GEO = os.path.join(RAIZ, "03_GEOMETRIA")
ext = json.load(open(os.path.join(GEO, "R05_extraccion", "r05_extraccion.json")))["boquillas"]
red = json.load(open(os.path.join(GEO, "R05_copia", "resultados_22.json")))
RHO = red["constantes"]["rho"]                     # 982,1203530851709 kg/m3 (62 C)
CV = 0.95                                          # SUPUESTO I4 (heredado)
Q0 = 9.11767                                       # L/min de catalogo a 4 bar (CFD02, D1)
toma = {b["toma"].split("_", 1)[1]: b for b in red["boquillas"]}   # SUP_1, LAT_4, INF_EXT, INT_5, ...

# nombre R05 -> (codigo CFD, ramal, estudio, toma de la red, superficie objetivo de diseno, caso CFD02, q CFD02)
MAPA = {
    "01_SUP_A1": ("SUP_1", "A", "E-SUP", "SUP_1", "cara superior", "F7_ESUP (ramal A)", 9.11766505),
    "02_SUP_A2": ("SUP_2", "A", "E-SUP", "SUP_2", "cara superior", "F7_ESUP (ramal A)", 9.11766505),
    "03_LAT_A1": ("LAT_1", "A", "E-OD", "LAT_1", "OD", "F7_EOD (ramal A)", 9.11766505),
    "04_LAT_A2": ("LAT_2", "A", "E-OD", "LAT_2", "OD", "F7_EOD (ramal A)", 9.11766505),
    "05_LAT_A3": ("LAT_3", "A", "E-OD", "LAT_3", "OD", "F7_EOD (ramal A)", 9.11766505),
    "06_LAT_A4": ("LAT_4", "A", "E-OD", "LAT_4", "OD", "F7_EOD (ramal A)", 9.11766505),
    "07_LAT_A5": ("LAT_5", "A", "E-OD", "LAT_5", "OD (parte baja)", "F7_EOD (ramal A)", 9.11766505),
    "08_INF_A": ("INF_EXT", "A", "E-INF", "INF_EXT", "OD (Z 890-1038) + cara inferior", "no simulada", None),
    "09_SUP_B1": ("SUP_1", "B", "E-SUP", "SUP_1", "cara superior", "= ramal A por S9", 9.11766505),
    "10_SUP_B2": ("SUP_2", "B", "E-SUP", "SUP_2", "cara superior", "= ramal A por S9", 9.11766505),
    "11_LAT_B1": ("LAT_1", "B", "E-OD", "LAT_1", "OD", "= ramal A por S9", 9.11766505),
    "12_LAT_B2": ("LAT_2", "B", "E-OD", "LAT_2", "OD", "= ramal A por S9", 9.11766505),
    "13_LAT_B3": ("LAT_3", "B", "E-OD", "LAT_3", "OD", "= ramal A por S9", 9.11766505),
    "14_LAT_B4": ("LAT_4", "B", "E-OD", "LAT_4", "OD", "= ramal A por S9", 9.11766505),
    "15_LAT_B5": ("LAT_5", "B", "E-OD", "LAT_5", "OD (parte baja)", "= ramal A por S9", 9.11766505),
    "16_INF_B": ("INF_EXT", "B", "E-INF", "INF_EXT", "OD (Z 890-1038) + cara inferior", "no simulada", None),
    "17_INT_1": ("INT_1", "lanza", "E-AGU", "INT_1", "agujero", "F5 (red rama B)", 9.13621),
    "18_INT_2": ("INT_2", "lanza", "E-AGU", "INT_2", "agujero", "F5 (red rama B)", 9.1436),
    "19_INT_3": ("INT_3", "lanza", "E-AGU", "INT_3", "agujero", "F5 (red rama B)", 9.1523),
    "20_INT_4": ("INT_4", "lanza", "E-AGU", "INT_4", "agujero", "F5 (red rama B)", 9.16194),
    "21_INT_5": ("INT_5", "lanza", "E-AGU", "INT_5", "agujero", "F5 (red rama B)", 9.17216),
    "22_INF_INT": ("INF_INT", "lanza", "E-AGU / E-INF", "INF_INT", "agujero (parte baja) + cara inferior",
                   "F5 (red rama B; cara inferior solo r <= 0,55 m)", 9.11767),
}

filas, js = [], {}
for nombre in sorted(ext):
    clave = nombre.replace("BOQUILLA_", "")
    cod, ramal, est, tm, sup, caso02, q02 = MAPA[clave]
    g = ext[nombre]
    t = toma[tm]
    p, q = t["p_bar"], t["q_Lmin"]
    v = CV * math.sqrt(2 * p * 1e5 / RHO)
    mdot = q / 60000.0 * RHO
    ex, ey, ez = g["eje"]
    elev = math.degrees(math.asin(max(-1, min(1, ez))))
    az = math.degrees(math.atan2(g["punta"][1], g["punta"][0])) % 360
    ident = ("%s_%s" % (cod, ramal)) if ramal in ("A", "B") else cod
    fila = dict(id=clave[:2], objeto_R05=nombre, ident_CFD=ident, codigo=cod, ramal=ramal, estudio=est,
                toma_red22=t["toma"], azimut_deg="%.1f" % az,
                punta_x_mm="%.3f" % g["punta"][0], punta_y_mm="%.3f" % g["punta"][1], punta_z_mm="%.3f" % g["punta"][2],
                eje_x="%.6f" % ex, eje_y="%.6f" % ey, eje_z="%.6f" % ez, elevacion_deg="%.3f" % elev,
                normal_abanico_x="%.6f" % g["normal_plano_abanico"][0],
                normal_abanico_y="%.6f" % g["normal_plano_abanico"][1],
                normal_abanico_z="%.6f" % g["normal_plano_abanico"][2],
                vertice_x_mm="%.4f" % g["salida_orificio"][0], vertice_y_mm="%.4f" % g["salida_orificio"][1],
                vertice_z_mm="%.4f" % g["salida_orificio"][2], h_punta_vertice_mm="%.3f" % g["h_punta_salida_mm"],
                angulo_V_deg="%.1f" % g["angulo_V_deg"],
                p_bar_red22="%.5f" % p, q_Lmin_red22="%.5f" % q, mdot_kg_s_red22="%.6f" % mdot,
                v_salida_m_s="%.4f" % v, superficie_objetivo_diseno=sup, caso_CFD02=caso02,
                q_Lmin_CFD02=("%.5f" % q02) if q02 else "-",
                dq_pct_red22_vs_CFD02=("%+.2f" % (100 * (q / q02 - 1))) if q02 else "-")
    filas.append(fila)
    js[ident] = dict(objeto_R05=nombre, vertice_m=[c / 1000 for c in g["salida_orificio"]], eje=g["eje"],
                     normal_abanico=g["normal_plano_abanico"], q_Lmin=q, v_m_s=v, mdot_kg_s=mdot, p_bar=p,
                     estudio=est, ramal=ramal)

os.makedirs(GEO, exist_ok=True)
with open(os.path.join(GEO, "tabla_maestra_22_boquillas.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
    w.writeheader()
    w.writerows(filas)
json.dump(dict(fuente="g1_tabla_maestra.py", rho=RHO, Cv=CV, boquillas=js),
          open(os.path.join(GEO, "boquillas_22.json"), "w"), indent=1)
Q = sum(float(r["q_Lmin_red22"]) for r in filas)
print("boquillas:", len(filas), "| suma q red22 = %.4f L/min (resultados_22: %.4f)" % (Q, red["Q_total_Lmin"]))
for r in filas:
    print("%-11s %-7s %-6s punta (%9s %8s %9s) elev %8s  q %s  v %s  CFD02 %s (%s %%)" % (
        r["objeto_R05"][9:], r["ident_CFD"], r["estudio"][:6], r["punta_x_mm"], r["punta_y_mm"], r["punta_z_mm"],
        r["elevacion_deg"], r["q_Lmin_red22"], r["v_salida_m_s"], r["q_Lmin_CFD02"], r["dq_pct_red22_vs_CFD02"]))
