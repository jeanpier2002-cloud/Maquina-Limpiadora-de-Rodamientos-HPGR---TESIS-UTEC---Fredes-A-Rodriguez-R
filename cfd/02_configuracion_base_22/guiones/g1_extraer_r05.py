# -*- coding: utf-8 -*-
"""
G1/G2 - Extraccion independiente de R05_GEOMETRICO_DETALLADO.FCStd (COPIA, solo lectura) con FreeCAD 1.1.

Boquillas (objetos BOQUILLA_nn_*): se MIDEN sobre el solido guardado, sin usar los datos de diseno:
  - eje      : eje de la cara cilindrica del orificio equivalente (R = 1,3843 mm), orientado hacia la punta
  - punta    : interseccion del eje con la cara plana frontal (la de mayor proyeccion sobre el eje)
  - salida   : extremo del orificio en el fondo de la ranura (vertice del abanico en gen_abanico.py)
  - ranura   : direccion de la arista de la V = n1 x n2 de las dos caras planas inclinadas ~45 grados
  - plano del abanico: contiene eje y ranura -> normal = eje x ranura
Contexto (grupo G00_CONTEXTO_MESA_R05): caja envolvente, volumen, tipos de cara (radios de cilindros,
cotas de planos) y STL teselado de PAD, topes, rodamiento de referencia, vigas y centradores.

Uso (ruta ASCII; la "o" con tilde hace fallar a freecadcmd):
  freecadcmd -c "import sys; sys.argv=['x','D:/CFD03_run/geom/R05_GEOMETRICO_DETALLADO.FCStd','D:/CFD03_run/geom/salida']; exec(open('D:/CFD03_run/geom/g1_extraer_r05.py').read())"
"""
import json
import math
import os
import sys

import FreeCAD
import Mesh
import Part

fc, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
os.makedirs(os.path.join(out, "stl"), exist_ok=True)
doc = FreeCAD.openDocument(fc)
R_ORIF = 2.7686 / 2.0          # parametros_r05.json: orificio_equivalente_D


def v3(v, n=4):
    return [round(v.x, n), round(v.y, n), round(v.z, n)]


def medir_boquilla(o):
    s = o.Shape
    cil = [f for f in s.Faces if isinstance(f.Surface, Part.Cylinder) and abs(f.Surface.Radius - R_ORIF) < 1e-3]
    if not cil:
        return dict(error="sin cara de orificio")
    f0 = cil[0]
    ax = FreeCAD.Vector(f0.Surface.Axis); ax.normalize()
    c0 = FreeCAD.Vector(f0.Surface.Center)
    # orientar el eje hacia la punta: la mayor parte del volumen (rosca, hexagono) queda detras de la punta
    cm = s.CenterOfMass if hasattr(s, "CenterOfMass") else s.BoundBox.Center
    if (c0 - cm).dot(ax) < 0:
        ax = -ax
    # caras planas perpendiculares al eje: la frontal es la de mayor proyeccion
    planas = [f for f in s.Faces if isinstance(f.Surface, Part.Plane)]
    perp = [f for f in planas if abs(abs(f.normalAt(0, 0).dot(ax)) - 1) < 1e-6]
    fr = max(perp, key=lambda f: f.CenterOfMass.dot(ax))
    t_fr = (fr.CenterOfMass - c0).dot(ax)
    punta = c0 + ax * t_fr
    # extremo del orificio mas cercano a la punta = salida al fondo de la ranura
    ext = [v.Point for v in f0.Vertexes]
    ts = [(p - c0).dot(ax) for p in ext] if ext else [0.0]
    salida = c0 + ax * max(ts)
    # caras de la V: planas con |n.eje| ~ cos 45
    inc = [f for f in planas if 0.2 < abs(f.normalAt(0, 0).dot(ax)) < 0.95]
    ranura = None
    if len(inc) >= 2:
        n1, n2 = inc[0].normalAt(0, 0), inc[1].normalAt(0, 0)
        g = n1.cross(n2)
        if g.Length > 1e-6:
            g.normalize(); ranura = g
    res = dict(punta=v3(punta, 4), eje=v3(ax, 6), salida_orificio=v3(salida, 4),
               h_punta_salida_mm=round((punta - salida).Length, 4),
               caras_V=len(inc), radio_orificio_mm=round(f0.Surface.Radius, 5))
    if ranura is not None:
        nrm = ax.cross(ranura); nrm.normalize()
        res.update(ranura=v3(ranura, 6), normal_plano_abanico=v3(nrm, 6),
                   angulo_V_deg=round(math.degrees(inc[0].normalAt(0, 0).getAngle(inc[1].normalAt(0, 0))), 3))
    return res


def describir(o):
    s = o.Shape
    bb = s.BoundBox
    caras = {}
    for f in s.Faces:
        su = f.Surface
        if isinstance(su, Part.Cylinder):
            k = "cil R=%.3f eje=%s" % (su.Radius, v3(su.Axis, 3))
        elif isinstance(su, Part.Plane):
            n = f.normalAt(0, 0)
            k = "plano n=%s d=%.3f" % (v3(n, 3), f.CenterOfMass.dot(n))
        elif isinstance(su, Part.Cone):
            k = "cono semiang=%.5f deg" % math.degrees(su.SemiAngle)
        else:
            k = type(su).__name__
        caras[k] = caras.get(k, 0) + 1
    return dict(bbox=[round(bb.XMin, 3), round(bb.XMax, 3), round(bb.YMin, 3), round(bb.YMax, 3),
                      round(bb.ZMin, 3), round(bb.ZMax, 3)],
                volumen_mm3=round(s.Volume, 3), n_caras=len(s.Faces), caras=caras,
                grupo=[g.Name for g in o.InList])


boq, ctx = {}, {}
for o in doc.Objects:
    if not hasattr(o, "Shape") or o.Shape.isNull():
        continue
    n = o.Name
    if n.startswith("BOQUILLA_"):
        boq[n] = medir_boquilla(o)
    elif n.startswith("CTX_"):
        ctx[n] = describir(o)
        if any(k in n for k in ("PAD", "BEARING", "_M0", "LOCATOR", "TABLE")):
            m = Mesh.Mesh(o.Shape.tessellate(0.5))
            m.write(os.path.join(out, "stl", n + ".stl"))

json.dump(dict(fuente=fc, boquillas=boq, contexto=ctx), open(os.path.join(out, "r05_extraccion.json"), "w"),
          indent=1, sort_keys=True)
print("boquillas:", len(boq), "contexto:", len(ctx))
