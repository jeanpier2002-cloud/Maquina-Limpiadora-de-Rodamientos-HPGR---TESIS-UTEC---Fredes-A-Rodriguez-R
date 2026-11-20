# -*- coding: utf-8 -*-
"""Anexo SAP del soporte superior, paso 2: Excel y figuras a partir de las tablas ORIGINALES de SAP2000 exportadas por
a01_tablas_sap.ps1 (tablas_sap/<modelo>_api/*.csv), como el anexo de la mesa (SAP_N3_R06_K2M_v573_export.xlsx).
Modelos: K32 (soporte aligerado de D-080, el vigente), K0 (soporte de D-065 con el rotor real de D-075) y K16 (postes dentro, x = +-1150).
Salidas: anexo_sap/SAP_SOPORTE_<modelo>_export.xlsx y anexo_sap/figuras/A1..A5_*.png."""
import csv
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm, colors
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

S = Path(r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\soporte_sap")
A = S / "anexo_sap"
FIG = A / "figuras"
FIG.mkdir(parents=True, exist_ok=True)
MODELOS = {"K32_M_80x4_150x100x3": "Soporte aligerado K32 (D-080): SHS80×4 y RHS150×100×3",
           "K0_O10R_MARCO_SOLO": "Soporte de D-065 (postes en los muros, luz 4 040 mm)",
           "K16_ANGOSTO_X1150_MISMOS": "Postes dentro de la cabina (x = ±1 150 mm, luz 2 300 mm), mismos perfiles"}
NUM = re.compile(r"^-?\d+(,\d+)?(E[-+]?\d+)?$", re.I)


def leer(modelo, tabla):
    p = A / "tablas_sap" / (modelo + "_api") / (tabla + ".csv")
    if not p.exists():
        return [], []
    filas = list(csv.reader(open(p, encoding="utf-8-sig"), delimiter=";"))
    if not filas:
        return [], []
    cab = filas[0]
    datos = [[float(v.replace(",", ".")) if NUM.match(v) else v for v in f] for f in filas[1:]]
    return cab, datos


def dic(cab, datos):
    return [dict(zip(cab, f)) for f in datos]


# ------------------------------------------------------------------ modelo geometrico desde las tablas de SAP
def geometria(modelo):
    nud = {str(int(r["Joint"])) if isinstance(r["Joint"], float) else r["Joint"]: (r["XorR"], r["Y"], r["Z"])
           for r in dic(*leer(modelo, "Joint_Coordinates"))}
    sec = {str(int(r["Frame"])) if isinstance(r["Frame"], float) else r["Frame"]: r["AnalSect"] for r in dic(*leer(modelo, "Frame_Section_Assignments"))}
    barras = []
    for r in dic(*leer(modelo, "Connectivity_Frame")):
        f = str(int(r["Frame"])) if isinstance(r["Frame"], float) else r["Frame"]
        i = str(int(r["JointI"])) if isinstance(r["JointI"], float) else r["JointI"]
        j = str(int(r["JointJ"])) if isinstance(r["JointJ"], float) else r["JointJ"]
        barras.append((f, i, j, sec.get(f, "")))
    return nud, barras


def desplazamientos(modelo, caso, paso=None):
    out = {}
    for r in dic(*leer(modelo, "Joint_Displacements")):
        if r["OutputCase"] != caso:
            continue
        if paso is not None and float(r.get("StepNum", 0) or 0) != paso:
            continue
        j = str(int(r["Joint"])) if isinstance(r["Joint"], float) else r["Joint"]
        out[j] = (r["U1"], r["U2"], r["U3"])
    return out


def nudo_cerca(nud, p):
    return min(nud, key=lambda k: sum((a - b) ** 2 for a, b in zip(nud[k], p)))


ESTILO = {"COL": ("#34495E", 2.6), "VIGA": ("#2E86C1", 2.6), "LAC": ("#7F8C8D", 1.1), "TACO": ("#34495E", 2.0)}


def dibujar(ax, nud, barras, valores=None, despl=None, escala=0.0, cmap=cm.turbo, norm=None, gris=False, titulo=""):
    for f, i, j, s in barras:
        c = np.array([nud[i], nud[j]], float)
        if despl is not None:
            for k, n in enumerate((i, j)):
                if n in despl:
                    c[k] = c[k] + escala * np.array(despl[n])
        col, lw = ESTILO.get(s, ("#555555", 1.2))
        if valores is not None:
            col = cmap(norm(valores.get(f, 0)))
        if gris:
            col = "#C8C8C8"
        elif despl is not None and valores is None:
            col = "#C0392B"
        ax.plot(c[:, 0], c[:, 1], c[:, 2], color=col, lw=lw)
    # cartucho, mensula y motor: cuerpo rigido (puntos del Body constraint de SAP)
    cuerpo = [nudo_cerca(nud, p) for p in ((0, 0, 2850), (0, 0, 3450), (800, 0, 3280))]
    for n in cuerpo:
        p = np.array(nud[n], float)
        if despl is not None and n in despl:
            p = p + escala * np.array(despl[n])
        ax.scatter(*p, s=16, color="#E67E22", depthshade=False)
    ax.set_xlabel("X (mm)", fontsize=7); ax.set_ylabel("Y (mm)", fontsize=7); ax.set_zlabel("Z (mm)", fontsize=7)
    ax.tick_params(labelsize=6); ax.set_box_aspect((4.6, 1.6, 3.6)); ax.view_init(elev=18, azim=-62)
    ax.set_xlim(-2200, 2200); ax.set_ylim(-500, 500); ax.set_zlim(0, 3500)
    ax.set_title(titulo, fontsize=9)


def cabina(ax):
    """contorno de la cabina (CTX_CABIN, planos medios) como referencia"""
    x, y, z = 2020, 2070, 2610
    for (a, b) in (((-x, -y, 0), (x, -y, 0)), ((x, -y, 0), (x, y, 0)), ((x, y, 0), (-x, y, 0)), ((-x, y, 0), (-x, -y, 0)),
                   ((-x, -y, z), (x, -y, z)), ((x, -y, z), (x, y, z)), ((x, y, z), (-x, y, z)), ((-x, y, z), (-x, -y, z)),
                   ((-x, -y, 0), (-x, -y, z)), ((x, -y, 0), (x, -y, z)), ((x, y, 0), (x, y, z)), ((-x, y, 0), (-x, y, z))):
        ax.plot(*zip(a, b), color="#BBBBBB", lw=0.7, ls="--")


# ------------------------------------------------------------------ Excel por modelo
HOJAS = [("01_NUDOS", ["Joint_Coordinates", "Joint_Restraint_Assignments", "Joint_Constraint_Assignments", "Constraint_Definitions_Body"]),
         ("02_BARRAS", ["Connectivity_Frame", "Frame_Section_Assignments", "Frame_Release_Assignments_1_General"]),
         ("03_SECCIONES_MATERIAL", ["Frame_Section_Properties_01_General", "Material_Properties_02_Basic_Mechanical_Properties", "Mass_Source"]),
         ("04_CARGAS_Y_COMBOS", ["Load_Pattern_Definitions", "Joint_Loads_Force", "Load_Case_Definitions", "Combination_Definitions"]),
         ("05_DESPLAZAMIENTOS", ["Joint_Displacements"]),
         ("06_REACCIONES", ["Joint_Reactions", "Base_Reactions"]),
         ("07_FUERZAS_BARRAS", ["Element_Forces_Frames"]),
         ("08_DISENO_ACERO", ["Steel_Design_1_Summary_Data_AISC_360_16", "Preferences_Steel_Design_AISC_360_16"]),
         ("09_MODOS", ["Modal_Periods_And_Frequencies", "Modal_Participating_Mass_Ratios"]),
         ("10_PANDEO", ["Buckling_Factors"])]
NEG = Font(bold=True)
GRIS = PatternFill("solid", fgColor="DDDDDD")


def excel(modelo, resumen):
    wb = Workbook()
    ws = wb.active; ws.title = "00_CONTROL"
    filas = [["Anexo SAP2000 del soporte superior del rotor y del motorreductor (HPGR D-065, D-078)"],
             ["Modelo", modelo, MODELOS[modelo]],
             ["Archivo SAP", "anexo_sap/modelos/%s_<hora>/%s.sdb (copia de soporte_sap/modelos_cabina/%s.sdb)" % (modelo, modelo, modelo)],
             ["Programa", "SAP2000 v27.1.0 Ultimate, por API (SoporteCabinaSAP.cs); diseño AISC 360-16 LRFD"],
             ["Unidades", "N, mm, °C (fila de cabecera de cada tabla tal como la entrega SAP)"],
             ["Cargas", "DEAD: peso propio + cartucho 1 789 N + ménsula 412 N + motorreductor 304 N + rotor real 2 266 N (D-075); BELT 1 071 N; TORQ 60 N·m; "
                        "accidental 1 000 N a z 1400 con el peso excéntrico 2 266 N × 79,6 mm (AXP/AXN/AYP/AYN)"],
             ["Combinaciones", "U1 = 1,4D; U2 = 1,2D + 1,6(BELT + TORQ); U3 = 1,2D + BELT + TORQ + A; S1 = D + BELT + TORQ; S2 = S1 + A"],
             ["Criterios [HIPÓTESIS del autor, D-080]", "D/C ≤ 0,9; flecha S1 ≤ L/1000; lateral del cojinete superior en S2 ≤ 5,0 mm (holgura de 22,9 mm del paso del eje por el techo, CAD V17B); f1 ≥ 3 Hz y sin modos con masa ≥ 5 % entre 17,6 y 26,4 Hz (motor ≈ 1 319 rpm = 22 Hz, ±20 %). D-065 usaba «no peor que el R04» (1,20 mm; 4,26 Hz)"],
             ["Fuente de los números", "tablas_sap/%s_api/*.csv (Database Tables de SAP, GetTableForDisplayArray)" % modelo],
             ["Rigidez de las tablas", "Las tablas son del reanálisis que SAP hace después del diseño AISC 360-16 con el Método de Análisis Directo: "
                                       "rigidez reducida 0,8·EI y 0,8·EA (C2.3), como el anexo de la mesa (D-048). Por eso f1 baja en √0,8 y los "
                                       "desplazamientos suben en 1/0,8 frente al estudio comparativo de D-065 y D-078, hecho con rigidez nominal"],
             [],
             ["RESUMEN", "Con 0,8·EI (tablas SAP)", "Rigidez nominal (estudio)", "Criterio", "Cumple"]]
    for f in filas:
        ws.append(f)
    for k, v in resumen.items():
        ws.append(list(v))
    for c in ws["A"]:
        c.font = NEG
    ws.column_dimensions["A"].width = 40; ws.column_dimensions["B"].width = 26; ws.column_dimensions["C"].width = 26; ws.column_dimensions["D"].width = 44
    # comparacion de todas las variantes con el rotor real (rigidez nominal), como en la seccion de resultados del informe
    wc = wb.create_sheet("11_VARIANTES")
    cab = ["caso", "masa_barras_kg", "masa_chapa_kg", "DC_max", "f1_Hz", "f2_Hz", "cojinete_sup_S2_max_mm", "flecha_apoyo_S1_mm",
           "techo_w_max_S1_mm", "pandeo_min_positivo", "chapa_vm_ultimo_MPa", "reac_M_max_U3_Nmm", "opciones"]
    wc.append(["Variantes con el rotor real, rigidez nominal (soporte_sap/resultados_cabina/RESUMEN_CABINA.csv)"]); wc.cell(1, 1).font = NEG
    wc.append(cab)
    for c in wc[2]:
        c.font = NEG; c.fill = GRIS
    for k, r in NOMINAL.items():
        wc.append([r[c] for c in cab])
    wc.column_dimensions["A"].width = 32; wc.column_dimensions["M"].width = 60
    for nombre, tablas in HOJAS:
        wh = wb.create_sheet(nombre)
        for t in tablas:
            cab, datos = leer(modelo, t)
            wh.append(["Tabla SAP: " + t.replace("_", " ")]); wh.cell(wh.max_row, 1).font = NEG
            if not cab:
                wh.append(["(sin registros)"]); wh.append([]); continue
            wh.append(cab)
            for c in wh[wh.max_row]:
                c.font = NEG; c.fill = GRIS
            for f in datos:
                wh.append(f)
            wh.append([])
        for i in range(1, 16):
            wh.column_dimensions[get_column_letter(i)].width = 13
    salida = A / ("SAP_SOPORTE_%s_export.xlsx" % modelo)
    wb.save(salida)
    return salida


# ------------------------------------------------------------------ resumenes y figuras
NOMINAL = {r["caso"]: r for r in csv.DictReader(open(S / "resultados_cabina" / "RESUMEN_CABINA.csv", encoding="utf-8"))}
# Referencia R04 (soporte anterior, O1 de D-065, rigidez nominal): lateral 1,20 mm y f1 4,26 Hz. Con 0,8·EI: 1,20/0,8 = 1,50 mm y 4,26·√0,8 = 3,81 Hz.


def resumen(modelo):
    """cada fila: indicador, valor con 0,8·EI (tablas SAP de este anexo), valor con rigidez nominal (estudio K), criterio, cumple"""
    nud, barras = geometria(modelo)
    ub = nudo_cerca(nud, (0, 0, 3450))
    lat = max(np.hypot(*desplazamientos(modelo, c)[ub][:2]) for c in ("S2_AXP", "S2_AXN", "S2_AYP", "S2_AYN"))
    dcmax = max(r["Ratio"] for r in dic(*leer(modelo, "Steel_Design_1_Summary_Data_AISC_360_16")))
    fr = [r["Frequency"] for r in dic(*leer(modelo, "Modal_Periods_And_Frequencies"))]
    d1 = desplazamientos(modelo, "S1")
    xc = max(p[0] for p in nud.values() if abs(p[2] - 2790) < 1)
    flecha = abs(d1[nudo_cerca(nud, (0, 300, 2790))][2] - d1[nudo_cerca(nud, (xc, 300, 2790))][2]); luz = 2 * xc
    pand = [r["ScaleFactor"] for r in dic(*leer(modelo, "Buckling_Factors")) if isinstance(r.get("ScaleFactor"), float) and r["ScaleFactor"] > 0]
    n = NOMINAL[modelo]
    # criterios funcionales de D-080 (s06_barrido_delgado.py): C1 D/C <= 0,9; C2 L/1000; C3 lateral <= 5,0 mm (holgura de 22,9 mm en el
    # paso del eje por el techo); C4 f1 >= 3 Hz (nominal) y sin modos de masa participante >= 0,05 entre 17,6 y 26,4 Hz (motor 22 Hz)
    return {"dc": ("D/C máximo AISC 360-16", round(dcmax, 3), float(n["DC_max"]), "≤ 0,9", "sí" if dcmax <= 0.9 else "no"),
            "lat": ("Lateral del cojinete superior en S2 (mm)", round(lat, 3), float(n["cojinete_sup_S2_max_mm"]),
                    "≤ 5,0 (holgura de 22,9 mm en el techo)", "sí" if lat <= 5.0 else "no"),
            "f1": ("Primera frecuencia (Hz)", round(fr[0], 2), float(n["f1_Hz"]), "≥ 3,0 nominal; sin modos en 17,6–26,4 Hz",
                   "sí" if float(n["f1_Hz"]) >= 3.0 else "no"),
            "fl": ("Flecha de la viga en S1 (mm), L = %d" % luz, round(flecha, 3), float(n["flecha_apoyo_S1_mm"]), "≤ L/1000 = %.2f" % (luz / 1000),
                   "sí" if flecha <= luz / 1000 else "no"),
            "pd": ("Primer factor de pandeo lineal (U2/U3)", round(min(pand), 1) if pand else None, float(n["pandeo_min_positivo"] or 0), "—", "—"),
            "mb": ("Masa de barras (kg)", float(n["masa_barras_kg"]), float(n["masa_barras_kg"]), "—", "—")}


res = {m: resumen(m) for m in MODELOS}
for m in MODELOS:
    print("Excel", excel(m, res[m]).name, {k: v[1] for k, v in res[m].items()})

# A1: modelo de D-065 con secciones y cabina de referencia
nud, barras = geometria("K32_M_80x4_150x100x3")
fig = plt.figure(figsize=(11, 7), dpi=140); ax = fig.add_subplot(111, projection="3d")
cabina(ax); dibujar(ax, nud, barras, titulo="")
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([], [], color=ESTILO[k][0], lw=ESTILO[k][1], label=t) for k, t in
                   (("COL", "Postes SHS80×4 (bases empotradas)"), ("VIGA", "Vigas RHS150×100×3 (cara superior z 2890)"), ("LAC", "Celosía y planta L40×4 (articuladas)"))] +
          [Line2D([], [], color="#E67E22", marker="o", ls="", label="Cartucho, cojinetes y motor (cuerpo rígido)"),
           Line2D([], [], color="#BBBBBB", ls="--", label="Cabina (CTX_CABIN), solo referencia")], fontsize=7, loc="upper left")
ax.set_ylim(-2100, 2100); ax.set_box_aspect((4.2, 4.2, 2.8))
fig.suptitle("A1. Modelo SAP2000 del soporte superior aligerado K32 (D-080; tablas Joint Coordinates y Connectivity - Frame)", fontsize=10)
fig.savefig(FIG / "A1_modelo_K32.png"); plt.close(fig)

# A2: D/C por barra (Steel Design Summary), D-065 frente a postes dentro
fig = plt.figure(figsize=(13, 5.6), dpi=140)
PAR = ("K0_O10R_MARCO_SOLO", "K32_M_80x4_150x100x3")
vmax = max(max(r["Ratio"] for r in dic(*leer(m, "Steel_Design_1_Summary_Data_AISC_360_16"))) for m in PAR)
norm = colors.Normalize(0, vmax)
for i, m in enumerate(PAR):
    nud, barras = geometria(m)
    dc = {str(int(r["Frame"])): r["Ratio"] for r in dic(*leer(m, "Steel_Design_1_Summary_Data_AISC_360_16"))}
    ax = fig.add_subplot(1, 2, i + 1, projection="3d")
    dibujar(ax, nud, barras, valores=dc, norm=norm, titulo="%s\nD/C máx. %.3f" % (MODELOS[m], res[m]["dc"][1]))
sm = cm.ScalarMappable(norm=norm, cmap=cm.turbo); sm.set_array([])
fig.colorbar(sm, ax=fig.axes, shrink=0.6, label="D/C (AISC 360-16, LRFD)")
fig.suptitle("A2. Aprovechamiento de las barras (tabla Steel Design 1 - Summary Data, AISC 360-16 con el Método de Análisis Directo)", fontsize=10)
fig.savefig(FIG / "A2_DC_D065_y_K32.png"); plt.close(fig)

# A3: deformada S2 mas desfavorable
fig = plt.figure(figsize=(13, 5.6), dpi=140)
for i, m in enumerate(PAR):
    nud, barras = geometria(m)
    ub = nudo_cerca(nud, (0, 0, 3450))
    peor = max(("S2_AXP", "S2_AXN", "S2_AYP", "S2_AYN"), key=lambda c: np.hypot(*desplazamientos(m, c)[ub][:2]))
    d = desplazamientos(m, peor)
    ax = fig.add_subplot(1, 2, i + 1, projection="3d")
    dibujar(ax, nud, barras, gris=True)
    dibujar(ax, nud, barras, despl=d, escala=300, titulo="%s\n%s: cojinete superior %.2f mm (×300)" % (MODELOS[m], peor, np.hypot(*d[ub][:2])))
fig.suptitle("A3. Deformada bajo la acción accidental de 1 000 N a z 1400 (tabla Joint Displacements, rigidez 0,8·EI; gris: sin deformar)", fontsize=10)
fig.savefig(FIG / "A3_deformada_accidental.png"); plt.close(fig)

# A4: modos 1 a 4 de K32
m = "K32_M_80x4_150x100x3"
nud, barras = geometria(m)
per = dic(*leer(m, "Modal_Periods_And_Frequencies")); par = dic(*leer(m, "Modal_Participating_Mass_Ratios"))
fig = plt.figure(figsize=(14, 9), dpi=130)
for k in range(4):
    d = desplazamientos(m, "MODAL", float(k + 1))
    amp = max(np.linalg.norm(v) for v in d.values()) or 1
    ax = fig.add_subplot(2, 2, k + 1, projection="3d")
    dibujar(ax, nud, barras, gris=True)
    p = par[k]
    dibujar(ax, nud, barras, despl=d, escala=400 / amp,
            titulo="Modo %d: %.2f Hz (masa participante UX %.2f, UY %.2f, UZ %.2f, RZ %.2f)" % (k + 1, per[k]["Frequency"], p["UX"], p["UY"], p["UZ"], p["RZ"]))
fig.suptitle("A4. Modos del soporte K32 (D-080) con rigidez 0,8·EI (tablas Modal Periods And Frequencies y Modal Participating Mass Ratios; con rigidez nominal, f × 1,118); motor ≈ 22 Hz", fontsize=10)
fig.tight_layout(); fig.savefig(FIG / "A4_modos_K32.png"); plt.close(fig)

# A5: comparacion de variantes con el rotor real (resultados_cabina/RESUMEN_CABINA.csv)
NOMV = {"K0_O10R_MARCO_SOLO": "D-065: SHS100×5 / RHS160×80×5", "K19_MUROS_LIVIANO_EMP": "Muros: SHS80×4 / RHS150×100×4",
        "K32_M_80x4_150x100x3": "K32 (D-080): SHS80×4 / RHS150×100×3", "K31_M_75x3_150x100x3": "Muros: SHS75×3 / RHS150×100×3",
        "K24_M_80x4_120x60x4": "Muros: SHS80×4 / RHS120×60×4 (modo 24 Hz)", "K21_M_75x3_150x50x3": "Muros: SHS75×3 / RHS150×50×3 (modo 23 Hz)",
        "K20_M_60x3_150x50x3": "Muros: SHS60×3 / RHS150×50×3 (flojo)", "K27_D_75x3_100x50x3": "Dentro: SHS75×3 / RHS100×50×3 (inox)",
        "K16_ANGOSTO_X1150_MISMOS": "Dentro: SHS100×5 / RHS160×80×5 (inox)"}
filas = {r["caso"]: r for r in csv.DictReader(open(S / "resultados_cabina" / "RESUMEN_CABINA.csv", encoding="utf-8"))}
orden = [k for k in NOMV if k in filas]
ind = [("masa_barras_kg", "Masa de barras (kg)", None), ("DC_max", "D/C máximo", 0.9), ("cojinete_sup_S2_max_mm", "Lateral del cojinete,\naccidental (mm)", 5.0),
       ("f1_Hz", "Primera frecuencia (Hz)", 3.0), ("flecha_apoyo_S1_mm", "Flecha de la viga en\nservicio (mm)", 4.04)]
fig, axs = plt.subplots(1, 5, figsize=(17, 4.2), dpi=140)
for ax, (k, t, lim) in zip(axs, ind):
    v = [float(filas[c][k]) for c in orden]
    col = ["#E45756" if c == "K32_M_80x4_150x100x3" else ("#9C9C9C" if c == "K0_O10R_MARCO_SOLO" else "#4C78A8") for c in orden]
    ax.barh([NOMV[c] for c in orden], v, color=col); ax.invert_yaxis(); ax.set_title(t, fontsize=9); ax.tick_params(labelsize=7)
    if lim:
        ax.axvline(lim, color="#333333", ls="--", lw=0.8)
    for i, x in enumerate(v):
        ax.text(x, i, " %g" % x, va="center", fontsize=7)
    if ax is not axs[0]:
        ax.set_yticklabels([])
fig.suptitle("A5. Barrido de perfiles del soporte en SAP2000 con el rotor real, rigidez nominal (rojo: K32 elegido, D-080; gris: D-065; línea: criterio de D-080)", fontsize=10)
fig.tight_layout(); fig.savefig(FIG / "A5_variantes_tamano_ancho.png"); plt.close(fig)
json.dump({m: {k: list(v) for k, v in r.items()} for m, r in res.items()}, open(A / "RESUMEN_ANEXO.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("figuras OK")
