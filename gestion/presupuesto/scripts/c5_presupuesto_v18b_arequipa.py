# -*- coding: utf-8 -*-
"""C1, variante V18B AREQUIPA (16/11/2026): el presupuesto de c4_presupuesto_v18b.py (que no se modifica) con los datos que Jean
Fredes adopto en la v3 de la P3 (`Downloads/Prismm/CAMBIOS_V3_RECORTES_2026-11-16.md`), para repartir la mano de obra por partida en
lugar de la fila de ajuste de -3 201 de su Tabla 9.4:
  - sueldo del soldador homologado: S/ 3 293 al mes (Indeed, Arequipa; extremo superior) -> tarifa de taller S/ 47,5/h;
  - motorreductor SF47: US$ 1 315,83 (MROSupply);
  - rotulo de la bomba: CRN 15-3 con motor de 4 kW a 60 Hz (el precio no cambia: es la CR 10-06 x 1,4 [HIPOTESIS]).
Las fuentes de Jean no se verificaron en este paso [VERIFICAR]. Lee resultados/METRADO_CAD_V18B.json (no necesita FreeCAD).
Salidas nuevas (no sobrescribe nada): resultados/PRESUPUESTO_R07_V18B_AREQUIPA.json e insumos_P3/tabla_*_v18b_arequipa.tex.
Uso: python c5_presupuesto_v18b_arequipa.py"""
import os
import sys

AQUI = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\presupuesto\scripts"
src = open(os.path.join(AQUI, "c4_presupuesto_v18b.py"), encoding="utf-8").read()
extra = (
    "        ('\"sueldo_soldador_mes\": (3500.0, \"PEN\", \"Aviso de soldador homologado en SJL, Lima, 2026 (cazvid.com)\", \"FUENTE\")',\n"
    "         '\"sueldo_soldador_mes\": (3293.0, \"PEN\", \"Indeed, soldador en Arequipa, extremo superior (dato de Jean, 16/11/2026) [VERIFICAR]\", \"FUENTE\")'),\n"
    "        ('\"motorreductor_SF47\": (1500.0, \"USD\", \"S37 con freno US$ 1226,14 (P2, mrosupply.com); el SF47 es un tamaño mayor [HIPOTESIS]\", \"HIPOTESIS\")',\n"
    "         '\"motorreductor_SF47\": (1315.83, \"USD\", \"SF47 US$ 1315,83 (MROSupply, dato de Jean, 16/11/2026) [VERIFICAR]\", \"FUENTE\")'),\n"
    "        ('\"Bomba Grundfos CRN 15-3 en 316 con motor de 3 kW\"', '\"Bomba Grundfos CRN 15-3 en 316 con motor de 4 kW (60 Hz)\"'),\n"
    "        ('c4_presupuesto_v18b.py (03/11/2026, R07 V18B)', 'c5_presupuesto_v18b_arequipa.py (16/11/2026, R07 V18B, Arequipa)'),\n"
    "    ]\n"
)
ancla = '        ("c1_presupuesto.py (HPGR D-077)", "c4_presupuesto_v18b.py (HPGR D-077, R07 V18B)"),\n    ]\n'
assert src.count(ancla) == 1
src = src.replace(ancla, ancla[:-6] + extra)
for a, b in (('\'"PRESUPUESTO_R07_V18B.json"\'', '\'"PRESUPUESTO_R07_V18B_AREQUIPA.json"\''),
             ('\'"tabla_presupuesto_completo_v18b.tex"\'', '\'"tabla_presupuesto_completo_v18b_arequipa.tex"\''),
             ('TEX.with_name("tabla_beneficio_requerido_v18b.tex")', 'TEX.with_name("tabla_beneficio_requerido_v18b_arequipa.tex")')):
    assert src.count(a) == 1, a
    src = src.replace(a, b)
sys.argv = [os.path.join(AQUI, "c4_presupuesto_v18b.py")]
__file__ = sys.argv[0]
exec(compile(src, "c4_presupuesto_v18b_AREQUIPA", "exec"))
