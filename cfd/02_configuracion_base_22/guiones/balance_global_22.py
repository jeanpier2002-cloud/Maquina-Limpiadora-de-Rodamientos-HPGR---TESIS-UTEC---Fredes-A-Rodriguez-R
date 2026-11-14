#!/usr/bin/env python3
"""
G7 - Balance global de las 22 boquillas: a donde va el caudal de la red de 22 (202,59 L/min = 3,31617 kg/s).

Cada boquilla se cuenta UNA vez, con la corrida que la representa:
  LAT_1-5 + INF_EXT ramal A : G3 (sector libre)      | ramal B : G4 explicito (o = A por S9)
  SUP_1-2 ramal A           : G6_ESUP_base x 2 (S9)
  INF_INT                   : sector G5_INT (cara inferior + agujero + escape)
  INT_1-5                   : F5_red22 (o F5 de CFD02 escalado a la red de 22); sin INF_INT (ya contada)
Destinos por boquilla = flujo de impactos en la ventana (CSV de dpm2csv) por zona. Las zonas abiertas = escape del
dominio. Los obstaculos de R05 (PAD, topes, vigas) se descuentan de cada superficie con las mascaras de rayos
(combinar_kpi.py: libre - obst) y se reportan aparte.
Uso: python balance_global_22.py --config casos_G7.json --salida 06_RESULTADOS/G7
"""
import argparse
import csv
import json
import os

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
import sys  # noqa: E402
sys.path.insert(0, AQUI)
RAIZ = os.path.dirname(AQUI)
B22 = json.load(open(os.path.join(RAIZ, "03_GEOMETRIA", "boquillas_22.json")))["boquillas"]
RHO = 982.1203530851709
OBJ = {"od": "OD", "cara_inf": "cara inferior", "sup": "cara superior", "agujero": "agujero",
       "pared_agujero": "agujero", "cara_inf_rodamiento": "cara inferior", "cara_sup_rodamiento": "cara superior",
       "lanza": "lanza", "pad": "PAD"}


def flujos(carpeta, t0, t1, boqs, escala=None):
    """{zona: {boquilla: kg/s}} en la ventana, solo para las boquillas pedidas (escala opcional por boquilla)."""
    out = {}
    for f in os.listdir(carpeta):
        if not f.endswith(".csv") or f.startswith("abanico_"):
            continue
        z = f[:-4]
        ruta = os.path.join(carpeta, f)
        with open(ruta, newline="", encoding="utf-8-sig") as fh:
            cab = next(csv.reader(fh), [])
        if not {"boquilla", "t", "masa"} <= set(cab):      # solo CSV de impactos (dpm2csv)
            continue
        # lectura por columnas con filtro de ventana (od.csv llega a ~1,6 GB con S18; lector_impactos.py)
        from lector_impactos import leer as _leer
        R = _leer(ruta, ["t", "masa"], texto=("boquilla",), filtro_t=(t0, t1))
        if not R.get("masa", np.zeros(0)).size:
            continue
        m = R["masa"]
        b = np.array([x.lower() for x in R["boquilla"]], dtype=object)
        for bb in boqs:
            v = m[b == bb].sum() / (t1 - t0) * (escala.get(bb, 1.0) if escala else 1.0)
            if v > 0:
                out.setdefault(z, {})[bb] = v
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()
    C = json.load(open(a.config))
    os.makedirs(a.salida, exist_ok=True)
    filas = []        # (grupo, boquilla, factor, inyectado, {destino: kg/s})

    def agrega(grupo, clave, boqs, fac=1.0, escala=None, ident=lambda b: b.upper()):
        c, t0, t1 = C[clave]
        F = flujos(c, t0, t1, boqs, escala)
        for bb in boqs:
            dest = {}
            for z, d in F.items():
                if bb in d:
                    k = OBJ.get(z, "escape")
                    dest[k] = dest.get(k, 0.0) + d[bb] * fac
            iny = B22[ident(bb)]["mdot_kg_s"] * fac
            filas.append((grupo, ident(bb), fac, iny, dest))

    lat = ["lat_%d_a" % i for i in range(1, 6)] + ["inf_ext_a"]
    agrega("ramal A (G3)", "G3", lat)
    if "G4" in C:
        agrega("ramal B (G4)", "G4", [b.replace("_a", "_b") for b in lat])
    else:
        agrega("ramal B (= A, S9)", "G3", lat)
    if "ESUP" in C:
        agrega("SUP A+B (S9)", "ESUP", ["sup_1_a", "sup_2_a"], fac=2.0)
    if "INT" in C:
        agrega("INF_INT (G5)", "INT", ["inf_int"])
    if "F5" in C:
        agrega("lanza INT_1-5 (F5)", "F5", ["int_%d" % i for i in range(1, 6)])
    elif "F5_CFD02" in C:
        F5_Q = {"int_1": 9.13621, "int_2": 9.1436, "int_3": 9.1523, "int_4": 9.16194, "int_5": 9.17216}
        esc = {b: B22[b.upper()]["q_Lmin"] / q for b, q in F5_Q.items()}
        agrega("lanza INT_1-5 (F5 CFD02 escalado)", "F5_CFD02", list(F5_Q), escala=esc)
    # descuento de obstaculos por superficie (combinar_kpi: libre - obst), si se dan
    obst = C.get("obstaculos_kg_s", {})
    destinos = ["OD", "cara superior", "cara inferior", "agujero", "lanza", "PAD", "escape"]
    tot_iny = sum(f[3] for f in filas)
    tot = {d: sum(f[4].get(d, 0.0) for f in filas) for d in destinos}
    with open(os.path.join(a.salida, "G7_balance_por_boquilla.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["grupo", "boquilla", "factor", "inyectado_kg_s"] + ["%s_kg_s" % d for d in destinos] + ["cierre_pct"])
        for g, b, fac, iny, d in filas:
            s = sum(d.values())
            w.writerow([g, b, fac, "%.6f" % iny] + ["%.6f" % d.get(x, 0.0) for x in destinos] + ["%.3f" % (100 * (s / iny - 1))])
    q = lambda kg: kg / RHO * 60000.0
    print("Inyectado total: %.6f kg/s = %.3f L/min (red de 22: 202,592 L/min)" % (tot_iny, q(tot_iny)))
    with open(os.path.join(a.salida, "G7_balance_global.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["destino", "kg_s", "L_min", "pct_del_inyectado"])
        for d in destinos:
            v = tot[d]
            if d in obst:
                v -= sum(obst[d].values()) if isinstance(obst[d], dict) else obst[d]
            w.writerow([d, "%.6f" % v, "%.3f" % q(v), "%.2f" % (100 * v / tot_iny)])
            print("  %-14s %.6f kg/s  %8.3f L/min  %6.2f %%" % (d, v, q(v), 100 * v / tot_iny))
        bl = sum(sum(o.values()) if isinstance(o, dict) else o for o in obst.values())
        if bl:
            w.writerow(["obstaculos R05 (PAD, topes, vigas; por rayos)", "%.6f" % bl, "%.3f" % q(bl), "%.2f" % (100 * bl / tot_iny)])
            print("  %-14s %.6f kg/s  %8.3f L/min  %6.2f %%" % ("obstaculos", bl, q(bl), 100 * bl / tot_iny))
        s = sum(tot.values())
        w.writerow(["CIERRE (salidas/inyectado - 1)", "", "", "%.3f" % (100 * (s / tot_iny - 1))])
        print("  cierre del balance: %.3f %%" % (100 * (s / tot_iny - 1)))


if __name__ == "__main__":
    main()
