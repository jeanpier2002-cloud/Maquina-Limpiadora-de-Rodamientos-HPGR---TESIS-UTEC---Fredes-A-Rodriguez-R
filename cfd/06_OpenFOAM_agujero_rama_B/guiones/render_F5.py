#!/usr/bin/env python3
"""
F5 - render del caso S2 con pvbatch: la nube de gotas y el mapa de deposicion
sobre la pared del agujero.

Uso:  pvbatch render_F5.py <carpeta con los .vtp> <carpeta de salida>
"""
import os
import sys

from paraview.simple import *

vtk_dir = sys.argv[1]
out_dir = sys.argv[2]
os.makedirs(out_dir, exist_ok=True)

paraview.simple._DisableFirstRenderCameraReset()
v = CreateView("RenderView")
v.ViewSize = [1500, 1500]
v.Background = [1.0, 1.0, 1.0]
v.UseColorPaletteForBackground = 0
v.OrientationAxesVisibility = 0


def leer(nombre):
    f = os.path.join(vtk_dir, nombre)
    if not os.path.exists(f):
        print("  falta", nombre)
        return None
    r = XMLPolyDataReader(FileName=[f])
    r.UpdatePipeline()
    return r


pared = leer("pared_agujero.vtp")
lanza = leer("lanza.vtp")
cara = leer("cara_inf_rodamiento.vtp")
nube = leer("kinematicCloud_700.vtp")

CAMPO = "kinematicCloud:campos_de_impacto:mass"

# ---------------------------------------------------- 1. mapa de deposicion
dp = Show(pared, v)
arr = [pared.CellData.GetArray(i).Name for i in range(pared.CellData.NumberOfArrays)]
print("  campos de celda en la pared:", arr)
campo = CAMPO if CAMPO in arr else (arr[0] if arr else None)
if campo:
    ColorBy(dp, ("CELLS", campo))
    lut = GetColorTransferFunction(campo)
    dp.RescaleTransferFunctionToDataRange(True, False)
    lut.ApplyPreset("Viridis", True)
    lut.MapControlPointsToLogSpace()
    lut.UseLogScale = 1
    barra = GetScalarBar(lut, v)
    barra.Title = "masa depositada acumulada"
    barra.ComponentTitle = "kg por cara"
    barra.TitleColor = [0, 0, 0]
    barra.LabelColor = [0, 0, 0]
    barra.TitleFontSize = 16
    barra.LabelFontSize = 14
    dp.SetScalarBarVisibility(v, True)
dp.Opacity = 1.0

if lanza:
    dl = Show(lanza, v)
    dl.ColorArrayName = ["POINTS", ""]
    dl.DiffuseColor = [0.35, 0.35, 0.38]
if cara:
    dc = Show(cara, v)
    dc.ColorArrayName = ["POINTS", ""]
    dc.DiffuseColor = [0.75, 0.75, 0.78]
    dc.Opacity = 0.55

v.CameraPosition = [1.9, -1.9, 2.15]
v.CameraFocalPoint = [0.0, 0.0, 1.12]
v.CameraViewUp = [0, 0, 1]
v.CameraParallelProjection = 0
ResetCamera()
v.CameraPosition = [1.75, -1.75, 2.05]
v.CameraFocalPoint = [0.0, 0.0, 1.12]
v.CameraViewUp = [0, 0, 1]
Render()
p1 = os.path.join(out_dir, "F5_mapa_deposicion_3D.png")  # solo de control
SaveScreenshot(p1, v, ImageResolution=[1500, 1500], TransparentBackground=0)
print("escrito", p1)

# ---------------------------------------------------- 2. la nube de gotas
if campo:
    dp.SetScalarBarVisibility(v, False)
dp.ColorArrayName = ["POINTS", ""]
dp.DiffuseColor = [0.85, 0.85, 0.88]
dp.Opacity = 0.22

if nube:
    g = Glyph(Input=nube, GlyphType="Sphere")
    g.ScaleArray = ["POINTS", "d"]
    g.ScaleFactor = 22.0   # d ~ 3e-4 m -> esferas de ~6,6 mm; con 90 salian de 27 mm
    g.GlyphMode = "Every Nth Point"
    g.Stride = 5
    g.GlyphType.ThetaResolution = 6
    g.GlyphType.PhiResolution = 6
    g.UpdatePipeline()
    dg = Show(g, v)
    ColorBy(dg, ("POINTS", "U", "Magnitude"))
    lu = GetColorTransferFunction("U")
    dg.RescaleTransferFunctionToDataRange(True, False)
    lu.ApplyPreset("Cool to Warm", True)
    b2 = GetScalarBar(lu, v)
    b2.Title = "velocidad de la gota"
    b2.ComponentTitle = "m/s"
    b2.TitleColor = [0, 0, 0]
    b2.LabelColor = [0, 0, 0]
    b2.TitleFontSize = 16
    b2.LabelFontSize = 14
    dg.SetScalarBarVisibility(v, True)

Render()
p2 = os.path.join(out_dir, "F5_nube_de_gotas_3D.png")
SaveScreenshot(p2, v, ImageResolution=[1500, 1500], TransparentBackground=0)
print("escrito", p2)
