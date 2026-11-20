# -*- coding: utf-8 -*-
"""Revision del CAD R07 V11, fase 5a (freecadcmd): tesela las piezas de cada hallazgo principal (y su volumen comun, si
hay) para dibujar las capturas con matplotlib (rv05b). Solo lectura. Salida: resultados/rv05_teselas.json."""
import json

import FreeCAD as App

R07 = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual"
OUT = R07 + r"\revision_cad_v11\resultados"
HALLAZGOS = {
    "H01_receptor_LOAD_sin_apoyo": (["Fixed double-ear lock receiver LOAD", "Floor and foundation reference"], [],
                                     "Receptor del bloqueo en la estacion LOAD: sin patas, a 470 mm del piso"),
    "H02_soporte_superior_y_muros": (["R04_SOP_PLACAS_BASE", "R04_SOP_COLUMNAS_SHS150x6", "CTX_CABIN_LEFT"], [("R04_SOP_PLACAS_BASE", "CTX_CABIN_LEFT")],
                                     "Soporte superior R04: columnas fuera de la cabina; placas base bajo el muro"),
    "H03_pasador_estacionamiento": (["R04_PASADOR_ESTACIONAMIENTO_ROTOR", "R04_CARTUCHO_PLACA_BASE", "POLEA_CONDUCIDA"], [],
                                    "Pasador de estacionamiento del rotor: solo toca su placa base"),
    "H04_delantal_reserva": (["R06_DELANTAL_EXTERIOR_RESERVA", "Rail support L-03", "Rail support R-03", "A45 rail L", "A45 rail R"],
                             [("R06_DELANTAL_EXTERIOR_RESERVA", "Rail support L-03")], "Delantal exterior RESERVA (no fisico) solapado con soportes de riel"),
    "H05_bandejas_sin_soporte": (["R07_C_BANDEJA_T5_SUBIDA_TECHO", "R07_C_BANDEJA_T6_ACCIONAMIENTO", "R04_SOP_COLUMNAS_SHS150x6"], [],
                                 "Bandejas T5/T6 sin soportes (a 7 mm de la columna)"),
    "H06_patas_receptor_piso_humedo": (["R06_PATA_RECEPTOR_WASH_IZQ", "R06_PISO_HUMEDO_IZQ", "LOCK_RECEIVER_WASH"],
                                       [("R06_PISO_HUMEDO_IZQ", "R06_PATA_RECEPTOR_WASH_IZQ")], "Patas del receptor WASH atraviesan el piso humedo"),
}
doc = App.openDocument(R07 + r"\cad\R07_V11_STEP.FCStd")
por_label = {}
for o in doc.Objects:
    if o.TypeId == "Part::Feature" and hasattr(o, "Shape") and not o.Shape.isNull() and o.Shape.Solids:
        por_label.setdefault(o.Label, o)


def tesela(s, tol=2.0):
    v, f = s.tessellate(tol)
    return {"v": [[round(p.x, 1), round(p.y, 1), round(p.z, 1)] for p in v], "f": [list(t) for t in f]}


out = {}
for k, (labels, comunes, titulo) in HALLAZGOS.items():
    piezas = {}
    for l in labels:
        o = por_label.get(l)
        if o is None:
            # la referencia de piso puede tener otra etiqueta
            o = next((x for x in por_label.values() if x.Name == l), None)
        if o is not None:
            piezas[l] = tesela(o.Shape)
    com = {}
    for a, b in comunes:
        if a in por_label and b in por_label:
            c = por_label[a].Shape.common(por_label[b].Shape)
            if c.Volume > 0.5:
                com[a + " & " + b] = tesela(c, 1.0)
                com[a + " & " + b]["mm3"] = round(c.Volume, 1)
    out[k] = {"titulo": titulo, "piezas": piezas, "comunes": com}
json.dump(out, open(OUT + r"\rv05_teselas.json", "w", encoding="utf-8"))
App.closeDocument(doc.Name)
print("RV05 OK", {k: len(v["piezas"]) for k, v in out.items()})
