#!/usr/bin/env python3
"""
Generador general de journals DPM para Fluent 2026 R1 (F6-F8). Solo usa secuencias de prompts
verificadas en F4/F5 (04_CASOS/F4_licencia/resultados/nombres_verificados.md; F5: jou_f5.py).

Modos:
  estacionario: flujo estacionario k-e acoplado a 2 vias; iteracion DPM cada 10 iteraciones
                (valor por defecto verificado en F4 t8). Al final /report/dpm-sample escribe
                <zona>.dpm con mass-flow (kg/s) por parcela.
  transitorio : igual que F5 (Delta t fijo, seguimiento no estacionario con el mismo paso,
                muestreo abierto desde t = 0 con flow-time; ventana en el post-proceso).

Uso:
  python jou_dpm.py --malla M.msh --dir D:/CFD02_run/F6 --tag F6_est_v1 --modo estacionario \
      --iny LAT_1 --paredes od --muestreo od,abierto_interior,... [--iter 300]
  python jou_dpm.py ... --modo transitorio --dt 5e-5 --pasos 500 --iter 10
Los archivos <inyeccion>.dpm deben estar en --dir.
"""
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("--malla", required=True)
ap.add_argument("--dir", required=True)
ap.add_argument("--tag", required=True)
ap.add_argument("--modo", choices=["estacionario", "transitorio"], required=True)
ap.add_argument("--iny", required=True, help="nombres de inyeccion separados por coma (archivos <n>.dpm)")
ap.add_argument("--paredes", required=True, help="zonas de pared con trap, separadas por coma")
ap.add_argument("--muestreo", required=True, help="zonas a muestrear, separadas por coma")
ap.add_argument("--iter", type=int, default=300, help="estacionario: iteraciones; transitorio: it/paso")
ap.add_argument("--dt", type=float, default=5e-5)
ap.add_argument("--pasos", type=int, default=500)
ap.add_argument("--gravedad", default="0 0 -9.81")
ap.add_argument("--uncoupled", action="store_true", help="sin acoplamiento de 2 vias (sensibilidad)")
ap.add_argument("--bc-dpm", default="trap", help="BC DPM de las paredes (trap; reflect para sensibilidad)")
a = ap.parse_args()

D = a.dir.rstrip("/")
N = lambda k: "\n" * k
L = []
w = L.append
iny = a.iny.split(",")
w(f'/file/start-transcript "{D}/{a.tag}_transcript.txt"')
w(f'/file/read-case "{a.malla}"')
w("/mesh/check")
w("/define/operating-conditions/operating-pressure\n76240")
w("/define/operating-conditions/gravity\nyes\n" + "\n".join(a.gravedad.split()))
w("/define/materials/change-create\nair\n\nyes\nconstant\n0.90610\nno\nno\nyes\nconstant\n1.8250e-05\nno\nno\nno")
w("/define/models/viscous/ke-standard?\nyes")
if a.modo == "transitorio":
    w("/define/models/unsteady-1st-order?\nyes")
for b in iny:
    base = f'/define/models/dpm/injections/create-injection\n{b}\nno\nyes\nfile\nno\n"{D}/{b}.dpm"\nno\nno\nno\nno'
    # transitorio: prompts extra "Set parcel release method?", Start, Stop (verificados en F5 t11_v2)
    w(base + ("\nno\n0\n1" if a.modo == "transitorio" else ""))
w("/define/materials/change-create\nanthracite\n\nyes\nconstant\n982.12\nno")
if not a.uncoupled:
    w("/define/models/dpm/interaction/coupled-calculations?\nyes")
if a.modo == "transitorio":
    w("/define/models/dpm/unsteady-tracking\nyes\nyes")
for z in a.paredes.split(","):
    # verificado con k-e activo: 6 prompts de pared y luego la BC DPM
    # reflect pide ademas coeficientes de restitucion normal y tangencial (3 prompts cada uno,
    # F4 t4): se aceptan los valores por defecto (polinomio de 1 coeficiente = 1)
    w(f"/define/boundary-conditions/wall\n{z}" + N(7) + f"yes\n{a.bc_dpm}"
      + (N(6) if a.bc_dpm == "reflect" else ""))
zonas = a.muestreo.split(",")
samp = "/report/dpm-sample" + N(len(iny) + 2) + "\n".join(zonas) + N(5)
if a.modo == "transitorio":
    w(f"/solve/set/transient-controls/time-step-size\n{a.dt}")
    w(f"/solve/set/transient-controls/max-iterations-per-time-step\n{a.iter}")
    w("/solve/initialize/initialize-flow")
    w(samp)                                   # abre el muestreo (registra flow-time)
    w(f"/solve/dual-time-iterate\n{a.pasos}\n{a.iter}")
    w("/report/dpm-sample")                   # cierra
else:
    w("/solve/initialize/initialize-flow")
    w(f"/solve/iterate {a.iter}")
    w(samp)                                   # estacionario: traza, escribe y cierra
w("/report/dpm-summary")
w(f'/file/write-case-data "{D}/{a.tag}_fin.cas.h5"')
open(f"{D}/{a.tag}.jou", "w", newline="\n").write("\n".join(L) + "\n" + N(2) + "/exit\nyes\n")
print(f"{D}/{a.tag}.jou")
