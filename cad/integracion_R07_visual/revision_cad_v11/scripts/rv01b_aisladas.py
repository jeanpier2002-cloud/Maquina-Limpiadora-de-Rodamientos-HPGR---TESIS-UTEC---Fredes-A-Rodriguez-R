# -*- coding: utf-8 -*-
"""Revision del CAD R07 V11, fase 1b (freecadcmd): para cada pieza aislada y cada grupo desconectado de rv01, distancia a la
pieza mas cercana (y cual es) y, para los grupos, si su punto mas bajo apoya en la cara superior de la referencia de piso.
Solo lectura. Salida: revision_cad_v11/resultados/rv01b_aisladas.json."""
import json

import FreeCAD as App

R07 = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual"
OUT = R07 + r"\revision_cad_v11\resultados"
res = json.load(open(OUT + r"\rv01_resumen.json", encoding="utf-8"))
doc = App.openDocument(R07 + r"\cad\R07_V11_STEP.FCStd")
por_label = {}
for o in doc.Objects:
    if o.TypeId == "Part::Feature" and hasattr(o, "Shape") and not o.Shape.isNull() and o.Shape.Solids and o.Visibility:
        por_label.setdefault(o.Label, o)
superados = set()
for g in doc.Objects:
    if "SUPERAD" in g.Label.upper() and hasattr(g, "Group"):
        superados |= {o.Label for o in g.Group}
activos = [o for l, o in por_label.items() if l not in superados]
piso = por_label.get("Floor and foundation reference")
z_piso = piso.Shape.BoundBox.ZMax if piso else None


def cercana(labels, radio=400.0):
    """distancia minima desde el conjunto 'labels' a cualquier otra pieza activa (cajas a menos de 'radio')."""
    forma = [por_label[l].Shape for l in labels if l in por_label]
    bb = forma[0].BoundBox
    for s in forma[1:]:
        bb.add(s.BoundBox)
    mejor = (1e9, None)
    for o in activos:
        if o.Label in labels:
            continue
        b = o.Shape.BoundBox
        if (b.XMax < bb.XMin - radio or b.XMin > bb.XMax + radio or b.YMax < bb.YMin - radio or b.YMin > bb.YMax + radio or
                b.ZMax < bb.ZMin - radio or b.ZMin > bb.ZMax + radio):
            continue
        for s in forma:
            try:
                d = s.distToShape(o.Shape)[0]
            except Exception:
                continue
            if d < mejor[0]:
                mejor = (d, o.Label)
    return round(mejor[0], 2), mejor[1], [round(v, 1) for v in (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax)]


salida = {"z_cara_superior_piso_referencia": z_piso, "aisladas": [], "grupos": []}
for l in res["aisladas"]:
    d, n, bb = cercana([l])
    salida["aisladas"].append({"pieza": l, "dist_min_mm": d, "mas_cercana": n, "caja": bb})
for grupo in res["grupos_sin_piso"]:
    ls = [x for x in grupo if x != "..."]
    d, n, bb = cercana(ls)
    salida["grupos"].append({"piezas": ls, "dist_min_mm": d, "mas_cercana": n, "caja": bb,
                             "apoya_en_piso": (z_piso is not None and abs(bb[4] - z_piso) <= 1.0)})
json.dump(salida, open(OUT + r"\rv01b_aisladas.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
App.closeDocument(doc.Name)
print("RV01B OK")
