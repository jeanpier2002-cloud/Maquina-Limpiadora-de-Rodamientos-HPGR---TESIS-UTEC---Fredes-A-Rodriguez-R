# CORRIDA 4 · T2a2 · Perfil de un rodillo (corte por un plano que contiene su eje) y parametros de sus toroides.
# Uso: freecadcmd r4_t2a2_rodillo_fc.py  -> 02_CAVIDAD_N1/step_rodillo.json
import json

import FreeCAD as App
import Part

STEP = r"D:/Explosionado tesis II/R06.3_o7_c2/explosionado/_trabajo/rodamiento_step/SKF_bearing_241_900_ECAK30F_W33_2.stp"
OUT = r"D:/CFD_Redosado/CORRIDA_4_PRIMER_LAVADO/02_CAVIDAD_N1/step_rodillo.json"
sh = Part.Shape()
sh.read(STEP)
res = {}
for k in (2, 3):
    s = sh.Solids[k]
    # agrupa caras por rodillo: los toroides de un rodillo comparten eje; se toma el rodillo con caras planas mas
    # cercanas al plano meridiano z = 0 y y > 0
    pl = [f for f in s.Faces if type(f.Surface).__name__ == "Plane"]
    cand = sorted(pl, key=lambda f: abs(f.CenterOfMass.z) + (0 if f.CenterOfMass.y > 0 else 1e6))[:2]
    c1, c2 = cand[0].CenterOfMass, cand[1].CenterOfMass
    ax = (c2 - c1)
    L = ax.Length
    ax.normalize()
    tor = []
    for f in s.Faces:
        if type(f.Surface).__name__ == "Toroid":
            S = f.Surface
            cc = f.CenterOfMass
            mid = (c1 + c2) * 0.5
            if (cc - mid).Length < 0.6 * L:
                tor.append({"R": S.MajorRadius, "r": S.MinorRadius, "c": [S.Center.x, S.Center.y, S.Center.z],
                            "eje": [S.Axis.x, S.Axis.y, S.Axis.z], "area": f.Area, "cm": [cc.x, cc.y, cc.z]})
    # corte por el plano que contiene el eje del rodillo y el eje x del rodamiento
    mid = (c1 + c2) * 0.5
    nrm = ax.cross(App.Vector(1, 0, 0)) if abs(ax.x) < 0.999 else App.Vector(0, 0, 1)
    nrm.normalize()
    pts = []
    try:
        for w in s.slice(nrm, nrm.dot(mid)):
            for e in w.Edges:
                q = e.discretize(Distance=0.5)
                pts.append([[p.x, p.y, p.z] for p in q])
    except Exception as ex:  # noqa: BLE001
        pts = str(ex)
    res[str(k)] = {"c1": [c1.x, c1.y, c1.z], "c2": [c2.x, c2.y, c2.z], "L": L, "eje": [ax.x, ax.y, ax.z],
                   "toroides": tor, "corte": pts, "nrm": [nrm.x, nrm.y, nrm.z]}
json.dump(res, open(OUT, "w"), indent=1)
print("OK")
