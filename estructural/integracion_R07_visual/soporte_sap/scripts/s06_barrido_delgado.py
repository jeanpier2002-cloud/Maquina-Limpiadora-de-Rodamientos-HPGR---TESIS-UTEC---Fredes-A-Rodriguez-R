# -*- coding: utf-8 -*-
"""Soporte superior: barrido de perfiles delgados (03/11/2026). El usuario: «hay que cambiar eso, me pueden observar por sobrediseño».
Lee resultados_cabina/K*.json (rigidez nominal, rotor real) y aplica criterios FUNCIONALES fijados antes de correr [HIPOTESIS del autor]:
  C1 resistencia: D/C <= 0,9 (AISC 360-16 LRFD, U1-U3);
  C2 servicio: flecha de la viga en S1 <= L/1000 (alineacion de la correa y del cojinete);
  C3 accidental: lateral del cojinete superior en S2 <= 3,0 mm (0,25 grados de desalineacion de la correa en ~700 mm) [VERIFICAR guia del fabricante];
  C4 dinamica: f1 >= 3 Hz y ningun modo en 18,6-28,0 Hz (motor 23,3 Hz +-20 %) [VERIFICAR velocidad del motor].
Costo (base del presupuesto C1, clase 4): A36 S/ 10,9/kg + taller 0,15 h/kg x S/ 50,5/h; inox 304 S/ 19,4/kg + taller igual.
Postes dentro de la cabina (zona humeda): inox, mas 4 pasos sellados por el techo (S/ 150 c/u) y 4 montantes SHS60x3 de 2,6 m en los muros,
que pierden su marco (D-065 usa los postes como marco) [HIPOTESIS].
Ajuste de los criterios con datos medidos (03/11, despues del primer barrido; se informan los dos juegos):
  C3' lateral <= 5,0 mm: la holgura radial real en el paso del eje por el techo es 22,9 mm (eje R57,15 frente al collar R80 de
      R04_PENETRACION_CUBIERTA) y 31 mm en el laberinto (R07_H_LABERINTO_FIJO R115 frente al giratorio R146), CAD V17B; margen 4,5.
      La correa no limita: el motor y el eje van en el mismo cartucho y se mueven juntos.
  C4' banda del motor 17,6-26,4 Hz: n = 1,7 rpm x 2 (HTD 2:1) x 388 (S47R17, D-056) = 1 319 rpm = 22,0 Hz, +-20 %; solo modos con
      masa participante >= 0,05 en UX, UY, UZ o RZ.
Salidas: resultados_cabina/BARRIDO_DELGADO.csv y .json."""
import csv
import glob
import json
import math
import os

R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados_cabina")
A36, INOX, TALLER = 3.16 * 3.448, 5.62 * 3.448, 0.15 * 50.5
EXTRA_DENTRO = 4 * 150 + 4 * 2.6 * 5.2 * (INOX + TALLER)
filas = []
for f in sorted(glob.glob(os.path.join(R, "K*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    o = dict(x.split("=") for x in d["opciones"].split(";") if "=" in x)
    if float(o.get("t", 0)) > 0 or o.get("vigas", "no") == "no" or o.get("postes", "no") == "no":
        continue
    xc = float(o.get("xc", 2020)); dentro = xc < 2000
    lat = max(math.hypot(*d["cojinetes"][k]["sup"][:2]) for k in d["cojinetes"] if k.startswith("S2"))
    fl = d["flecha_apoyo_S1_mm"]; L = 2 * xc
    fr = d["frecuencias_Hz"]; banda = [round(x, 1) for x in fr if 18.6 <= x <= 28.0]
    part = d["participacion"]
    banda2 = [round(x, 1) for i, x in enumerate(fr) if 17.6 <= x <= 26.4 and max(part[i]) >= 0.05]
    masa = d["masa_barras_kg"]
    costo = masa * ((INOX if dentro else A36) + TALLER) + (EXTRA_DENTRO if dentro else 0)
    c = {"C1": d["DC_max"] <= 0.9, "C2": fl <= L / 1000, "C3": lat <= 3.0, "C4": fr[0] >= 3.0 and not banda}
    c2 = {"C3b": lat <= 5.0, "C4b": fr[0] >= 3.0 and not banda2}
    filas.append({"caso": d["caso"], "posicion": "dentro x±%g" % xc if dentro else "muros x±2020", "postes": o["postes"], "vigas": o["vigas"],
                  "bases": o.get("bases", ""), "masa_kg": round(masa, 1), "DC": round(d["DC_max"], 3), "flecha_mm": round(fl, 2), "L_flecha": round(L / fl),
                  "lateral_mm": round(lat, 2), "f1_Hz": round(fr[0], 2), "modos_banda_motor": banda,
                  "M_base_kNm": round(d["reacciones"]["U3_AXP"]["M_max"] / 1e6, 2) if d["reacciones"]["U3_AXP"]["M_max"] else 0.0,
                  "modos_banda_ajustada": banda2, "costo_PEN": round(costo), **c, "cumple": all(c.values()), **c2,
                  "cumple_ajustado": c["C1"] and c["C2"] and all(c2.values())})
filas.sort(key=lambda r: (not r["cumple_ajustado"], r["costo_PEN"]))
with open(os.path.join(R, "BARRIDO_DELGADO.csv"), "w", newline="", encoding="utf-8") as fo:
    w = csv.DictWriter(fo, fieldnames=list(filas[0].keys())); w.writeheader(); w.writerows(filas)
json.dump({"criterios": "C1 D/C<=0,9; C2 flecha<=L/1000; C3 lateral S2<=3,0 mm; C4 f1>=3 Hz y sin modos 18,6-28 Hz", "extra_dentro_PEN": round(EXTRA_DENTRO),
           "filas": filas}, open(os.path.join(R, "BARRIDO_DELGADO.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for r in filas:
    print("%-30s %-14s %-15s %-15s %6.1f kg D/C %.3f flecha %.2f (L/%d) lat %.2f f1 %.2f banda %s  S/ %d %s %s" % (
        r["caso"], r["posicion"], r["postes"], r["vigas"], r["masa_kg"], r["DC"], r["flecha_mm"], r["L_flecha"], r["lateral_mm"], r["f1_Hz"],
        r["modos_banda_ajustada"], r["costo_PEN"], "inicial:" + ("SI" if r["cumple"] else "no"), "ajustado:" + ("SI" if r["cumple_ajustado"] else "no " + "".join(k for k in ("C1", "C2", "C3b", "C4b") if not r[k]))))
