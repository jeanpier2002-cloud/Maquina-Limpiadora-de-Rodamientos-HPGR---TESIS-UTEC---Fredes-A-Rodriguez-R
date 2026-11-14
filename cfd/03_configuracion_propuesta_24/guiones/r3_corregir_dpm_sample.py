#!/usr/bin/env python3
"""
CORRIDA 3 · T4 · Correccion del bloque /report/dpm-sample en los journals ya preparados (25/10, tras el humo R3_00).
Con 7 inyecciones el primer /report/dpm-sample necesita 8 lineas en blanco (7 aceptan los nombres por defecto y la
octava cierra la lista) antes de los nombres de las fronteras; el journal del kit trae 7 (heredadas de la base de 6
inyecciones) y Fluent no escribio ninguna muestra. Misma correccion que ya aplica r3_preparar_casos.py.
Edita solo los journals de 03_FLUENT/casos/*/ (archivos de esta tanda). Comprueba 1 aparicion antes de cambiar.
Uso: python -I -B r3_corregir_dpm_sample.py
"""
import glob
import os

FL = "D:/CFD_Redosado/CORRIDA_3_O7C2/03_FLUENT"
VIEJO = "/report/dpm-sample\n" + "\n" * 7 + "od\n"
NUEVO = "/report/dpm-sample\n" + "\n" * 8 + "od\n"
for d in sorted(glob.glob(FL + "/casos/*/")):
    tag = os.path.basename(d.rstrip("/\\"))
    p = os.path.join(d, tag + ".jou")
    j = open(p, encoding="utf-8").read()
    if j.count(NUEVO) == 1:
        print("%-24s ya corregido" % tag)
        continue
    if j.count(VIEJO) != 1:
        raise SystemExit("%s: esperaba 1 aparicion del bloque viejo y hay %d" % (tag, j.count(VIEJO)))
    open(p, "w", newline="\n", encoding="utf-8").write(j.replace(VIEJO, NUEVO))
    print("%-24s corregido (8 lineas en blanco en el primer /report/dpm-sample)" % tag)
