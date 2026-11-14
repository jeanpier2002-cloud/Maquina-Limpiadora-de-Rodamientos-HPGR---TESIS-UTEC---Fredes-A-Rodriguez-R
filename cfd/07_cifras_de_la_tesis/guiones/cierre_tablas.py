#!/usr/bin/env python3
"""
CIERRE DEL CFD PARA LA TESIS (11/11/2026, a pedido de Jean) · tabla unica de resultados finales del capitulo 7.
Solo LEE resultados ya ejecutados (CFD03, Corridas 2, 3 y 4); no corre nada ni modifica originales.
Cada cifra sale de un archivo y queda en salida/CIFRAS_CIERRE_CFD.csv con su fuente.
Salidas:
  salida/CIFRAS_CIERRE_CFD.csv     cifra por cifra, con fuente (archivo, fila, columna)
  salida/tablas_cap07_cfd.tex       BORRADOR de tablas LaTeX para Prism (lo audita Jean)
  salida/CIERRE_CFD_tablas_para_Jean.pdf  lectura (HTML -> Edge headless)
Terminologia (Jean, 11/11): E1 = «lavado» (objetivo: inspeccion visual), no «prelavado»; el lavado de detalle
va despues, en la remanufactura, con el rodamiento desarmado. La empresa no se nombra en la tesis.
Uso: python -I -B cierre_tablas.py
"""
import csv
import os
import subprocess
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
OUT = RAIZ + "/salida"
BUILD = OUT + "/build"
os.makedirs(BUILD, exist_ok=True)
EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"

G = "G:/Mi unidad/Semestre X/TESIS II/Sistema de aspersión/CFD03_ANSYS_COMPLETO/06_RESULTADOS"
R2 = "D:/CFD_Redosado/CORRIDA_2_desde24oct"
R3 = "D:/CFD_Redosado/CORRIDA_3_O7C2/03_FLUENT/resultados"
R4 = "D:/CFD_Redosado/CORRIDA_4_PRIMER_LAVADO"
TESIS_P2 = "D:/ENTREGABLE P2/PRISM_ACTUAL_EXTRAIDO/secciones/cap07_pruebas_resultados/00_capitulo.tex"

F_G7 = G + "/G7/G7_tabla_K1_K6.csv"
F_C2 = G + "/G8/comparacion/C2/G7_%s_indicadores.csv"
F_C3 = G + "/G8/comparacion/C3/G7_%s_indicadores.csv"
F_KIT = R3 + "/KPI/R3_01_kit/R3_01_kit_resumen.csv"
F_VIG = R3 + "/KPI/R3_02_03_AB/R3_02_03_AB_resumen.csv"
F_MALLA = R3 + "/T9_malla.csv"
F_PART = R3 + "/T9_particulas.csv"
F_RUIDO = R3 + "/T9_ruido_AB.csv"
F_N1 = R3 + "/T7_N1_vs_CFD.csv"
F_CO = R2 + "/03_FLUENT/resultados/RESUMEN_Co_vs_dt_fijo.csv"
F_BALCO = R2 + "/03_FLUENT/resultados/BALANCES_Co.csv"
F_T4 = R4 + "/03_DOSIS_TIEMPO/T4_t95_tabla.csv"
F_EQ = R3 + "/T10_tiempo_lavado_equipo.csv"
F_GATE = R4 + "/02_CAVIDAD_N1/d2400_M8_gate.csv"
F_UNION = R4 + "/02_CAVIDAD_N1/d2400_M8_union.csv"
F_GRASA = R4 + "/02_CAVIDAD_N1/T3b_grasa_skf.csv"
F_SOMB = R4 + "/03_DOSIS_TIEMPO/T4b_sombras.csv"
F_DEST = R3 + "/destino_R3_02_caso2.csv"
F_VOF2 = R2 + "/02_VOF_v3/INFORME_E1_OD_v3.md"
F_VOF1 = "D:/CFD_Redosado/CORRIDA_1_13a21oct/06_VOF/RESUMEN_PARA_JEAN_VOF.md"

CIFRAS = []


def leer(p):
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def una(filas, **k):
    for r in filas:
        if all(r.get(c) == v for c, v in k.items()):
            return r
    raise KeyError("%s no encontrado" % k)


def c(v, nd=2):
    """numero con coma decimal"""
    if isinstance(v, str):
        return v
    s = ("%." + str(nd) + "f") % v
    return s.replace(".", ",")


def reg(tabla, fila, magnitud, valor, unidad, fuente, nota=""):
    CIFRAS.append([tabla, fila, magnitud, valor if isinstance(valor, str) else repr(round(valor, 6)), unidad, fuente, nota])
    return valor


# =====================================================================  A · evolucion por caso
g7 = leer(F_G7)
A = []   # filas: superficie, caso, D, Dmin, CV, seca10, seca2, eta, J, fuente


def fila_g7(caso, sup, etiqueta):
    r = una(g7, caso=caso, superficie=sup)
    v = dict(D=float(r["K2_D_media"]), Dmin=float(r["K2_D_min_10mm"]), CV=float(r["K3_CV_10mm"]),
             s10=float(r["K4_seca_10mm_pct"]), s2=float(r["K4_seca_2mm_pct"]), eta=float(r["K5_eta_pct"]), J=float(r["K6_J_media"]))
    A.append((sup, etiqueta, v, F_G7 + " [caso=%s]" % caso))


def fila_ind(path, sup_txt, etiqueta, sup_csv=None):
    """indicadores G8 (variante obst_10mm y obst_2mm) o resumen R3 (superficie,variante)"""
    filas = leer(path)
    if sup_csv:
        r10 = una(filas, superficie=sup_csv, variante="obst_10mm")
        r2 = una(filas, superficie=sup_csv, variante="obst_2mm")
    else:
        r10 = una(filas, variante="obst_10mm")
        r2 = una(filas, variante="obst_2mm")
    v = dict(D=float(r10["D_media"]), Dmin=float(r10["D_min"]), CV=float(r10["CV"]), s10=float(r10["seca_pct"]),
             s2=float(r2["seca_pct"]), eta=float(r10["eta_pct"]), J=float(r10["J_media"]))
    A.append((sup_txt, etiqueta, v, path))


fila_g7("Caso Base", "OD", "Caso Base (22 boquillas)")
fila_ind(F_C2 % "od", "OD", "Casos 2 y 3 (LAT_1 a −4°)")
fila_ind(F_KIT, "OD", "O7+C2 sin Caso 2 (24 boq.)", "od")
fila_ind(F_VIG, "OD", "Vigente: O7+C2 + Caso 2", "od")
fila_g7("Caso Base", "Cara superior", "Caso Base y Caso 2")
fila_ind(F_C3 % "sup", "Cara superior", "Caso 3 (SUP_2 +15 mm) ‡")
fila_g7("Caso Base", "Cara inferior", "Caso Base, Casos 2 y 3")
fila_ind(F_VIG, "Cara inferior", "Vigente: O7+C2", "cara_inf")
fila_g7("Caso Base", "Agujero", "Todos los casos †")
for sup, et, v, src in A:
    for k, u in (("D", "kg/m2/vuelta"), ("Dmin", "kg/m2/vuelta"), ("CV", "-"), ("s10", "%"), ("s2", "%"), ("eta", "%"),
                 ("J", "N s/m2/vuelta")):
        reg("A_evolucion", sup + " | " + et, k, v[k], u, src)

# =====================================================================  B · verificacion
B = []   # estudio, superficie, dD, dCV, fuente
malla, part, ruido = leer(F_MALLA), leer(F_PART), leer(F_RUIDO)
for (sup_txt, k_d, k_cv) in (("OD (vigente)", "OD: D̄ (kg·m⁻²·vuelta⁻¹)", "OD: CV (−)"),
                             ("Cara inferior (vigente)", "Cara inferior: D̄ (kg·m⁻²·vuelta⁻¹)", "Cara inferior: CV (−)")):
    d = float(una(malla, kpi=k_d)["cambio_dos_mas_finos"]); cv = float(una(malla, kpi=k_cv)["cambio_dos_mas_finos"])
    gci = float(una(malla, kpi=k_d)["GCI_fino_pct"])
    B.append(("Malla, 3 niveles con Courant constante (GCI %s %%)" % c(gci, 2), sup_txt, d, cv, F_MALLA))
    reg("B_verificacion", "malla " + sup_txt, "dD_pct", d, "%", F_MALLA, "cambio entre las dos mallas mas finas")
    reg("B_verificacion", "malla " + sup_txt, "dCV_abs", cv, "-", F_MALLA)
    reg("B_verificacion", "malla " + sup_txt, "GCI_fino_pct", gci, "%", F_MALLA)
co = leer(F_CO)
for (fam, sup, txt) in (("Cara superior (E-SUP)", "cara superior", "Cara superior (geometría del Caso Base)"),
                        ("INF_INT (agujero y cara inferior)", "agujero", "Agujero")):
    d = float(una(co, familia=fam, superficie=sup, kpi="K2_D_media_kg_m2_vuelta")["fina_menos_base_Co"])
    cv = float(una(co, familia=fam, superficie=sup, kpi="K3_CV")["fina_menos_base_Co"])
    B.append(("Malla, 3 niveles con Courant constante", txt, d, cv, F_CO))
    reg("B_verificacion", "malla Co " + txt, "dD_pct", d, "%", F_CO, "fina menos base, Courant constante")
    reg("B_verificacion", "malla Co " + txt, "dCV_abs", cv, "-", F_CO)
for (sup_txt, k_d, k_cv) in (("OD (vigente)", "OD: D̄ (kg·m⁻²·vuelta⁻¹)", "OD: CV (−)"),
                             ("Cara inferior (vigente)", "Cara inferior: D̄ (kg·m⁻²·vuelta⁻¹)", "Cara inferior: CV (−)")):
    d = float(una(part, kpi=k_d)["cambio_dos_mas_finos"]); cv = float(una(part, kpi=k_cv)["cambio_dos_mas_finos"])
    B.append(("Número de parcelas ×0,5 / ×1 / ×2", sup_txt, d, cv, F_PART))
    reg("B_verificacion", "parcelas " + sup_txt, "dD_pct", d, "%", F_PART)
    reg("B_verificacion", "parcelas " + sup_txt, "dCV_abs", cv, "-", F_PART)
for (sup_txt, k_d, k_cv) in (("OD (vigente)", "OD: D̄ (kg·m⁻²·vuelta⁻¹)", "OD: CV (−)"),
                             ("Cara inferior (vigente)", "Cara inferior: D̄ (kg·m⁻²·vuelta⁻¹)", "Cara inferior: CV (−)")):
    d = float(una(ruido, kpi=k_d)["B_menos_A"]); cv = float(una(ruido, kpi=k_cv)["B_menos_A"])
    B.append(("Ruido entre brazos A y B equivalentes", sup_txt, d, cv, F_RUIDO))
    reg("B_verificacion", "ruido AB " + sup_txt, "dD_pct", d, "%", F_RUIDO)
    reg("B_verificacion", "ruido AB " + sup_txt, "dCV_abs", cv, "-", F_RUIDO)
# Δt y dominio: tabla de verificacion de la tesis P2 (origen CFD03 G6); se copian como texto
B.append(("Paso de tiempo a la mitad", "Todas", "≤ 0,01", "≤ 0,0001", TESIS_P2 + " [tab:verificacion-cfd]"))
B.append(("Dominio ampliado", "Todas", "≤ 0,14", "≤ 0,0084", TESIS_P2 + " [tab:verificacion-cfd]"))
B.append(("Caso puente OpenFOAM ↔ Fluent", "Agujero", "0,27", "0,0035", TESIS_P2 + " [Modelo de mojado y verificación]"))
reg("B_verificacion", "dt/2", "dD_pct", "≤ 0,01", "%", TESIS_P2, "tesis P2, origen G6")
reg("B_verificacion", "dominio", "dD_pct", "≤ 0,14", "%", TESIS_P2, "tesis P2, origen G6")
reg("B_verificacion", "caso puente", "dD_pct", "0,27", "%", TESIS_P2, "tesis P2: OpenFOAM rama B vs Fluent")
n1 = leer(F_N1)
r_n1 = una(n1, superficie="cara_inferior", magnitud="D_media_A+B")
d_n1 = 100 * (float(r_n1["N1"]) / float(r_n1["CFD_Caso2_AB"]) - 1)
cv_n1 = float(una(n1, superficie="cara_inferior", magnitud="CV")["N1"]) - float(una(n1, superficie="cara_inferior", magnitud="CV")["CFD_Caso2_AB"])
B.append(("Predicción previa por trazado de rayos frente a CFD", "Cara inferior (vigente)", d_n1, cv_n1, F_N1))
reg("B_verificacion", "N1 vs CFD cara inferior", "dD_pct", d_n1, "%", F_N1, "N1 / CFD - 1")
# balances
bal3 = []
for f in sorted(os.listdir(R3)):
    if f.endswith("_aceptacion.txt") and "humo" not in f:
        t = open(R3 + "/" + f, encoding="utf-8").read()
        bal3.append(float(t.split("balance")[1].split("%")[0]))
balco = list({r["caso"]: float(r["error_balance_pct"]) for r in leer(F_BALCO)}.values())   # sin casos base repetidos
bal_min, bal_max = min(bal3 + balco), max(bal3 + balco)
reg("B_verificacion", "balance de masa", "min_pct", bal_min, "%", R3 + "/*_aceptacion.txt + " + F_BALCO)
reg("B_verificacion", "balance de masa", "max_pct", bal_max, "%", R3 + "/*_aceptacion.txt + " + F_BALCO)
n_bal = len(bal3) + len(balco)

# =====================================================================  C · lavado E1 (t95)
t4 = leer(F_T4)
C = []
for sup in ("OD", "Cara superior", "Agujero", "Cara inferior"):
    fila = [sup]
    for lect, col in (("media θ", "t95_acc_min_media_theta"), ("por celdas", "t95_acc_min_celdas")):
        vals = []
        for dr in ("65", "183", "305"):
            r = una(t4, superficie=sup, zona="total", D_req=dr)
            v = r[col]
            vals.append(v)
            reg("C_lavado_E1", sup + " | " + lect, "t95_min_Dreq" + dr, v if v == "no alcanzada" else float(v), "min",
                F_T4, "95 % del area accesible con D >= D_req")
        fila.append((lect, vals))
    C.append(fila)
eq = leer(F_EQ)
manda = una(eq, D_req="183")["superficie_que_manda"]
somb = leer(F_SOMB)

# =====================================================================  D · cavidad y grasa
gate = leer(F_GATE)
un = leer(F_UNION)


def fu(sup, mitad):
    return float(una(un, tag="d2400", subconjunto="todas", superficie=sup, fila_o_mitad=mitad, prof_mm="todo")["frac_N1_media"])


def fe(sup, mitad):
    return float(una(un, tag="d2400", subconjunto="todas", superficie=sup, fila_o_mitad=mitad, prof_mm="extremo")["frac_N1_media"])


cav_tot = float(una(gate, tag="d2400", subconjunto="todas")["frac_area_rodillos_mas_pistas_N1"])
D = [("Rodillos y pistas, total (cota superior, sin jaula)", cav_tot),
     ("Hilera superior: flanco de los rodillos", fu("rodillo_flanco", "hilera_sup")),
     ("Hilera superior: extremo de los rodillos hacia la cara", fe("rodillo_extremo_cara", "hilera_sup")),
     ("Hilera inferior: flanco de los rodillos", fu("rodillo_flanco", "hilera_inf")),
     ("Hilera inferior: extremo de los rodillos hacia la cara", fe("rodillo_extremo_cara", "hilera_inf")),
     ("Pista exterior, mitad superior", fu("pista_exterior", "mitad_sup")),
     ("Pista exterior, mitad inferior", fu("pista_exterior", "mitad_inf")),
     ("Pista interior, mitad superior", fu("pista_interior", "mitad_sup")),
     ("Pista interior, mitad inferior", fu("pista_interior", "mitad_inf"))]
for t, v in D:
    reg("D_cavidad", t, "frac_N1", v, "-", F_UNION if "total" not in t else F_GATE, "2 400 rayos/plano, dphi 0,1 deg")
gr = leer(F_GRASA)
vlib = [float(r["V_libre_SKF_dm3"]) for r in gr]
mg = [float(r["M_grasa_cavidad_kg"]) for r in gr if r["llenado_pct"] == "100"]
pct = [r["pct_masa_en_cavidad"] for r in gr if r["llenado_pct"] == "100"]
pmin = min(float(p.split("-")[0]) for p in pct); pmax = max(float(p.split("-")[1]) for p in pct)
reg("D_cavidad", "volumen libre (SKF)", "V_dm3", "%s-%s" % (c(min(vlib), 0), c(max(vlib), 0)), "dm3", F_GRASA)
reg("D_cavidad", "grasa en la cavidad, llena", "M_kg", "%s-%s" % (c(min(mg), 0), c(max(mg), 0)), "kg", F_GRASA)
reg("D_cavidad", "fraccion de la grasa en la cavidad", "pct", "%s-%s" % (c(pmin, 0), c(pmax, 0)), "%", F_GRASA)
dest = leer(F_DEST)
c2_aguj = float(una(dest, boquilla="c2_a")["pct_abierto_agujero"])
reg("A_evolucion", "nota agujero", "C2 hacia el agujero", c2_aguj, "% del caudal de C2_A", F_DEST, "no contabilizado en el agujero")

# =====================================================================  E · accion hidraulica (VOF) — de informes .md
E = [("Empuje de la película en el OD a 0,33 mm del eje (lámina 2D, LAT_3_A)", "17,0 N/m (0,94 del valor teórico)", F_VOF2),
     ("Cortante en la pared, lámina intacta (cota superior)", "≈ 2 kPa a 0,33 mm; 0,6–1 kPa en la película", F_VOF2 + " ; " + F_VOF1),
     ("Cortante en la pared, mezcla equivalente 3D (cota inferior)", "5 → 25 Pa (no converge al refinar)", F_VOF1),
     ("Umbral τ₀ candidato de la grasa (por analogía)", "20 / 300 / 1000 Pa", "D:/CFD_Redosado/CORRIDA_1_13a21oct/METRICA_GRASA/04_ENTREGA/U9_UMBRAL_ANALOGICO.md"),
     ("KPI-1 (τ_w > τ₀)", "Indeterminado: las dos cotas quedan a ambos lados del umbral", F_VOF1)]
for t, v, s in E:
    reg("E_accion", t, "valor", v, "", s)

# =====================================================================  CSV maestro
with open(OUT + "/CIFRAS_CIERRE_CFD.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["tabla", "fila", "magnitud", "valor", "unidad", "fuente", "nota"])
    w.writerows(CIFRAS)

# =====================================================================  textos comunes
NOTA_A = ("D en kg·m⁻² por vuelta y J en N·s·m⁻² por vuelta, a 1,7 rpm; bandas de 10 mm con las sombras del soporte. "
          "Los Casos 2 y 3 se compararon contra un Caso Base emparejado (brazo A duplicado: OD con D_mín 0,27 y franja seca "
          "de 2 mm de 1,17 %). La transferencia η depende de qué boquillas se asignan a cada superficie, por eso baja en el "
          "OD del diseño vigente (INF_EXT y C2 reparten su caudal entre el OD y la cara inferior).")
NOTA_DAGA = ("† Agujero: no se re-simuló en el diseño vigente (cambio de caudal ≤ 0,03 %%); la boquilla C2 envía además "
             "%s %% de su caudal hacia el agujero, que no está contabilizado: la dosis del agujero es una cota inferior." % c(c2_aguj, 1))
NOTA_DOBLE = ("‡ El diseño vigente usa el Caso 3 en la cara superior solo si la SUP_2 desplazada 15 mm está en los planos "
              "[INTERFAZ ISMAEL]; si no, rige la fila «Caso Base y Caso 2».")
NOTA_C = ("t₉₅: tiempo hasta que el 95 % del área accesible recibe la dosis acumulada D_req (vueltas enteras de 35,294 s; "
          "horizonte 120 min). «Media θ»: dosis media de cada banda de 10 mm; «por celdas»: celdas de 10 mm × 0,5°, que ven las "
          "sombras parciales de las bases de los apoyos y de los topes. D_req = 65/183/305 kg·m⁻² es un dato externo pendiente "
          "(analogía con ensayos de remoción de grasa por aspersión). Alcanzar D_req no equivale a limpiar.")

# =====================================================================  LaTeX (borrador)
def tx(s):
    s = s.replace("_", "\\_").replace("D\\_req", "D_req").replace("D\\_mín", "D_mín").replace("τ\\_w", "τ_w")
    return (s.replace("%", "\\%").replace("≤", "$\\leq$").replace("→", "$\\rightarrow$").replace("×", "$\\times$")
            .replace("↔", "$\\leftrightarrow$").replace("τ₀", "$\\tau_0$").replace("τ_w", "$\\tau_w$").replace("θ", "$\\theta$")
            .replace("η", "$\\eta$").replace("t₉₅", "$t_{95}$").replace("D_req", "$D_{req}$").replace("D_mín", "$D_{mín}$")
            .replace("−", "$-$").replace("°", "$^\\circ$").replace("·", "\\,").replace("⁻²", "$^{-2}$").replace("₀", "$_0$")
            .replace("†", "$^\\dagger$").replace("‡", "$^\\ddagger$").replace("≈", "$\\approx$").replace("²", "$^2$")
            .replace("π", "$\\pi$").replace("<", "$<$").replace(" > ", " $>$ ").replace("±", "$\\pm$"))


L = ["% ======================================================================",
     "% BORRADOR de tablas del capitulo 7 (subsistema de aspersion) - 11/11/2026",
     "% Generado por D:/CFD_Redosado/CIERRE_CFD_TESIS/scripts/cierre_tablas.py desde los CSV de resultados.",
     "% Cada cifra tiene su fuente en salida/CIFRAS_CIERRE_CFD.csv. AUDITAR antes de pegar en Prism.",
     "% Estilo copiado de la tesis P2 (booktabs, \\small\\singlespacing, columna Y de tabularx).",
     "% ======================================================================", ""]
# --- A
L += ["\\begin{table}[htbp]", "\\centering\\small\\singlespacing", "\\setlength{\\tabcolsep}{3.5pt}",
      "\\caption{Indicadores de mojado por superficie, desde el Caso Base hasta el diseño vigente}",
      "\\label{tab:cfd-evolucion}", "\\begin{tabular}{@{}llcccccc@{}}", "\\toprule",
      "\\textbf{Superficie} & \\textbf{Caso} & \\textbf{$\\bar D$} & \\textbf{$D_{mín}$} & \\textbf{CV} & "
      "\\textbf{Seca 10/2 mm (\\%)} & \\textbf{$\\eta$ (\\%)} & \\textbf{$\\bar J$}\\\\", "\\midrule"]
prev = None
for sup, et, v, _ in A:
    if prev is not None and sup != prev:
        L.append("\\addlinespace")
    L.append("%s & %s & %s & %s & %s & %s / %s & %s & %s\\\\" % (
        sup if sup != prev else "", tx(et), c(v["D"]), c(v["Dmin"]), c(v["CV"], 3), c(v["s10"], 0) if v["s10"] == 0 else c(v["s10"]),
        c(v["s2"], 0) if v["s2"] == 0 else c(v["s2"]), c(v["eta"], 1), c(v["J"], 0)))
    prev = sup
L += ["\\bottomrule", "\\end{tabular}", "\\par\\smallskip\\footnotesize", tx(NOTA_A) + "\\\\", tx(NOTA_DAGA) + "\\\\", tx(NOTA_DOBLE),
      "\\end{table}", ""]
# --- B
L += ["\\begin{table}[htbp]", "\\centering\\small\\singlespacing", "\\setlength{\\tabcolsep}{3.5pt}",
      "\\caption{Verificación numérica del modelo de mojado del diseño vigente}", "\\label{tab:cfd-verificacion-vigente}",
      "\\begin{tabularx}{\\textwidth}{@{}YlcC{2.0cm}@{}}" .replace("C{2.0cm}", "c"), "\\toprule",
      "\\textbf{Estudio} & \\textbf{Superficie} & \\textbf{Cambio en $\\bar D$ (\\%)} & \\textbf{Cambio en CV}\\\\", "\\midrule"]
for est, sup, d, cv, _ in B:
    L.append("%s & %s & %s & %s\\\\" % (tx(est), tx(sup),
                                         tx(d if isinstance(d, str) else ("%+.2f" % d).replace(".", ",").replace("-", "−")),
                                         tx(cv if isinstance(cv, str) else ("%+.4f" % cv).replace(".", ",").replace("-", "−"))))
L += ["\\bottomrule", "\\end{tabularx}", "\\par\\smallskip\\footnotesize",
      tx("Criterio de trabajo: cambio < 5 %% en $\\bar D$ y < 0,03 en CV. Balance de masa en las %d corridas revisadas: "
         "%s–%s %% (criterio < 1 %%). La dosis mínima cambia hasta ±18 %% porque la fija una sola banda; se informa, pero no se usa "
         "para juzgar convergencia. Concordancia entre programas no equivale a validación física." % (n_bal, c(bal_min, 3), c(bal_max, 3))),
      "\\end{table}", ""]
# --- C
L += ["\\begin{table}[htbp]", "\\centering\\small\\singlespacing", "\\setlength{\\tabcolsep}{4pt}",
      "\\caption{Tiempo del lavado (rodamiento armado) hasta la dosis de referencia en el 95\\,\\% del área accesible}",
      "\\label{tab:cfd-tiempo-lavado}", "\\begin{tabular}{@{}llccc@{}}", "\\toprule",
      "\\textbf{Superficie} & \\textbf{Lectura} & \\textbf{$D_{req}=65$} & \\textbf{$D_{req}=183$} & \\textbf{$D_{req}=305$}\\\\",
      "& & \\multicolumn{3}{c}{\\textbf{$t_{95}$ (min)}}\\\\", "\\midrule"]
for fila in C:
    sup = fila[0]
    for i, (lect, vals) in enumerate(fila[1:]):
        if sup != "Cara inferior" and i == 1:
            continue
        lect_txt = "media $\\theta$ y por celdas" if sup != "Cara inferior" else tx(lect)
        L.append("%s & %s & %s\\\\" % (sup if i == 0 else "", lect_txt,
                                       " & ".join("$>120$" if v == "no alcanzada" else c(float(v), 1) for v in vals)))
L += ["\\bottomrule", "\\end{tabular}", "\\par\\smallskip\\footnotesize", tx(NOTA_C), "\\end{table}", ""]
# --- D
L += ["\\begin{table}[htbp]", "\\centering\\small\\singlespacing",
      "\\caption{Acceso geométrico a la cavidad con el rodamiento armado y masa de grasa estimada}",
      "\\label{tab:cfd-cavidad}", "\\begin{tabularx}{\\textwidth}{@{}Yc@{}}", "\\toprule",
      "\\textbf{Zona} & \\textbf{Área con línea de vista (\\%)}\\\\", "\\midrule"]
for t, v in D:
    L.append("%s & %s\\\\" % (tx(t), c(100 * v, 2 if v < 0.01 else 1)))
L += ["\\midrule",
      "Volumen libre del rodamiento (regla del fabricante) & %s--%s dm$^3$\\\\" % (c(min(vlib), 0), c(max(vlib), 0)),
      "Grasa en la cavidad, llena (0,9 kg/dm$^3$) & %s--%s kg\\\\" % (c(min(mg), 0), c(max(mg), 0)),
      "Fracción de la grasa que está en la cavidad & %s--%s\\,\\%%\\\\" % (c(pmin, 0), c(pmax, 0)),
      "\\bottomrule", "\\end{tabularx}", "\\par\\smallskip\\footnotesize",
      tx("Trazado de rayos desde las 24 boquillas con el barrido de 360° del aplicador, 2 400 rayos por plano; geometría de aros "
         "y rodillos medida en el modelo del fabricante, sin jaula, por lo que el acceso es una cota superior. La línea de vista no "
         "incluye el escurrimiento ni la película que bajan desde la hilera superior. Volumen libre: π/4·B·(D² − d²) − M/7,8, con el "
         "agujero cónico tomado en su extremo menor y en su diámetro medio; grasa con la cavidad llena, como en la lubricación por "
         "purga de estos equipos."),
      "\\end{table}", ""]
# --- E
L += ["\\begin{table}[htbp]", "\\centering\\small\\singlespacing",
      "\\caption{Acción hidráulica local de un chorro sobre el diámetro exterior (VOF) y estado del indicador de cortante}",
      "\\label{tab:cfd-accion}", "\\begin{tabularx}{\\textwidth}{@{}YX@{}}".replace("X@", "l@"), "\\toprule",
      "\\textbf{Magnitud} & \\textbf{Valor}\\\\", "\\midrule"]
for t, v, _ in E:
    L.append("%s & %s\\\\" % (tx(t), tx(v)))
L += ["\\bottomrule", "\\end{tabularx}", "\\end{table}", ""]
with open(OUT + "/tablas_cap07_cfd.tex", "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")

# =====================================================================  HTML -> PDF (lectura para Jean)
CSS = """
@page { size: A4; margin: 11mm 12mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 9pt; line-height: 1.32; color: #1b1b1b; }
h1 { font-size: 15.5pt; margin: 0 0 2px 0; } h2 { font-size: 11.4pt; margin: 12px 0 4px 0; border-bottom: 1.5px solid #1f4e79; color: #1f4e79; padding-bottom: 1px; }
.sub { color: #555; font-size: 8.6pt; margin-bottom: 6px; }
.caja { background: #eef4fb; border-left: 4px solid #1f4e79; padding: 5px 10px; margin: 6px 0; }
.aviso { background: #fff6e0; border-left: 4px solid #d99000; padding: 5px 10px; margin: 6px 0; }
.malo { background: #fdeeee; border-left: 4px solid #b22222; padding: 5px 10px; margin: 6px 0; }
table { border-collapse: collapse; width: 100%; margin: 3px 0; font-size: 8.1pt; }
th { background: #1f4e79; color: #fff; text-align: left; padding: 2px 4px; } td { border-bottom: 1px solid #ccc; padding: 2px 4px; vertical-align: top; }
tr.vig td { background: #eaf5ea; font-weight: 600; } tr.mal td { background: #fdeeee; }
.pie { color: #555; font-size: 7.7pt; margin-top: 2px; } .pb { page-break-before: always; }
ul { margin: 3px 0 3px 18px; padding: 0; } li { margin-bottom: 2px; }
"""


def tabla_html(cab, filas, clases=None):
    h = "<table><tr>" + "".join("<th>%s</th>" % x for x in cab) + "</tr>"
    for i, f in enumerate(filas):
        cl = (" class='%s'" % clases[i]) if clases and clases[i] else ""
        h += "<tr%s>" % cl + "".join("<td>%s</td>" % x for x in f) + "</tr>"
    return h + "</table>"


H = ["<!doctype html><html lang='es'><head><meta charset='utf-8'><style>%s</style></head><body>" % CSS]
H.append("<h1>Cierre del CFD · tabla única de resultados para el capítulo 7</h1>")
H.append("<div class='sub'>11/11/2026 · Borrador de trabajo para auditar (Jean). Solo junta resultados ya ejecutados (CFD03, Corridas 2, 3 y 4); "
         "no hay corridas nuevas. Cada cifra tiene su fuente en <b>CIFRAS_CIERRE_CFD.csv</b>; las tablas en LaTeX están en "
         "<b>tablas_cap07_cfd.tex</b> (misma carpeta).</div>")
H.append("<div class='caja'><b>Qué cambia frente a la tesis de P2 (11/10).</b> P2 llega hasta los Casos 2 y 3 con 22 boquillas. Faltan: "
         "(1) el <b>diseño vigente O7+C2 con el Caso 2</b> (24 boquillas), que mejora mucho la cara inferior y empeora la uniformidad del OD; "
         "(2) su verificación (malla con Courant constante, parcelas, brazos A/B); (3) el <b>tiempo del lavado</b>; (4) la <b>cavidad</b> y la "
         "<b>masa de grasa</b>; (5) el VOF y el estado del indicador de cortante. Tablas A–E abajo; la tabla F lista las limitaciones que se "
         "agregan.</div>")
H.append("<div class='malo'><b>Antes de pegar nada: dos cosas que debes confirmar con Ismael.</b> (a) Que los planos tengan la "
         "<b>LAT_1 inclinada −4°</b> (Caso 2): sin ella reaparece una franja sin impacto de 2 mm en el OD (1,56 %) y el D_mín cae a 0,13. "
         "(b) Si los planos tienen la <b>SUP_2 desplazada 15 mm</b> (Caso 3): decide qué fila de la cara superior es la vigente.</div>")

# A
H.append("<h2>A · Indicadores por caso y superficie</h2>")
cl = []
fil = []
for sup, et, v, _ in A:
    fil.append([sup, et, c(v["D"]), c(v["Dmin"]), c(v["CV"], 3), "%s / %s" % (c(v["s10"], 2), c(v["s2"], 2)), c(v["eta"], 1), c(v["J"], 0)])
    cl.append("vig" if et.startswith("Vigente") else ("mal" if "sin Caso 2" in et else ""))
H.append(tabla_html(["Superficie", "Caso", "D̄", "D_mín (10 mm)", "CV", "Seca 10 / 2 mm (%)", "η (%)", "J̄"], fil, cl))
H.append("<div class='pie'>%s<br>%s<br>%s</div>" % (NOTA_A, NOTA_DAGA, NOTA_DOBLE))
H.append("<div class='caja'><b>Cómo se lee.</b> El diseño vigente sube la cara inferior de 5,5 a 14,2 kg·m⁻²·vuelta⁻¹ y su D_mín de 2,9 a 7,3; "
         "el OD mantiene la dosis media y queda sin zona seca, pero su CV pasa de 0,27 a 0,65 porque la INF_EXT nueva concentra dosis "
         "en la parte baja (z 890–1000 mm). Ninguna superficie tiene zona seca en el diseño vigente.</div>")
# B
H.append("<h2>B · Verificación numérica</h2>")
fil = []
for est, sup, d, cv, _ in B:
    fil.append([est, sup, d if isinstance(d, str) else ("%+.2f" % d).replace(".", ","), cv if isinstance(cv, str) else ("%+.4f" % cv).replace(".", ",")])
H.append(tabla_html(["Estudio", "Superficie", "Cambio en D̄ (%)", "Cambio en CV (abs.)"], fil))
H.append("<div class='pie'>Criterio de trabajo: &lt; 5 %% en D̄ y &lt; 0,03 en CV. Balance de masa en %d corridas: %s–%s %% (criterio &lt; 1 %%). "
         "Δt, dominio, caso puente y las mallas de la cara superior y del agujero se hicieron sobre el Caso Base (P2 y Corrida 2); "
         "el diseño vigente solo cambia la LAT_1 y las boquillas inferiores, y esas superficies tienen su propio estudio. "
         "Verificado ≠ validado.</div>" % (n_bal, c(bal_min, 3), c(bal_max, 3)))
# C
H.append("<h2 class='pb'>C · Tiempo del lavado (E1, rodamiento armado)</h2>")
fil = []
cl = []
for fila in C:
    sup = fila[0]
    for i, (lect, vals) in enumerate(fila[1:]):
        if sup != "Cara inferior" and i == 1:
            continue
        fil.append([sup if i == 0 else "", "media θ y por celdas" if sup != "Cara inferior" else lect] +
                   ["&gt; 120" if v == "no alcanzada" else c(float(v), 1) for v in vals])
        cl.append("mal" if (sup == "Cara inferior" and i == 1) else "")
H.append(tabla_html(["Superficie", "Lectura", "t₉₅ con D_req 65 (min)", "D_req 183", "D_req 305"], fil, cl))
H.append("<div class='pie'>%s Superficie que manda: %s.</div>" % (NOTA_C, manda.lower()))
H.append("<div class='aviso'><b>Para el texto:</b> con la dosis media por banda, el lavado lleva las cuatro superficies externas a la meta en "
         "≈ 3–24 min según D_req; con la lectura por celdas la cara inferior tarda 27–76 min (y más de 120 con D_req 305) por las sombras "
         "parciales de las bases de los apoyos y de los topes. Las dos lecturas deben ir juntas; la tabla de P2/T10 llamaba «peor celda» "
         "a lo que era la peor banda.</div>")
# D
H.append("<h2>D · Cavidad (rodillos y pistas) y grasa</h2>")
H.append(tabla_html(["Zona", "Área con línea de vista (%)"], [[t, c(100 * v, 2 if v < 0.01 else 1)] for t, v in D] +
                    [["<b>Volumen libre del rodamiento (regla del fabricante)</b>", "%s–%s dm³" % (c(min(vlib), 0), c(max(vlib), 0))],
                     ["<b>Grasa en la cavidad, llena</b>", "%s–%s kg" % (c(min(mg), 0), c(max(mg), 0))],
                     ["<b>Fracción de la grasa que está en la cavidad</b>", "%s–%s %%" % (c(pmin, 0), c(pmax, 0))]]))
H.append("<div class='pie'>Sin jaula en el modelo: el acceso es cota superior. La línea de vista no incluye escurrimiento ni película. "
         "Contraste: el registro de reuniones de la tesis anota ≈ 300 kg de residuos por campaña de cuatro rodamientos (≈ 75 kg por "
         "rodamiento, por confirmar), coherente con la estimación.</div>")
H.append("<div class='caja'><b>Lectura para la tesis.</b> El lavado (E1) tiene como objetivo la inspección visual con el rodamiento armado; "
         "lo que el chorro ve desde fuera es, a grandes rasgos, lo mismo que puede ver el inspector. La hilera inferior y la mitad baja de "
         "las pistas quedan fuera de ambos y se tratan en el lavado de detalle, con el rodamiento desarmado, en la remanufactura "
         "(argumento razonado, no demostrado).</div>")
# E
H.append("<h2>E · Acción hidráulica local (VOF) e indicador de cortante</h2>")
H.append(tabla_html(["Magnitud", "Valor"], [[t, v] for t, v, _ in E]))
H.append("<div class='pie'>VOF con interFoam (OpenFOAM v2606): corte 2D de la lámina de LAT_3_A sobre el OD y caso 3D con mezcla "
         "equivalente. Son cotas, no valores de diseño.</div>")
# F
H.append("<h2>F · Limitaciones que se agregan o cambian en la tabla de limitaciones</h2>")
F = [["Cavidad", "Solo ≈ %s %% de rodillos y pistas tiene línea de vista; la hilera inferior casi nada (flanco %s %%); sin jaula (cota superior)."
      % (c(100 * cav_tot, 0), c(100 * D[3][1], 2)), "Lavado de detalle tras el desarme; ensayo futuro"],
     ["Cara inferior", "Sombras parciales de bases de apoyos y topes: t₉₅ por celdas de 14 a 76 min (D_req 183)", "Informar ambas lecturas; ensayo de la cara inferior primero"],
     ["Agujero (vigente)", "No incluye el aporte de C2 hacia el agujero (%s %% de su caudal)" % c(c2_aguj, 1), "Declarar como cota inferior"],
     ["Planos [INTERFAZ ISMAEL]", "Los números del diseño vigente suponen la LAT_1 a −4° (y la SUP_2 +15 mm si rige el Caso 3)", "Confirmar en los planos"],
     ["Indicador de cortante", "Indeterminado: cotas de 5–25 Pa y ≈ 2 kPa frente a τ₀ = 20–1000 Pa", "Ensayo de huella o modelo de película (trabajo futuro)"],
     ["Dosis de referencia", "D_req y τ₀ por analogía con literatura; dato externo pendiente", "Ensayo de remoción con la grasa real"],
     ["Remoción (E14, E15)", "El CFD no mide remoción ni water-break", "Quedan «pendiente de ensayo»"]]
H.append(tabla_html(["Resultado", "Limitación", "Acción"], F))
H.append("<div class='aviso'><b>Qué no se puede escribir:</b> «queda limpio», «se lava a la primera», «validado», «cumple la inspección». "
         "<b>Qué sí:</b> «alcanza la dosis de referencia en el X % del área accesible en t min», «verificado numéricamente», "
         "«cumple en el modelo; pendiente de ensayo».</div>")
H.append("</body></html>")
html = BUILD + "/CIERRE_CFD.html"
with open(html, "w", encoding="utf-8") as f:
    f.write("\n".join(H))
pdf = OUT + "/CIERRE_CFD_tablas_para_Jean.pdf"
if os.path.exists(pdf):
    os.remove(pdf)
perfil = BUILD + "/perfil_edge"
os.makedirs(perfil, exist_ok=True)
cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-first-run", "--user-data-dir=" + perfil, "--no-pdf-header-footer",
       "--allow-file-access-from-files", "--print-to-pdf=" + pdf.replace("/", "\\"), "file:///" + html]
subprocess.run(cmd, capture_output=True, text=True, timeout=240)
ult, est = -1, 0
for _ in range(90):
    tam = os.path.getsize(pdf) if os.path.exists(pdf) else -1
    est = est + 1 if (tam == ult and tam > 0) else 0
    ult = tam
    if est >= 3:
        break
    time.sleep(1)
print("cifras:", len(CIFRAS), "| PDF:", pdf, os.path.getsize(pdf) if os.path.exists(pdf) else "NO")
print("balance %d corridas: %.3f-%.3f %%" % (n_bal, bal_min, bal_max), "| C2->agujero %.2f %%" % c2_aguj, "| manda:", manda)
