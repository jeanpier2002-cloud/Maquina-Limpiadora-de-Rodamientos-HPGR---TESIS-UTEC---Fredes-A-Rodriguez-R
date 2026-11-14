#!/usr/bin/env python3
"""
G7 - Tabla final K1-K6 del Caso Base de 22 boquillas (R05) y del Caso 3, por superficie, y K5 por boquilla.
NO recalcula KPIs: los lee de
  K1           : 06_RESULTADOS/G1_G2_rayos/K1_22boq_v2_K1.csv (rayos con obstaculos de R05)
  K2-K5, J     : <g7>/G7_<sup>_indicadores.csv (caso_base_22.py / combinar_kpi.py; variantes obst_10mm, obst_2mm)
  p_huella, v_n: indicadores por corrida de post_kpi.py (magnitudes locales del impacto, no se suman entre ramales)
  K5 por boquilla: <g7>/G7_balance_por_boquilla.csv (balance_global_22.py) + <g7>/G7_<sup>_aportes.csv (obstaculos)
Uso: python tabla_k1k6.py --g7 06_RESULTADOS/G7 [--c3 06_RESULTADOS/G8/comparacion/C3]
Salida: <g7>/G7_tabla_K1_K6.csv, <g7>/G7_K5_por_boquilla.csv, <g7>/G7_tabla_K1_K6.md
"""
import argparse
import csv
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
RES = os.path.join(RAIZ, "06_RESULTADOS")
SUPERF = [("od", "OD"), ("sup", "Cara superior"), ("cara_inf", "Cara inferior"), ("agujero", "Agujero")]
BOQ_SUP = {"od": "LAT_1-5 + INF_EXT (A y B)", "sup": "SUP_1-2 (A y B)", "cara_inf": "INF_EXT (A y B) + INF_INT",
           "agujero": "INT_1-5 + INF_INT"}
# K6 local: corridas cuyos indicadores (post_kpi.py) dan p_huella y v_n de cada superficie
K6_CB = {"od": [("", ["G3/G3_A_base_v3_od", "G4/G4_B_base_v2_od"])],
         "sup": [("", ["G6/G6_ESUP_base_v2_sup"])],
         "cara_inf": [("INF_EXT", ["G3/G3_A_base_v3_cara_inf", "G4/G4_B_base_v2_cara_inf"]),
                      ("INF_INT", ["G5/G5_INT_base_v2_cara_inf"])],
         "agujero": [("", ["G7/F5_red22_pared_agujero"])]}
K6_C3 = dict(K6_CB, od=[("", ["G8/G8_C2_OD_od"])], sup=[("", ["G8/G8_C3_SUP_sup"])])


def leer(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fmt(x, nd):
    return ("%%.%df" % nd % x).replace(".", ",")


def k6_local(spec):
    """[(etiqueta, p_huella_kPa, v_n)] promediando las corridas de cada aporte; None si falta alguna."""
    out = []
    for lab, corr in spec:
        vals = []
        for c in corr:
            p = os.path.join(RES, c + "_indicadores.csv")
            if not os.path.exists(p):
                return None
            r = leer(p)[0]
            vals.append((float(r["K6_p_huella_Pa"]) / 1e3, float(r["K6_vn_medio_m_s"])))
        out.append((lab, sum(v[0] for v in vals) / len(vals), sum(v[1] for v in vals) / len(vals)))
    return out


def tabla(carpeta, k6spec, nombre_caso):
    K1 = {r["superficie"]: r for r in leer(os.path.join(RES, "G1_G2_rayos", "K1_22boq_v2_K1.csv"))}
    filas = []
    for s, lab in SUPERF:
        ind = {r["variante"]: r for r in leer(os.path.join(carpeta, "G7_%s_indicadores.csv" % s))}
        o10, o2 = ind["obst_10mm"], ind["obst_2mm"]
        k6 = k6_local(k6spec[s])
        if k6 is None:
            ph, vn = "pendiente", "pendiente"
        else:
            ph = " / ".join(("%s %s" % (fmt(p, 2), "(%s)" % l if l else "")).strip() for l, p, _ in k6)
            vn = " / ".join(("%s %s" % (fmt(v, 1), "(%s)" % l if l else "")).strip() for l, _, v in k6)
        filas.append(dict(caso=nombre_caso, superficie=lab, boquillas=BOQ_SUP[s],
                          K1_libre_pct=K1[s]["K1_libre_pct"], K1_obst_pct=K1[s]["K1_con_obstaculos_pct"],
                          area_contacto_excluida_pct=K1[s]["area_contacto_excluida_pct"],
                          K2_D_media=o10["D_media"], K2_D_min_10mm=o10["D_min"], K2_D_min_celdas=o10["D_min_celdas"],
                          K2_D_max_10mm=o10["D_max"], K3_CV_10mm=o10["CV"], K3_CV_2mm=o2["CV"],
                          K4_seca_10mm_pct=o10["seca_pct"], K4_seca_2mm_pct=o2["seca_pct"],
                          K4_seca_celdas_2mm_pct=o2["seca_celdas_pct"], K4_cob_D1_pct=o10["cob1_pct"],
                          K4_cob_D5_pct=o10["cob5_pct"], K5_eta_pct=o10["eta_pct"], K6_J_media=o10["J_media"],
                          K6_p_huella_kPa=ph, K6_vn_m_s=vn))
    return filas


def k5_por_boquilla(g7):
    """Destino del caudal de cada una de las 22 boquillas (% de su caudal), libre y con obstaculos."""
    B22 = json.load(open(os.path.join(RAIZ, "03_GEOMETRIA", "boquillas_22.json")))["boquillas"]
    tm = leer(os.path.join(RAIZ, "03_GEOMETRIA", "tabla_maestra_22_boquillas.csv"))
    obj = {r["ident_CFD"]: r["superficie_objetivo_diseno"] for r in tm}
    orden = {r["ident_CFD"]: int(r["id"]) for r in tm}
    dep = {}
    for s, _ in SUPERF:
        for r in leer(os.path.join(g7, "G7_%s_aportes.csv" % s)):
            fac = 2.0 if s == "sup" else 1.0       # cara superior: A x 2 (S9); por boquilla se divide entre 2
            for b in r["boquillas"].split(","):
                dep[(b.upper(), s)] = (float(r["mdot_dep_libre_kg_s"]) / fac, float(r["mdot_dep_obst_kg_s"]) / fac)
    con_dep = {b for b, _ in dep}
    filas = []
    for k in sorted(B22, key=lambda x: orden[x]):
        iny = B22[k]["mdot_kg_s"]
        # ramal B explicito si sus impactos estan en los aportes (OD y cara inferior, G4); si no, B = A (S9)
        kd = k if k in con_dep else k.replace("_B", "_A")
        explicito_B = kd == k
        v = {s: dep.get((kd, s), (0.0, 0.0)) for s, _ in SUPERF}
        libre = sum(x[0] for x in v.values())
        obst = sum(x[1] for x in v.values())
        objetivo = obj[k]
        sup_obj = [s for s, lab in (("od", "OD"), ("sup", "cara superior"), ("cara_inf", "cara inferior"),
                                    ("agujero", "agujero")) if lab in objetivo]
        filas.append(dict(boquilla=k, superficie_objetivo=objetivo, p_bar="%.3f" % B22[k]["p_bar"],
                          q_Lmin="%.3f" % B22[k]["q_Lmin"], mdot_kg_s="%.6f" % iny,
                          eta_objetivo_libre_pct="%.2f" % (100 * sum(v[s][0] for s in sup_obj) / iny),
                          eta_objetivo_obst_pct="%.2f" % (100 * sum(v[s][1] for s in sup_obj) / iny),
                          OD_pct="%.2f" % (100 * v["od"][1] / iny), sup_pct="%.2f" % (100 * v["sup"][1] / iny),
                          cara_inf_pct="%.2f" % (100 * v["cara_inf"][1] / iny),
                          agujero_pct="%.2f" % (100 * v["agujero"][1] / iny),
                          obstaculos_pct="%.2f" % (100 * (libre - obst) / iny),
                          escape_pct="%.2f" % (100 * max(iny - libre, 0.0) / iny),
                          fuente_B=("G4" if explicito_B else "= A, S9") if k.endswith("_B") else ""))
    return filas


def md(filas_cb, filas_c3, k5, salida):
    L = ["# G7 — Tabla K1-K6 del Caso Base de 22 boquillas (R05) y del Caso 3", "",
         "> Generada por `05_SCRIPTS/tabla_k1k6.py` a partir de los CSV de `06_RESULTADOS` (no recalcula KPIs). "
         "Estado: CANDIDATO, verificado numéricamente; nada validado. KPIs pendientes de aprobación del asesor (F2).", "",
         "Unidades: D y D_min en kg·m⁻²·vuelta⁻¹ (1,7 rpm, HIPÓTESIS); J̄ en N·s·m⁻²·vuelta⁻¹; p_huella en kPa; v_n en m/s. "
         "Con PAD, topes y vigas de R05 (máscaras de rayos). Zona seca = bandas con D ≤ 10⁻⁹ (10 mm oficial; 2 mm "
         "complementario).", ""]
    bloques = [("Caso Base R05 (oficial: ramales A y B explícitos en OD y cara inferior; cara superior A × 2, S9)",
                filas_cb)]
    if filas_c3:
        bloques.append(("Rediseño: Caso Base frente a Caso 3 con la misma base (ramal A × 2, `G8/comparacion`); "
                        "solo las superficies que cambian (la cara inferior y el agujero no cambian)",
                        [f for f in filas_c3 if f["superficie"] in ("OD", "Cara superior")]))
    for nombre, filas in bloques:
        if not filas:
            continue
        L += ["## %s" % nombre, "",
              "| Superficie | Boquillas | K1 (%) | K2 D̄ | K2 D_min 10 mm | K3 CV 10 / 2 mm | K4 seca 10 / 2 mm (%) | "
              "K4 área con D ≥ 5 (%) | K5 η (%) | K6 J̄ | K6 p_huella | K6 v_n |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for f in filas:
            L.append("| %s | %s | %s | %s | %s | %s / %s | %s / %s | %s | %s | %s | %s | %s |" % (
                f["superficie"] + ("" if f["caso"] == "Caso Base" or len(bloques) == 1 else " · " + f["caso"]),
                f["boquillas"], fmt(float(f["K1_obst_pct"]), 1), fmt(float(f["K2_D_media"]), 2),
                fmt(float(f["K2_D_min_10mm"]), 2), fmt(float(f["K3_CV_10mm"]), 3), fmt(float(f["K3_CV_2mm"]), 3),
                fmt(float(f["K4_seca_10mm_pct"]), 2), fmt(float(f["K4_seca_2mm_pct"]), 2),
                fmt(float(f["K4_cob_D5_pct"]), 1), fmt(float(f["K5_eta_pct"]), 1), fmt(float(f["K6_J_media"]), 0),
                f["K6_p_huella_kPa"], f["K6_vn_m_s"]))
        L.append("")
    L += ["## K5 por boquilla (Caso Base, % del caudal de cada boquilla, con obstáculos)", "",
          "| Boquilla | Objetivo de diseño | p (bar) | q (L/min) | η objetivo (%) | OD | Cara sup. | Cara inf. | Agujero | "
          "PAD/topes/vigas | Escape |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for f in k5:
        L.append("| %s%s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            f["boquilla"], (" (%s)" % f["fuente_B"]) if f["fuente_B"] else "", f["superficie_objetivo"],
            fmt(float(f["p_bar"]), 2), fmt(float(f["q_Lmin"]), 2), fmt(float(f["eta_objetivo_obst_pct"]), 1),
            fmt(float(f["OD_pct"]), 1), fmt(float(f["sup_pct"]), 1), fmt(float(f["cara_inf_pct"]), 1),
            fmt(float(f["agujero_pct"]), 1), fmt(float(f["obstaculos_pct"]), 1), fmt(float(f["escape_pct"]), 1)))
    L += ["", "Notas: η con pared `trap` es cota superior; los valores levemente mayores que 100 % son fluctuación de la "
          "ventana de muestreo, dentro del cierre del balance (< 0,1 %). p_huella y v_n son magnitudes locales del impacto "
          "por corrida (no se suman entre ramales). Cara superior: ramal B = A (S9, verificado en el OD ±0,09 %). "
          "Ramal B 'G4' = corrida explícita del ramal B."]
    open(salida, "w", encoding="utf-8").write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--g7", required=True)
    ap.add_argument("--c3", default=os.path.join(RES, "G8", "comparacion", "C3"))
    a = ap.parse_args()
    g7 = a.g7 if os.path.isabs(a.g7) else os.path.join(RAIZ, a.g7)
    cb = tabla(g7, K6_CB, "Caso Base")
    c3 = []
    if os.path.isdir(a.c3):
        K6_CB_A2 = dict(K6_CB, od=[("", ["G3/G3_A_base_v3_od"])])   # base A x 2 (misma corrida que la comparacion)
        cbA2 = tabla(os.path.join(os.path.dirname(a.c3), "CB"), K6_CB_A2, "Caso Base (A × 2)")
        c3 = [x for par in zip(cbA2, tabla(a.c3, K6_C3, "Caso 3")) for x in par]
    with open(os.path.join(g7, "G7_tabla_K1_K6.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(cb[0]))
        w.writeheader()
        w.writerows(cb + c3)
    k5 = k5_por_boquilla(g7)
    with open(os.path.join(g7, "G7_K5_por_boquilla.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(k5[0]))
        w.writeheader()
        w.writerows(k5)
    md(cb, c3, k5, os.path.join(g7, "G7_tabla_K1_K6.md"))
    for f in cb + c3:
        print("%-9s %-14s K1 %s D %7.2f Dmin %6.2f CV %.3f seca %s/%s eta %5.1f J %6.0f pH %s vn %s" % (
            f["caso"], f["superficie"], f["K1_obst_pct"], float(f["K2_D_media"]), float(f["K2_D_min_10mm"]),
            float(f["K3_CV_10mm"]), f["K4_seca_10mm_pct"], f["K4_seca_2mm_pct"], float(f["K5_eta_pct"]),
            float(f["K6_J_media"]), f["K6_p_huella_kPa"], f["K6_vn_m_s"]))
    print("->", os.path.join(g7, "G7_tabla_K1_K6.md"))


if __name__ == "__main__":
    main()
