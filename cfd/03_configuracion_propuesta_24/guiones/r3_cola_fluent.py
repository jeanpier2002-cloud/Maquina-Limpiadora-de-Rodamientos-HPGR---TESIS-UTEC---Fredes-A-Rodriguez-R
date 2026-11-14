#!/usr/bin/env python3
"""
CORRIDA 3 · T5/T8 · Cola en serie de Fluent (licencia Student: una sola sesion). Copia de v3_cola_fluent.py
(CORRIDA 2) con BASE = CORRIDA_3_O7C2 y tres reglas del modo autonomo (PROMPT_CORRIDA_3 §0 bis):
  - disco: antes de cada corrida exige >= 20 GB libres en D:; si no, detiene la cola (no borra nada);
  - reintento: si una corrida falla (rc != 0, timeout o pasos incompletos) mueve sus salidas a _fallo1/ y la repite
    UNA vez; si vuelve a fallar, sigue con la siguiente;
  - aceptacion previa: una linea <carpeta>|<timeout>|<caso> solo se lanza si resultados/<caso>_aceptacion.txt
    (lo escribe r3_procesar_auto.py) empieza por OK; si empieza por FALLA, lanza en su lugar <carpeta>_humo
    (100 pasos, para dejar los scripts verificados); si no existe, espera hasta 2 h y luego tambien usa el humo.
Lee <cola> (lineas <carpeta>|<timeout_s>[|caso]; '#' se salta; 'FIN' termina) y la relee en cada vuelta (se puede
editar en marcha). Si existe 03_FLUENT/PARAR, no lanza el siguiente caso. Lo hecho queda en <cola>.hecho.

Uso: python -I r3_cola_fluent.py ../cola_r3.txt
"""
import csv
import os
import re
import shutil
import subprocess
import sys
import time

BASE = "D:/CFD_Redosado/CORRIDA_3_O7C2"
FL = BASE + "/03_FLUENT"
RUN_LOG = BASE + "/00_ADMIN/run_log.csv"
LOG = FL + "/logs/cola_r3.log"
PARAR = FL + "/PARAR"
RUN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "r3_run_fluent.py")
MIN_GB = 20
COLA = os.path.abspath(sys.argv[1])
HECHO = COLA + ".hecho"


def log(m):
    s = time.strftime("%Y-%m-%d %H:%M:%S ") + m
    print(s, flush=True)
    open(LOG, "a", encoding="utf-8").write(s + "\n")


def fluent_activo():
    out = subprocess.run(["tasklist"], capture_output=True, text=True).stdout.lower()
    return "fl2610.exe" in out or "cx2610.exe" in out


def libre_gb():
    return shutil.disk_usage("D:/").free / 1e9


def revisar(carpeta, tag):
    """Ultimo paso y tiempo de flujo del transcript, numero de lineas de error y pasos pedidos en el journal."""
    tr = os.path.join(carpeta, tag + "_transcript.txt")
    jou = open(os.path.join(carpeta, tag + ".jou")).read()
    pedidos = int(re.search(r"/solve/dual-time-iterate\n(\d+)\n", jou).group(1))
    if not os.path.exists(tr):
        return pedidos, None, None, -1
    txt = open(tr, errors="replace").read()
    pasos = re.findall(r"Flow time = ([0-9.eE+-]+)s, time step = (\d+)", txt)
    errores = len(re.findall(r"^\s*Error", txt, flags=re.M))
    if not pasos:
        return pedidos, None, None, errores
    return pedidos, float(pasos[-1][0]), int(pasos[-1][1]), errores


def actualizar_run_log(caso, **campos):
    filas = list(csv.DictReader(open(RUN_LOG, newline="")))
    cols = list(filas[0].keys())
    for f in filas:
        if f["caso"] == caso and f["etapa"] == "fluent_R3":
            f.update({k: v for k, v in campos.items() if k in cols})
    tmp = RUN_LOG + ".tmp"
    with open(tmp, "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)
    os.replace(tmp, RUN_LOG)


def apartar(carpeta, tag, k):
    """Mueve las salidas de un intento fallido a <carpeta>/_fallo<k>/ (deja journal e inyecciones)."""
    dst = os.path.join(carpeta, "_fallo%d" % k)
    os.makedirs(dst, exist_ok=True)
    entradas = {tag + ".jou"} | {f for f in os.listdir(carpeta) if re.match(r"^(LAT|INF|C2).*\.dpm$", f)}
    for f in os.listdir(carpeta):
        p = os.path.join(carpeta, f)
        if os.path.isfile(p) and f not in entradas:
            shutil.move(p, os.path.join(dst, f))
    return dst


def correr(carpeta, tmax):
    tag = os.path.basename(carpeta.rstrip("/\\"))
    for intento in (1, 2):
        while fluent_activo():
            log("hay un Fluent activo; espero 60 s")
            time.sleep(60)
        log("inicio %s intento %d (timeout %s s; libre en D: %.0f GB)" % (tag, intento, tmax, libre_gb()))
        actualizar_run_log(tag, estado="EN CURSO", notas="inicio %s (intento %d)" % (time.strftime("%d/%m %H:%M"), intento))
        t0 = time.time()
        rc = subprocess.call([sys.executable, "-I", RUN, os.path.join(carpeta, tag + ".jou"), carpeta, "--t", "4",
                              "--timeout", str(tmax)])
        dt = time.time() - t0
        pedidos, t_fin, paso, err = revisar(carpeta, tag)
        ok = rc == 0 and paso == pedidos
        log("fin %s rc=%s t=%.0f s (%.2f h) paso %s/%s t_flujo %s errores %s -> %s" % (
            tag, rc, dt, dt / 3600, paso, pedidos, t_fin, err, "OK" if ok else "REVISAR"))
        actualizar_run_log(tag, estado="EJECUTADO" if ok else "FALLIDO o INCOMPLETO", costo_real_h="%.2f" % (dt / 3600),
                           pared_s="%.0f" % dt, pared_h="%.3f" % (dt / 3600),
                           s_por_paso="%.3f" % (dt / paso) if paso else "", End=1 if ok else 0, FATAL=err,
                           notas="rc=%s; paso %s/%s; t_flujo %s s; fin %s; intento %d" % (
                               rc, paso, pedidos, t_fin, time.strftime("%d/%m %H:%M"), intento))
        if ok:
            return True
        if intento == 1:
            d = apartar(carpeta, tag, 1)
            log("%s fallo: salidas movidas a %s; se repite una vez" % (tag, d))
            time.sleep(30)
    log("%s fallo dos veces: sigo con la siguiente" % tag)
    return False


def aceptacion(caso, espera_max=7200):
    p = os.path.join(FL, "resultados", caso + "_aceptacion.txt")
    t0 = time.time()
    while not os.path.exists(p) and time.time() - t0 < espera_max and not os.path.exists(PARAR):
        log("espero la aceptacion de %s (%s)" % (caso, p))
        time.sleep(120)
    if not os.path.exists(p):
        return "SIN ACEPTACION"
    return open(p, encoding="utf-8").read().strip().split()[0]


log("cola iniciada: " + COLA)
while not os.path.exists(PARAR):
    hechos = set(l.strip() for l in open(HECHO)) if os.path.exists(HECHO) else set()
    lineas = [l.strip() for l in open(COLA) if l.strip() and not l.lstrip().startswith("#")]
    pend = [l for l in lineas if l.split("|")[0] not in hechos]
    if not pend or pend[0] == "FIN":
        log("FIN leido; cola terminada")
        break
    partes = pend[0].split("|")
    carpeta, tmax = partes[0], partes[1]
    if libre_gb() < MIN_GB:
        log("DETENIDA: solo %.1f GB libres en D: (< %d GB); no se borra nada" % (libre_gb(), MIN_GB))
        break
    if len(partes) > 2 and partes[2]:
        est = aceptacion(partes[2])
        if est != "OK":
            humo = carpeta.rstrip("/\\") + "_humo"
            log("%s: aceptacion de %s = %s -> se corre %s en su lugar" % (os.path.basename(carpeta), partes[2], est,
                                                                         os.path.basename(humo)))
            actualizar_run_log(os.path.basename(carpeta), estado="NO CORRIDA (R3_02 sin aceptacion: %s)" % est)
            correr(humo, 1800)
            open(HECHO, "a").write(carpeta + "\n")
            time.sleep(10)
            continue
    correr(carpeta, tmax)
    open(HECHO, "a").write(carpeta + "\n")
    time.sleep(10)
log("cola detenida")
