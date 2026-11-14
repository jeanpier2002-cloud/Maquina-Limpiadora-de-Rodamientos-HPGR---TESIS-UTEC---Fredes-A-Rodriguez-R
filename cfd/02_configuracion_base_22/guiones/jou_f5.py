#!/usr/bin/env python3
"""
Genera el journal del caso puente F5 (interior de la rama B en Fluent 2026 R1).
Solo usa comandos y secuencias de prompts verificados en F4/F5
(04_CASOS/F4_licencia/resultados/nombres_verificados.md y logs t11 de F5).

Uso: python jou_f5.py --malla D:/.../agujero_base.msh --dir D:/CFD02_run/F5 --tag F5_base
       [--pasos 700] [--dt 5e-5] [--iter 10] [--muestreo 0.020] [--solo-prueba]
Fases del journal:
  1) modelos, materiales, BC, inyecciones file (6 boquillas)
  2) transitorio hasta t = muestreo (sin muestreo)
  3) muestreo DPM activado en pared_agujero y resto de fronteras hasta t_fin
     (reproduce la ventana de promediado 0,020-0,035 s de la rama B)
"""
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("--malla", required=True)
ap.add_argument("--dir", required=True)
ap.add_argument("--tag", required=True)
ap.add_argument("--pasos", type=int, default=700)
ap.add_argument("--dt", type=float, default=5e-5)
ap.add_argument("--iter", type=int, default=10)
ap.add_argument("--muestreo", type=float, default=0.020)
ap.add_argument("--boquillas", default="INT_1,INT_2,INT_3,INT_4,INT_5,INF_INT")
ap.add_argument("--extra", default="", help="comandos TUI de descubrimiento antes de correr")
ap.add_argument("--solo-prueba", action="store_true", help="2 pasos antes y 2 despues")
a = ap.parse_args()

D = a.dir.rstrip("/")
N = lambda k: "\n" * k
L = []
w = L.append
w(f'/file/start-transcript "{D}/{a.tag}_transcript.txt"')
w(f'/file/read-case "{a.malla}"')
w("/mesh/check")
w("/define/operating-conditions/operating-pressure\n76240")
w("/define/operating-conditions/gravity\nyes\n0\n0\n-9.81")
w("/define/materials/change-create\nair\n\nyes\nconstant\n0.90610\nno\nno\nyes\nconstant\n1.8250e-05\nno\nno\nno")
w("/define/models/viscous/ke-standard?\nyes")
w("/define/models/unsteady-1st-order?\nyes")
for b in a.boquillas.split(","):
    # prompts verificados en t11_v2 (transitorio): ... Cloud Tracking? / Set parcel release method? / Start / Stop
    w(f'/define/models/dpm/injections/create-injection\n{b}\nno\nyes\nfile\nno\n"{D}/{b}.dpm"\nno\nno\nno\nno\nno\n0\n1')
w("/define/materials/change-create\nanthracite\n\nyes\nconstant\n982.12\nno")
w("/define/models/dpm/interaction/coupled-calculations?\nyes")
w("/define/models/dpm/unsteady-tracking\nyes\nyes")
for z in ("pared_agujero", "cara_inf_rodamiento", "cara_sup_rodamiento", "lanza"):
    # secuencia verificada en F4 t8_v3 con k-e activo: 6 prompts de pared y luego la BC DPM
    w(f"/define/boundary-conditions/wall\n{z}" + N(7) + "yes\ntrap")
w(f"/solve/set/transient-controls/time-step-size\n{a.dt}")
w(f"/solve/set/transient-controls/max-iterations-per-time-step\n{a.iter}")
if a.extra:
    w(a.extra)
w("/solve/initialize/initialize-flow")
n1 = 2 if a.solo_prueba else int(round(a.muestreo / a.dt))
n2 = 2 if a.solo_prueba else a.pasos - n1
# Muestreo DPM (verificado en F4 t12): la 1.a llamada abre los archivos <zona>.dpm y registra cada
# impacto con su flow-time durante todo el transitorio; la 2.a llamada los cierra. La ventana
# 0,020-0,035 s se aplica en el post-proceso con la columna flow-time.
nb = len(a.boquillas.split(","))
zonas = ["pared_agujero", "cara_inf_rodamiento", "cara_sup_rodamiento", "lanza", "abierto_inferior",
         "abierto_superior", "lateral_abierto", "nucleo_abierto"]
# nb+1 lineas vacias (acepta las nb inyecciones por defecto y cierra la lista), zonas, y 4 vacias
# (fin de lista de zonas, planos, append, erosion)
w("/report/dpm-sample" + N(nb + 2) + "\n".join(zonas) + N(5))
w(f"/solve/dual-time-iterate\n{n1}\n{a.iter}")
w("/report/dpm-summary")
w(f'/file/write-case-data "{D}/{a.tag}_t1.cas.h5"')
w(f"/solve/dual-time-iterate\n{n2}\n{a.iter}")
w("/report/dpm-sample")
w("/report/dpm-summary")
w(f'/file/write-case-data "{D}/{a.tag}_fin.cas.h5"')
open(f"{D}/{a.tag}.jou", "w", newline="\n").write("\n".join(L) + "\n" + N(2) + "/exit\nyes\n")
print(f"{D}/{a.tag}.jou  pasos antes de muestreo = {n1}, despues = {n2}")
