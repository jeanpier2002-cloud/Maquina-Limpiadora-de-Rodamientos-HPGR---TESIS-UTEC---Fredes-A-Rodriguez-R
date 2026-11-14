#!/usr/bin/env python3
"""
G6 - Resumen de la verificacion numerica (malla, dt, dominio, parcelas) de CFD03. No recalcula KPIs: compara los
indicadores de post_kpi.py (06_RESULTADOS/<fase>/<caso>_<zona>_indicadores.csv) de cada estudio con su corrida base.
  Mallas (3 niveles): GCI de Celik et al. (2008) con gci.py (h = N^-1/3), solo si existen las tres corridas.
  dt/2, dominio y parcelas: cambio relativo frente a la base.
  Ruido de corrida medido con el par A/B (G4_S9_A_vs_B_S18.csv) para el OD y la cara inferior (INF_EXT).
Criterio de trabajo (CLAUDE.md, checklist): cambio < 5 % entre las dos mallas mas finas (objetivo inicial, no norma).
Uso: python informe_g6.py      Salida: 06_RESULTADOS/G6/G6_resumen_verificacion.csv y .md
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gci import gci  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(AQUI), "06_RESULTADOS")
KPIS = [("K2_D_media_kg_m2_vuelta", "D̄"), ("K3_CV", "CV"), ("K2_D_min", "D_min"),
        ("K6_J_media_N_s_m2_vuelta", "J̄"), ("K6_p_huella_Pa", "p_huella"), ("K5_eta_pct", "η")]
TRIADAS = [  # (nombre, zona, [gruesa, base, fina], celdas)
    ("E-SUP (SUP_1-2)", "sup", ["G6/G6_ESUP_gruesa", "G6/G6_ESUP_base_v2", "G6/G6_ESUP_fina"], [112480, 237552, 464820]),
    ("OD (LAT_1-5 + INF_EXT)", "od", ["G6/G6_G3_gruesa", "G3/G3_A_base_v3", "G6/G6_G3_fina"], [202616, 430560, 846960]),
    ("Cara inferior (INF_EXT)", "cara_inf", ["G6/G6_G3_gruesa", "G3/G3_A_base_v3", "G6/G6_G3_fina"],
     [202616, 430560, 846960]),
    ("Cara inferior (INF_INT)", "cara_inf", ["G6/G6_INT_gruesa", "G5/G5_INT_base_v2", "G6/G6_INT_fina"],
     [90896, 197280, 381300]),
    ("Borde del agujero (INF_INT)", "agujero", ["G6/G6_INT_gruesa", "G5/G5_INT_base_v2", "G6/G6_INT_fina"],
     [90896, 197280, 381300]),
]
PARES = [  # (estudio, superficie, zona, variante, base)
    ("Δt / 2 (2,5·10⁻⁵ s)", "Cara inferior (INF_INT)", "cara_inf", "G6/G6_INT_dt25", "G5/G5_INT_base_v2"),
    ("Δt / 2 (2,5·10⁻⁵ s)", "Borde del agujero (INF_INT)", "agujero", "G6/G6_INT_dt25", "G5/G5_INT_base_v2"),
    ("Dominio ampliado (±18°, r 400-1050 mm, z 750-1450 mm)", "OD", "od", "G6/G6_G3_dominio", "G3/G3_A_base_v3"),
    ("Dominio ampliado (±18°, r 400-1050 mm, z 750-1450 mm)", "Cara inferior (INF_EXT)", "cara_inf",
     "G6/G6_G3_dominio", "G3/G3_A_base_v3"),
    ("Parcelas: 150 frente a 600/1200 rayos", "OD", "od", "G3/G3_A_base", "G3/G3_A_base_v3"),
    ("Parcelas: 150 frente a 600 rayos", "Cara superior", "sup", "G6/G6_ESUP_base", "G6/G6_ESUP_base_v2"),
    ("Parcelas: 150 frente a 1200 rayos", "Cara inferior (INF_INT)", "cara_inf", "G6/G6_INT_n150", "G5/G5_INT_base_v2"),
    ("Ruido de corrida: ramal B frente a A", "OD", "od", "G4/G4_B_base_v2", "G3/G3_A_base_v3"),
    ("Ruido de corrida: ramal B frente a A", "Cara inferior (INF_EXT)", "cara_inf", "G4/G4_B_base_v2", "G3/G3_A_base_v3"),
]


def ind(caso, zona):
    p = os.path.join(RES, "%s_%s_indicadores.csv" % (caso, zona))
    if not os.path.exists(p):
        return None
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))[0]


def fmt(x, nd=2):
    if x != x:                       # nan (base nula, p. ej. D_min = 0 en una zona parcial)
        return "—"
    return ("%%+.%df" % nd % x).replace(".", ",")


RUIDO_PAR = {"od": ("G4/G4_B_base_v2", "G3/G3_A_base_v3"), "cara_inf_INF_EXT": ("G4/G4_B_base_v2", "G3/G3_A_base_v3")}


def ruido(nombre, zona):
    """Ruido de corrida medido con el par A/B (geometricamente identicos): |cambio| relativo (%) o absoluto (CV).
    Solo existe para el OD y la cara inferior con INF_EXT; para el resto devuelve None."""
    clave = "od" if zona == "od" else ("cara_inf_INF_EXT" if "INF_EXT" in nombre else None)
    if clave is None:
        return None
    a, b = ind(RUIDO_PAR[clave][0], zona), ind(RUIDO_PAR[clave][1], zona)
    out = {}
    for k, _ in KPIS:
        x, y = float(a[k]), float(b[k])
        out[k] = abs(x - y) if k == "K3_CV" else (abs(100 * (x / y - 1)) if y else float("nan"))
    return out


def main():
    filas = []
    md = ["# G6 — Verificación numérica de CFD03 (malla, Δt, dominio, parcelas)", "",
          "> Generado por `05_SCRIPTS/informe_g6.py`. **Verificación, no validación.** Criterio de trabajo del checklist: "
          "cambio < 5 % entre las dos mallas más finas (objetivo inicial, no norma). CV y zona seca se comparan en valor "
          "absoluto; el resto en %.", ""]
    md += ["## 1. Estudios de malla (3 niveles; GCI de Celik et al. 2008)", ""]
    for nombre, zona, casos, celdas in TRIADAS:
        I = [ind(c, zona) for c in casos]
        if any(x is None for x in I):
            falta = [c for c, x in zip(casos, I) if x is None]
            md += ["**%s:** pendiente (%s)." % (nombre, ", ".join(falta)), ""]
            continue
        h = [(1.0 / n) ** (1.0 / 3.0) for n in celdas]
        r21, r32 = h[1] / h[2], h[0] / h[1]
        md += ["### %s — %s / %s / %s celdas (r21 = %s, r32 = %s)" % (nombre, *[format(n, ",").replace(",", " ") for n in celdas],
                                                   ("%.3f" % r21).replace(".", ","), ("%.3f" % r32).replace(".", ",")), "",
               "| KPI | gruesa | base | fina | fina − base | ruido de corrida (A/B) | convergencia | p | GCI fina | ¿< 5 %? |",
               "|---|---|---|---|---|---|---|---|---|---|"]
        rz = ruido(nombre, zona)
        for k, lab in KPIS:
            f3, f2, f1 = (float(x[k]) for x in I)
            g = gci(f1, f2, f3, r21, r32)
            absoluto = k == "K3_CV"
            d = (f1 - f2) if absoluto else 100 * (f1 / f2 - 1) if f2 else float("nan")
            ok = abs(d / f2 * 100) < 5 if absoluto and f2 else abs(d) < 5
            c = lambda v: ("%.4g" % v).replace(".", ",")
            if rz is None:
                txt_r = "sin par A/B"
            else:
                r = rz[k]
                txt_r = (("±%.4f" % r) if absoluto else ("±%.2f %%" % r)).replace(".", ",")
                if abs(d) <= r:
                    txt_r += " → **cambio dentro del ruido**"
            tipo = g["tipo"].replace("monotona", "monótona").replace("oscilatoria", "oscilante").replace(
                " (diverge: |e21| > |e32|)", ", sin reducción (cambio fina−base mayor que base−gruesa)")
            md.append("| %s | %s | %s | %s | %s%s | %s | %s | %s | %s | %s |" % (
                lab, c(f3), c(f2), c(f1), fmt(d, 4 if absoluto else 2), "" if (absoluto or d != d) else " %", txt_r,
                tipo,
                ("%.2f" % g["p"]).replace(".", ",") if g["p"] == g["p"] else "—",
                ("%.2f %%" % (100 * g["gci"])).replace(".", ",") if g["gci"] == g["gci"] else "—", "sí" if ok else "**no**"))
            filas.append(["malla", nombre, lab, casos[0], casos[1], casos[2], f3, f2, f1, d, g["tipo"], g["p"],
                          100 * g["gci"] if g["gci"] == g["gci"] else "", ok])
        md.append("")
    md += ["**Cómo leer el GCI.** El procedimiento de Celik et al. supone que la diferencia entre mallas es error de "
           "discretización. Cuando el cambio entre las dos mallas finas es menor que el ruido de corrida del flujo acoplado "
           "(medido con el par A/B), la diferencia está dominada por ese ruido: el GCI y el orden p no son interpretables y "
           "basta con comprobar que el cambio sea pequeño (< 5 %). D_min lo fija una sola banda y no se usa para juzgar la "
           "convergencia.", ""]
    md += ["## 2. Δt, dominio, parcelas y ruido de corrida (cambio frente a la corrida base)", "",
           "| Estudio | Superficie | " + " | ".join(l for _, l in KPIS) + " |", "|---|---|" + "---|" * len(KPIS)]
    for est, sup, zona, var, base in PARES:
        a, b = ind(var, zona), ind(base, zona)
        if a is None or b is None:
            md.append("| %s | %s | " % (est, sup) + " | ".join("pendiente" for _ in KPIS) + " |")
            continue
        celdas = []
        for k, _ in KPIS:
            x, y = float(a[k]), float(b[k])
            d = (x - y) if k == "K3_CV" else (100 * (x / y - 1) if y else float("nan"))
            celdas.append(fmt(d, 4) if (k == "K3_CV" or d != d) else fmt(d, 2) + " %")
            filas.append([est, sup, k, var, base, "", y, "", x, d, "", "", "", ""])
        md.append("| %s | %s | %s |" % (est, sup, " | ".join(celdas)))
    md += ["", "D_min es el KPI más sensible (lo fija una sola banda, p. ej. la franja del OD): se informa pero no se usa "
           "para juzgar la convergencia.", ""]
    out = os.path.join(RES, "G6")
    with open(os.path.join(out, "G6_resumen_verificacion.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["estudio", "superficie", "kpi", "c1", "c2", "c3", "v_gruesa_o_base", "v_base", "v_fina_o_variante",
                    "cambio", "convergencia", "p", "GCI_fina_pct", "cumple_5pct"])
        w.writerows(filas)
    open(os.path.join(out, "G6_resumen_verificacion.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
