# -*- coding: utf-8 -*-
"""C1, revision V18 (03/11/2026): el presupuesto de c1_presupuesto.py (que no se modifica) sobre el CAD R07 V18, con el soporte
superior aligerado K32 (HPGR D-080). Aplica los mismos cambios de c2_presupuesto_v17b.py (pedestales del CAD y titulo de la tabla de
beneficio corregido) y suma al soporte el grupo nuevo R07_V18_SOPORTE_K32 (las barras de V12 reemplazadas estan en NO_VIGENTE_V18,
que el metrado no cuenta).
Uso: freecadcmd c3_presupuesto_v18.py metrado   -> resultados/METRADO_CAD_V18.json
     python c3_presupuesto_v18.py               -> resultados/PRESUPUESTO_R07_V18.json e insumos_P3/tabla_*_v18.tex"""
import os
import sys

AQUI = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\presupuesto\scripts"
if "metrado" in sys.argv:
    src = open(os.path.join(AQUI, "c1_metrado_cad.py"), encoding="utf-8").read()
    for a, b in (('"R07_V16B_STEP.FCStd"', '"R07_V18_STEP.FCStd"'), ('"METRADO_CAD_V16B.json"', '"METRADO_CAD_V18.json"')):
        assert src.count(a) == 1, a
        src = src.replace(a, b)
    __file__ = os.path.join(AQUI, "c1_metrado_cad.py")
    exec(compile(src, "c1_metrado_cad_V18", "exec"))
else:
    src = open(os.path.join(AQUI, "c1_presupuesto.py"), encoding="utf-8").read()
    cambios = [
        ('"METRADO_CAD_V16B.json"', '"METRADO_CAD_V18.json"'),
        ('"PRESUPUESTO_R07_V16B.json"', '"PRESUPUESTO_R07_V18.json"'),
        ('"tabla_presupuesto_completo.tex"', '"tabla_presupuesto_completo_v18.tex"'),
        ('TEX.with_name("tabla_beneficio_requerido.tex")', 'TEX.with_name("tabla_beneficio_requerido_v18.tex")'),
        ("al 10\\\\,\\\\%% anual}", "al 10\\\\,\\\\% anual}"),
        ("m_ped = 24 * (0.300 * 0.280 * 0.020 + 0.250 * 0.280 * 0.020) * 7930 + 24 * 0.165 * 17.8",
         'm_ped = kg(lambda p: p["grupo"] == "R07_V17_PEDESTALES_RIEL" and p["pieza"].startswith(("R07_V17_PEDESTAL", "R07_V17_FALDON")), 7.93)'),
        ('"D-073: placa base 300x280x20, placa superior 250x280x20 y SHS 120x5 de 165 mm"',
         '"CAD V18, grupo R07_V17_PEDESTALES_RIEL: placas, columna SHS 120x5 y faldones (D-073)"'),
        ('kg(g("R07_V12_SOPORTE_MARCO_CABINA"))', 'kg(g("R07_V12_SOPORTE_MARCO_CABINA")) + kg(g("R07_V18_SOPORTE_K32"))'),
        ('"Soporte superior (HPGR D-065), cartucho', '"Soporte superior aligerado K32 (HPGR D-080), cartucho'),
        ("c1_presupuesto.py (02/11/2026)", "c3_presupuesto_v18.py (03/11/2026, R07 V18)"),
        ("c1_presupuesto.py (HPGR D-077)", "c3_presupuesto_v18.py (HPGR D-077, R07 V18)"),
    ]
    for a, b in cambios:
        assert src.count(a) == 1, (a, src.count(a))
        src = src.replace(a, b)
    src = src.replace("CAD V16B", "CAD V18")
    __file__ = os.path.join(AQUI, "c1_presupuesto.py")
    sys.argv = [__file__]
    exec(compile(src, "c1_presupuesto_V18", "exec"))
