# -*- coding: utf-8 -*-
"""Variante del brazo de aspersión (ASP-220, R07 V15B) con la placa diagonal que sugirió el asesor (10/11/2026). Ejecutar con freecadcmd.

Entrada (solo lectura): `planos/sw/fuente/BRAZO_V15B.step`: brazo A como conjunto soldado, en coordenadas locales con origen en
(300,75; 0; 1740) globales: X a lo largo del transversal desde la cara de la brida, Z vertical (0 en el eje del transversal).
Cerca del brazo, el recorte con el cilindro ideal deja un solape con la pieza real, así que la placa se recorta también con las piezas que pisa.
Placa [HIPÓTESIS]: pletina de 40 mm de ancho en el plano de la U y 6 mm de espesor (fuera del plano), entre el eje del transversal en
x = 770 global (469,25 local) y el eje del brazo en Z 1550 global (−190 local), recortada por las superficies exteriores de los
tubos para que solo las toque (en SOLIDWORKS se une por contacto pegado, como una soldadura continua idealizada).
Salida: `geometria/BRAZO_CON_PLACA_V15B.step` y un registro con los volúmenes y los solapes.
"""
import os
import FreeCAD
import Part
from FreeCAD import Vector as V

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(AQUI)
HO = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho"
ENT = os.path.join(HO, r"01_DISENO_VIGENTE\integracion_R07_visual\planos\sw\fuente\BRAZO_V15B.step")
SAL = os.path.join(BASE, "geometria")
os.makedirs(SAL, exist_ok=True)

s = Part.Shape()
s.read(ENT)
solidos = list(s.Solids)
log = ["entrada %s: %d sólidos, volumen %.0f mm3" % (os.path.basename(ENT), len(solidos), sum(x.Volume for x in solidos))]
for i, x in enumerate(solidos):
    b = x.BoundBox
    log.append("  %2d vol %9.1f caja x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (i, x.Volume, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))

# Arreglos para el FEM (diagnóstico en s00_contactos_brazo.py, geometria/contactos_log.txt):
# 1. tubo DN50 (0) y brida deslizante (1): holgura radial de 0,6 mm (agujero r 30,75 frente a r 30,15). En la máquina la llena la
#    soldadura W1 (a3 interior y exterior, plano ASP-220 rev. B): se agrega un anillo r 30,15–30,75 de x = 3 a 20 (cordón idealizado).
# 2. tubo DN15 (6) y bloque B-MEC (7): se solapan; se recorta el bloque con el tubo para que solo se toquen.
anillo = Part.makeCylinder(30.75, 17.0, V(3.0, 0, 0), V(1, 0, 0)).cut(Part.makeCylinder(30.15, 17.0, V(3.0, 0, 0), V(1, 0, 0)))
ov = solidos[7].common(solidos[6]).Volume
solidos[7] = max(solidos[7].cut(solidos[6]).Solids, key=lambda x: x.Volume)
log.append("arreglo 1: anillo de soldadura W1 de %.1f mm3 (toca tubo %.4f mm y brida %.4f mm)" % (anillo.Volume, anillo.distToShape(solidos[0])[0], anillo.distToShape(solidos[1])[0]))
log.append("arreglo 2: bloque B-MEC recortado con el tubo DN15 (solape antes %.1f mm3, después %.3f mm3)" % (ov, solidos[7].common(solidos[6]).Volume))
solidos.append(anillo)

# ejes de los tubos, medidos en la entrada. Ejes del STEP: X a lo largo del transversal, Y vertical (hacia arriba; el brazo va de
# y −76 a −796), Z fuera del plano de la U. Desde las coordenadas globales: x = X − 300,75; y = Z − 1740; z = −Y.
import math
X_ARM = 599.39          # eje del brazo DN40 (caja 568,7..623,4 con las coplas; tubo 575,24..623,54)
R50, R40 = 30.15, 24.15
A = V(469.25, 0.0, 0.0)          # en el eje del transversal (x = 770 global)
B = V(X_ARM, -190.0, 0.0)        # en el eje del brazo (Z 1550 global)
d = B - A
L = d.Length
ANCHO, ESP = 40.0, 6.0
caja = Part.makeBox(L, ANCHO, ESP)                     # x: largo, y: ancho en el plano de la U, z: espesor
caja.translate(V(0, -ANCHO / 2, -ESP / 2))
ang = math.degrees(math.atan2(d.y, d.x))
caja.rotate(V(0, 0, 0), V(0, 0, 1), ang)
caja.translate(A)
cil50 = Part.makeCylinder(R50, 700.0, V(0, 0, 0), V(1, 0, 0))
cil40 = Part.makeCylinder(R40, 1000.0, V(X_ARM, -950.0, 0), V(0, 1, 0))
placa = caja.cut(cil50).cut(cil40)
placa = max(placa.Solids, key=lambda x: x.Volume)
sol0 = [(i, placa.common(x).Volume) for i, x in enumerate(solidos)]
log.append("solape antes de recortar con las piezas: %s" % [(i, round(v, 2)) for i, v in sol0 if v > 1e-6])
for i, v in sol0:
    if v > 1e-6:
        placa = max(placa.cut(solidos[i]).Solids, key=lambda x: x.Volume)
log.append("placa: largo entre ejes %.1f mm, ángulo %.1f°, volumen %.1f mm3 (%.3f kg de acero)" % (L, ang, placa.Volume, placa.Volume * 7.95e-6))
sol = max(placa.common(x).Volume for x in solidos)
log.append("solape máximo de la placa con las piezas: %.3f mm3" % sol)
dist = [placa.distToShape(x)[0] for x in solidos]
log.append("piezas que toca la placa (distancia < 0,01 mm): %s" % [i for i, dd in enumerate(dist) if dd < 0.01])
Part.makeCompound(solidos + [placa]).exportStep(os.path.join(SAL, "BRAZO_CON_PLACA_V15B.step"))
Part.makeCompound(solidos).exportStep(os.path.join(SAL, "BRAZO_SIN_PLACA_V15B.step"))
open(os.path.join(SAL, "geometria_log.txt"), "w", encoding="utf-8").write("\n".join(log) + "\n")
