# -*- coding: utf-8 -*-
"""C1, revision V17B (03/11/2026): el presupuesto de c1_presupuesto.py (que no se modifica) con tres cambios:
  1. metrado del CAD R07 V17B (c2_metrado_cad_v17b.py);
  2. pedestales del riel con la masa del CAD V17B (placas, columna y faldones de D-073) en lugar de la formula de c1;
  3. corrige el titulo de tabla_beneficio_requerido.tex: el "%%" sin formatear dejaba "% anual}" como comentario de LaTeX
     y el \\caption sin cerrar (la tabla no compilaba).
Salidas: presupuesto/resultados/PRESUPUESTO_R07_V17B.json y 05_ENTREGABLES_TESIS/insumos_P3/tabla_presupuesto_completo_v17b.tex
y tabla_beneficio_requerido_v17b.tex (las de V16B quedan como estaban)."""
import os
import sys

AQUI = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\presupuesto\scripts"
src = open(os.path.join(AQUI, "c1_presupuesto.py"), encoding="utf-8").read()
cambios = [
    ('"METRADO_CAD_V16B.json"', '"METRADO_CAD_V17B.json"', 1),
    ('"PRESUPUESTO_R07_V16B.json"', '"PRESUPUESTO_R07_V17B.json"', 1),
    ('"tabla_presupuesto_completo.tex"', '"tabla_presupuesto_completo_v17b.tex"', 1),
    ('TEX.with_name("tabla_beneficio_requerido.tex")', 'TEX.with_name("tabla_beneficio_requerido_v17b.tex")', 1),
    ("al 10\\\\,\\\\%% anual}", "al 10\\\\,\\\\% anual}", 1),
    ("m_ped = 24 * (0.300 * 0.280 * 0.020 + 0.250 * 0.280 * 0.020) * 7930 + 24 * 0.165 * 17.8",
     'm_ped = kg(lambda p: p["grupo"] == "R07_V17_PEDESTALES_RIEL" and p["pieza"].startswith(("R07_V17_PEDESTAL", "R07_V17_FALDON")), 7.93)', 1),
    ('"D-073: placa base 300x280x20, placa superior 250x280x20 y SHS 120x5 de 165 mm"',
     '"CAD V17B, grupo R07_V17_PEDESTALES_RIEL: placas, columna SHS 120x5 y faldones (D-073)"', 1),
    ("c1_presupuesto.py (02/11/2026)", "c2_presupuesto_v17b.py (03/11/2026, R07 V17B)", 1),
    ("c1_presupuesto.py (HPGR D-077)", "c2_presupuesto_v17b.py (HPGR D-077, R07 V17B)", 1),
]
for a, b, n in cambios:
    assert src.count(a) == n, (a, src.count(a))
    src = src.replace(a, b)
src = src.replace("CAD V16B", "CAD V17B")
__file__ = os.path.join(AQUI, "c1_presupuesto.py")
sys.argv = [__file__]
exec(compile(src, "c1_presupuesto_V17B", "exec"))
