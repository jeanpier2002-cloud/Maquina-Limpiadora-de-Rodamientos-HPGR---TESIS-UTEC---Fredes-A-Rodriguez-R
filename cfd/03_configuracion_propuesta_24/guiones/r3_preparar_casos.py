#!/usr/bin/env python3
"""
CORRIDA 3 · T4 · Prepara los casos de Fluent R3_00-R3_07 (PROMPT_CORRIDA_3 §3 y §0 bis) a partir del journal del kit
G3_A_O7_O4.jou (SOLO LECTURA: se copia). Respecto del kit solo cambian:
  rutas (carpeta del caso, transcript, cas/dat final), malla (se lee de D:/CFD03_run/mallas, sin copiarla; hash en T0),
  paso de tiempo y numero de pasos (Courant de gota constante: dt_i = dt_base*dr_i/dr_base, n = T/dt redondeado y
  dt reajustado a T/n, como v3_preparar_co.py de la Corrida 2), tablas .dpm (variante de T2) y, en R3_03, los
  nombres de las 7 inyecciones (_A -> _B).
Todo lo demas (aire, k-e, DPM transitorio acoplado, trap en od y cara_inf, 8 muestras, 10 it/paso) es identico al kit:
se comprueba con un diff por caso (logs/diff_journals_kit.txt).
Tambien prepara, por si R3_02 no pasa la aceptacion (§0 bis regla 2), la version de humo (100 pasos) de R3_04-07.

Uso: python -I -B r3_preparar_casos.py
Salidas: casos/<caso>/<caso>.jou + .dpm, casos_r3.csv, cola_humo.txt, cola_r3.txt, filas PLANIFICADO en run_log.csv
"""
import csv
import difflib
import json
import os
import shutil

BASE = "D:/CFD_Redosado/CORRIDA_3_O7C2"
FL = BASE + "/03_FLUENT"
KIT_JOU = ("D:/CFD_Redosado/Diseño actual/PAQUETE_JEAN_O7C2_v2_2026-10-25/01_KIT_G3_A_O7_O4/G3_A_O7_O4.jou")
KIT_DIR = "D:/CFD03_run/G3/G3_A_O7_O4"          # ruta escrita dentro del journal del kit (no se usa ni se crea)
MALLAS = "D:/CFD03_run/mallas"
INY = BASE + "/01_ENTRADA/inyecciones"
RUN_LOG = BASE + "/00_ADMIN/run_log.csv"
DT_BASE, T_FIN = 5e-5, 0.050
IDS_A = ["LAT_1_A", "LAT_2_A", "LAT_3_A", "LAT_4_A", "LAT_5_A", "INF_EXT_A", "C2_A"]

# id, caso, ramal, malla, variante de inyecciones, pasos forzados, costo estimado h (MATRIZ_CORRIDAS_3.csv),
# timeout s (§0 bis: 2,5 x costo), aceptacion previa requerida
CASOS = [
    ("R3_00", "R3_00_humo", "A", "L_A_base", "kit_A", 100, 0.2, 1800, ""),
    ("R3_02", "R3_02_caso2", "A", "L_A_base", "caso2_A", None, 2.3, 20700, ""),
    ("R3_01", "R3_01_kit", "A", "L_A_base", "kit_A", None, 2.3, 20700, ""),
    ("R3_03", "R3_03_B_caso2", "B", "L_B_base", "caso2_B", None, 2.1, 18900, ""),
    ("R3_04", "R3_04_gruesa", "A", "L_A_gruesa", "caso2_A", None, 1.0, 9000, "R3_02_caso2"),
    ("R3_05", "R3_05_fina", "A", "L_A_fina", "caso2_A", None, 4.6, 41400, "R3_02_caso2"),
    ("R3_06", "R3_06_np050", "A", "L_A_base", "caso2_A_np050", None, 1.8, 16200, "R3_02_caso2"),
    ("R3_07", "R3_07_np200", "A", "L_A_base", "caso2_A_np200", None, 3.2, 28800, "R3_02_caso2"),
]


def dr(malla):
    d = json.load(open("%s/%s_info.json" % (MALLAS, malla), encoding="utf-8"))
    return d["dr_max_m"], d["celdas"]


def una(txt, viejo, nuevo):
    if txt.count(viejo) != 1:
        raise SystemExit("esperaba 1 aparicion de %r y hay %d" % (viejo, txt.count(viejo)))
    return txt.replace(viejo, nuevo)


kit = open(KIT_JOU, encoding="utf-8").read()
# CORRECCION (25/10 21:25, humo R3_00): /report/dpm-sample pide los nombres de inyeccion uno a uno con el siguiente por
# defecto, y una linea en blanco de mas cierra la lista. El journal del kit trae 7 lineas en blanco (copiadas de la
# base, que tenia 6 inyecciones) para 7 inyecciones: la septima acepta lat_5_a, «od» y demas se leen como nombres de
# inyeccion, la lista de fronteras queda vacia y no se escribe ninguna muestra (transcript de R3_00_humo/_fallo1).
# Con 7 inyecciones hacen falta 8 lineas en blanco (G3_A_base_v3_transcript.txt: 6 inyecciones + 1 en blanco).
kit = una(kit, "/report/dpm-sample\n" + "\n" * 7 + "od\n", "/report/dpm-sample\n" + "\n" * 8 + "od\n")
dr_base, _ = dr("L_A_base")
filas, diffs = [], []


def preparar(cid, caso, ramal, malla, var, n_forz, est_h, tmax, gate):
    dst = FL + "/casos/" + caso
    if os.path.exists(dst):
        raise SystemExit("ya existe %s: no se sobrescribe" % dst)
    dri, celdas = dr(malla)
    n = round(T_FIN / (DT_BASE * dri / dr_base))
    dt = T_FIN / n
    if n_forz:
        n = n_forz
    j = kit
    j = una(j, '"%s/G3_A_O7_O4_transcript.txt"' % KIT_DIR, '"%s/%s_transcript.txt"' % (dst, caso))
    j = una(j, '/file/read-case "%s/L_A_base.msh"' % KIT_DIR, '/file/read-case "%s/%s.msh"' % (MALLAS, malla))
    j = una(j, '"%s/G3_A_O7_O4_fin.cas.h5"' % KIT_DIR, '"%s/%s_fin.cas.h5"' % (dst, caso))
    j = una(j, "/solve/set/transient-controls/time-step-size\n5e-05\n",
            "/solve/set/transient-controls/time-step-size\n%.6e\n" % dt)
    j = una(j, "/solve/dual-time-iterate\n1000\n10\n", "/solve/dual-time-iterate\n%d\n10\n" % n)
    ids = IDS_A if ramal == "A" else [i[:-1] + "B" for i in IDS_A]
    for ia, ii in zip(IDS_A, ids):
        j = una(j, '"%s/%s.dpm"' % (KIT_DIR, ia), '"%s/%s.dpm"' % (dst, ii))
        j = una(j, "/define/models/dpm/injections/create-injection\n%s\n" % ia,
                "/define/models/dpm/injections/create-injection\n%s\n" % ii)
    if KIT_DIR in j:
        raise SystemExit("quedan rutas del kit en " + caso)
    os.makedirs(dst)
    open("%s/%s.jou" % (dst, caso), "w", newline="\n", encoding="utf-8").write(j)
    for ii in ids:
        shutil.copy2("%s/%s/%s.dpm" % (INY, var, ii), dst)
    d = [l for l in difflib.unified_diff(kit.splitlines(), j.splitlines(), "kit/G3_A_O7_O4.jou", caso + ".jou", n=0,
                                         lineterm="") if not l.startswith("@@")]
    diffs.append("==== %s (%d lineas distintas)\n%s\n" % (caso, sum(1 for l in d if l[:1] in "+-") - 2, "\n".join(d)))
    filas.append(dict(id=cid, caso=caso, ramal=ramal, malla=malla, celdas=celdas, dr_m="%.6g" % dri,
                      dt_s="%.6e" % dt, pasos=n, t_fin_s="%.6g" % (n * dt), Co_gota="%.3f" % (27.11 * dt / dri),
                      inyecciones=var, costo_estimado_h=est_h, timeout_s=tmax, requiere=gate))
    return dst


rutas = {}
for c in CASOS:
    rutas[c[1]] = preparar(*c)
# versiones de humo (100 pasos) de R3_04-07, solo para el caso de que R3_02 no pase la aceptacion
for c in CASOS[4:]:
    preparar(c[0] + "h", c[1] + "_humo", c[2], c[3], c[4], 100, 0.2, 1800, "")

with open(FL + "/casos_r3.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(filas[0]))
    w.writeheader()
    w.writerows(filas)
open(FL + "/logs/diff_journals_kit.txt", "w", encoding="utf-8").write("\n".join(diffs))
with open(FL + "/cola_humo.txt", "w", newline="\n") as f:
    f.write("# carpeta|timeout_s\n%s|1800\nFIN\n" % rutas["R3_00_humo"])
with open(FL + "/cola_r3.txt", "w", newline="\n") as f:
    f.write("# carpeta|timeout_s|aceptacion_requerida  (orden de §0 bis; R3_08-10 no se corren)\n")
    for c in CASOS[1:]:
        f.write("%s|%d%s\n" % (rutas[c[1]], c[7], ("|" + c[8]) if c[8] else ""))
    f.write("FIN\n")

COLS = ("etapa,caso,malla,celdas,dx_min_m,maxCo,modelo,np,pasos,t_fin_s,dt_medio_s,dt_min_s,dt_max_s,"
        "Co_max_ultimo,alphaCo_max_ultimo,pared_s,pared_h,s_por_paso,RAM_max_MB,End,FATAL,tarea_v2,estimado_h,"
        "estado,id,costo_estimado_h,costo_real_h,notas").split(",")   # cabecera de la Corrida 2 (ya trae los costos)
nuevo = not os.path.exists(RUN_LOG)
with open(RUN_LOG, "a", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    if nuevo:
        w.writeheader()
    for r in filas:
        humo = r["caso"].endswith("_humo") and r["id"] != "R3_00"
        w.writerow(dict(etapa="fluent_R3", caso=r["caso"], malla=r["malla"], celdas=r["celdas"], dx_min_m=r["dr_m"],
                        maxCo=r["Co_gota"], modelo="DPM k-e 2 vias", np=4, pasos=r["pasos"], t_fin_s=r["t_fin_s"],
                        dt_medio_s=r["dt_s"], dt_min_s=r["dt_s"], dt_max_s=r["dt_s"],
                        tarea_v2="T4" if r["id"].startswith("R3_00") or humo else ("T5" if r["id"] <= "R3_03" else "T8"),
                        estado="RESERVA (solo si R3_02 no pasa)" if humo else "PLANIFICADO", id=r["id"],
                        costo_estimado_h=r["costo_estimado_h"],
                        notas="inyecciones %s; Co de gota con v=27,11 m/s y dr; estimado de MATRIZ_CORRIDAS_3.csv" % r["inyecciones"]))
for r in filas:
    print("%-6s %-22s %-10s %7s celdas dr %s dt %s n %5d Co %s iny %-14s est %s h timeout %s %s" % (
        r["id"], r["caso"], r["malla"], r["celdas"], r["dr_m"], r["dt_s"], r["pasos"], r["Co_gota"], r["inyecciones"],
        r["costo_estimado_h"], r["timeout_s"], r["requiere"]))
print("total cola (sin humo ni reservas): %.1f h" % sum(c[6] for c in CASOS[1:]))
