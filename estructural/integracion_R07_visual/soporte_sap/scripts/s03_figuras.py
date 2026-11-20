# -*- coding: utf-8 -*-
"""Soporte superior (R07): figuras para la tesis a partir de los resultados de SAP2000 (resultados/*.json).
F1 comparacion de indicadores; F2 modelo con barras coloreadas por D/C (AISC 360-16); F3 deformada accidental mas
desfavorable (amplificada); F4 modos 1 a 4 de la alternativa elegida. Salida: soporte_sap/figuras/*.png."""
import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm, colors

B = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\soporte_sap"
OUT = B + r"\figuras"
os.makedirs(OUT, exist_ok=True)
NOM = {"O1_V11_ACTUAL": "O1 actual (V11)", "O2_V11_PERFILES_LIVIANOS": "O2 perfiles livianos", "O3_MARCO_CABINA": "O3 marco de cabina",
       "O4_MARCO_CABINA_MINIMO": "O4 marco minimo", "O5_MARCO_CABINA_CARTELAS": "O5 + cartelas",
       "O6_MARCO_CABINA_CARTELAS_EMPOTRADO": "O6 + bases empotradas", "O7_MARCO_CABINA_LIVIANO_EMPOTRADO": "O7 liviano empotrado",
       "O8_MARCO_CABINA_CARTELAS_EMPOTRADO_PLANTA": "O8 + cartelas y planta (cartelas atraviesan el techo)", "O9_MARCO_CABINA_LIVIANO_EMPOTRADO_PLANTA": "O9 liviano + planta",
       "O10_MARCO_CABINA_EMPOTRADO_PLANTA": "O10 ELEGIDO: marco de cabina", "O11_MARCO_CABINA_120_EMPOTRADO_PLANTA": "O11 postes SHS120"}
ELEGIDO = "O10_MARCO_CABINA_EMPOTRADO_PLANTA"
filas = list(csv.DictReader(open(B + r"\resultados\RESUMEN_CASOS.csv", encoding="utf-8")))
datos = {f["caso"]: json.load(open(B + rf"\resultados\{f['caso']}.json", encoding="utf-8")) for f in filas}

# F1: indicadores
ind = [("masa_barras_kg", "Masa de barras (kg)"), ("DC_max", "D/C maximo AISC 360-16"), ("cojinete_sup_S2_max_mm", "Desplazamiento lateral del\ncojinete superior, accidental (mm)"),
       ("f1_Hz", "Primera frecuencia (Hz)")]
fig, axs = plt.subplots(1, 4, figsize=(15, 4.6), dpi=140)
nombres = [NOM.get(f["caso"], f["caso"]) for f in filas]
for ax, (k, t) in zip(axs, ind):
    v = [float(f[k]) for f in filas]
    col = ["#E45756" if f["caso"] == ELEGIDO else ("#9C9C9C" if f["caso"] == "O1_V11_ACTUAL" else "#4C78A8") for f in filas]
    ax.barh(nombres, v, color=col)
    ax.set_title(t, fontsize=9); ax.tick_params(labelsize=7); ax.invert_yaxis()
    for i, x in enumerate(v):
        ax.text(x, i, f" {x:g}", va="center", fontsize=7)
axs[0].set_ylabel("Alternativa", fontsize=8)
fig.suptitle("Soporte superior del rotor y del motorreductor: comparacion de alternativas en SAP2000 (gris: actual; rojo: elegida)", fontsize=10)
fig.tight_layout(); fig.savefig(OUT + r"\F1_comparacion_alternativas.png"); plt.close(fig)


def dibujar(ax, d, valores=None, despl=None, escala=0.0, titulo="", cmap=cm.viridis, vmax=None):
    nud = d["nudos"]
    norm = colors.Normalize(0, vmax or max(valores.values()) if valores else 1)
    for b in d["barras"]:
        c = np.array(b["c"]).reshape(2, 3)
        if despl is not None:
            for j, p in enumerate((b["p1"], b["p2"])):
                if p in despl:
                    c[j] = c[j] + escala * np.array(despl[p][:3])
        col = cmap(norm(valores.get(b["n"], 0))) if valores else ("#C0392B" if despl is not None else "#34495E")
        lw = 2.4 if b["sec"] in ("VIGA", "COL") else 1.1
        ax.plot(c[:, 0], c[:, 1], c[:, 2], color=col, lw=lw)
    # cuerpo rigido (cartucho y motor) como puntos
    for k in ("COJ_INF", "COJ_SUP", "MOTOR_CG"):
        if k in nud:
            p = np.array(nud[k], float)
            if despl is not None and k in despl:
                p = p + escala * np.array(despl[k][:3])
            ax.scatter(*p, s=14, color="#E67E22")
    ax.set_xlabel("X (mm)", fontsize=7); ax.set_ylabel("Y (mm)", fontsize=7); ax.set_zlabel("Z (mm)", fontsize=7)
    ax.tick_params(labelsize=6); ax.set_box_aspect((4.6, 1.6, 3.6)); ax.view_init(elev=18, azim=-62)
    ax.set_title(titulo, fontsize=9)
    return norm


# F2: D/C por barra, actual frente a elegido
fig = plt.figure(figsize=(13, 5.6), dpi=140)
vmax = max(max(r[1] for r in datos[c]["diseno"]) for c in ("O1_V11_ACTUAL", ELEGIDO))
for i, c in enumerate(("O1_V11_ACTUAL", ELEGIDO)):
    ax = fig.add_subplot(1, 2, i + 1, projection="3d")
    dc = {r[0]: r[1] for r in datos[c]["diseno"]}
    f = next(x for x in filas if x["caso"] == c)
    norm = dibujar(ax, datos[c], dc, titulo=f"{NOM[c]}: {f['masa_barras_kg']} kg, D/C max {f['DC_max']}", cmap=cm.turbo, vmax=vmax)
sm = cm.ScalarMappable(norm=norm, cmap=cm.turbo); sm.set_array([])
fig.colorbar(sm, ax=fig.axes, shrink=0.6, label="D/C (AISC 360-16, LRFD)")
fig.suptitle("Aprovechamiento de las barras del soporte (SAP2000 v27)", fontsize=10)
fig.savefig(OUT + r"\F2_aprovechamiento_DC.png"); plt.close(fig)

# F3: deformada accidental mas desfavorable (cojinete superior)
fig = plt.figure(figsize=(13, 5.6), dpi=140)
for i, c in enumerate(("O1_V11_ACTUAL", ELEGIDO)):
    d = datos[c]
    nud = d["nudos"]
    ub = min(nud, key=lambda k: nud[k][0] ** 2 + nud[k][1] ** 2 + (nud[k][2] - 3450) ** 2)
    peor = max((k for k in d["despl"] if k.startswith("S2")), key=lambda k: np.hypot(*d["despl"][k][ub][:2]))
    ax = fig.add_subplot(1, 2, i + 1, projection="3d")
    dibujar(ax, d, titulo="", despl=None)
    dibujar(ax, d, despl=d["despl"][peor], escala=200, titulo=f"{NOM[c]}: {peor}, cojinete superior {np.hypot(*d['despl'][peor][ub][:2]):.2f} mm (x200)")
fig.suptitle("Deformada bajo la accion accidental de 1 000 N a z 1400 (servicio; gris: sin deformar; rojo: deformada x200)", fontsize=10)
fig.savefig(OUT + r"\F3_deformada_accidental.png"); plt.close(fig)

# F4: modos 1 a 4 del elegido
d = datos[ELEGIDO]
fig = plt.figure(figsize=(14, 9), dpi=130)
for k in range(min(4, len(d["modos"]))):
    ax = fig.add_subplot(2, 2, k + 1, projection="3d")
    md = d["modos"][k]
    amp = max(np.linalg.norm(v[:3]) for v in md.values()) or 1
    dibujar(ax, d, despl=None)
    p = d["participacion"][k]
    dibujar(ax, d, despl=md, escala=400 / amp,
            titulo=f"Modo {k + 1}: {d['frecuencias_Hz'][k]:.2f} Hz (masa participante Ux {p[0]:.2f}, Uy {p[1]:.2f}, Uz {p[2]:.2f}, Rz {p[3]:.2f})")
fig.suptitle(f"Modos de vibracion de la alternativa elegida ({NOM[ELEGIDO]}); motor a ~1 400 rpm = 23,3 Hz [VERIFICAR velocidad real]", fontsize=10)
fig.tight_layout(); fig.savefig(OUT + r"\F4_modos_elegido.png"); plt.close(fig)
print("figuras OK")
