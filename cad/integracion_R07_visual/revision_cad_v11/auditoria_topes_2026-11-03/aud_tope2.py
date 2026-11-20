# -*- coding: utf-8 -*-
"""Solo lectura: vecinos del tope de 60 grados en el marco radial (x radial, y tangencial) y seccion del conjunto."""
import json

import FreeCAD as App
import Part

R07 = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual"
doc = App.openDocument(R07 + r"\cad\R07_V18C_STEP.FCStd", True)
V = App.Vector
uno = lambda l: doc.getObjectsByLabel(l)[0]
rot = App.Placement(V(0, 0, 0), App.Rotation(V(0, 0, 1), -60.0))
sal = {}
s = uno("CTX_BEARING_RETENTION_STOP_01").Shape


def local(sh):
    c = sh.copy(); c.Placement = rot.multiply(c.Placement); return c


def caja(sh):
    b = sh.BoundBox
    return [round(v, 2) for v in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)]


sal["tope_local"] = caja(local(s))
sal["tope_verts_local"] = sorted({tuple(round(q, 2) for q in (v.X, v.Y, v.Z)) for v in local(s).Vertexes})
for lab in ("R061_K2M_1_MONTANTE_FIJO", "R061_RET_1_SOPORTE_FIJO", "R07_V16_M06_W6X9"):
    o = uno(lab)
    d, pares, _ = s.distToShape(o.Shape)
    pts = []
    for a, b in pares[:12]:
        pa = rot.multVec(a)
        pts.append([round(pa.x, 2), round(pa.y, 2), round(pa.z, 2)])
    r = {"grupos": [g.Label for g in o.InList if g.isDerivedFrom("App::DocumentObjectGroup")], "caja_maquina": caja(o.Shape), "caja_local": caja(local(o.Shape)), "vol": round(o.Shape.Volume, 1), "contactos_local": pts, "vis": bool(o.Visibility)}
    if lab != "R07_V16_M06_W6X9":
        r["verts_local"] = sorted({tuple(round(q, 1) for q in (v.X, v.Y, v.Z)) for v in local(o.Shape).Vertexes})[:40]
    sal[lab] = r
# ¿que hay exactamente bajo la huella de las cartelas? seccion en z = 804 en una caja amplia (marco de maquina)
bb = s.BoundBox
vec = []
for o in doc.Objects:
    if not hasattr(o, "Shape") or not o.Visibility or o.Shape.Volume <= 0 or o.isDerivedFrom("App::DocumentObjectGroup"):
        continue
    b = o.Shape.BoundBox
    if b.XMin > bb.XMax + 60 or b.XMax < bb.XMin - 60 or b.YMin > bb.YMax + 60 or b.YMax < bb.YMin - 60 or b.ZMin > 930 or b.ZMax < 600:
        continue
    vec.append({"o": o.Label, "caja_local": caja(local(o.Shape)), "vol": round(o.Shape.Volume, 0), "dist": round(s.distToShape(o.Shape)[0], 2), "grupos": [g.Label for g in o.InList if g.isDerivedFrom("App::DocumentObjectGroup")]})
sal["cercanos"] = sorted(vec, key=lambda x: x["dist"])[:30]
json.dump(sal, open(r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\revision_cad_v11\auditoria_topes_2026-11-03\aud_tope2.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("LISTO")
