# -*- coding: utf-8 -*-
"""Revision del CAD R07 V11, fase 1 (freecadcmd): auditoria geometrica de TODAS las piezas, incluida la parte heredada de R05
que los chequeos de R07 no revisaban (solo comparaban cada bloque nuevo contra el contexto). Solo lectura: no se guarda nada.
Mide, para cada par de solidos visibles cuyas cajas se tocan (tolerancia 0,5 mm):
  - volumen comun exacto (solape) y, si no hay solape, la distancia (contacto si <= 0,1 mm);
y con eso arma: lista de solapes, grafo de contactos (piezas aisladas y grupos que no llegan al piso), uniones con
tornilleria (pernos/pasadores que no atraviesan dos piezas o que se solapan con una pieza sin agujero), solidos invalidos,
duplicados y objetos de grupos superados que siguen visibles.
Salida en revision_cad_v11/resultados/: rv01_objetos.csv, rv01_pares.jsonl (se escribe a medida que avanza, para poder
retomar), rv01_resumen.json. Uso: freecadcmd -c "exec(open(r'...rv01_auditoria_geometrica.py',encoding='utf-8').read())"."""
import csv
import json
import os
import re
import time

import FreeCAD as App

R07 = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual"
OUT = R07 + r"\revision_cad_v11\resultados"
os.makedirs(OUT, exist_ok=True)
TOL_CAJA, TOL_CONTACTO, MIN_SOLAPE = 0.5, 0.1, 0.5
FIJACION = re.compile(r"(?i)PERNO|BOLT|SCREW|TORNILLO|TUERCA|NUT\b|NUT_|ARANDELA|WASHER|ESPARRAGO|STUD|PASADOR|_PIN\b|PIN_|PIN$|REMACHE|RIVET|ANCLAJE|ANCHOR")

t0 = time.time()
doc = App.openDocument(R07 + r"\cad\R07_V11_STEP.FCStd")


def ancestros(o):
    cad, p = [], o
    for _ in range(12):
        ps = [q for q in p.InList if q.TypeId in ("App::DocumentObjectGroup", "App::Part", "App::LinkGroup")]
        if not ps:
            break
        p = ps[0]
        cad.append(p)
    return cad


objs = []
for o in doc.Objects:
    if o.TypeId != "Part::Feature" or not hasattr(o, "Shape"):
        continue
    s = o.Shape
    if s.isNull() or not s.Solids:
        continue
    anc = ancestros(o)
    vis_propia = bool(getattr(o, "Visibility", True))
    vis_efectiva = vis_propia and all(bool(getattr(a, "Visibility", True)) for a in anc)
    objs.append({"obj": o, "name": o.Name, "label": o.Label, "grupos": [a.Label for a in anc][::-1],
                 "vis_propia": vis_propia, "vis_efectiva": vis_efectiva, "shape": s, "bb": s.BoundBox,
                 "vol": s.Volume, "valido": s.isValid(), "caras": len(s.Faces), "solidos": len(s.Solids),
                 "superado": any("SUPERAD" in a.Label.upper() for a in anc),
                 "fijacion": bool(FIJACION.search(o.Label))})

with open(OUT + r"\rv01_objetos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["name", "label", "grupos", "vis_propia", "vis_efectiva", "superado", "fijacion", "valido", "solidos", "caras",
                "volumen_mm3", "xmin", "xmax", "ymin", "ymax", "zmin", "zmax"])
    for d in objs:
        b = d["bb"]
        w.writerow([d["name"], d["label"], " / ".join(d["grupos"]), d["vis_propia"], d["vis_efectiva"], d["superado"], d["fijacion"],
                    d["valido"], d["solidos"], d["caras"], round(d["vol"], 1)] + [round(v, 1) for v in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)])

# piezas que se revisan: visibles en el archivo (propia) y no superadas; los superados se reportan aparte
act = [d for d in objs if d["vis_propia"] and not d["superado"]]
print("objetos con solido:", len(objs), "revisados:", len(act), "t", round(time.time() - t0))

# retomar si ya hay pares calculados
hechos = {}
ruta_pares = OUT + r"\rv01_pares.jsonl"
if os.path.exists(ruta_pares):
    for linea in open(ruta_pares, encoding="utf-8"):
        try:
            r = json.loads(linea); hechos[(r["a"], r["b"])] = r
        except Exception:
            pass


def cajas_tocan(a, b, t):
    return not (a.XMax + t < b.XMin or b.XMax + t < a.XMin or a.YMax + t < b.YMin or b.YMax + t < a.YMin or
                a.ZMax + t < b.ZMin or b.ZMax + t < a.ZMin)


candidatos = []
for i in range(len(act)):
    for j in range(i + 1, len(act)):
        if cajas_tocan(act[i]["bb"], act[j]["bb"], TOL_CAJA):
            candidatos.append((i, j))
print("pares candidatos:", len(candidatos), "ya hechos:", len(hechos))

fout = open(ruta_pares, "a", encoding="utf-8")
n = 0
for i, j in candidatos:
    a, b = act[i], act[j]
    clave = (a["name"], b["name"])
    if clave in hechos:
        continue
    r = {"a": a["name"], "b": b["name"], "la": a["label"], "lb": b["label"]}
    t1 = time.time()
    try:
        v = a["shape"].common(b["shape"]).Volume
        r["solape_mm3"] = round(v, 2)
        if v <= MIN_SOLAPE:
            r["dist_mm"] = round(a["shape"].distToShape(b["shape"])[0], 3)
    except Exception as e:
        r["error"] = str(e)[:120]
    r["s"] = round(time.time() - t1, 2)
    fout.write(json.dumps(r, ensure_ascii=False) + "\n"); fout.flush()
    hechos[clave] = r
    n += 1
    if n % 200 == 0:
        print("pares", n, "t", round(time.time() - t0))
fout.close()

# ---- analisis
por_nombre = {d["name"]: d for d in act}
solapes, contactos, errores = [], [], []
vecinos = {d["name"]: set() for d in act}
for (an, bn), r in hechos.items():
    if an not in por_nombre or bn not in por_nombre:
        continue
    if "error" in r:
        errores.append(r); continue
    toca = r.get("solape_mm3", 0) > MIN_SOLAPE or r.get("dist_mm", 99) <= TOL_CONTACTO
    if toca:
        vecinos[an].add(bn); vecinos[bn].add(an)
    if r.get("solape_mm3", 0) > MIN_SOLAPE:
        solapes.append(r)
    elif r.get("dist_mm", 99) <= TOL_CONTACTO:
        contactos.append(r)

# componentes conexas y piso
zmin_global = min(d["bb"].ZMin for d in act)
piso = {d["name"] for d in act if d["bb"].ZMin <= zmin_global + 1.0}
visto, comps = set(), []
for d in act:
    if d["name"] in visto:
        continue
    pila, comp = [d["name"]], []
    visto.add(d["name"])
    while pila:
        x = pila.pop(); comp.append(x)
        for y in vecinos[x]:
            if y not in visto:
                visto.add(y); pila.append(y)
    comps.append(comp)
comps.sort(key=len, reverse=True)
sin_piso = [c for c in comps if not (set(c) & piso)]

# tornilleria: cuantas piezas no-fijacion toca/atraviesa cada fijacion y si se solapa con alguna (agujero faltante)
fij = []
for d in act:
    if not d["fijacion"]:
        continue
    toca_no_fij = [y for y in vecinos[d["name"]] if not por_nombre[y]["fijacion"]]
    solapa_no_fij = []
    for (an, bn), r in hechos.items():
        if d["name"] in (an, bn) and r.get("solape_mm3", 0) > MIN_SOLAPE:
            otro = bn if an == d["name"] else an
            if otro in por_nombre and not por_nombre[otro]["fijacion"]:
                solapa_no_fij.append([por_nombre[otro]["label"], r["solape_mm3"]])
    fij.append({"label": d["label"], "grupos": " / ".join(d["grupos"]), "piezas_que_toca": len(toca_no_fij),
                "toca": [por_nombre[y]["label"] for y in toca_no_fij][:8], "solapa_con": solapa_no_fij[:8]})

# duplicados (mismo volumen y misma caja)
dup, firmas = [], {}
for d in act:
    b = d["bb"]
    k = (round(d["vol"], 0), round(b.XMin, 0), round(b.XMax, 0), round(b.YMin, 0), round(b.YMax, 0), round(b.ZMin, 0), round(b.ZMax, 0))
    if k in firmas:
        dup.append([firmas[k], d["label"]])
    else:
        firmas[k] = d["label"]

res = {
    "fuente": doc.FileName, "segundos": round(time.time() - t0),
    "objetos_con_solido": len(objs), "revisados": len(act),
    "superados_visibles_en_archivo": [d["label"] for d in objs if d["superado"] and d["vis_propia"]],
    "ocultos_por_grupo": len([d for d in objs if d["vis_propia"] and not d["vis_efectiva"]]),
    "invalidos": [d["label"] for d in act if not d["valido"]],
    "pares_evaluados": len(hechos), "solapes": len(solapes), "contactos": len(contactos), "errores_boolean": len(errores),
    "solapes_detalle": sorted([[r["la"], r["lb"], r["solape_mm3"]] for r in solapes], key=lambda x: -x[2]),
    "errores_detalle": [[r["la"], r["lb"], r["error"]] for r in errores],
    "piso_zmin_mm": round(zmin_global, 1), "n_piezas_en_piso": len(piso),
    "componentes": len(comps), "tamano_componentes": [len(c) for c in comps[:15]],
    "aisladas": [por_nombre[c[0]]["label"] for c in comps if len(c) == 1],
    "grupos_sin_piso": [[por_nombre[x]["label"] for x in c][:25] + (["..."] if len(c) > 25 else []) for c in sin_piso if len(c) > 1],
    "fijaciones": fij, "duplicados": dup,
}
json.dump(res, open(OUT + r"\rv01_resumen.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
App.closeDocument(doc.Name)
print("RV01 OK", res["segundos"], "s; solapes", res["solapes"], "aisladas", len(res["aisladas"]), "grupos sin piso", len(res["grupos_sin_piso"]))
