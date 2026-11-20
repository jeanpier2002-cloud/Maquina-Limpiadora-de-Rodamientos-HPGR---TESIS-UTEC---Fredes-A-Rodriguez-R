# -*- coding: utf-8 -*-
"""Envoltorio (freecadcmd, solo lectura): rv06 y rv06b (auditoria geometrica de todas las piezas visibles y piezas aisladas)
aplicados a R07_V18D_STEP.FCStd (03/11/2026, HPGR D-083). Los scripts de V12 no se modifican.
Salidas en revision_cad_v11/resultados/: rv08_objetos_v18d.csv, rv08_pares_v18d.jsonl, rv08_resumen_v18d.json y rv08b_aisladas_v18d.json."""
AQUI = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\revision_cad_v11\scripts"
for nombre in ("rv06_auditoria_v12.py", "rv06b_aisladas_v12.py"):
    src = open(AQUI + "\\" + nombre, encoding="utf-8").read()
    for a, b in (("R07_V12_STEP.FCStd", "R07_V18D_STEP.FCStd"), ("rv06_objetos_v12", "rv08_objetos_v18d"), ("rv06_pares_v12", "rv08_pares_v18d"),
                 ("rv06_resumen_v12", "rv08_resumen_v18d"), ("rv06b_aisladas_v12", "rv08b_aisladas_v18d")):
        src = src.replace(a, b)
    assert "V12_STEP" not in src and "_v12." not in src.replace("_v12.py", "")
    exec(compile(src, nombre.replace("v12", "v18d"), "exec"), {"__name__": "__main__"})
