# -*- coding: utf-8 -*-
"""C3 (03/11/2026): sensibilidad de la aspersion a las tolerancias de las coplas (+-2 mm y +-1 grado [HIPOTESIS] de los planos
HPGR-ASP-220 y ASP-600). Cribado geometrico N1 por rayos: reutiliza, sin modificarlos, estudio_n1.py y rayos_r05.py de
cfd/CFD_ANSYS/02_ANALISIS/cara_inferior/alternativas_2026-10-07/decision_o7c2_vs_o8b/scripts (el mismo modelo de D-047, D-060 y
D-061: rayos rectos por vuelta del rotor, obstaculos de R05, sin gravedad ni arrastre). No equivale a CFD ni a limpieza.
Boquillas: caso 2 vigente (integracion_R06/R06.4_o7_c2_caso2/boquillas_O7_C2_caso2.json, 24 boquillas); las 1520 (INF_EXT y C2)
con abanico de 16,8 grados como en el estudio original; las 5020 con 50 grados (valor por defecto del modelo).
Perturbaciones de UNA boquilla a la vez (las otras 23 nominales):
  posicion del vertice +-2 mm en las direcciones radial, tangencial y vertical (6 casos);
  eje +-1 grado alrededor de la normal del abanico (giro en su plano) y alrededor del ancho del abanico (fuera de su plano) (4 casos).
Medidas por superficie del aro (od, sup, agujero y zonas Z1-Z3 de la cara inferior): masa del primer impacto por vuelta (D) y
cobertura K1 (% de celdas tocadas), del conjunto de 24 boquillas, frente al nominal.
Criterio propio fijado antes de correr [HIPOTESIS]: la tolerancia se acepta si, en cada superficie, la cota combinada (suma de los
peores |dD| de las 24 boquillas, como si todas se desviaran a la vez en el peor sentido) es <= 10 % y ninguna perturbacion
individual baja K1 mas de 1 punto porcentual.
Salida: resultados/C3_TOLERANCIAS.json y resultados/C3_RESUMEN.csv."""
import copy
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

HO = Path(r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho")
sys.path.insert(0, str(HO / r"01_DISENO_VIGENTE\cfd\CFD_ANSYS\02_ANALISIS\cara_inferior\alternativas_2026-10-07\decision_o7c2_vs_o8b\scripts"))
import estudio_n1 as en  # noqa: E402  (al importarlo no ejecuta su run())

SALIDA = Path(__file__).resolve().parent / "resultados"
SALIDA.mkdir(exist_ok=True)
DPOS, DANG = 0.002, 1.0
# segunda pasada: tolerancia angular propia de las salidas del bloque mecanizado (INF_EXT y C2): --dang-bloque 0.5
DANG_BLOQUE = float(sys.argv[sys.argv.index("--dang-bloque") + 1]) if "--dang-bloque" in sys.argv else DANG
DPOS_BLOQUE = float(sys.argv[sys.argv.index("--dpos-bloque") + 1]) / 1000 if "--dpos-bloque" in sys.argv else DPOS
SUF = ("" if DANG_BLOQUE == DANG else "_BLOQUE%s" % str(DANG_BLOQUE).replace(".", "")) + ("" if DPOS_BLOQUE == DPOS else "_POS%g" % (DPOS_BLOQUE * 1000))
CRIT_D, CRIT_K1 = 10.0, 1.0

caso2 = json.load(open(HO / r"01_DISENO_VIGENTE\integracion_R06\R06.4_o7_c2_caso2\boquillas_O7_C2_caso2.json", encoding="utf-8"))["boquillas"]
B = {}
for k, b in caso2.items():
    b = copy.deepcopy(b)
    if "angulo_deg" in b:
        b["angulo_abanico_deg"] = b["angulo_deg"]
    B[k] = b
en.B = B
en.set_height(0)


def rot(v, eje, grados):
    """Rodrigues: gira v alrededor de eje (unitario)"""
    k = np.asarray(eje, float); k /= np.linalg.norm(k); v = np.asarray(v, float); a = math.radians(grados)
    return v * math.cos(a) + np.cross(k, v) * math.sin(a) + k * (k @ v) * (1 - math.cos(a))


def perturbaciones(b, dang=DANG, dpos=DPOS):
    v = np.array(b["vertice_m"], float); e = np.array(b["eje"], float); e /= np.linalg.norm(e)
    n = np.array(b["normal_abanico"], float); n -= (n @ e) * e; n /= np.linalg.norm(n)
    w = np.cross(n, e)
    r = np.array([v[0], v[1], 0.0])
    er = r / np.linalg.norm(r) if np.linalg.norm(r) > 1e-6 else np.array([1.0, 0, 0])
    et = np.cross([0, 0, 1.0], er)
    out = {}
    for nom, d in (("radial", er), ("tangencial", et), ("vertical", np.array([0, 0, 1.0]))):
        for s in (1, -1):
            out["pos_%s_%+d" % (nom, s * 2)] = {"vertice_m": (v + s * dpos * d).tolist()}
    for s in (1, -1):
        out["eje_en_plano_%+d" % s] = {"eje": rot(e, n, s * dang).tolist(), "normal_abanico": n.tolist()}
        out["eje_fuera_plano_%+d" % s] = {"eje": rot(e, w, s * dang).tolist(), "normal_abanico": rot(n, w, s * dang).tolist()}
    return out


nombres = list(B)
nominal = {k: en.trace(k) for k in nombres}
base = en.merge(nominal)
SURF = en.SURFS
res = {"config": {"dpos_m": DPOS, "dang_deg": DANG, "dang_bloque_deg": DANG_BLOQUE, "dpos_bloque_m": DPOS_BLOQUE, "boquillas": len(nombres), "criterio": {"suma_dD_pct_max": CRIT_D, "caida_K1_pp_max": CRIT_K1},
                  "modelo": "N1 de estudio_n1.py / rayos_r05.py (D-047, D-060, D-061)"},
       "nominal": {s: {"D": base["surfaces"][s]["mass"], "K1_pct": base["surfaces"][s]["K1_pct"]} for s in SURF},
       "escape_nominal_pct": base["escape_pct"], "boquillas": {}}
filas = []
for k in nombres:
    rk = {}
    for pn, ov in perturbaciones(B[k], *((DANG_BLOQUE, DPOS_BLOQUE) if k.startswith(("INF_EXT", "C2")) else (DANG, DPOS))).items():
        tr = en.trace(k, ov)
        c = en.merge({**nominal, k: tr})
        d = {}
        for s in SURF:
            D0, K0 = base["surfaces"][s]["mass"], base["surfaces"][s]["K1_pct"]
            d[s] = {"dD_pct": 100 * (c["surfaces"][s]["mass"] - D0) / D0 if D0 else 0.0,
                    "dK1_pp": c["surfaces"][s]["K1_pct"] - K0}
        d["escape_pct"] = c["escape_pct"]
        rk[pn] = d
        filas.append([k, pn] + ["%.3f" % d[s]["dD_pct"] for s in SURF] + ["%.3f" % d[s]["dK1_pp"] for s in SURF])
    res["boquillas"][k] = rk
    print(k, "max |dD| %:", {s: round(max(abs(x[s]["dD_pct"]) for x in rk.values()), 2) for s in SURF}, flush=True)

# resumen por superficie: peor perturbacion individual, cota combinada y peor caida de K1
resumen = {}
for s in SURF:
    peor = max(((k, p, x[s]["dD_pct"]) for k, rk in res["boquillas"].items() for p, x in rk.items()), key=lambda t: abs(t[2]))
    suma = sum(max(abs(x[s]["dD_pct"]) for x in rk.values()) for rk in res["boquillas"].values())
    caida = min(((k, p, x[s]["dK1_pp"]) for k, rk in res["boquillas"].items() for p, x in rk.items()), key=lambda t: t[2])
    resumen[s] = {"peor_individual": {"boquilla": peor[0], "perturbacion": peor[1], "dD_pct": round(peor[2], 3)},
                  "suma_peores_dD_pct": round(suma, 3),
                  "suma_peores_perdidas_pct": round(sum(max(0.0, -min(x[s]["dD_pct"] for x in rk.values())) for rk in res["boquillas"].values()), 3),
                  "peor_caida_K1": {"boquilla": caida[0], "perturbacion": caida[1], "dK1_pp": round(caida[2], 3)},
                  "cumple": bool(suma <= CRIT_D and caida[2] >= -CRIT_K1)}
res["resumen"] = resumen
res["cumple_todo"] = all(v["cumple"] for v in resumen.values())
(SALIDA / ("C3_TOLERANCIAS%s.json" % SUF)).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
with open(SALIDA / ("C3_RESUMEN%s.csv" % SUF), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["boquilla", "perturbacion"] + ["dD_%s_pct" % s for s in SURF] + ["dK1_%s_pp" % s for s in SURF])
    w.writerows(filas)
for s, v in resumen.items():
    print(s, v)
print("CUMPLE TODO", res["cumple_todo"], "| escape nominal %.2f %%" % base["escape_pct"])
