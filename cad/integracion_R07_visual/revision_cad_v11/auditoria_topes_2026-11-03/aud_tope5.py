# -*- coding: utf-8 -*-
"""Solo lectura: comprueba si una chapa de asiento de 16 mm (z 789-805) cabe bajo cada tope, sin guardar nada."""
import json
import math

import FreeCAD as App
import Part

R07 = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual"
SC = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\revision_cad_v11\auditoria_topes_2026-11-03"
doc = App.openDocument(R07 + r"\cad\R07_V18C_STEP.FCStd", True)
V = App.Vector
uno = lambda l: doc.getObjectsByLabel(l)[0]
PIV = 776.0
sal = {}
for nom, ang, viga, t_off, n in (("60", 60.0, "R07_V16_M06_W6X9", 0.0, 1), ("300", 300.0, "R07_V16_M05_W6X9", 0.0, 3), ("190", 189.86, None, 1.8, 2)):
    rot = App.Placement(V(0, 0, 0), App.Rotation(V(0, 0, 1), ang))
    ch = Part.makeBox(812 - 710, 80, 16, V(710, -40 + t_off, 789))
    ch = ch.cut(Part.makeCylinder(30, 40, V(PIV, 0, 780)))
    ch.Placement = rot
    ch = ch.copy()
    if viga:
        ch = ch.cut(uno(viga).Shape)
    bb = ch.BoundBox
    cho = []
    for o in doc.Objects:
        if not hasattr(o, "Shape") or not o.Visibility or o.isDerivedFrom("App::DocumentObjectGroup") or o.Shape.Volume <= 0:
            continue
        b = o.Shape.BoundBox
        if b.XMin > bb.XMax or b.XMax < bb.XMin or b.YMin > bb.YMax or b.YMax < bb.YMin or b.ZMin > bb.ZMax or b.ZMax < bb.ZMin:
            continue
        v = ch.common(o.Shape).Volume
        if v > 0.5:
            cho.append({"o": o.Label, "comun": round(v, 1)})
    # posicion real del montante respecto del angulo supuesto
    m = uno("R061_K2M_%d_MONTANTE_FIJO" % n).Shape.BoundBox.Center
    ret = uno("R061_RET_%d_SOPORTE_FIJO" % n).Shape.BoundBox
    # huecos sobre r 710-812 en la seccion de la chapa
    sal[nom] = {"vol_mm3": round(ch.Volume, 0), "masa_kg": round(ch.Volume * 7.85e-6, 2), "choques": cho,
                "centro_montante_r_ang": [round(math.hypot(m.x, m.y), 1), round(math.degrees(math.atan2(m.y, m.x)) % 360, 2)],
                "ret_z": [ret.ZMin, ret.ZMax]}
json.dump(sal, open(SC + r"\aud_tope5.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("LISTO")
