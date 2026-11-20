# -*- coding: utf-8 -*-
"""Solo lectura: como apoya realmente el tope de retencion sobre el ala de M06 en R07 V18C."""
import json
import math

import FreeCAD as App
import Part

R07 = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual"
doc = App.openDocument(R07 + r"\cad\R07_V18C_STEP.FCStd", True)
V = App.Vector
uno = lambda l: doc.getObjectsByLabel(l)[0]
sal = {}
for tope, viga, ang in (("CTX_BEARING_RETENTION_STOP_01", "R07_V16_M06_W6X9", 60.0), ("CTX_BEARING_RETENTION_STOP_03", "R07_V16_M05_W6X9", 300.0)):
    s = uno(tope).Shape
    m = uno(viga).Shape
    c = s.common(m)
    r = {"vol_comun": round(c.Volume, 1), "caja_comun": [round(v, 2) for v in (c.BoundBox.XMin, c.BoundBox.XMax, c.BoundBox.YMin, c.BoundBox.YMax, c.BoundBox.ZMin, c.BoundBox.ZMax)] if c.Volume > 0 else None}
    # huella del tope en z = 805 (cara superior del ala) y en z = 802
    for z in (805.5, 803.0):
        pl = Part.makeBox(4000, 4000, 0.01, V(-2000, -2000, z))
        sec = s.common(pl)
        sec_m = m.common(Part.makeBox(4000, 4000, 0.01, V(-2000, -2000, min(z, 804.9))))
        r["area_tope_z%.1f" % z] = round(sec.Volume / 0.01, 1)
        r["area_ala_z%.1f" % z] = round(sec_m.Volume / 0.01, 1)
    # marco local del tope: x radial, y tangencial, origen en el centro de la placa en R720
    rot = App.Placement(V(0, 0, 0), App.Rotation(V(0, 0, 1), -ang))
    sl = s.copy(); sl.Placement = rot.multiply(sl.Placement)
    cl = c.copy(); cl.Placement = rot.multiply(cl.Placement)
    ml = m.copy(); ml.Placement = rot.multiply(ml.Placement)
    r["caja_tope_marco_radial"] = [round(v, 2) for v in (sl.BoundBox.XMin, sl.BoundBox.XMax, sl.BoundBox.YMin, sl.BoundBox.YMax, sl.BoundBox.ZMin, sl.BoundBox.ZMax)]
    if c.Volume > 0:
        r["vertices_comun_marco_radial"] = sorted({tuple(round(q, 2) for q in (v.X, v.Y, v.Z)) for v in cl.Vertexes})
        r["vertices_comun_maquina"] = sorted({tuple(round(q, 2) for q in (v.X, v.Y, v.Z)) for v in c.Vertexes})
    # que objetos visibles tocan el tope (o estan a < 2 mm)
    vec = []
    bb = s.BoundBox
    for o in doc.Objects:
        if not hasattr(o, "Shape") or o is uno(tope) or not o.Visibility or o.Shape.Volume <= 0:
            continue
        if o.isDerivedFrom("App::DocumentObjectGroup"):
            continue
        b = o.Shape.BoundBox
        if b.XMin > bb.XMax + 2 or b.XMax < bb.XMin - 2 or b.YMin > bb.YMax + 2 or b.YMax < bb.YMin - 2 or b.ZMin > bb.ZMax + 2 or b.ZMax < bb.ZMin - 2:
            continue
        try:
            d = s.distToShape(o.Shape)[0]
        except Exception:
            d = None
        if d is not None and d < 2.0:
            vec.append({"obj": o.Label, "dist": round(d, 2), "comun": round(s.common(o.Shape).Volume, 1)})
    r["vecinos_menos_2mm"] = vec
    # bajo el tope: seccion del ala y de lo que haya a z 790-800 en la huella de las cartelas
    sal[tope] = r
json.dump(sal, open(r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\revision_cad_v11\auditoria_topes_2026-11-03\aud_tope.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("LISTO")
