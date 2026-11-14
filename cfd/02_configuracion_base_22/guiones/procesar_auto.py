#!/usr/bin/env python3
"""
CFD03 - Procesado automatico de las corridas que la cola marca como terminadas (cola_hecho.txt).
Ventana por tipo de caso (estacionariedad verificada): INT (sector de INF_INT) 70-100 ms; E-SUP 20-40 ms;
F5 20-35 ms; resto (G3/G4/G5_PAD/G8 con L) 25-50 ms. Registro: D:/CFD03_run/procesar_auto.log.
Se detiene si existe D:/CFD03_run/PARAR_AUTO.
"""
import os, subprocess, sys, time
AQUI = os.path.dirname(os.path.abspath(__file__))
HECHO, LISTO, LOG = "D:/CFD03_run/cola_hecho.txt", "D:/CFD03_run/procesados.txt", "D:/CFD03_run/procesar_auto.log"
def ventana(nombre):
    if "INT" in nombre and "PAD" not in nombre: return 0.070, 0.100
    if "ESUP" in nombre or "_SUP" in nombre: return 0.020, 0.040
    if nombre.startswith("F5"): return 0.020, 0.035
    return 0.025, 0.050
def log(m):
    s = time.strftime("%Y-%m-%d %H:%M:%S ") + m; print(s, flush=True); open(LOG, "a").write(s + "\n")
log("procesar_auto iniciado")
while not os.path.exists("D:/CFD03_run/PARAR_AUTO"):
    hechos = [l.strip() for l in open(HECHO)] if os.path.exists(HECHO) else []
    listos = set(l.strip() for l in open(LISTO)) if os.path.exists(LISTO) else set()
    for c in hechos:
        if c in listos or not c:
            continue
        nombre = os.path.basename(c.rstrip("/\\")); fase = os.path.basename(os.path.dirname(c.rstrip("/\\")))
        t0, t1 = ventana(nombre)
        log("procesando %s (fase %s, ventana %.3f-%.3f s)" % (nombre, fase, t0, t1))
        r = subprocess.run([sys.executable, os.path.join(AQUI, "procesar_caso.py"), c, "--fase", fase, "--t0", str(t0), "--t1", str(t1)],
                           capture_output=True, text=True)
        resumen = [l for l in r.stdout.splitlines() if l.startswith("balance") or "D media" in l or "archivado" in l]
        log(" | ".join(resumen) if resumen else ("ERROR rc=%s %s" % (r.returncode, r.stderr[-600:])))
        open(LISTO, "a").write(c + "\n")
    time.sleep(60)
log("procesar_auto detenido")
