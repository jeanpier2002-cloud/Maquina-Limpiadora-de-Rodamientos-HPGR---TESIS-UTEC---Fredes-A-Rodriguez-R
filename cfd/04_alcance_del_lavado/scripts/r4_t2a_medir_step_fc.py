# CORRIDA 4 · T2a · Medicion del STEP de SKF con FreeCAD (freecadcmd). SOLO LECTURA del STEP.
# Salida: 02_CAVIDAD_N1/step_medicion.json (solidos, volumen, caja, centro de masa, ejes principales; perfil meridiano
# de los aros en el plano que contiene el eje). Uso:
#   "C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" r4_t2a_medir_step_fc.py
import json
import math

import FreeCAD as App
import Part

STEP = r"D:/Explosionado tesis II/R06.3_o7_c2/explosionado/_trabajo/rodamiento_step/SKF_bearing_241_900_ECAK30F_W33_2.stp"
OUT = r"D:/CFD_Redosado/CORRIDA_4_PRIMER_LAVADO/02_CAVIDAD_N1/step_medicion.json"

sh = Part.Shape()
sh.read(STEP)
sol = sh.Solids
res = {"step": STEP, "n_solidos": len(sol), "solidos": []}
for i, s in enumerate(sol):
    bb = s.BoundBox
    cm = s.CenterOfMass
    try:
        pp = s.PrincipalProperties
        ejes = [[v.x, v.y, v.z] for v in (pp["FirstAxisOfInertia"], pp["SecondAxisOfInertia"], pp["ThirdAxisOfInertia"])]
        mom = [pp["FirstMomentOfInertia"], pp["SecondMomentOfInertia"], pp["ThirdMomentOfInertia"]]
    except Exception as ex:  # noqa: BLE001
        ejes, mom = [], [str(ex)]
    tipos = {}
    for f in s.Faces:
        n = type(f.Surface).__name__
        tipos[n] = tipos.get(n, 0) + 1
    res["solidos"].append({"i": i, "vol_mm3": s.Volume, "area_mm2": s.Area,
                           "bb": [bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax],
                           "cm": [cm.x, cm.y, cm.z], "ejes": ejes, "mom": mom, "caras": tipos})

# eje del rodamiento: la dimension de la caja global con extension ~515 mm
bb = sh.BoundBox
ext = [bb.XLength, bb.YLength, bb.ZLength]
res["bb_global"] = [bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax]
k_eje = min(range(3), key=lambda k: abs(ext[k] - 515.0))
res["k_eje"] = k_eje
# perfil meridiano de los dos solidos mas grandes (aros) con un plano que contiene el eje
grandes = sorted(range(len(sol)), key=lambda i: -sol[i].Volume)[:2]
c = bb.Center
# normal del plano meridiano: un eje perpendicular al del rodamiento
normales = [App.Vector(1, 0, 0), App.Vector(0, 1, 0), App.Vector(0, 0, 1)]
nk = (k_eje + 1) % 3
nrm = normales[nk]
d = [c.x, c.y, c.z][nk]
res["perfiles"] = {}
for i in grandes:
    try:
        wires = sol[i].slice(nrm, d)
        pts = []
        for w in wires:
            for e in w.Edges:
                q = e.discretize(Distance=0.5)
                pts.append([[p.x, p.y, p.z] for p in q])
        res["perfiles"][str(i)] = pts
    except Exception as ex:  # noqa: BLE001
        res["perfiles"][str(i)] = str(ex)
# geometria de cada rodillo: superficie de revolucion lateral -> radio maximo; caras planas extremas -> centros
rod = []
for i, s in enumerate(sol):
    if i in grandes:
        continue
    info = {"i": i, "planas": [], "otras": []}
    for f in s.Faces:
        n = type(f.Surface).__name__
        if n == "Plane":
            cc = f.CenterOfMass
            info["planas"].append({"c": [cc.x, cc.y, cc.z], "area": f.Area,
                                   "n": [f.Surface.Axis.x, f.Surface.Axis.y, f.Surface.Axis.z]})
        else:
            info["otras"].append({"tipo": n, "area": f.Area})
    rod.append(info)
res["rodillos"] = rod
json.dump(res, open(OUT, "w"), indent=1)
print("OK", len(sol), "solidos; eje k =", k_eje, "; grandes:", grandes)
