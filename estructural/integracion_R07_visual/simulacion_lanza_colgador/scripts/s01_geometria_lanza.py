# -*- coding: utf-8 -*-
"""Geometría para SOLIDWORKS de la zona lanza–carro–mástil–tambor–transversal (R07 V18D), leída sobre una COPIA del CAD.
Ejecutar con freecadcmd y la variable HPGR_COPIA_V18D. Solo crea archivos en geometria/.

Qué entra (piezas visibles del CAD, sin las copias «GUARDADA»):
  eje del rotor cortado en Z2840 (centro del rodamiento inferior: ahí se empotra), cubo distribuidor («tambor»), transversal DN50
  central con su injerto, bridas centrales A y B con un anillo de soldadura que llena la holgura de 0,6 mm (como en el brazo de la U),
  colgador del mástil, puentes inferior y superior, varillas, placa de bloqueo, abrazadera al eje y su brazo, carro, lanza DN25,
  codo superior, «cuello» (tubos y codos DN25 hasta el racor de la manguera), coplas de las 6 boquillas y el pie de la lanza.
Qué no entra: husillo Tr20 (pasa con 0,5 mm de holgura), émbolo indexador, barra de retención, purgas, boquillas (cuerpo de bronce),
  red fija y válvula de la lanza, tubo de alimentación interior, alojamientos de rodamientos, manguera y cadena.
Ajustes: el transversal se recorta contra el cubo (el CAD lo hunde 0,15 mm: «asiento plano»), para que se toquen sin interferir.
Ejes: se exporta en el marco de SOLIDWORKS con Y vertical: (X, Y, Z)_SW = (−x, z, y) del CAD (rotación propia, det = +1),
  para que la vista Frontal de SOLIDWORKS mire desde el lado de la lanza con Z del CAD hacia arriba."""
import json
import os
import FreeCAD as App
import Part

COPIA = os.environ.get("HPGR_COPIA_V18D")
G = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "geometria")
doc = App.openDocument(COPIA)
log = []


def obj(et):
    c = [o for o in doc.Objects if o.Label == et]
    if len(c) != 1:
        raise RuntimeError("etiqueta %s: %d objetos" % (et, len(c)))
    return c[0].Shape.copy()


Z_EMP = 2840.0
eje = obj("EJE_ROTOR").common(Part.makeBox(400, 400, Z_EMP - 1800, App.Vector(-200, -200, 1800)))
cubo = obj("CUBO_DISTRIBUIDOR")
transv = obj("R07_V15_TRANSVERSAL_CENTRO_DN50").cut(cubo)
piezas = [("EJE", eje), ("CUBO", cubo), ("TRANSVERSAL", transv)]
for lado, s in (("A", 1), ("B", -1)):
    br = obj("R07_V15_BRIDA_%s_CENTRO" % lado)
    x0, x1 = (279.25, 296.25) if s > 0 else (-296.25, -279.25)
    anillo = Part.makeCylinder(30.75, x1 - x0, App.Vector(x0, 0, 1740), App.Vector(1, 0, 0)).cut(
        Part.makeCylinder(30.15, x1 - x0, App.Vector(x0, 0, 1740), App.Vector(1, 0, 0)))
    piezas.append(("BRIDA_" + lado, br.fuse(anillo).removeSplitter()))
for k, sol in enumerate(obj("MASTIL_COLGADOR_CUBO").Solids):
    piezas.append(("COLGADOR_%d" % (k + 1), sol))
for k, sol in enumerate(sorted(obj("MASTIL_VARILLAS").Solids, key=lambda q: q.BoundBox.XMin)):
    piezas.append(("VARILLA_%d" % (k + 1), sol))
for et, nom in (("MASTIL_PUENTE_INFERIOR", "PUENTE_INF"), ("MASTIL_PUENTE_SUPERIOR", "PUENTE_SUP"), ("PLACA_BLOQUEO", "PLACA_BLOQUEO"),
                ("MASTIL_ABRAZADERA_EJE", "ABRAZADERA"), ("MASTIL_BRAZO_ABRAZADERA", "BRAZO_ABRAZADERA"), ("CARRO_LANZA", "CARRO"),
                ("TUBO_LANZA_VERTICAL_DN25", "LANZA"), ("CODO_LANZA_SUP", "CODO_LANZA_SUP"),
                ("TUBO_CUELLO_1", "CUELLO_T1"), ("CODO_CUELLO_1", "CUELLO_C1"), ("TUBO_CUELLO_2", "CUELLO_T2"), ("CODO_CUELLO_2", "CUELLO_C2"),
                ("TUBO_CUELLO_3", "CUELLO_T3"), ("CODO_CUELLO_3", "CUELLO_C3"), ("TUBO_CUELLO_4", "CUELLO_T4"), ("CODO_CUELLO_4", "CUELLO_C4"),
                ("TUBO_CUELLO_5", "CUELLO_T5"), ("RACOR_MANGUERA_MOVIL", "RACOR"),
                ("COPLA_17_INT_1", "COPLA_INT_1"), ("COPLA_18_INT_2", "COPLA_INT_2"), ("COPLA_19_INT_3", "COPLA_INT_3"),
                ("COPLA_20_INT_4", "COPLA_INT_4"), ("COPLA_21_INT_5", "COPLA_INT_5"), ("COPLA_22_INF_INT", "COPLA_INF_INT"),
                ("CODO_LANZA_PIE_90", "PIE_CODO_90"), ("TUBO_LANZA_PIE_DN25", "PIE_TUBO"), ("CODO_LANZA_PIE_25", "PIE_CODO_25"),
                ("TAPA_LANZA_PIE", "PIE_TAPA")):
    s = obj(et)
    if len(s.Solids) != 1:
        raise RuntimeError("%s tiene %d sólidos" % (et, len(s.Solids)))
    piezas.append((nom, s.Solids[0]))

def solido(nom, s):
    if len(s.Solids) != 1:
        raise RuntimeError("%s: %d sólidos" % (nom, len(s.Solids)))
    return s.Solids[0]


piezas = [(n, solido(n, s)) for n, s in piezas]

# Diagnóstico de contactos (en el marco del CAD): distancia y solape entre piezas vecinas
par = []
for i in range(len(piezas)):
    for j in range(i + 1, len(piezas)):
        a, b = piezas[i][1].BoundBox, piezas[j][1].BoundBox
        if a.XMin - 2 > b.XMax or b.XMin - 2 > a.XMax or a.YMin - 2 > b.YMax or b.YMin - 2 > a.YMax or a.ZMin - 2 > b.ZMax or b.ZMin - 2 > a.ZMax:
            continue
        d = piezas[i][1].distToShape(piezas[j][1])[0]
        v = piezas[i][1].common(piezas[j][1]).Volume if d < 1e-6 else 0.0
        if d < 2.0:
            par.append([piezas[i][0], piezas[j][0], round(d, 4), round(v, 2)])

M = App.Matrix(-1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1)
cuerpos, solidos = [], []
for nom, s in piezas:
    t = s.copy()
    t.transformShape(M)
    b = t.BoundBox
    cuerpos.append({"nombre": nom, "vol_mm3": round(t.Volume, 1), "caja_sw_mm": [round(v, 3) for v in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)],
                    "centro_sw_mm": [round(v, 3) for v in (t.CenterOfMass.x, t.CenterOfMass.y, t.CenterOfMass.z)]})
    solidos.append(t)
Part.makeCompound(solidos).exportStep(os.path.join(G, "LANZA_COLGADOR_V18D.step"))
json.dump({"marco": "(X, Y, Z)_SW = (-x, z, y)_CAD; mm", "empotramiento_Y_sw": Z_EMP, "cuerpos": cuerpos, "contactos_cad": par},
          open(os.path.join(G, "geometria_lanza.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
os._exit(0)
