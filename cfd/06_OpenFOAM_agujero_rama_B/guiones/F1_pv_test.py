# F1 - prueba de la cadena de posproceso: pvpython lee la nube lagrangiana y saca numeros
from paraview.simple import *
from paraview import servermanager as sm
from paraview.numpy_support import vtk_to_numpy
import numpy as np, os, sys

vtp = sys.argv[1]
print("archivo:", os.path.basename(vtp), "| existe:", os.path.exists(vtp))
r = XMLPolyDataReader(FileName=[vtp]); r.UpdatePipeline()
d = sm.Fetch(r)
pts = vtk_to_numpy(d.GetPoints().GetData())
pd  = d.GetPointData()
campos = [pd.GetArrayName(i) for i in range(pd.GetNumberOfArrays())]
print("n parcels :", pts.shape[0])
print("campos    :", campos)
for nombre in ("d", "U", "nParticle", "rho", "origProc", "origId", "age"):
    if nombre in campos:
        a = vtk_to_numpy(pd.GetArray(nombre))
        if a.ndim == 1:
            print("  %-10s min=%.6g max=%.6g media=%.6g" % (nombre, a.min(), a.max(), a.mean()))
        else:
            m = np.linalg.norm(a, axis=1)
            print("  %-10s |.| min=%.6g max=%.6g media=%.6g" % (nombre, m.min(), m.max(), m.mean()))
if all(k in campos for k in ("d", "nParticle", "rho")):
    dd = vtk_to_numpy(pd.GetArray("d")); nn = vtk_to_numpy(pd.GetArray("nParticle")); rr = vtk_to_numpy(pd.GetArray("rho"))
    masa = float((rr * nn * np.pi/6.0 * dd**3).sum())
    print("masa reconstruida desde el VTP = %.6g kg" % masa)
print("bbox parcels (m):", pts.min(axis=0), pts.max(axis=0))
print("OK: pvpython lee la nube y da numeros")
