# -*- coding: utf-8 -*-
"""Revision de R07 V18D (freecadcmd, solo lectura): barrido de la traslacion de la mesa, LAVADO -> CARGA (dy de 0 a -3320 mm, cada 40 mm).
Es el barrido de r07_v14b_chequeo.py, pero con TODO lo que va sobre la mesa contra TODO lo fijo, porque desde la V14B cambiaron el bastidor
(V16), los pedestales (V17B), el soporte (V18, V18B) y los topes (V18D).
Moviles: mesa, ruedas, PAD, topes, K2-M (brazos activos y retraidos, como envolvente), rodamiento, bloqueo y barras de tiro.
Fijos: lo demas visible, con la lanza en su posicion guardada (D-003) y la puerta guillotina abierta.
Criterio: choque = volumen comun > 1 mm3 en algun dy. Se separan los pares que ya se solapan en dy = 0 con el mismo volumen (uniones o
envolventes, no son del movimiento). Salida: revision_cad_v11/resultados/rv08c_barrido_v18d.json."""
import json
import re

import FreeCAD as App

R07 = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual"
doc = App.openDocument(R07 + r"\cad\R07_V18D_STEP.FCStd", True)
vis = json.load(open(R07 + r"\resultados\VISIBILIDAD_R07_V18D.json", encoding="utf-8"))
MESA = re.compile(r"^(CTX_PAD_|CTX_WHEEL|CTX_AXLE|CTX_FORK|CTX_WEB_STIFF|CTX_HANDLE|CTX_TABLE_LOCK|CTX_ARANDELA|CTX_TUERCA|CTX_DISTANCIADOR|R061_|R07_V16_|R07_V18D_|SKF_|"
                  r"R07_V14_(CHAPA_FRONTAL_M04|RIGIDIZADORES_M04|BRAZO_HORIZONTAL|BRAZO_VERTICAL|GOLPEADOR|ENGANCHE_CADENA))")
PUERTA = re.compile(r"^(R07_H_PUERTA_GUILLOTINA_HOJA|R07_H_PUERTA_MIRILLA|R07_V8_SELLO_RIELES_EN_HOJA)")
# pares esperados: la rueda rueda sobre el riel y el enganche va unido a la cadena, que se mueve con el
ESPERADOS = [(re.compile(r"^CTX_(WHEEL|FORK|AXLE)"), re.compile(r"^A45 rail")), (re.compile(r"ENGANCHE_CADENA"), re.compile(r"CADENA_08B"))]


def valido(o):
    if o.isDerivedFrom("App::DocumentObjectGroup") or not hasattr(o, "Shape") or o.Shape.isNull():
        return False
    try:
        return bool(o.Shape.Solids) and o.Shape.Volume > 1
    except Exception:
        return False


grupos = {g.Label: g for g in doc.Objects if g.isDerivedFrom("App::DocumentObjectGroup")}
guardada = [o for o in grupos["R06_LANZA_GUARDADA"].Group if valido(o)]
base_guard = {re.sub(r"_GUARDAD[AO]$", "", o.Label) for o in guardada}
objs = [o for o in doc.Objects if valido(o)]
moviles, fijos, sustituidos = [], [], []
for o in objs:
    retraido = "RETRAIDO" in o.Label and o.Label.startswith("R061_")
    if MESA.search(o.Label) and (vis.get(o.Name, True) or retraido):
        moviles.append(o)
    elif vis.get(o.Name, True) and not PUERTA.search(o.Label):
        if o.Label in base_guard:
            sustituidos.append(o.Label)
            continue
        if o in guardada:
            continue
        fijos.append(o)
fijos += guardada
# piezas de la lanza que no tienen copia guardada con el mismo nombre: se listan para revisarlas
lanza = {x.Label for x in grupos["A6_LANZA"].Group} if "A6_LANZA" in grupos else set()
lanza_sin_copia = sorted(x for x in lanza if x not in sustituidos and any(f.Label == x for f in fijos))

env = App.BoundBox(-1300, -5500, 0, 1300, 1500, 2100)
fijos = [f for f in fijos if f.Shape.BoundBox.intersect(env)]
pasos = list(range(0, -3320, -40)) + [-3320]


def solapa(a, b, tol=0.5):
    return a.XMin - tol <= b.XMax and b.XMin - tol <= a.XMax and a.ZMin - tol <= b.ZMax and b.ZMin - tol <= a.ZMax


res = {}
n_pares = 0
for m in moviles:
    bm = m.Shape.BoundBox
    for f in fijos:
        bf = f.Shape.BoundBox
        if not solapa(bm, bf):
            continue
        # dy en los que las cajas se cruzan tambien en Y
        dys = [d for d in pasos if bm.YMin + d - 0.5 <= bf.YMax and bf.YMin - 0.5 <= bm.YMax + d]
        if not dys:
            continue
        n_pares += 1
        for d in dys:
            s = m.Shape.copy()
            s.translate(App.Vector(0, d, 0))
            if not s.BoundBox.intersect(bf):
                continue
            try:
                v = s.common(f.Shape).Volume
            except Exception:
                v = -1
            if v > 1.0 or v < 0:
                k = (m.Label, f.Label)
                r = res.setdefault(k, {"dy": [], "max_mm3": 0.0, "en_dy0": 0.0})
                r["dy"].append(d)
                r["max_mm3"] = max(r["max_mm3"], round(v, 1))
                if d == 0:
                    r["en_dy0"] = round(v, 1)
choques, estaticos, esperados = [], [], []
for (a, b), r in res.items():
    fila = {"movil": a, "fijo": b, "dy_min": min(r["dy"]), "dy_max": max(r["dy"]), "n_pasos": len(r["dy"]), "max_mm3": r["max_mm3"], "en_dy0_mm3": r["en_dy0"]}
    if any(p.search(a) and q.search(b) for p, q in ESPERADOS):
        esperados.append(fila)
    elif r["en_dy0"] > 0 and r["max_mm3"] <= r["en_dy0"] + 1 and min(r["dy"]) >= -40:
        estaticos.append(fila)
    else:
        choques.append(fila)
sal = {"pasos": len(pasos), "moviles": len(moviles), "fijos": len(fijos), "pares_con_cajas_cruzadas": n_pares, "lanza_sustituida_por_guardada": len(sustituidos),
       "lanza_sin_copia_guardada": lanza_sin_copia, "choques": sorted(choques, key=lambda x: -x["max_mm3"]), "solapes_estaticos_en_dy0": estaticos, "esperados_rueda_riel_y_enganche": esperados}
json.dump(sal, open(R07 + r"\revision_cad_v11\resultados\rv08c_barrido_v18d.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("BARRIDO", len(moviles), "moviles;", len(fijos), "fijos;", n_pares, "pares;", len(choques), "choques;", len(estaticos), "estaticos;", len(esperados), "esperados")
for c in sal["choques"][:40]:
    print("  CHOQUE", c)
print("lanza sin copia:", lanza_sin_copia)
