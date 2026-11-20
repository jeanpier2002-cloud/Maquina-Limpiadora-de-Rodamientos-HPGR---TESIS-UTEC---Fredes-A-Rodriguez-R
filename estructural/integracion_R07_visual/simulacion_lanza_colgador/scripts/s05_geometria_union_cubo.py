# -*- coding: utf-8 -*-
"""Submodelo de la unión transversal–cubo (soldadura W5) para el estudio de convergencia en SOLIDWORKS (12/11/2026).
Pedido por la revisión de Codex: el golpe de 1 000 N en el brazo A dio 212 MPa (fuera del plano) y 169 MPa (en el plano)
en el transversal junto al borde del cubo, en la malla de 6/1,2 mm del modelo completo.
Piezas (de una COPIA del CAD R07 V18D, como s01): eje cortado en Z2840, cubo, transversal central y bridas A y B con su
anillo de soldadura. El transversal se parte en tres cuerpos para refinar solo el tramo x = 170–250 (lado A, donde
termina el contacto con el cubo en x ≈ 200): TRANSV_CENTRO, TRANSV_FINO y TRANSV_EXT.
Ejecutar con freecadcmd y HPGR_COPIA_V18D. Escribe geometria/UNION_CUBO_V18D.step y geometria/geometria_union_cubo.json."""
import json
import os
import FreeCAD as App
import Part

COPIA = os.environ.get("HPGR_COPIA_V18D")
G = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "geometria")
doc = App.openDocument(COPIA)


def obj(et):
    c = [o for o in doc.Objects if o.Label == et]
    if len(c) != 1:
        raise RuntimeError("etiqueta %s: %d objetos" % (et, len(c)))
    return c[0].Shape.copy()


def solido(nom, s):
    if len(s.Solids) != 1:
        raise RuntimeError("%s: %d sólidos" % (nom, len(s.Solids)))
    return s.Solids[0]


Z_EMP = 2840.0
eje = obj("EJE_ROTOR").common(Part.makeBox(400, 400, Z_EMP - 1800, App.Vector(-200, -200, 1800)))
cubo = obj("CUBO_DISTRIBUIDOR")
transv = obj("R07_V15_TRANSVERSAL_CENTRO_DN50").cut(cubo)
caja = lambda x0, x1: Part.makeBox(x1 - x0, 200, 200, App.Vector(x0, -100, 1640))
piezas = [("EJE", eje), ("CUBO", cubo),
          ("TRANSV_CENTRO", transv.common(caja(-300, 170))),
          ("TRANSV_FINO", transv.common(caja(170, 250))),
          ("TRANSV_EXT", transv.common(caja(250, 300)))]
for lado, s in (("A", 1), ("B", -1)):
    br = obj("R07_V15_BRIDA_%s_CENTRO" % lado)
    x0, x1 = (279.25, 296.25) if s > 0 else (-296.25, -279.25)
    anillo = Part.makeCylinder(30.75, x1 - x0, App.Vector(x0, 0, 1740), App.Vector(1, 0, 0)).cut(
        Part.makeCylinder(30.15, x1 - x0, App.Vector(x0, 0, 1740), App.Vector(1, 0, 0)))
    piezas.append(("BRIDA_" + lado, br.fuse(anillo).removeSplitter()))
# Cordones W5 (ASP-150: filete a4 en contorno) a ambos lados de la línea de contacto tubo–placa inferior del cubo.
# Sección (y, z): de la orilla del asiento plano (|y| = 3,0; el tubo se aplanó 0,15 mm contra el cubo) hasta |y| = 12 sobre la
# placa, con cara a 45°; se recorta contra el tubo y contra la huella del cubo (R200). Garganta resultante ≈ 4 mm (HIPÓTESIS
# geométrica: el plano no da el perfil del cordón entre un tubo y una placa tangente).
tubo_lleno = Part.makeCylinder(30.15, 700, App.Vector(-350, 0, 1740), App.Vector(1, 0, 0))
huella = Part.makeCylinder(200.0, 80, App.Vector(0, 0, 1690), App.Vector(0, 0, 1))
for sg, nom in ((1, "POS"), (-1, "NEG")):
    pts = [App.Vector(-205, sg * 2.9, 1770), App.Vector(-205, sg * 12.0, 1770), App.Vector(-205, sg * 6.0, 1764),
           App.Vector(-205, sg * 2.9, 1764), App.Vector(-205, sg * 2.9, 1770)]
    cara = Part.Face(Part.makePolygon(pts))
    w = cara.extrude(App.Vector(410, 0, 0)).cut(tubo_lleno).cut(transv).common(huella)   # sin el injerto central
    trozos = sorted([q for q in w.common(caja(-300, 170)).Solids if q.Volume > 1.0], key=lambda q: q.BoundBox.XMin)
    for k, q in enumerate(trozos):          # el injerto central parte el cordón en dos tramos
        piezas.append(("W5_%s_%d" % (nom, k + 1), q))
    piezas.append(("W5_%s_FINO" % nom, w.common(caja(170, 250))))
piezas = [(n, solido(n, s)) for n, s in piezas]
par = []
for i in range(len(piezas)):
    for j in range(i + 1, len(piezas)):
        d = piezas[i][1].distToShape(piezas[j][1])[0]
        if d < 2.0:
            v = piezas[i][1].common(piezas[j][1]).Volume if d < 1e-6 else 0.0
            par.append([piezas[i][0], piezas[j][0], round(d, 4), round(v, 2)])
M = App.Matrix(-1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1)
cuerpos, sol = [], []
for nom, s in piezas:
    t = s.copy(); t.transformShape(M); b = t.BoundBox
    cuerpos.append({"nombre": nom, "vol_mm3": round(t.Volume, 1), "caja_sw_mm": [round(v, 3) for v in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)],
                    "centro_sw_mm": [round(v, 3) for v in (t.CenterOfMass.x, t.CenterOfMass.y, t.CenterOfMass.z)]})
    sol.append(t)
Part.makeCompound(sol).exportStep(os.path.join(G, "UNION_CUBO_V18D.step"))
json.dump({"marco": "(X, Y, Z)_SW = (-x, z, y)_CAD; mm", "cuerpos": cuerpos, "contactos_cad": par},
          open(os.path.join(G, "geometria_union_cubo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(os.path.join(G, "cuerpos_union_cubo.csv"), "w", encoding="utf-8") as f:
    f.write("nombre;vol_mm3;cx;cy;cz\n")
    for c in cuerpos:
        f.write("%s;%s;%s;%s;%s\n" % (c["nombre"], c["vol_mm3"], *c["centro_sw_mm"]))
os._exit(0)
