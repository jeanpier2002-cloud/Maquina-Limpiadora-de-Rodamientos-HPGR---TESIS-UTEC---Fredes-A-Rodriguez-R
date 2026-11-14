#!/usr/bin/env python3
"""
CORRIDA 3 · T2 · Inyecciones DPM (tablas *file* de Fluent) de todas las variantes de la tanda.

  kit_A        : copia de los 7 .dpm del kit de Ismael (R3_00 humo y R3_01)
  verif_kit_A  : regeneracion con r3_gen_inyecciones.py + boquillas_O7_C2.json del kit (mismo comando que el
                 LEEME del kit) -> se compara SHA-256 con kit_A (prueba de fidelidad del generador en este PC)
  caso2_A      : 01_ENTRADA/boquillas_O7_C2_LAT1m4.json (LAT_1_A a -4 grados), 7 boquillas del ramal A (R3_02)
  caso2_B      : mismo JSON, 7 boquillas del ramal B (R3_03). El JSON ya trae B como giro de 180 grados de A
                 alrededor de Z (mismo metodo que G4_B_base_v2, que genero B desde boquillas_22.json)
  caso2_A_np050: idem caso2_A con la mitad de rayos en el plano (R3_06)
  caso2_A_np200: idem con el doble (R3_07)
Parcelas en el plano: base 600 (LAT) y 1200 (INF_EXT, C2) por plano x 3 planos (kit, LEEME_JEAN.md).

Comprobaciones: SHA-256 frente al kit; suma de mass-flow de cada .dpm frente a q_Lmin*rho/60000 del JSON;
masa total por variante (debe ser igual en x0,5 / x1 / x2: el caudal por parcela escala).
Salida: 01_ENTRADA/inyecciones/<variante>/*.dpm, 01_ENTRADA/inyecciones/VERIFICACION_T2.csv y T2_log.txt
Uso: python -I -B r3_t2_inyecciones.py
"""
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

BASE = "D:/CFD_Redosado/CORRIDA_3_O7C2"
KIT = "D:/CFD_Redosado/Diseño actual/PAQUETE_JEAN_O7C2_v2_2026-10-25/01_KIT_G3_A_O7_O4"
GENI = BASE + "/03_FLUENT/scripts/kit/r3_gen_inyecciones.py"
J_KIT = BASE + "/03_FLUENT/scripts/kit/boquillas_O7_C2.json"
J_C2 = BASE + "/01_ENTRADA/boquillas_O7_C2_LAT1m4.json"
OUT = BASE + "/01_ENTRADA/inyecciones"
RHO = 982.12
A = ["LAT_1_A", "LAT_2_A", "LAT_3_A", "LAT_4_A", "LAT_5_A", "INF_EXT_A", "C2_A"]
Bq = [x[:-1] + "B" for x in A]


def npl(ids, f):
    return ",".join("%s=%d" % (i, round((1200 if i.startswith(("INF_EXT", "C2")) else 600) * f)) for i in ids)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()


def suma_dpm(p):
    s, n = 0.0, 0
    for ln in open(p):
        m = re.match(r"\(\(\s*(.*?)\)\s*(\S+)\)\s*$", ln.strip())
        if m:
            s += float(m.group(1).split()[8]); n += 1
    return n, s


log = []


def gen(var, js, ids, f):
    d = OUT + "/" + var
    if os.path.exists(d):
        raise SystemExit("ya existe %s: no se sobrescribe" % d)
    cmd = [sys.executable, "-I", "-B", GENI, "--json", js, "--dir", d, "--boq", ",".join(ids), "--n-plano-boq", npl(ids, f)]
    log.append("CMD " + subprocess.list2cmdline(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    log.append(r.stdout.strip() + (("\nSTDERR " + r.stderr) if r.stderr.strip() else ""))
    if r.returncode:
        raise SystemExit(r.stderr)


os.makedirs(OUT, exist_ok=True)
d = OUT + "/kit_A"
if not os.path.exists(d):
    os.makedirs(d)
    for i in A:
        shutil.copy2(KIT + "/inyecciones/%s.dpm" % i, d)
gen("verif_kit_A", J_KIT, A, 1.0)
gen("caso2_A", J_C2, A, 1.0)
gen("caso2_B", J_C2, Bq, 1.0)
gen("caso2_A_np050", J_C2, A, 0.5)
gen("caso2_A_np200", J_C2, A, 2.0)

JK = json.load(open(J_KIT))["boquillas"]
JC = json.load(open(J_C2))["boquillas"]
filas = []
tot = {}
for var, js, ids in (("kit_A", JK, A), ("verif_kit_A", JK, A), ("caso2_A", JC, A), ("caso2_B", JC, Bq),
                     ("caso2_A_np050", JC, A), ("caso2_A_np200", JC, A)):
    for i in ids:
        p = "%s/%s/%s.dpm" % (OUT, var, i)
        n, s = suma_dpm(p)
        obj = JC[i]["q_Lmin"] * RHO / 60000 if js is JC else JK[i]["q_Lmin"] * RHO / 60000
        h = sha(p)
        ref = ""
        if var == "verif_kit_A":
            ref = "IDENTICO al kit" if h == sha("%s/kit_A/%s.dpm" % (OUT, i)) else "DISTINTO del kit"
        elif var == "caso2_A" and i != "LAT_1_A":
            ref = "IDENTICO al kit" if h == sha("%s/kit_A/%s.dpm" % (OUT, i)) else "DISTINTO del kit"
        elif var == "caso2_B" and i in ("INF_EXT_B", "C2_B"):
            k = KIT + "/mascara_fuentes/%s.dpm" % i
            ref = "IDENTICO a mascara_fuentes del kit" if h == sha(k) else "DISTINTO de mascara_fuentes del kit"
        filas.append([var, i, n, "%.9f" % s, "%.9f" % obj, "%.2e" % (100 * (s / obj - 1)), h, ref])
        tot[var] = tot.get(var, 0.0) + s
with open(OUT + "/VERIFICACION_T2.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["variante", "inyeccion", "parcelas", "mdot_dpm_kg_s", "mdot_json_kg_s", "error_pct", "sha256", "comparacion"])
    w.writerows(filas)
    for var, s in tot.items():
        w.writerow([var, "TOTAL", "", "%.9f" % s, "", "", "", ""])
for r in filas:
    log.append("%-14s %-10s %5d  %.9f / %.9f  err %s %%  %s" % (r[0], r[1], r[2], float(r[3]), float(r[4]), r[5], r[7]))
for var, s in tot.items():
    log.append("TOTAL %-14s %.9f kg/s" % (var, s))
open(OUT + "/T2_log.txt", "w", encoding="utf-8").write("\n".join(log) + "\n")
print("\n".join(log[-60:]))
