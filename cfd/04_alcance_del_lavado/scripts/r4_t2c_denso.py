#!/usr/bin/env python3
"""
CORRIDA 4 · T2c · Re-evaluacion densa (600 rayos/plano, dphi 0,25) de las 3 mejores poses de cada barrido (ventana superior e
inferior) y de una pose de referencia de cada ventana (superior: como SUP_1, r 545, h 190, vertical, abanico radial; inferior:
como INF_EXT, r 840, z 853,8, 15 grados, abanico radial de 50 grados). PROPUESTA, N1, [INTERFAZ ISMAEL].
El barrido grueso (150 rayos, dphi 0,5) sirve para ordenar; esta re-evaluacion da el valor menos sesgado por el muestreo.
Salida: 02_CAVIDAD_N1/T2c_pose_denso.csv. Uso: python -I -B r4_t2c_denso.py
"""
import csv
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import r4_t2_cavidad_n1 as T  # noqa: E402
import r4_t2c_pose as PS  # noqa: E402
import r4_t2c_pose_inf as PI  # noqa: E402


def leer(p):
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.exists(p) else []


sup = leer(T.OUT + "/T2c_pose_radial.csv") + leer(T.OUT + "/T2c_pose_tangencial.csv")
inf = sum([leer(T.OUT + "/T2c_pose_inf_%s_%s.csv" % (g, f)) for g in ("interior", "exterior") for f in ("radial", "tangencial")], [])
filas = []
cand_s = sorted(sup, key=lambda r: -float(r["frac_N1_total"]))[:3]
cand_s.append({"r_vertice_mm": "545.0", "h_sobre_cara_mm": "190.0", "incl_radial_deg": "0.0", "incl_tangencial_deg": "0.0",
               "abanico": "radial", "frac_N1_total": "", "ref": "1"})
for r in cand_s:
    b = PS.boquilla(float(r["r_vertice_mm"]), float(r["h_sobre_cara_mm"]), float(r["incl_radial_deg"]), float(r["incl_tangencial_deg"]), r["abanico"])
    v = PS.n1(b, 600, 0.25)
    filas.append(["superior", "referencia (como SUP_1)" if r.get("ref") else "mejor del barrido", r["r_vertice_mm"], r["h_sobre_cara_mm"],
                  r["incl_radial_deg"], r["incl_tangencial_deg"], r["abanico"], r["frac_N1_total"]] +
                 ["%.5f" % v[k] for k in ("tot", "flanco", "extremos", "pista_ext", "pista_int")])
    print(filas[-1], flush=True)
cand_i = sorted(inf, key=lambda r: -float(r["frac_N1_total"]))[:3]
cand_i.append({"grupo": "exterior", "r_vertice_mm": "840.0", "z_vertice_mm": "853.8", "elevacion_deg": "15.0", "incl_tangencial_deg": "0.0",
               "abanico": "radial", "frac_N1_total": "", "ref": "1"})
for r in cand_i:
    b = PI.boquilla(float(r["r_vertice_mm"]), float(r["z_vertice_mm"]), float(r["elevacion_deg"]), float(r["incl_tangencial_deg"]),
                    r["abanico"], r["grupo"] == "interior")
    v = PI.n1_inf(b, 600, 0.25)
    filas.append(["inferior (%s)" % r["grupo"], "referencia (como INF_EXT, 50°)" if r.get("ref") else "mejor del barrido", r["r_vertice_mm"],
                  r["z_vertice_mm"], r["elevacion_deg"], r["incl_tangencial_deg"], r["abanico"], r["frac_N1_total"]] +
                 ["%.5f" % v[k] for k in ("tot", "flanco", "extremos", "pista_ext", "pista_int")])
    print(filas[-1], flush=True)
with open(T.OUT + "/T2c_pose_denso.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ventana", "tipo", "r_vertice_mm", "h_o_z_mm", "incl_radial_o_elevacion_deg", "incl_tangencial_deg", "abanico",
                "frac_N1_total_grueso", "frac_N1_total_denso", "frac_N1_flanco", "frac_N1_extremos", "frac_N1_pista_ext", "frac_N1_pista_int"])
    w.writerows(filas)
