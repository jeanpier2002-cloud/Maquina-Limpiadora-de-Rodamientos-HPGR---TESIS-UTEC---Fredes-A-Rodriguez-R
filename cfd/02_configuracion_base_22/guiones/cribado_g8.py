#!/usr/bin/env python3
"""
G8 - Cribado por RAYOS (N1) de variantes de rediseno del OD (ramal A; el ramal B es igual por simetria).
No sustituye al CFD: ordena variantes para proponer Caso 2 / Caso 3 (la dosis por rayos reprodujo F7 con
CV 0,399 vs 0,404, zona seca 2 mm 1,553 % = 1,553 %, correlacion por banda 0,982).

Variantes: se parte de boquillas_22.json (red de 22) y se modifica, por boquilla:
  elev (grados, + hacia arriba) manteniendo la punta; psi (giro del plano del abanico alrededor de su eje);
  ang (angulo del abanico); z (cota de la punta). El vertice sigue 4,5 mm detras de la punta.
Uso: python cribado_g8.py --salida D:/CFD03_run/g8
"""
import argparse
import csv
import json
import math
import os
import subprocess
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from dosis_rayos import dosis  # noqa: E402

GEN = os.path.join(RAIZ, "02_ENTRADAS", "de_rama_B", "gen_abanico.py")
B = json.load(open(os.path.join(RAIZ, "03_GEOMETRIA", "boquillas_22.json")))["boquillas"]
LAT = ["LAT_1_A", "LAT_2_A", "LAT_3_A", "LAT_4_A", "LAT_5_A", "INF_EXT_A"]


def tabla(ident, carpeta, elev=None, psi=0.0, ang=50.0, dz=0.0):
    b = B[ident]
    eje = np.array(b["eje"], float)
    vert = np.array(b["vertice_m"], float)
    punta = vert + 0.0045 * eje
    if elev is not None:                       # eje en el plano radial-vertical con la elevacion pedida
        er = np.array([punta[0], punta[1], 0.0]); er /= np.linalg.norm(er)
        eje = -math.cos(math.radians(elev)) * er + math.sin(math.radians(elev)) * np.array([0, 0, 1.0])
    punta = punta + np.array([0, 0, dz])
    n0 = np.array(b["normal_abanico"], float)
    n0 = n0 - n0.dot(eje) * eje; n0 /= np.linalg.norm(n0)
    n = math.cos(math.radians(psi)) * n0 + math.sin(math.radians(psi)) * np.cross(eje, n0)
    vert = punta - 0.0045 * eje
    csvp = os.path.join(carpeta, "abanico_%s.csv" % ident)
    cmd = [sys.executable, GEN, "--salida", os.path.join(carpeta, "tabla_" + ident), "--csv", csvp,
           "--vertice", *map(str, vert), "--eje", *map(str, eje), "--plano-abanico", *map(str, n),
           "--q-lmin", str(b["q_Lmin"]), "--vel", str(b["v_m_s"]), "--h-punta-mm", "4.5", "--angulo-deg", str(ang),
           "--angulo-fuera-deg", "2", "--n-plano", "150", "--n-fuera", "3", "--diam", "RR", "--rr-lambda-um", "300",
           "--rr-n", "2.5", "--rr-dmin-um", "50", "--rr-dmax-um", "900", "--duracion", "0.035",
           "--omega-rad-s", "0.1780235837034216", "--eje-giro", "0", "0", "1"]
    subprocess.run(cmd, check=True, capture_output=True)
    return csvp


VARIANTES = {
    "V0_base": {},
    "V1_INF_31": {"INF_EXT_A": dict(elev=31.0)},
    "V1_INF_32": {"INF_EXT_A": dict(elev=32.0)},
    "V1_INF_34": {"INF_EXT_A": dict(elev=34.0)},
    "V2_LAT5_29": {"LAT_5_A": dict(elev=-29.0)},
    "V2_LAT5_28": {"LAT_5_A": dict(elev=-28.0)},
    "V3_LAT1_z-5": {"LAT_1_A": dict(dz=-0.005)},
    "V4_psi15": {k: dict(psi=15.0) for k in LAT[:4]},
    "V4_psi25": {k: dict(psi=25.0) for k in LAT[:4]},
    "V4_psi35": {k: dict(psi=35.0) for k in LAT[:4]},
    "V5_ang40": {k: dict(ang=40.0) for k in LAT[:4]},
    "V6_INF32_psi25": dict({k: dict(psi=25.0) for k in LAT[:4]}, INF_EXT_A=dict(elev=32.0)),
    "V6_INF32_psi35": dict({k: dict(psi=35.0) for k in LAT[:4]}, INF_EXT_A=dict(elev=32.0)),
    "V7_LAT1z-5_INF31": {"LAT_1_A": dict(dz=-0.005), "INF_EXT_A": dict(elev=31.0)},
    # reespaciado de LAT_1-4 (paso 90 mm desde 1095): menos solape, LAT_4 mas alta
    "V8_paso90": {"LAT_1_A": dict(dz=-0.005), "LAT_2_A": dict(dz=0.002895), "LAT_3_A": dict(dz=0.01079),
                  "LAT_4_A": dict(dz=0.018685)},
    "V8b_paso90_LAT4-8": {"LAT_1_A": dict(dz=-0.005), "LAT_2_A": dict(dz=0.002895), "LAT_3_A": dict(dz=0.01079),
                          "LAT_4_A": dict(dz=0.018685, elev=-8.0)},
    "V9_paso86": {"LAT_1_A": dict(dz=-0.005), "LAT_2_A": dict(dz=-0.001105), "LAT_3_A": dict(dz=0.00279),
                  "LAT_4_A": dict(dz=0.006685)},
}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()
    filas = []
    for nom, mods in VARIANTES.items():
        c = os.path.join(a.salida, nom)
        os.makedirs(c, exist_ok=True)
        tabs = [tabla(k, c, **mods.get(k, {})) for k in LAT]
        r10 = dosis(tabs, "od", 10.0)
        r2 = dosis(tabs, "od", 2.0)
        ri = dosis([t for t in tabs if "INF_EXT" in t], "cara_inf", 10.0)
        filas.append([nom, "%.4f" % r10["D_media"], "%.4f" % r10["CV"], "%.4f" % r10["D_min"], "%.3f" % r10["seca"],
                      "%.4f" % r2["CV"], "%.3f" % r2["seca"], "%.2f" % (100 * r10["mdot"] / sum(B[k]["mdot_kg_s"] for k in LAT)),
                      "%.2f" % (100 * ri["mdot"] / B["INF_EXT_A"]["mdot_kg_s"])])
        print("%-16s D %s | CV10 %s | Dmin10 %s | seca10 %s %% | CV2 %s | seca2 %s %% | eta_OD %s %% | INF->cara_inf %s %%" % tuple(filas[-1]))
    with open(os.path.join(a.salida, "cribado_g8_rayos.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["variante", "D_media_10mm", "CV_10mm", "D_min_10mm", "seca_10mm_pct", "CV_2mm", "seca_2mm_pct",
                    "eta_OD_pct", "INF_EXT_a_cara_inf_pct"])
        w.writerows(filas)
