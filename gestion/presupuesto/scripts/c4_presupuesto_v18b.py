# -*- coding: utf-8 -*-
"""C1, revision V18B (03/11/2026): el presupuesto de c1_presupuesto.py (que no se modifica) sobre el CAD R07 V18B, con las bases,
anclajes y uniones del soporte K32 (HPGR D-081) y las correas del techo. Aplica los mismos cambios de c3_presupuesto_v18.py y ademas:
  - soporte = grupos R07_V12_SOPORTE_MARCO_CABINA + R07_V18_SOPORTE_K32 + R07_V18B_BASES_UNIONES_K32 (lo reemplazado esta en
    NO_VIGENTE_*, que el metrado no cuenta);
  - 16 anclajes M16 A4-70 del soporte con 1 cartucho de adhesivo (antes no estaban costeados);
  - silletas de las bandejas: R07_V18B_SILLETAS_BANDEJAS se suma donde c1 contaba R07_V12_CORRECCIONES;
  - correas del techo RHS80x40x3 inox (grupo R07_V18B_CORREAS_TECHO) como partida aparte de la cabina.
Uso: freecadcmd c4_presupuesto_v18b.py metrado   -> resultados/METRADO_CAD_V18B.json
     python c4_presupuesto_v18b.py               -> resultados/PRESUPUESTO_R07_V18B.json e insumos_P3/tabla_*_v18b.tex"""
import os
import sys

AQUI = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\presupuesto\scripts"
if "metrado" in sys.argv:
    src = open(os.path.join(AQUI, "c1_metrado_cad.py"), encoding="utf-8").read()
    for a, b in (('"R07_V16B_STEP.FCStd"', '"R07_V18B_STEP.FCStd"'), ('"METRADO_CAD_V16B.json"', '"METRADO_CAD_V18B.json"')):
        assert src.count(a) == 1, a
        src = src.replace(a, b)
    __file__ = os.path.join(AQUI, "c1_metrado_cad.py")
    exec(compile(src, "c1_metrado_cad_V18B", "exec"))
else:
    src = open(os.path.join(AQUI, "c1_presupuesto.py"), encoding="utf-8").read()
    cambios = [
        ('"METRADO_CAD_V16B.json"', '"METRADO_CAD_V18B.json"'),
        ('"PRESUPUESTO_R07_V16B.json"', '"PRESUPUESTO_R07_V18B.json"'),
        ('"tabla_presupuesto_completo.tex"', '"tabla_presupuesto_completo_v18b.tex"'),
        ('TEX.with_name("tabla_beneficio_requerido.tex")', 'TEX.with_name("tabla_beneficio_requerido_v18b.tex")'),
        ("al 10\\\\,\\\\%% anual}", "al 10\\\\,\\\\% anual}"),
        ("m_ped = 24 * (0.300 * 0.280 * 0.020 + 0.250 * 0.280 * 0.020) * 7930 + 24 * 0.165 * 17.8",
         'm_ped = kg(lambda p: p["grupo"] == "R07_V17_PEDESTALES_RIEL" and p["pieza"].startswith(("R07_V17_PEDESTAL", "R07_V17_FALDON")), 7.93)'),
        ('"D-073: placa base 300x280x20, placa superior 250x280x20 y SHS 120x5 de 165 mm"',
         '"CAD V18B, grupo R07_V17_PEDESTALES_RIEL: placas, columna SHS 120x5 y faldones (D-073)"'),
        ('m_mesa += kg(g("R07_V12_CORRECCIONES"))', 'm_mesa += kg(g("R07_V12_CORRECCIONES")) + kg(n("R07_V18B_SILLETAS"))'),
        ('kg(g("R07_V12_SOPORTE_MARCO_CABINA"))',
         'kg(g("R07_V12_SOPORTE_MARCO_CABINA")) + kg(g("R07_V18_SOPORTE_K32")) + kg(g("R07_V18B_BASES_UNIONES_K32"))'),
        ('"Soporte superior (HPGR D-065), cartucho', '"Soporte superior aligerado K32 con bases y uniones (HPGR D-080 y D-081), cartucho'),
        ('    # ---------------- C. Hidraulica y filtrado ----------------',
         '    com(B, "Anclajes M16 A4-70 del soporte superior (16; HPGR D-081)", "anclaje_M16_A4", 16)\n'
         '    com(B, "Adhesivo con calificacion sismica para los 16 anclajes del soporte (~15 ml c/u)", "adhesivo_500ml", 1)\n\n'
         '    # ---------------- C. Hidraulica y filtrado ----------------'),
        ('    com(E, "Motorreductor de la puerta',
         '    fab(E, "Correas del techo RHS 80x40x3 en inox 304 (4)", kg(g("R07_V18B_CORREAS_TECHO"), 7.93), "inox", "inox_chapa",\n'
         '        "CAD V18B, grupo R07_V18B_CORREAS_TECHO (P1-35)")\n'
         '    com(E, "Motorreductor de la puerta'),
        ("c1_presupuesto.py (02/11/2026)", "c4_presupuesto_v18b.py (03/11/2026, R07 V18B)"),
        ("c1_presupuesto.py (HPGR D-077)", "c4_presupuesto_v18b.py (HPGR D-077, R07 V18B)"),
    ]
    for a, b in cambios:
        assert src.count(a) == 1, (a, src.count(a))
        src = src.replace(a, b)
    src = src.replace("CAD V16B", "CAD V18B")
    __file__ = os.path.join(AQUI, "c1_presupuesto.py")
    sys.argv = [__file__]
    exec(compile(src, "c1_presupuesto_V18B", "exec"))
