#!/usr/bin/env python3
"""
CFD03 - Procesado estandar de una corrida transitoria de Fluent (jou_dpm.py):
  1. <zona>.dpm -> <zona>.csv (dpm2csv.py, formato transitorio verificado en F4/F5)
  2. estacionariedad: caudal que sale por todas las fronteras en ventanas de 5 ms vs inyectado
  3. balance de masa en la ventana [t0, t1): sum(salidas)/inyectado - 1  (criterio < 1 %)
  4. post_kpi.py por superficie objetivo (argumentos de SUPERFICIES), sin factor (ramal simulado)
  5. archivo: journal, transcript y .dpm.gz de paredes a 04_CASOS/<fase>/<caso>/; CSV de KPIs a 06_RESULTADOS/<fase>/
Uso: python procesar_caso.py D:/CFD03_run/G3/G3_A_base --fase G3 --t0 0.025 --t1 0.050 [--sin-archivo]
"""
import argparse
import csv
import glob
import gzip
import os
import re
import shutil
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SUPERFICIES = {
    "od": ["--superficie", "cilindro", "--R", "0.710", "--lim", "0.890", "1.405"],
    "cara_inf": ["--superficie", "anillo_inf", "--lim", "0.450", "0.710"],
    "sup": ["--superficie", "anillo", "--lim", "0.45858", "0.710"],
    "agujero": ["--superficie", "cono", "--lim", "0.890", "1.405"],
    "pared_agujero": ["--superficie", "cono", "--lim", "0.890", "1.405"],          # zona del caso F5 (malla_agujero)
    "cara_inf_rodamiento": ["--superficie", "anillo_inf", "--lim", "0.450", "0.710"],  # F5 (solo r <= 0,55 m)
}
PAREDES = set(SUPERFICIES) | {"pad", "pared_agujero", "lanza", "cara_inf_rodamiento", "cara_sup_rodamiento"}


def inyectado(carpeta):
    """Suma de mass-flow de las tablas <INY>.dpm que el journal cargo (create-injection)."""
    jou = open(glob.glob(os.path.join(carpeta, os.path.basename(carpeta) + ".jou"))[0]).read()
    tablas = re.findall(r'"([^"]+\.dpm)"', jou)
    tot, por = 0.0, {}
    for t in tablas:
        s = 0.0
        for ln in open(t):
            m = re.match(r"\(\(\s*(.*?)\)\s*(\S+)\)\s*$", ln.strip())
            if m:
                s += float(m.group(1).split()[8])
        por[os.path.splitext(os.path.basename(t))[0]] = s
        tot += s
    return tot, por


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta")
    ap.add_argument("--fase", required=True)
    ap.add_argument("--t0", type=float, default=0.025)
    ap.add_argument("--t1", type=float, default=0.050)
    ap.add_argument("--sin-archivo", action="store_true")
    a = ap.parse_args()
    C = a.carpeta.rstrip("/\\")
    caso = os.path.basename(C)
    res = os.path.join(RAIZ, "06_RESULTADOS", a.fase)
    os.makedirs(res, exist_ok=True)
    mt, por = inyectado(C)
    print("%s: inyectado %.6f kg/s %s" % (caso, mt, {k: round(v, 6) for k, v in por.items()}))
    zonas = sorted(glob.glob(os.path.join(C, "*.dpm")))
    zonas = [z for z in zonas if os.path.splitext(os.path.basename(z))[0] not in por]
    datos = {}
    for zp in zonas:
        z = os.path.splitext(os.path.basename(zp))[0]
        cs = os.path.join(C, z + ".csv")
        if not os.path.exists(cs) or os.path.getmtime(cs) < os.path.getmtime(zp):
            subprocess.run([sys.executable, os.path.join(AQUI, "dpm2csv.py"), zp, cs], check=True,
                           capture_output=True)
        from lector_impactos import leer as _leer      # lectura por columnas (archivos de varios GB, S18)
        R = _leer(cs, ["t", "masa"], texto=())
        datos[z] = (R.get("t", np.zeros(0)), R.get("masa", np.zeros(0)))
    # estacionariedad por ventanas de 5 ms
    tmax = max((d[0].max() for d in datos.values() if d[0].size), default=0)
    print("salida total / inyectado por ventanas de 5 ms:")
    lin = []
    for t in np.arange(0.0, tmax, 0.005):
        s = sum(d[1][(d[0] >= t) & (d[0] < t + 0.005)].sum() for d in datos.values()) / 0.005
        lin.append((t, s / mt))
        print("  %.3f-%.3f s: %.4f" % (t, t + 0.005, s / mt))
    # balance en la ventana
    filas = []
    tot = 0.0
    for z, (t, m) in sorted(datos.items()):
        v = m[(t >= a.t0) & (t < a.t1)].sum() / (a.t1 - a.t0)
        tot += v
        filas.append([z, len(t), "%.6e" % m.sum(), "%.6e" % v])
    err = 100 * (tot / mt - 1)
    filas += [["TOTAL_salidas_ventana", "", "", "%.6e" % tot], ["inyectado", "", "", "%.6e" % mt],
              ["error_balance_ventana_pct", "", "", "%.4f" % err]]
    with open(os.path.join(res, caso + "_balance.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["zona", "n_parcelas_total", "masa_total_kg", "mdot_ventana_kg_s"])
        w.writerows(filas)
    print("balance ventana %.3f-%.3f s: %.4f %%  (%s)" % (a.t0, a.t1, err, " | ".join("%s %s" % (f[0], f[3]) for f in filas[:-3])))
    with open(os.path.join(res, caso + "_estacionariedad.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_ini_s", "salida_sobre_inyectado"])
        w.writerows([["%.3f" % t, "%.5f" % r] for t, r in lin])
    # KPIs por superficie objetivo
    for z, args in SUPERFICIES.items():
        cs = os.path.join(C, z + ".csv")
        if z in datos and datos[z][0].size:
            r = subprocess.run([sys.executable, os.path.join(AQUI, "post_kpi.py"), "--entrada", cs,
                                "--caso", "%s_%s" % (caso, z), "--salida", res, *args, "--modo", "transitorio",
                                "--t-estable", str(a.t0), "--t-fin", str(a.t1), "--mdot-inyectado", "%.9f" % mt],
                               capture_output=True, text=True)
            print("  %-9s %s" % (z, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-500:]))
    if a.sin_archivo:
        return
    dst = os.path.join(RAIZ, "04_CASOS", a.fase, caso)
    for sub in ("journals", "logs", "export", "inyeccion"):
        os.makedirs(os.path.join(dst, sub), exist_ok=True)
    for p in glob.glob(os.path.join(C, "*.jou")):
        shutil.copy2(p, os.path.join(dst, "journals"))
    for p in glob.glob(os.path.join(C, "*transcript*.txt")) + glob.glob(os.path.join(C, "*.trn")):
        shutil.copy2(p, os.path.join(dst, "logs"))
    for p in glob.glob(os.path.join(C, "tabla_*")) + glob.glob(os.path.join(C, "abanico_*.csv")):
        shutil.copy2(p, os.path.join(dst, "inyeccion"))
    for iny in por:
        shutil.copy2(os.path.join(C, iny + ".dpm"), os.path.join(dst, "inyeccion"))
    # Exportaciones pesadas (.dpm de impactos, hasta varios GB con S18): se comprimen en D: (no en Google Drive);
    # en el proyecto solo queda la ruta y el SHA-256 de cada una.
    import hashlib
    arch = os.path.join("D:/CFD03_archivo", a.fase, caso)
    os.makedirs(arch, exist_ok=True)
    lineas = []
    for zp in zonas:
        z = os.path.splitext(os.path.basename(zp))[0]
        gz = os.path.join(arch, "%s_%s.dpm.gz" % (caso, z))
        with open(zp, "rb") as fi, gzip.open(gz, "wb") as fo:
            shutil.copyfileobj(fi, fo)
        hs = hashlib.sha256()
        with open(gz, "rb") as fh:
            for bloque in iter(lambda: fh.read(1 << 22), b""):
                hs.update(bloque)
        lineas.append("%s *%s  (%.1f MB)" % (hs.hexdigest(), gz, os.path.getsize(gz) / 1e6))
    with open(os.path.join(dst, "export", "EXPORTACIONES_EN_D.txt"), "w", encoding="utf-8") as f:
        f.write("Exportaciones de impactos (.dpm.gz) guardadas fuera de Google Drive por tamano.\n"
                "Formato: SHA-256 *ruta (tamano). Se convierten a CSV con 05_SCRIPTS/dpm2csv.py.\n\n")
        f.write("\n".join(lineas) + "\n")
    print("archivado en", dst, "| exportaciones en", arch)


if __name__ == "__main__":
    main()
