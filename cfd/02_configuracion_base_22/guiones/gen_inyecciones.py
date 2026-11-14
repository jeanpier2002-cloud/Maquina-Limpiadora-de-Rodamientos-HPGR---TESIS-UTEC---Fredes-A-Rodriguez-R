#!/usr/bin/env python3
"""
Tablas de inyeccion *file* de Fluent para las boquillas de CFD03, desde 03_GEOMETRIA/boquillas_22.json (G1).

Para cada boquilla: gen_abanico.py (copia sin modificar de la rama B, 02_ENTRADAS/de_rama_B, hash verificado)
con los MISMOS argumentos fijos que CFD02/rama B (E2 de MODO_AUTONOMO.md):
  150 x 3 rayos, 50 grados, 2 grados fuera del plano (SUPUESTO I1), h punta 4,5 mm (medido en R05),
  Rosin-Rammler en masa lambda 300 um, n 2,5, [50, 900] um (SUPUESTO I2), omega x r (1,7 rpm, HIPOTESIS)
y, por boquilla, vertice (salida del orificio medida en R05), eje, normal del plano del abanico, q y v:
  --caudal red22     : q y v = Cv*sqrt(2p/rho) de la red de 22 (E1, por defecto)
  --caudal catalogo  : q = 9,11766505450028 L/min y v = 27,11354121556065 m/s (CFD02, sensibilidad G6)
Luego tabla_a_dpm.py -> <IDENT>.dpm (formato verificado en F4).

Uso: python gen_inyecciones.py --dir D:/CFD03_run/G3/G3_A_base --boq LAT_1_A,LAT_2_A,... [--caudal red22]
"""
import argparse
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
GEN = os.path.join(RAIZ, "02_ENTRADAS", "de_rama_B", "gen_abanico.py")
T2D = os.path.join(AQUI, "tabla_a_dpm.py")
FIJOS = ["--h-punta-mm", "4.5", "--angulo-deg", "50", "--angulo-fuera-deg", "2",
         "--n-fuera", "3", "--diam", "RR", "--rr-lambda-um", "300", "--rr-n", "2.5", "--rr-dmin-um", "50",
         "--rr-dmax-um", "900", "--duracion", "0.035", "--omega-rad-s", "0.1780235837034216",
         "--eje-giro", "0", "0", "1"]

ap = argparse.ArgumentParser()
ap.add_argument("--dir", required=True)
ap.add_argument("--boq", required=True, help="identificadores de boquillas_22.json separados por coma")
ap.add_argument("--caudal", choices=["red22", "catalogo"], default="red22")
ap.add_argument("--json", default=os.path.join(RAIZ, "03_GEOMETRIA", "boquillas_22.json"),
                help="geometria de las boquillas (por defecto R05; G8: variantes de rediseno)")
ap.add_argument("--n-plano-boq", default="",
                help="IDENT=N,... rayos en el plano por boquilla (defecto 150, como la rama B). CFD03: INF_EXT e INF_INT "
                     "llegan rasantes a la cara inferior y necesitan 1200 (prueba de rayos, S17)")
a = ap.parse_args()
B = json.load(open(a.json))["boquillas"]
os.makedirs(a.dir, exist_ok=True)
NPL = {k: v for k, v in (x.split("=") for x in a.n_plano_boq.split(",") if x)}
tot = 0.0
for ident in a.boq.split(","):
    b = B[ident]
    q, v = (b["q_Lmin"], b["v_m_s"]) if a.caudal == "red22" else (9.11766505450028, 27.11354121556065)
    tabla = os.path.join(a.dir, "tabla_" + ident)
    csvp = os.path.join(a.dir, "abanico_" + ident + ".csv")
    cmd = [sys.executable, GEN, "--salida", tabla, "--csv", csvp,
           "--vertice", *["%.10g" % c for c in b["vertice_m"]],
           "--eje", *["%.9f" % c for c in b["eje"]],
           "--plano-abanico", *["%.9f" % c for c in b["normal_abanico"]],
           "--q-lmin", "%.10g" % q, "--vel", "%.10g" % v, "--n-plano", NPL.get(ident, "150")] + FIJOS
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr)
    r2 = subprocess.run([sys.executable, T2D, csvp, os.path.join(a.dir, ident + ".dpm"), "--nombre", ident],
                        capture_output=True, text=True)
    if r2.returncode:
        raise SystemExit(r2.stderr)
    md = float(r2.stdout.strip().split("=")[-1].split()[0])
    tot += md
    print("%-10s q %.5f L/min v %.4f m/s -> %s" % (ident, q, v, r2.stdout.strip()))
print("TOTAL mdot = %.9f kg/s" % tot)
