# -*- coding: utf-8 -*-
"""C1 (obs. 3.8, presupuesto): metrado desde el CAD R07 V16B (freecadcmd, solo lectura).
Vuelca cada solido visible con su grupo, volumen, caja y area de la cara mayor, para que c1_presupuesto.py lo clasifique en
partidas. El volumen del CAD solo es masa cuando la pieza esta modelada como pieza real (perfiles, chapas, tubos); las
envolventes (muros de contexto, equipos comerciales, concreto) se marcan alli y se costean de otra forma.
Salida: presupuesto/resultados/METRADO_CAD_V16B.json"""
import json
import os

import FreeCAD as App

R07 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CAD = os.path.join(R07, "cad", "R07_V16B_STEP.FCStd")
SALIDA = os.path.join(R07, "presupuesto", "resultados", "METRADO_CAD_V16B.json")
EXCLUIR_GRUPOS = {"RODAMIENTO_SKF_REAL", "REFERENCIA_ENVOLVENTE_V573", "R06_REFERENCIAS"}

doc = App.openDocument(CAD)
filas = []
for g in doc.Objects:
    if g.TypeId != "App::DocumentObjectGroup" or g.Label in EXCLUIR_GRUPOS or g.Label.startswith("NO_VIGENTE"):
        continue
    for o in g.Group:
        if not hasattr(o, "Shape") or o.TypeId.startswith("App::") or not o.Visibility or o.Shape.isNull():
            continue
        try:
            s = o.Shape
            v = s.Volume
            bb = s.BoundBox
            cara = max((f.Area for f in s.Faces), default=0.0)
        except Exception:
            continue
        if v <= 0:
            continue
        filas.append({"grupo": g.Label, "pieza": o.Label, "volumen_cm3": round(v / 1000, 3), "area_cara_mayor_m2": round(cara / 1e6, 4),
                      "caja_mm": [round(x, 1) for x in (bb.XLength, bb.YLength, bb.ZLength)],
                      "centro_mm": [round(x, 1) for x in (bb.Center.x, bb.Center.y, bb.Center.z)], "solidos": len(s.Solids)})
os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
with open(SALIDA, "w", encoding="utf-8") as f:
    json.dump({"cad": CAD, "piezas": filas}, f, ensure_ascii=False, indent=1)
print("piezas", len(filas))
