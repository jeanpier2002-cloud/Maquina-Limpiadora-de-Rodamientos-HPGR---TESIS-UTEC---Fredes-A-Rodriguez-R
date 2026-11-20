# -*- coding: utf-8 -*-
"""Solo lectura: a quien pertenece cada buje del compuesto R07_V12_BUJES y como es el pasador frente a las orejas."""
import FreeCAD as App
R07 = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual"
doc = App.openDocument(R07 + r"\cad\R07_V18D_STEP.FCStd", True)
uno = lambda l: doc.getObjectsByLabel(l)[0]
body = uno("CTX_TABLE_LOCK_BODY").Shape
pin = uno("CTX_TABLE_LOCK_PIN").Shape
rw = uno("Fixed double-ear lock receiver WASH").Shape
caja = lambda s: [round(v, 1) for v in (s.BoundBox.XMin, s.BoundBox.XMax, s.BoundBox.YMin, s.BoundBox.YMax, s.BoundBox.ZMin, s.BoundBox.ZMax)]
print("BODY", caja(body), "PIN", caja(pin), "RECEPTOR", caja(rw))
print("pasador en dy=0: comun con receptor", round(pin.common(rw).Volume, 1), "| dist", round(pin.distToShape(rw)[0], 2))
for i, s in enumerate(uno("R07_V12_BUJES_D050_D32_D25").Shape.Solids):
    print("BUJE", i, caja(s), "vol", round(s.Volume), "| dist al cuerpo movil", round(s.distToShape(body)[0], 2), "| dist al receptor WASH", round(s.distToShape(rw)[0], 2))
print("FIN")
