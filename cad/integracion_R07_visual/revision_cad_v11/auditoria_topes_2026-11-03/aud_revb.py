# -*- coding: utf-8 -*-
"""Solo lectura: compara en R07 V18C las piezas de MES-400, MES-800 y MES-900 con las de sus fuentes (V10 y V17B)."""
import json
import re

import FreeCAD as App

R07 = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual"
doc = App.openDocument(R07 + r"\cad\R07_V18C_STEP.FCStd", True)
d17 = App.openDocument(R07 + r"\cad\R07_V17B_STEP.FCStd", True)
d10 = App.openDocument(R07 + r"\cad\R07_V10_STEP.FCStd", True)
sal = {}


def grupos_de(o):
    return [g.Label for g in o.InList if g.isDerivedFrom("App::DocumentObjectGroup")]


def info(o):
    b = o.Shape.BoundBox
    return {"vol": round(o.Shape.Volume, 1), "caja": [round(v, 1) for v in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)], "vis": bool(o.Visibility), "grupos": grupos_de(o)}


def comp(label, a, b):
    ra, rb = a.getObjectsByLabel(label), b.getObjectsByLabel(label)
    if not ra or not rb:
        return {"label": label, "falta_en": "V18C" if not ra else "fuente"}
    ia, ib = info(ra[0]), info(rb[0])
    igual = abs(ia["vol"] - ib["vol"]) < 0.5 and ia["caja"] == ib["caja"]
    return {"label": label, "igual": igual, "vis_V18C": ia["vis"], "grupos_V18C": ia["grupos"], **({} if igual else {"V18C": ia, "fuente": ib})}


# ---------- MES-900 ----------
r = []
for o in d17.Objects:
    if o.Label.startswith("R07_V17_") and re.search(r"PEDESTAL|FALDON|ALMOHADILLA|ANCLAJES|GROUT", o.Label):
        r.append(comp(o.Label, doc, d17))
sal["mes900_total"] = len(r)
sal["mes900_diferentes"] = [x for x in r if not x.get("igual")]
sal["mes900_no_visibles"] = [x["label"] for x in r if x.get("igual") and not x.get("vis_V18C")]
sal["mes900_grupos"] = sorted({g for x in r for g in x.get("grupos_V18C", [])})

# ---------- MES-800 ----------
P = "R07_V14_"
labs = []
for n in ("CADENA_08B", "PINON_TENSOR", "EJE_TENSOR", "PINON_MOTRIZ", "RODAMIENTO_EJE", "PLACA_RODAMIENTO", "CHAPA_FRONTAL_M04", "RIGIDIZADORES_M04", "BRAZO_HORIZONTAL", "BRAZO_VERTICAL", "GOLPEADOR", "ENGANCHE_CADENA"):
    labs += [P + n + "_D", P + n + "_I"]
labs += [P + "SOPORTE_TENSOR_D", P + "SOPORTE_TENSOR_I", P + "TOPE_LAVADO_D", P + "TOPE_LAVADO_I", P + "TOPE_CARGA_D", P + "TOPE_CARGA_I", P + "RODAMIENTO_MURO", P + "EJE_MOTRIZ", P + "RETEN_MURO", P + "REDUCTOR_NMRV050_I5", P + "EJE_VOLANTE", P + "SOPORTE_VOLANTE", P + "EMBOLO_BLOQUEO", P + "DISCO_BLOQUEO", P + "VOLANTE_D400", P + "EMPUNADURA"]
labs += [P + "MENSULA_GUIA_%s_%02d" % (l, i) for l in "DI" for i in range(6, 13)]
labs += [P + "ALMOHADILLA_UHMW_%s_%02d" % (l, i) for l in "DI" for i in range(6, 13)]
r = [comp(l, doc, d17) for l in labs]
sal["mes800_total"] = len(r)
sal["mes800_diferentes"] = [x for x in r if not x.get("igual")]
sal["mes800_no_visibles"] = [x["label"] for x in r if not x.get("vis_V18C", True)]
sal["mes800_V18C_nuevos"] = [{**info(o), "label": o.Label} for o in doc.Objects if o.Label.startswith("R07_V18C_") and hasattr(o, "Shape") and o.Shape.Volume > 0]

# ---------- MES-400 ----------
r = []
for o in doc.Objects:
    if hasattr(o, "Shape") and re.search(r"STOP|TOPE_RET|RETENCION|RETENTION", o.Label, re.I) and o.Shape.Volume > 0:
        i = info(o)
        i["label"] = o.Label
        r.append(i)
sal["topes_en_V18C"] = r
sal["topes_V10"] = [{**info(o), "label": o.Label} for o in d10.Objects if hasattr(o, "Shape") and re.search(r"STOP", o.Label) and o.Shape.Volume > 0]
# ala de la viga M06 y M05 vigentes
sal["vigas"] = [{**info(o), "label": o.Label} for o in doc.Objects if hasattr(o, "Shape") and re.search(r"M0?[456]\b|W6|VIGA_M|_M05|_M06", o.Label) and o.Shape.Volume > 0 and o.Visibility][:14]
json.dump(sal, open(r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\revision_cad_v11\auditoria_topes_2026-11-03\aud_revb.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("LISTO")
