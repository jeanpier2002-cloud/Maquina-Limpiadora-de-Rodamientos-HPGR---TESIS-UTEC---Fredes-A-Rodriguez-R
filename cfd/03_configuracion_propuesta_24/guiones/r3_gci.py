#!/usr/bin/env python3
"""
CFD03 - Indice de convergencia de malla (GCI) con el procedimiento de Celik et al. (2008, J. Fluids Eng. 130):
  h_i = (1/N_i)^(1/3) (mismo dominio), r21 = h2/h1, r32 = h3/h2 (1 = fina, 2 = base, 3 = gruesa)
  eps21 = phi2 - phi1, eps32 = phi3 - phi2, s = sign(eps32/eps21)
  p = |ln|eps32/eps21| + q(p)| / ln r21,  q(p) = ln((r21^p - s)/(r32^p - s))   (iteracion de punto fijo)
  phi_ext = (r21^p phi1 - phi2)/(r21^p - 1); e_a21 = |(phi1 - phi2)/phi1|; GCI_fina = 1,25 e_a21/(r21^p - 1)
Ademas compara |eps21| con el ruido de corrida medido (par A/B, --ruido KPI=valor_relativo): si el cambio entre
las dos mallas finas es menor que el ruido, el efecto de malla no es resoluble y se reporta como tal.
Uso: python gci.py --casos G6/G6_G3_gruesa G3/G3_A_base_v3 G6/G6_G3_fina --celdas 202616 430560 846960 \
        --zona od --salida G6/G6_GCI_G3_od [--ruido K3_CV=0.0023]
"""
import argparse
import csv
import math
import os

RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "06_RESULTADOS")
KPIS = ["K2_D_media_kg_m2_vuelta", "K3_CV", "K4_zona_seca_pct", "K2_D_min", "K6_J_media_N_s_m2_vuelta",
        "K6_p_huella_Pa", "K6_vn_medio_m_s", "K5_eta_pct"]


def gci(f1, f2, f3, r21, r32):
    e21, e32 = f2 - f1, f3 - f2
    if abs(e21) < 1e-14 or abs(e32) < 1e-14:
        return dict(tipo="sin cambio", p=float("nan"), ext=float("nan"), gci=0.0 if abs(e21) < 1e-14 else float("nan"))
    s = 1.0 if e32 / e21 > 0 else -1.0
    p = abs(math.log(abs(e32 / e21))) / math.log(r21)
    for _ in range(200):
        try:
            q = math.log((r21 ** p - s) / (r32 ** p - s))
        except (ValueError, ZeroDivisionError):
            break
        pn = abs(math.log(abs(e32 / e21)) + q) / math.log(r21)
        if abs(pn - p) < 1e-10:
            p = pn
            break
        p = pn
    tipo = "monotona" if s > 0 else "oscilatoria"
    if abs(e21) > abs(e32):
        tipo += " (diverge: |e21| > |e32|)"
    ext = (r21 ** p * f1 - f2) / (r21 ** p - 1) if p > 0 else float("nan")
    ea = abs((f1 - f2) / f1) if f1 else float("nan")
    g = 1.25 * ea / (r21 ** p - 1) if p > 0 else float("nan")
    return dict(tipo=tipo, p=p, ext=ext, gci=g)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--casos", nargs=3, required=True, help="gruesa base fina (rutas relativas a 06_RESULTADOS)")
    ap.add_argument("--celdas", nargs=3, type=float, required=True)
    ap.add_argument("--zona", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ruido", action="append", default=[], help="KPI=ruido relativo (fraccion) o absoluto para CV/seca")
    a = ap.parse_args()
    ruido = {k: float(v) for k, v in (x.split("=") for x in a.ruido)}
    ind = []
    for c in a.casos:
        ind.append(list(csv.DictReader(open(os.path.join(RES, "%s_%s_indicadores.csv" % (c, a.zona)))))[0])
    N3, N2, N1 = a.celdas
    h = lambda n: (1.0 / n) ** (1.0 / 3.0)
    r21, r32 = h(N2) / h(N1), h(N3) / h(N2)
    filas = []
    print("zona %s | r21 = %.3f, r32 = %.3f" % (a.zona, r21, r32))
    for k in KPIS:
        f3, f2, f1 = (float(i[k]) for i in ind)
        g = gci(f1, f2, f3, r21, r32)
        cambio = 100 * (f1 / f2 - 1) if f2 else float("nan")
        absol = k in ("K3_CV", "K4_zona_seca_pct")
        dif = (f1 - f2) if absol else cambio / 100
        rz = ruido.get(k)
        res = "" if rz is None else ("dentro del ruido (|%.4g| <= %.4g)" % (dif, rz) if abs(dif) <= rz else "mayor que el ruido")
        filas.append([k, "%.6g" % f3, "%.6g" % f2, "%.6g" % f1, "%.3f" % cambio, g["tipo"], "%.3g" % g["p"],
                      "%.6g" % g["ext"], "%.3f" % (100 * g["gci"]) if g["gci"] == g["gci"] else "nan", res])
        print("  %-26s %10s %10s %10s | fina vs base %+7s %% | %-30s p %6s GCI_fina %7s %% %s" % (
            k, filas[-1][1], filas[-1][2], filas[-1][3], filas[-1][4], g["tipo"], filas[-1][6], filas[-1][8], res))
    out = os.path.join(RES, a.salida + ".csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kpi", "gruesa", "base", "fina", "cambio_fina_vs_base_pct", "convergencia", "p", "phi_extrapolado",
                    "GCI_fina_pct", "frente_al_ruido_de_corrida"])
        w.writerows(filas)
    print("->", out)


if __name__ == "__main__":
    main()
