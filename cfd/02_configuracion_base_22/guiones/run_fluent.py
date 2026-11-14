#!/usr/bin/env python3
"""
Lanza ANSYS Fluent 2026 R1 Student en batch con un journal y un tiempo limite.

Opciones del lanzador verificadas en F4 (texto de ayuda embebido en fluent.exe):
  3ddp  (version doble precision), -t<n> (procesos; la licencia permite 4),
  -g (sin GUI ni graficos), -hidden (modo batch en Windows), -wait, -i <journal>.

Uso: python run_fluent.py <journal> <carpeta_trabajo> [--t 4] [--timeout 3600] [--dim 3ddp]
Se trabaja en una carpeta con ruta ASCII (D:/CFD02_run/...) porque la ruta del
proyecto tiene espacios y tildes; los logs se copian luego a 04_CASOS/<caso>/logs.
"""
import argparse
import subprocess
import sys
import time

FLUENT = r"D:\Ansys\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\fluent.exe"

p = argparse.ArgumentParser()
p.add_argument("journal")
p.add_argument("cwd")
p.add_argument("--t", type=int, default=4)
p.add_argument("--timeout", type=float, default=3600)
p.add_argument("--dim", default="3ddp")
a = p.parse_args()

t0 = time.time()
proc = subprocess.Popen([FLUENT, a.dim, f"-t{a.t}", "-g", "-hidden", "-wait", "-i", a.journal], cwd=a.cwd,
                        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
# stdin cerrado: si el journal falla, Fluent lee EOF y termina ("Halting due to end of file")
# en vez de quedarse esperando entrada (verificado en F4).
try:
    rc = proc.wait(timeout=a.timeout)
except subprocess.TimeoutExpired:
    subprocess.call(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # limpieza de procesos de Fluent que queden colgados (script que genera el propio Fluent),
    # con PATH de Windows para que 'timeout' sea el de System32 y no el de Git Bash
    import glob
    import os
    env = dict(os.environ, PATH=os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32"))
    for bat in glob.glob(os.path.join(a.cwd, "cleanup-fluent-*.bat")):
        subprocess.call(["cmd", "/c", bat], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"TIMEOUT tras {a.timeout} s")
    sys.exit(124)
print(f"exit={rc} t={time.time() - t0:.1f}s")
sys.exit(rc)
