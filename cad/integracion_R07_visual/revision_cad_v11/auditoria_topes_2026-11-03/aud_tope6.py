# -*- coding: utf-8 -*-
"""Solo lectura: que objetos visibles ocupan z 805-885 con radio entre 630 y 715 (posibles choques de las cartelas interiores al girar)."""
import json
import math

import FreeCAD as App

R07 = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual"
SC = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\revision_cad_v11\auditoria_topes_2026-11-03"
doc = App.openDocument(R07 + r"\cad\R07_V18C_STEP.FCStd", True)
res = {}
for o in doc.Objects:
    if not hasattr(o, "Shape") or not o.Visibility or o.isDerivedFrom("App::DocumentObjectGroup") or o.Shape.Volume <= 0:
        continue
    b = o.Shape.BoundBox
    if b.ZMax < 805 or b.ZMin > 885:
        continue
    # radio minimo y maximo por vertices y caras (cota por caja)
    xs = (b.XMin, b.XMax)
    ys = (b.YMin, b.YMax)
    rmax = max(math.hypot(x, y) for x in xs for y in ys)
    rmin = 0.0 if (b.XMin <= 0 <= b.XMax and b.YMin <= 0 <= b.YMax) else min(math.hypot(x if not (b.XMin <= 0 <= b.XMax) else 0, y if not (b.YMin <= 0 <= b.YMax) else 0) for x in xs for y in ys)
    if rmax < 630 or rmin > 715:
        continue
    g = [q.Label for q in o.InList if q.isDerivedFrom("App::DocumentObjectGroup")]
    res.setdefault(g[0] if g else "(sin grupo)", []).append([o.Label, round(rmin), round(rmax), round(b.ZMin), round(b.ZMax)])
json.dump(res, open(SC + r"\aud_tope6.json", "w", encoding="utf-8"), indent=0, ensure_ascii=False)
print("LISTO")
