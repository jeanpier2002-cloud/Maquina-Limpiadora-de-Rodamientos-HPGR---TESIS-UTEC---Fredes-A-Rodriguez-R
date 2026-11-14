#!/usr/bin/env python3
"""
Cola dinamica de corridas de Fluent en serie (licencia Student: una sola sesion, S8).
Lee D:/CFD03_run/cola.txt (una carpeta por linea: <carpeta>|<timeout_s>), ejecuta en orden las que no
figuran en cola_hecho.txt, cada una con run_fluent.py y <carpeta>/<nombre_carpeta>.jou. Se pueden
anadir lineas mientras corre. Termina al leer una linea 'FIN' o si existe D:/CFD03_run/PARAR.
Registro: D:/CFD03_run/cola.log
"""
import os
import subprocess
import sys
import time

BASE = "D:/CFD03_run"
COLA, HECHO, LOG, PARAR = [os.path.join(BASE, n) for n in ("cola.txt", "cola_hecho.txt", "cola.log", "PARAR")]
RUN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_fluent.py")


def log(m):
    s = time.strftime("%Y-%m-%d %H:%M:%S ") + m
    print(s, flush=True)
    open(LOG, "a").write(s + "\n")


def fluent_activo():
    out = subprocess.run(["tasklist"], capture_output=True, text=True).stdout.lower()
    return "fl2610.exe" in out or "cx2610.exe" in out


log("cola dinamica iniciada")
while not os.path.exists(PARAR):
    hechos = set(l.strip() for l in open(HECHO)) if os.path.exists(HECHO) else set()
    lineas = [l.strip() for l in open(COLA)] if os.path.exists(COLA) else []
    pend = [l for l in lineas if l and not l.startswith("#") and l.split("|")[0] not in hechos]
    if not pend:
        time.sleep(30)
        continue
    if pend[0] == "FIN":
        log("FIN leido; cola terminada")
        break
    carpeta, *resto = pend[0].split("|")
    tmax = resto[0] if resto else "14400"
    while fluent_activo():
        time.sleep(20)
    tag = os.path.basename(carpeta.rstrip("/\\"))
    log("inicio %s (timeout %s s)" % (tag, tmax))
    t0 = time.time()
    rc = subprocess.call([sys.executable, RUN, os.path.join(carpeta, tag + ".jou"), carpeta, "--t", "4",
                          "--timeout", tmax])
    log("fin %s rc=%s t=%.0f s" % (tag, rc, time.time() - t0))
    open(HECHO, "a").write(carpeta + "\n")
    time.sleep(10)
log("cola detenida")
