# -*- coding: utf-8 -*-
"""C1, revision V17B (03/11/2026): el mismo metrado de c1_metrado_cad.py (que no se modifica) sobre el CAD R07 V17B,
que agrega los pedestales del riel con faldones (HPGR D-073). freecadcmd, solo lectura.
Salida: presupuesto/resultados/METRADO_CAD_V17B.json"""
import os

AQUI = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\presupuesto\scripts"
src = open(os.path.join(AQUI, "c1_metrado_cad.py"), encoding="utf-8").read()
for a, b in (('"R07_V16B_STEP.FCStd"', '"R07_V17B_STEP.FCStd"'), ('"METRADO_CAD_V16B.json"', '"METRADO_CAD_V17B.json"')):
    assert src.count(a) == 1, a
    src = src.replace(a, b)
__file__ = os.path.join(AQUI, "c1_metrado_cad.py")
exec(compile(src, "c1_metrado_cad_V17B", "exec"))
