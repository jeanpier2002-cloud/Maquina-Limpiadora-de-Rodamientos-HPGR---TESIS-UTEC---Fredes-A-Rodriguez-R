# -*- coding: utf-8 -*-
"""Solo lectura. (1) Secciones en planta y radial alrededor de los topes de 60 y 190 grados. (2) Prueba de interferencia de
cartelas interiores candidatas (lado del rodamiento, bajo el asiento) con todo lo que hay en la V18C, visible o no."""
import json
import math

import FreeCAD as App
import Part

R07 = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual"
SC = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\revision_cad_v11\auditoria_topes_2026-11-03"
doc = App.openDocument(R07 + r"\cad\R07_V18C_STEP.FCStd", True)
V = App.Vector
uno = lambda l: doc.getObjectsByLabel(l)[0]
sal = {}


def solidos():
    for o in doc.Objects:
        if hasattr(o, "Shape") and not o.isDerivedFrom("App::DocumentObjectGroup") and o.Shape.Volume > 0:
            yield o


def polilineas(shape, normal, d, rot):
    res = []
    try:
        wires = shape.slice(normal, d)
    except Exception:
        return res
    for w in wires:
        pts = [rot.multVec(p) for p in w.discretize(Distance=2.0)]
        res.append([[round(p.x, 2), round(p.y, 2), round(p.z, 2)] for p in pts])
    return res


def seccion(angulo, nombre, zplano, ventana):
    rot = App.Placement(V(0, 0, 0), App.Rotation(V(0, 0, 1), -angulo))
    inv = rot.inverse()
    r0, r1, t0, t1, z0, z1 = ventana
    # caja de la ventana en coordenadas de maquina
    caja = Part.makeBox(r1 - r0, t1 - t0, z1 - z0, V(r0, t0, z0))
    caja.Placement = inv
    bb = caja.BoundBox
    n = V(math.sin(math.radians(angulo)) * -1, math.cos(math.radians(angulo)), 0)    # normal del plano radial (t = cte)
    out = {"planta": {}, "radial_t0": {}, "radial_t-32": {}, "radial_t+32": {}}
    for o in solidos():
        if not o.Visibility:
            continue
        b = o.Shape.BoundBox
        if b.XMin > bb.XMax or b.XMax < bb.XMin or b.YMin > bb.YMax or b.YMax < bb.YMin or b.ZMin > bb.ZMax or b.ZMax < bb.ZMin:
            continue
        pl = polilineas(o.Shape, V(0, 0, 1), zplano, rot)
        if pl:
            out["planta"][o.Label] = pl
        for clave, t in (("radial_t0", 0.0), ("radial_t-32", -32.0), ("radial_t+32", 32.0)):
            pl = polilineas(o.Shape, n, t, rot)
            if pl:
                out[clave][o.Label] = pl
    sal[nombre] = out


seccion(60.0, "tope60", 802.0, (560, 880, -180, 140, 640, 960))
seccion(60.0, "tope60_z806", 806.0, (560, 880, -180, 140, 640, 960))
seccion(189.86, "tope190", 802.0, (560, 880, -180, 180, 640, 960))
json.dump(sal, open(SC + r"\aud_tope3_secc.json", "w", encoding="utf-8"))

# ---------- 2) cartelas interiores candidatas: radio r_i a 710, z 805 a 885 (triangulares), t en ±(28..36) ----------
res = {}
rot60 = App.Placement(V(0, 0, 0), App.Rotation(V(0, 0, 1), 60.0))


def cartela(r_i, t0, t1, z_top=885.0):
    tri = Part.Face(Part.makePolygon([V(r_i, t0, 805), V(710, t0, 805), V(710, t0, z_top), V(r_i, t0, 805)]))
    s = tri.extrude(V(0, t1 - t0, 0))
    s.Placement = rot60
    return s


bb_total = None
for r_i in (660.0, 640.0):
    cand = {"-": cartela(r_i, -36, -28), "+": cartela(r_i, 28, 36)}
    for lado, s in cand.items():
        cho = []
        bb = s.BoundBox
        for o in solidos():
            b = o.Shape.BoundBox
            if b.XMin > bb.XMax or b.XMax < bb.XMin or b.YMin > bb.YMax or b.YMax < bb.YMin or b.ZMin > bb.ZMax or b.ZMax < bb.ZMin:
                continue
            try:
                v = s.common(o.Shape).Volume
            except Exception:
                v = -1
            d = s.distToShape(o.Shape)[0]
            if v > 0.5 or v < 0 or d < 3:
                cho.append({"o": o.Label, "comun": round(v, 1), "dist": round(d, 2), "vis": bool(o.Visibility), "grupos": [g.Label for g in o.InList if g.isDerivedFrom("App::DocumentObjectGroup")][:2]})
        res["r%d_%s" % (r_i, lado)] = {"vol": round(s.Volume, 0), "choques": cho}
sal2 = {"cartelas": res}
# que hay en la franja r 620-712, |t| < 60, z 805-890 en cualquier objeto
rot = App.Placement(V(0, 0, 0), App.Rotation(V(0, 0, 1), -60.0))
zona = Part.makeBox(92, 120, 85, V(620, -60, 805))
zona.Placement = rot.inverse()
bb = zona.BoundBox
hay = []
for o in solidos():
    b = o.Shape.BoundBox
    if b.XMin > bb.XMax or b.XMax < bb.XMin or b.YMin > bb.YMax or b.YMax < bb.YMin or b.ZMin > bb.ZMax or b.ZMax < bb.ZMin:
        continue
    v = zona.common(o.Shape).Volume
    if v > 0.5:
        hay.append({"o": o.Label, "comun": round(v, 0), "vis": bool(o.Visibility)})
sal2["franja_interior"] = hay
# boquillas y chorros cercanos: objetos con BOQ o INF en el nombre, distancia al tope
bq = []
for o in solidos():
    if any(k in o.Label.upper() for k in ("BOQ", "INF_EXT", "C2_", "NOZZ", "H3/8", "R063")) and o.Visibility:
        c = o.Shape.BoundBox.Center
        r = math.hypot(c.x, c.y)
        a = math.degrees(math.atan2(c.y, c.x)) % 360
        bq.append({"o": o.Label, "r": round(r, 0), "ang": round(a, 1), "z": round(c.z, 0)})
sal2["boquillas"] = sorted(bq, key=lambda q: q["z"])[:30]
json.dump(sal2, open(SC + r"\aud_tope3.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("LISTO")
