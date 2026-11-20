# -*- coding: utf-8 -*-
"""Revision de R07 V18B, fase de clasificacion (Python, sin FreeCAD): reparte los solapes de rv07 por criterio fisico y los compara
con la auditoria de la V12 (rv06). Un solape de V18B se considera heredado si el par ya estaba en V12, o si tiene una etiqueta en comun
con un par de V12 y el mismo volumen (la pieza solo cambio de nombre, p. ej. CTX_M03_W6X9 -> R07_V16_M03_W6X9).
Salida: revision_cad_v11/resultados/rv07d_clasificacion_v18b.json."""
import json
import re

R = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\revision_cad_v11\resultados"
v12 = json.load(open(R + r"\rv06_resumen_v12.json", encoding="utf-8"))
v18 = json.load(open(R + r"\rv07_resumen_v18b.json", encoding="utf-8"))
REGLAS = [
    ("Empotrado previsto en la losa o el piso", r"Floor and foundation|PATA_RECEPTOR_WASH.*PISO_HUMEDO"),
    ("Clip Gantrex con el riel (envolvente comercial)", r"rail [LR].*Gantrex"),
    ("K2-M: union soldada representada por solape (UNION_PREVISTA de R06.1)", r"R061_K2M|R061_RET"),
    ("Bastidor N3: union por solape ya declarada (H13 de la revision V11)", r"CTX_WEB_STIFFENERS|CTX_BEARING_RETENTION_STOP|CTX_TABLE_LOCK_BODY"),
    ("Contacto numerico (espesor comun < 0,01 mm)", r"R07_V14_(CHAPA_FRONTAL|RIGIDIZADORES)_M04.*R07_V16_M04"),
    ("Envolvente de la correa sobre las poleas (R04)", r"CORREA_ENVOLVENTE"),
    ("Partes internas de un STEP de fabricante o entre equipos comerciales", r"R07_STEP_.*R07_STEP_"),
    ("Tuberia o pedestal contra el STEP de la bomba (< 40 mm3)", r"(PEDESTAL_BOMBA|COLADOR_Y_SUCCION|RETENCION_).*GRUNDFOS"),
    ("Union representada por solape en piezas heredadas de R04, V9 o el manillar", r"R04_|CTX_HANDLE|R07_V9_MENSULA"),
    ("Aspersion: asiento B-MEC con el pie y la boquilla (union representada)", r"B-MEC"),
]
clave = lambda s: tuple(sorted(s[:2]))
p12 = {clave(s): s[2] for s in v12["solapes_detalle"]}
res = {r[0]: [] for r in REGLAS}
res["SIN CLASIFICAR"] = []
for x, y, v in v18["solapes_detalle"]:
    t = x + " | " + y
    grupo = next((n for n, pat in REGLAS if re.search(pat, t)), "SIN CLASIFICAR")
    k = clave([x, y])
    if k in p12:
        origen = "igual que en V12"
    elif any(abs(vv - v) < 1 and (kk[0] in k or kk[1] in k) for kk, vv in p12.items()):
        origen = "de V12 con otro nombre"
    else:
        origen = "posterior a V12"
    res[grupo].append({"a": x, "b": y, "mm3": v, "origen": origen})
resumen = {g: {"n": len(l), "mm3_max": round(max((i["mm3"] for i in l), default=0), 1),
               "igual_V12": sum(i["origen"] == "igual que en V12" for i in l),
               "V12_otro_nombre": sum(i["origen"] == "de V12 con otro nombre" for i in l),
               "posterior_V12": sum(i["origen"] == "posterior a V12" for i in l)} for g, l in res.items()}
assert sum(d["n"] for d in resumen.values()) == v18["solapes"]
json.dump({"resumen": resumen, "detalle": res}, open(R + r"\rv07d_clasificacion_v18b.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for g, d in resumen.items():
    print(d["n"], "|", g, "| max", d["mm3_max"], "| V12", d["igual_V12"], "| renombrado", d["V12_otro_nombre"], "| posterior", d["posterior_V12"])
print("posteriores a V12:", sorted({re.sub(r"\d+", "#", i["a"] + " | " + i["b"]) for l in res.values() for i in l if i["origen"] == "posterior a V12"}))
