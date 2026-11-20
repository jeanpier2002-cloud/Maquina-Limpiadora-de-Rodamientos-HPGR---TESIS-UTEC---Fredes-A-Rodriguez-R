# -*- coding: utf-8 -*-
"""Envoltorio (freecadcmd, solo lectura): rv01c aplicado a R07_V18B_STEP.FCStd (03/11/2026). El barrido queda vacio porque las vigas
ya no se llaman CTX_M01/M02 y B_COM esta en NO_VIGENTE: aqui solo interesa la parte de fijaciones (cada perno, tuerca, arandela o
pasador y las piezas no-fijacion a <= 1,5 mm). Salida: revision_cad_v11/resultados/rv07c_fijaciones_v18b.json."""
AQUI = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\revision_cad_v11\scripts"
src = open(AQUI + r"\rv01c_fijaciones_y_barrido.py", encoding="utf-8").read()
for a, b in (("R07_V11_STEP.FCStd", "R07_V18B_STEP.FCStd"), ("rv01c_fijaciones_y_barrido.json", "rv07c_fijaciones_v18b.json")):
    assert a in src, a
    src = src.replace(a, b)
exec(compile(src, "rv07c", "exec"), {"__name__": "__main__"})
