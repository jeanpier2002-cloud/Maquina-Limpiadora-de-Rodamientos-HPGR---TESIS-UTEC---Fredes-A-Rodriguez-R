# -*- coding: utf-8 -*-
"""Solo lectura: objetos visibles de la V18D por grupo, para definir los subconjuntos de MES-000 rev. B y el barrido."""
import json
import FreeCAD as App
R07 = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual"
doc = App.openDocument(R07 + r"\cad\R07_V18D_STEP.FCStd", True)
vis = json.load(open(R07 + r"\resultados\VISIBILIDAD_R07_V18D.json", encoding="utf-8"))
gr = {}
for o in doc.Objects:
    if o.isDerivedFrom("App::DocumentObjectGroup") or not hasattr(o, "Shape") or o.Shape.isNull() or not o.Shape.Solids:
        continue
    if not vis.get(o.Name, True) or "RETRAIDO" in o.Label:
        continue
    g = [q.Label for q in o.InList if q.isDerivedFrom("App::DocumentObjectGroup")]
    b = o.Shape.BoundBox
    gr.setdefault(g[0] if g else "(sin)", []).append((o.Label, [round(v) for v in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)]))
sal = {k: v for k, v in sorted(gr.items())}
json.dump(sal, open(r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\revision_cad_v11\auditoria_topes_2026-11-03\lista_mesa.json", "w", encoding="utf-8"), indent=0, ensure_ascii=False)
print("LISTO")
