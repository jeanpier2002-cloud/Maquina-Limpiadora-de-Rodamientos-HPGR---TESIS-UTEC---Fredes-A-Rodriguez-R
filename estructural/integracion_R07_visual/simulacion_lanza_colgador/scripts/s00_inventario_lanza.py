# -*- coding: utf-8 -*-
"""Inventario (solo lectura, sobre una COPIA del CAD R07 V18D) de las piezas de la zona lanza, carro, mástil, tambor y transversal:
tipo, sólidos, volumen, caja y distancias entre piezas vecinas (qué se toca y qué tiene holgura). Ejecutar con freecadcmd, con la
variable de entorno HPGR_COPIA_V18D apuntando a la copia. Escribe geometria/inventario_lanza.json."""
import json
import os
import FreeCAD

COPIA = os.environ.get("HPGR_COPIA_V18D")
SAL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "geometria", "inventario_lanza.json")
doc = FreeCAD.openDocument(COPIA)
fil = []
for o in doc.Objects:
    if not hasattr(o, "Shape") or o.Shape.isNull() or not o.Shape.Solids:
        continue
    if o.TypeId == "App::DocumentObjectGroup" or "GUARDADA" in o.Label.upper():
        continue
    b = o.Shape.BoundBox
    if b.XMin > -330 and b.XMax < 330 and b.YMin > -130 and b.YMax < 600 and b.ZMin > 780 and b.ZMax < 3600:
        fil.append({"nombre": o.Name, "etiqueta": o.Label, "tipo": o.TypeId, "visible": bool(getattr(o, "Visibility", True)),
                    "solidos": len(o.Shape.Solids), "vol_mm3": round(o.Shape.Volume, 0),
                    "caja": [round(v, 2) for v in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)]})
fil.sort(key=lambda f: -f["caja"][5])
vis = [f for f in fil if f["visible"] and f["tipo"] != "Part::Compound"]
par = []
for i in range(len(vis)):
    for j in range(i + 1, len(vis)):
        a, c = vis[i]["caja"], vis[j]["caja"]
        if a[0] - 3 > c[1] or c[0] - 3 > a[1] or a[2] - 3 > c[3] or c[2] - 3 > a[3] or a[4] - 3 > c[5] or c[4] - 3 > a[5]:
            continue
        sa, sc = doc.getObject(vis[i]["nombre"]).Shape, doc.getObject(vis[j]["nombre"]).Shape
        d = sa.distToShape(sc)[0]
        sol = sa.common(sc).Volume if d < 1e-6 else 0.0
        par.append([vis[i]["etiqueta"], vis[j]["etiqueta"], round(d, 3), round(sol, 1)])
json.dump({"objetos": fil, "pares": par}, open(SAL, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
os._exit(0)
