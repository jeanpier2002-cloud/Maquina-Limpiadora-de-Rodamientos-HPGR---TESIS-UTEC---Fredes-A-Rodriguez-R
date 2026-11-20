# -*- coding: utf-8 -*-
"""Revision del CAD R07 V11, fase 1c (freecadcmd), solo lectura:
1) Fijaciones: para cada perno, tuerca, arandela o pasador de rv01, piezas no-fijacion a <= 1,5 mm (agujero pasante con
   holgura). Un perno o pasador que no queda dentro de al menos 2 piezas no sujeta nada.
2) Traslacion de la mesa: volumen comun entre las piezas fijas de la aspersion inferior exterior (B_COM_*, B-MEC, pies
   exteriores) y las vigas M01/M02 desplazadas en -Y (de 0 a 3 320 mm, paso de 50 mm). Comprueba si el solape de la rotula
   con el ala superior bloquearia la salida de la mesa.
Salida: revision_cad_v11/resultados/rv01c_fijaciones_y_barrido.json."""
import json
import re

import FreeCAD as App

R07 = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual"
OUT = R07 + r"\revision_cad_v11\resultados"
FIJ = re.compile(r"(?i)PERNO|BOLT|SCREW|TORNILLO|TUERCA|NUT\b|NUT_|ARANDELA|WASHER|ESPARRAGO|STUD|PASADOR|_PIN\b|PIN_|PIN$|REMACHE|RIVET|ANCLAJE|ANCHOR")
doc = App.openDocument(R07 + r"\cad\R07_V11_STEP.FCStd")
sup = set()
for g in doc.Objects:
    if "SUPERAD" in g.Label.upper() and hasattr(g, "Group"):
        sup |= {o.Name for o in g.Group}
act = [o for o in doc.Objects if o.TypeId == "Part::Feature" and o.Visibility and o.Name not in sup and hasattr(o, "Shape")
       and not o.Shape.isNull() and o.Shape.Solids]
fij = [o for o in act if FIJ.search(o.Label)]
nofij = [o for o in act if not FIJ.search(o.Label)]
res = {"fijaciones": []}
for f in fij:
    bb = f.Shape.BoundBox
    cerca = []
    for o in nofij:
        b = o.Shape.BoundBox
        if b.XMax < bb.XMin - 2 or b.XMin > bb.XMax + 2 or b.YMax < bb.YMin - 2 or b.YMin > bb.YMax + 2 or b.ZMax < bb.ZMin - 2 or b.ZMin > bb.ZMax + 2:
            continue
        try:
            d = f.Shape.distToShape(o.Shape)[0]
        except Exception:
            continue
        if d <= 1.5:
            cerca.append([o.Label, round(d, 2)])
    res["fijaciones"].append({"fijacion": f.Label, "piezas_a_1_5mm": cerca, "n": len(cerca)})

# barrido de la traslacion: vigas M01/M02 en -Y contra lo fijo de la aspersion inferior exterior
vigas = [o for o in act if o.Label in ("CTX_M01_W6X9", "CTX_M02_W6X9")]
fijo = [o for o in act if re.match(r"(?i)B_COM_|R063 B-MEC|PORTABOQUILLA_\d+_INF|TUBO_PIE_|R063 INF_EXT", o.Label)]
bar = []
for paso in range(0, 3321, 50):
    for v in vigas:
        s = v.Shape.copy(); s.translate(App.Vector(0, -paso, 0))
        for o in fijo:
            if not s.BoundBox.intersect(o.Shape.BoundBox):
                continue
            c = s.common(o.Shape).Volume
            if c > 0.5:
                bar.append([paso, v.Label, o.Label, round(c, 1)])
res["barrido_mesa_contra_aspersion_inferior"] = bar
res["piezas_fijas_revisadas"] = [o.Label for o in fijo]
json.dump(res, open(OUT + r"\rv01c_fijaciones_y_barrido.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
App.closeDocument(doc.Name)
print("RV01C OK", len(res["fijaciones"]), "fijaciones;", len(bar), "choques en el barrido")
