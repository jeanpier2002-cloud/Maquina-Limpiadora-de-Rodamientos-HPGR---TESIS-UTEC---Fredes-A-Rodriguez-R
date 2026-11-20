# -*- coding: utf-8 -*-
"""Solo lectura. Tope de 190 grados: que lo sostiene. Secciones radiales y datos de las piezas de K2-M bajo el tope."""
import json
import math

import FreeCAD as App
import Part

R07 = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual"
SC = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\revision_cad_v11\auditoria_topes_2026-11-03"
doc = App.openDocument(R07 + r"\cad\R07_V18C_STEP.FCStd", True)
V = App.Vector
uno = lambda l: doc.getObjectsByLabel(l)[0]
tope = uno("R061_K2M_2_TOPE_RETENCION_FIJO").Shape
c = tope.BoundBox.Center
ANG = 189.86
rot = App.Placement(V(0, 0, 0), App.Rotation(V(0, 0, 1), -ANG))


def loc(sh):
    s = sh.copy(); s.Placement = rot.multiply(s.Placement); return s


def caja(sh):
    b = sh.BoundBox
    return [round(v, 1) for v in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)]


sal = {"angulo_centro": round(math.degrees(math.atan2(c.y, c.x)) % 360, 2), "tope_local": caja(loc(tope)),
       "verts": sorted({tuple(round(q, 1) for q in (v.X, v.Y, v.Z)) for v in loc(tope).Vertexes})}
vec = []
for o in doc.Objects:
    if not hasattr(o, "Shape") or not o.Visibility or o.isDerivedFrom("App::DocumentObjectGroup") or o.Shape.Volume <= 0:
        continue
    if o.Label == "R061_K2M_2_TOPE_RETENCION_FIJO":
        continue
    b = o.Shape.BoundBox
    bb = tope.BoundBox
    if b.XMin > bb.XMax + 80 or b.XMax < bb.XMin - 80 or b.YMin > bb.YMax + 80 or b.YMax < bb.YMin - 80 or b.ZMin > 930 or b.ZMax < 640:
        continue
    d, pares, _ = tope.distToShape(o.Shape)
    r = {"o": o.Label, "dist": round(d, 2), "comun": round(tope.common(o.Shape).Volume, 1), "caja_local": caja(loc(o.Shape)), "grupo": [g.Label for g in o.InList if g.isDerivedFrom("App::DocumentObjectGroup")][:1]}
    if d < 0.01:
        r["contactos"] = [[round(q, 1) for q in rot.multVec(a)] for a, _b in pares[:6]]
    vec.append(r)
sal["cercanos"] = sorted(vec, key=lambda x: x["dist"])[:24]
# secciones radiales
sec = {}
ax = V(-math.sin(math.radians(ANG)), math.cos(math.radians(ANG)), 0)
for t in (0.0, -32.0, 32.0):
    q = {}
    for o in doc.Objects:
        if not hasattr(o, "Shape") or not o.Visibility or o.isDerivedFrom("App::DocumentObjectGroup") or o.Shape.Volume <= 0:
            continue
        b = o.Shape.BoundBox
        if b.XMin > -500 or b.XMax < -1050 or abs(b.Center.y) > 900 or b.ZMin > 960 or b.ZMax < 640:
            continue
        try:
            w = o.Shape.slice(ax, t)
        except Exception:
            continue
        if w:
            q[o.Label] = [[[round(p.x, 1), round(p.z, 1)] for p in [rot.multVec(p) for p in wi.discretize(Distance=3.0)]] for wi in w]
    sec[str(t)] = q
json.dump(sec, open(SC + r"\aud_tope4_secc.json", "w", encoding="utf-8"))
json.dump(sal, open(SC + r"\aud_tope4.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("LISTO")
