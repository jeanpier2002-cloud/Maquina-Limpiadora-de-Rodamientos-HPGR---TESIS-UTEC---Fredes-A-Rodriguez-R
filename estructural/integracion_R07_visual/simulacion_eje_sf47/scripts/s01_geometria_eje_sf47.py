# -*- coding: utf-8 -*-
"""Geometría del eje de salida del SEW SF47 para la simulación en SOLIDWORKS (10/11/2026). Ejecutar con freecadcmd.

Medidas tomadas del STEP de SEW `04_REFERENCIAS/cad_comerciales_R07/SF47R17DRN63MS4_brida160_eje25x50.stp` (caras medidas con FreeCAD):
  - eje Ø25 desde la cara de la brida (resalte) hasta la punta, 50 mm, chaflán 1 × 45° en la punta;
  - resalte a Ø29,76 en la cara de la brida (Y −84 del STEP);
  - chavetero forma A (extremos redondos r 4): ancho 8, fondo a 4 mm de la superficie (chaveta 8 × 7 que sobresale 3 mm),
    de 5 a 45 mm desde el resalte (40 mm de largo).
Simplificaciones [HIPÓTESIS]:
  - el agujero de centro M10 de la punta no se modela (está donde el momento es menor);
  - el STEP de SEW dibuja el resalte con canto vivo: se pone un radio de 1 mm (un canto vivo da una singularidad en el FEM);
  - el fondo del chavetero lleva radio de 0,4 mm (DIN 6885: 0,16–0,25 mm; 0,4 suaviza la singularidad; ver la nota);
  - dentro del reductor: muñón Ø29,76 de 14 mm (hasta Y −70 del STEP) y después un cuerpo de apoyo Ø50 × 16 mm, con radio de 2 mm,
    cuya cara interior va empotrada. Es un apoyo idealizado: lejos del resalte y grueso para que su singularidad no tape la zona
    que interesa. El momento en el resalte no depende del apoyo (M = F·x, la referencia x del método de SEW).
Ejes: Z a lo largo del eje, Z = 0 en el resalte, la punta en Z = 50; chavetero del lado +Y.
"""
import os
import FreeCAD
import Part
from FreeCAD import Vector as V

AQUI = os.path.dirname(os.path.abspath(__file__))
SAL = os.path.join(os.path.dirname(AQUI), "geometria")
os.makedirs(SAL, exist_ok=True)

R, L, RS, LS = 12.5, 50.0, 29.76 / 2, 14.0
RA, LA, R_APOYO = 25.0, 16.0, 2.0     # cuerpo de apoyo idealizado dentro del reductor
CH = 1.0                     # chaflán de la punta
B, T, Z0, Z1 = 8.0, 4.0, 5.0, 45.0   # chavetero
R_FILETE, R_FONDO = 1.0, 0.4

munon = Part.makeCylinder(RS, LS, V(0, 0, -LS))
apoyo = Part.makeCylinder(RA, LA, V(0, 0, -LS - LA))
base = munon.fuse(apoyo).removeSplitter()
ar = [e for e in base.Edges if hasattr(e.Curve, "Radius") and abs(e.Curve.Radius - RS) < 1e-6 and abs(e.BoundBox.ZMin + LS) < 1e-6 and abs(e.BoundBox.ZMax + LS) < 1e-6]
base = base.makeFillet(R_APOYO, ar)
eje = Part.makeCylinder(R, L - CH, V(0, 0, 0)).fuse(Part.makeCone(R, R - CH, CH, V(0, 0, L - CH)))
cuerpo = base.fuse(eje).removeSplitter()
# radio en el resalte: arista circular r = 12,5 en Z = 0
arista = [e for e in cuerpo.Edges if hasattr(e.Curve, "Radius") and abs(e.Curve.Radius - R) < 1e-6 and abs(e.BoundBox.ZMin) < 1e-6 and abs(e.BoundBox.ZMax) < 1e-6]
cuerpo = cuerpo.makeFillet(R_FILETE, arista)

# chavetero: caja central más dos cilindros (fresa de r = B/2), fondo en y = R − T
yb = R - T
caja = Part.makeBox(B, Z1 - Z0 - B, 10.0, V(-B / 2, yb, Z0 + B / 2))
caja.rotate(V(0, yb, Z0 + B / 2), V(1, 0, 0), 0)   # makeBox(lx, ly, lz): orientar como x, z, y
caja = Part.makeBox(B, 10.0, Z1 - Z0 - B, V(-B / 2, yb, Z0 + B / 2))
c1 = Part.makeCylinder(B / 2, 10.0, V(0, yb, Z0 + B / 2), V(0, 1, 0))
c2 = Part.makeCylinder(B / 2, 10.0, V(0, yb, Z1 - B / 2), V(0, 1, 0))
ranura = caja.fuse(c1).fuse(c2).removeSplitter()
cuerpo = cuerpo.cut(ranura).removeSplitter()
# radio de fondo del chavetero: aristas en el plano y = yb (contorno del fondo)
fondo = [e for e in cuerpo.Edges if abs(e.BoundBox.YMin - yb) < 1e-6 and abs(e.BoundBox.YMax - yb) < 1e-6]
try:
    cuerpo = cuerpo.makeFillet(R_FONDO, fondo)
    nota_fondo = "radio de fondo %.2f mm en %d aristas" % (R_FONDO, len(fondo))
except Exception as ex:
    nota_fondo = "sin radio de fondo (" + str(ex) + ")"

cuerpo = cuerpo.removeSplitter()
assert cuerpo.isValid() and len(cuerpo.Solids) == 1
step = os.path.join(SAL, "EJE_SF47_D25.step")
cuerpo.exportStep(step)
doc = FreeCAD.newDocument("EJE_SF47")
o = doc.addObject("Part::Feature", "EJE_SF47_D25")
o.Shape = cuerpo
doc.saveAs(os.path.join(SAL, "EJE_SF47_D25.FCStd"))
with open(os.path.join(SAL, "geometria_log.txt"), "w", encoding="utf-8") as f:
    f.write("volumen %.1f mm3, caras %d, %s, filete del resalte en %d arista(s)\n" % (cuerpo.Volume, len(cuerpo.Faces), nota_fondo, len(arista)))
    f.write("bbox %s\n" % cuerpo.BoundBox)
