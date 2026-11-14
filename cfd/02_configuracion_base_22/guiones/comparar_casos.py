#!/usr/bin/env python3
"""
CFD03 - Compara KPIs (salidas de post_kpi.py) de varias corridas frente a una referencia, por superficie.
Lee 06_RESULTADOS/<fase>/<caso>_<zona>_indicadores.csv y _dosis_por_banda.csv.
Diferencia relativa (%) para D, J, p_huella, v_n, eta; absoluta para CV y zona seca; RMSE del perfil D por banda
(en % de la media de la referencia).

Uso: python comparar_casos.py --ref G3/G3_A_base --casos G4/G4_B_base [...] --zonas od,cara_inf --salida G4/G4_S9
     (rutas relativas a 06_RESULTADOS; --salida = prefijo del CSV)
"""
import argparse
import csv
import os

import numpy as np

RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "06_RESULTADOS")
REL = ["K2_D_media_kg_m2_vuelta", "K2_D_min", "K6_J_media_N_s_m2_vuelta", "K6_p_huella_Pa", "K6_vn_medio_m_s",
       "K5_eta_pct", "mdot_depositado_kg_s"]
ABS = ["K3_CV", "K4_zona_seca_pct"]


def ind(c, z):
    p = os.path.join(RES, "%s_%s_indicadores.csv" % (c, z))
    return list(csv.DictReader(open(p)))[0] if os.path.exists(p) else None


def perfil(c, z):
    p = os.path.join(RES, "%s_%s_dosis_por_banda.csv" % (c, z))
    return np.array([float(r["D_kg_m2_vuelta"]) for r in csv.DictReader(open(p))]) if os.path.exists(p) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--casos", nargs="+", required=True)
    ap.add_argument("--zonas", default="od")
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()
    filas = []
    for z in a.zonas.split(","):
        r = ind(a.ref, z)
        pr = perfil(a.ref, z)
        if r is None:
            print("sin referencia para", z)
            continue
        for c in [a.ref] + a.casos:
            k = ind(c, z)
            if k is None:
                print("falta", c, z)
                continue
            f = {"zona": z, "caso": c}
            for q in REL:
                f[q] = k[q]
                f["d_" + q + "_pct"] = "%.3f" % (100 * (float(k[q]) / float(r[q]) - 1)) if float(r[q]) else ""
            for q in ABS:
                f[q] = k[q]
                f["d_" + q] = "%.4f" % (float(k[q]) - float(r[q]))
            p = perfil(c, z)
            if p is not None and pr is not None and len(p) == len(pr):
                f["RMSE_perfil_pct"] = "%.2f" % (100 * np.sqrt(np.mean((p - pr) ** 2)) / pr.mean())
            filas.append(f)
            print("%-9s %-24s D %s (%s %%) | CV %s (%s) | seca %s | Dmin %s | J %s (%s %%) | p %s (%s %%) | eta %s | RMSE %s %%" % (
                z, c, k["K2_D_media_kg_m2_vuelta"], f["d_K2_D_media_kg_m2_vuelta_pct"], k["K3_CV"], f["d_K3_CV"],
                k["K4_zona_seca_pct"], k["K2_D_min"], k["K6_J_media_N_s_m2_vuelta"], f["d_K6_J_media_N_s_m2_vuelta_pct"],
                k["K6_p_huella_Pa"], f["d_K6_p_huella_Pa_pct"], k["K5_eta_pct"], f.get("RMSE_perfil_pct", "-")))
    out = os.path.join(RES, a.salida + ".csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    claves = []
    for f in filas:
        claves += [k for k in f if k not in claves]
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=claves)
        w.writeheader()
        w.writerows(filas)
    print("->", out)


if __name__ == "__main__":
    main()
