#!/usr/bin/env python3
"""
Cola de corridas de Fluent en serie (la licencia Student admite una sola sesion, S8).
Espera a que no haya ningun fl2610.exe activo, y ejecuta cada journal en su carpeta.

Uso: python cola.py <carpeta1> [<carpeta2> ...] [--timeout 7200] [--t 4]
Cada carpeta contiene <nombre_carpeta>.jou. Registro en <carpeta>/cola.log y en la salida.
"""
import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("carpetas", nargs="+")
ap.add_argument("--timeout", type=float, default=7200)
ap.add_argument("--t", type=int, default=4)
a = ap.parse_args()


def fluent_activo():
    out = subprocess.run(["tasklist"], capture_output=True, text=True).stdout.lower()
    return "fl2610.exe" in out or "cx2610.exe" in out


for c in a.carpetas:
    while fluent_activo():
        time.sleep(30)
    tag = os.path.basename(c.rstrip("/\\"))
    t0 = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] inicio {tag}", flush=True)
    rc = subprocess.call([sys.executable, os.path.join(HERE, "run_fluent.py"), os.path.join(c, tag + ".jou"), c,
                          "--t", str(a.t), "--timeout", str(a.timeout)])
    msg = f"[{time.strftime('%H:%M:%S')}] fin {tag} rc={rc} t={time.time() - t0:.0f}s"
    print(msg, flush=True)
    open(os.path.join(c, "cola.log"), "a").write(msg + "\n")
    time.sleep(5)
