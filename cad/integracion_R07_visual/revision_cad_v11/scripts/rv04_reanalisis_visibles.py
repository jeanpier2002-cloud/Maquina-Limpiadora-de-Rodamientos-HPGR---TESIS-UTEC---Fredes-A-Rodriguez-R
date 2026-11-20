# -*- coding: utf-8 -*-
"""Revision del CAD R07 V11, fase 1d (Python, sin FreeCAD): reanalisis de rv01 restringido al conjunto VIGENTE = solidos
visibles en la GUI. La visibilidad de consola (Document.xml) no refleja la GUI: se toma de GuiDocument.xml de
cad/R07_COMPLETO_COLOR_V10.FCStd (rv00_visibilidad_gui_color_v10.json; V11 solo cambia la forma de los postes del manillar,
con los mismos nombres). Salida: resultados/rv04_vigente.json."""
import csv
import json
import collections

R = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\revision_cad_v11\resultados"
vis = json.load(open(R + r"\rv00_visibilidad_gui_color_v10.json", encoding="utf-8"))
ob = {o["name"]: o for o in csv.DictReader(open(R + r"\rv01_objetos.csv", encoding="utf-8"))}
vig = {n for n, o in ob.items() if vis.get(n, True) and o["superado"] == "False"}
grupo = lambda n: ob[n]["grupos"].split(" / ")[0] if ob[n]["grupos"] else "(raiz)"
pares = [json.loads(l) for l in open(R + r"\rv01_pares.jsonl", encoding="utf-8")]
vec = {n: set() for n in vig}
sol = []
for p in pares:
    if p["a"] not in vig or p["b"] not in vig or "error" in p:
        continue
    v, d = p.get("solape_mm3", 0), p.get("dist_mm", 99)
    if v > 0.5 or d <= 0.1:
        vec[p["a"]].add(p["b"]); vec[p["b"]].add(p["a"])
    if v > 0.5:
        sol.append({"a": p["la"], "ga": grupo(p["a"]), "b": p["lb"], "gb": grupo(p["b"]), "mm3": v})
visto, comps = set(), []
for n in vig:
    if n in visto:
        continue
    pila, c = [n], []
    visto.add(n)
    while pila:
        x = pila.pop(); c.append(x)
        for y in vec[x]:
            if y not in visto:
                visto.add(y); pila.append(y)
    comps.append(c)
comps.sort(key=len, reverse=True)
intra = collections.defaultdict(lambda: [0, 0.0])
for s in sol:
    if s["ga"] == s["gb"]:
        intra[s["ga"]][0] += 1; intra[s["ga"]][1] += s["mm3"]
res = {"vigentes": len(vig), "ocultos_en_gui": sum(1 for n in ob if not vis.get(n, True)),
       "solapes_vigentes": len(sol),
       "solapes_entre_grupos": sorted([s for s in sol if s["ga"] != s["gb"]], key=lambda s: -s["mm3"]),
       "solapes_dentro_de_grupo": {k: {"n": v[0], "mm3": round(v[1])} for k, v in sorted(intra.items(), key=lambda kv: -kv[1][1])},
       "componentes": len(comps), "tamanos": [len(c) for c in comps[:10]],
       "aisladas": sorted(ob[c[0]]["label"] for c in comps if len(c) == 1),
       "grupos_pequenos": [[ob[x]["label"] for x in c] for c in comps[1:] if len(c) > 1]}
json.dump(res, open(R + r"\rv04_vigente.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("vigentes", res["vigentes"], "solapes", res["solapes_vigentes"], "entre grupos", len(res["solapes_entre_grupos"]),
      "componentes", res["componentes"], res["tamanos"], "aisladas", len(res["aisladas"]))
for s in res["solapes_entre_grupos"]:
    print(f"  {s['mm3']:12.1f} | {s['a']} [{s['ga']}] | {s['b']} [{s['gb']}]")
print("dentro de grupo:", json.dumps(res["solapes_dentro_de_grupo"], ensure_ascii=False))
print("aisladas:", res["aisladas"])
print("grupos pequenos:", res["grupos_pequenos"])
