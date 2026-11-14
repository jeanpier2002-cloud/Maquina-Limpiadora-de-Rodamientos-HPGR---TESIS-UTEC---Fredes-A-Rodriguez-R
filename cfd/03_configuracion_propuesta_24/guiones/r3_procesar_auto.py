#!/usr/bin/env python3
"""
CORRIDA 3 · T5/T8 · Procesa cada corrida en cuanto la cola la marca como terminada (copia adaptada de
v3_procesar_auto.py de la CORRIDA 2). Ventana de evaluacion 25-50 ms (identica a G3_A_base_v3); en los humos
(100 pasos) toda la corrida (0 - 100*dt).
Ademas escribe resultados/<caso>_aceptacion.txt (PROMPT_CORRIDA_3 §5 y §0 bis regla 2), que lee r3_cola_fluent.py:
  OK    si: pasos completos, sin lineas 'Error'/'FATAL' en el transcript, las 8 muestras DPM presentes y
        |error de balance de la ventana| < 1 % (en los humos el balance no se exige: el chorro aun no es estacionario)
  FALLA en otro caso (con el motivo).
Salidas: 03_FLUENT/resultados/R3/<caso>_{balance,estacionariedad,<superficie>_*}.csv; logs/<caso>_post.txt;
registro logs/procesar_r3.log. Se detiene al procesar todo lo de la cola o si existe 03_FLUENT/PARAR_AUTO.
Uso: python -I r3_procesar_auto.py ../cola_r3.txt
"""
import csv
import os
import re
import subprocess
import sys
import time

FL = "D:/CFD_Redosado/CORRIDA_3_O7C2/03_FLUENT"
AQUI = os.path.dirname(os.path.abspath(__file__))
COLA = os.path.abspath(sys.argv[1])
HECHO, LISTO, LOG = COLA + ".hecho", COLA + ".procesados", FL + "/logs/procesar_r3.log"
MUESTRAS = ["od", "cara_inf", "abierto_agujero", "abierto_interior", "abierto_exterior", "abierto_lateral",
            "abierto_inferior", "abierto_superior"]


def log(m):
    s = time.strftime("%Y-%m-%d %H:%M:%S ") + m
    print(s, flush=True)
    open(LOG, "a", encoding="utf-8").write(s + "\n")


def leer_journal(c, nombre):
    jou = open(os.path.join(c, nombre + ".jou")).read()
    n = int(re.search(r"/solve/dual-time-iterate\n(\d+)\n", jou).group(1))
    dt = float(re.search(r"/solve/set/transient-controls/time-step-size\n(\S+)\n", jou).group(1))
    return n, dt


def aceptar(c, nombre, humo):
    n, dt = leer_journal(c, nombre)
    motivos = []
    tr = os.path.join(c, nombre + "_transcript.txt")
    txt = open(tr, errors="replace").read() if os.path.exists(tr) else ""
    pasos = re.findall(r"Flow time = ([0-9.eE+-]+)s, time step = (\d+)", txt)
    ult = int(pasos[-1][1]) if pasos else 0
    if ult != n:
        motivos.append("pasos %d/%d" % (ult, n))
    nerr = len(re.findall(r"^\s*Error", txt, flags=re.M)) + len(re.findall(r"FATAL", txt))
    if nerr:
        motivos.append("%d lineas Error/FATAL en el transcript" % nerr)
    falta = [m for m in MUESTRAS if not os.path.exists(os.path.join(c, m + ".dpm"))]
    if falta:
        motivos.append("faltan muestras: " + ",".join(falta))
    err = None
    bal = os.path.join(FL, "resultados", "R3", nombre + "_balance.csv")
    if os.path.exists(bal):
        for f in csv.reader(open(bal)):
            if f and f[0] == "error_balance_ventana_pct":
                err = float(f[3])
    if err is None:
        motivos.append("sin balance")
    elif abs(err) >= 1.0 and not humo:
        motivos.append("balance %.3f %% (>= 1 %%)" % err)
    est = "OK" if not motivos else "FALLA"
    linea = "%s %s | pasos %d/%d | Error/FATAL %d | muestras %d/8 | balance %s %%%s" % (
        est, nombre, ult, n, nerr, 8 - len(falta), "%.4f" % err if err is not None else "-",
        (" | " + "; ".join(motivos)) if motivos else "")
    open(os.path.join(FL, "resultados", nombre + "_aceptacion.txt"), "w", encoding="utf-8").write(linea + "\n")
    return linea


casos = [l.split("|")[0].strip() for l in open(COLA) if l.strip() and not l.lstrip().startswith("#") and "|" in l]
log("procesar_auto iniciado (%d casos) para %s" % (len(casos), COLA))
while not os.path.exists(FL + "/PARAR_AUTO"):
    hechos = [l.strip() for l in open(HECHO)] if os.path.exists(HECHO) else []
    listos = set(l.strip() for l in open(LISTO)) if os.path.exists(LISTO) else set()
    for c in hechos:
        if not c or c in listos:
            continue
        reales = [c]
        if not os.path.exists(os.path.join(c, os.path.basename(c.rstrip("/\\")) + "_transcript.txt")) and \
                os.path.isdir(c.rstrip("/\\") + "_humo"):
            reales = [c.rstrip("/\\") + "_humo"]          # la cola corrio el humo en su lugar
        for cr in reales:
            nombre = os.path.basename(cr.rstrip("/\\"))
            humo = nombre.endswith("_humo")
            n, dt = leer_journal(cr, nombre)
            t0, t1 = (0.0, n * dt) if humo else (0.025, 0.050)
            log("procesando %s (ventana %.5f-%.5f s)" % (nombre, t0, t1))
            r = subprocess.run([sys.executable, "-I", os.path.join(AQUI, "post_cfd03", "r3_procesar_caso.py"), cr,
                                "--fase", "R3", "--t0", repr(t0), "--t1", repr(t1)], capture_output=True, text=True)
            open(os.path.join(FL, "logs", nombre + "_post.txt"), "w", encoding="utf-8").write(r.stdout + r.stderr)
            resumen = [l for l in r.stdout.splitlines() if l.startswith("balance") or "D media" in l or "inyectado" in l]
            log(" | ".join(resumen) if r.returncode == 0 else "ERROR rc=%s %s" % (r.returncode, r.stderr[-600:]))
            log("aceptacion: " + aceptar(cr, nombre, humo))
        open(LISTO, "a").write(c + "\n")
        listos.add(c)
    if len(listos) >= len(casos):
        break
    time.sleep(60)
log("procesar_auto detenido")
