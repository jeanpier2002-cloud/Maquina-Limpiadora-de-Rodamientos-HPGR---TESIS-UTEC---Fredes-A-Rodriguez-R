#!/usr/bin/env python3
"""
G8 - Genera un JSON de boquillas para una variante de rediseno a partir de boquillas_22.json (R05):
  elev=<grados> : nuevo eje en el plano radial-vertical de la boquilla, con la PUNTA fija (el vertice queda
                  4,5 mm detras de la punta sobre el nuevo eje). Signo: + hacia arriba. Sentido horizontal: el
                  del eje original (hacia dentro en las exteriores).
  dr=<m>, dz=<m>: traslacion radial / vertical de la punta (y del vertice), mismo eje.
Uso: python gen_variante_g8.py --salida boquillas_C2.json --mod LAT_1_A:elev=-4 --mod LAT_1_B:elev=-4
"""
import argparse, json, math, os
import numpy as np
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("--salida", required=True)
ap.add_argument("--mod", action="append", default=[])
a = ap.parse_args()
J = json.load(open(os.path.join(RAIZ, "03_GEOMETRIA", "boquillas_22.json")))
for m in a.mod:
    ident, cambios = m.split(":")
    b = J["boquillas"][ident]
    eje = np.array(b["eje"], float); vert = np.array(b["vertice_m"], float); punta = vert + 0.0045 * eje
    er = np.array([punta[0], punta[1], 0.0]); er /= np.linalg.norm(er)
    for c in cambios.split(";"):
        k, v = c.split("="); v = float(v)
        if k == "elev":
            sh = 1.0 if np.dot(eje, er) > 0 else -1.0          # conserva el sentido radial del eje original
            eje = sh * math.cos(math.radians(v)) * er + math.sin(math.radians(v)) * np.array([0, 0, 1.0])
        elif k == "dr":
            punta = punta + v * er
        elif k == "dz":
            punta = punta + np.array([0, 0, v])
    eje = eje / np.linalg.norm(eje)
    b["eje"] = eje.tolist(); b["vertice_m"] = (punta - 0.0045 * eje).tolist()
    b["variante_G8"] = cambios
J["fuente"] = "gen_variante_g8.py " + " ".join(a.mod)
json.dump(J, open(a.salida, "w"), indent=1)
print(a.salida, a.mod)
