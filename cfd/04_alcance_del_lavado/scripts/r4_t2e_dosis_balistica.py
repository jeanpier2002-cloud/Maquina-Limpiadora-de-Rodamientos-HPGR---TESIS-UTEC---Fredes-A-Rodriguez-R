#!/usr/bin/env python3
"""
CORRIDA 4 · T2e · Orden de magnitud EXPLORATORIO de la dosis balistica en la cavidad (N1 balistico: rayos rectos con la masa
de la boquilla repartida uniforme por angulo, como gen_abanico; SIN arrastre, gravedad, rebote, pelicula ni escurrimiento).
NO es N2 (no es CFD) y NO entra en las conclusiones: solo sirve para dimensionar el plan siguiente (T6 / pelicula).
  D_bal = (kg/vuelta que llega a la region) / (area de la region con N1 > 0)   [kg m-2 vuelta-1]
  vueltas para D_req = D_req / D_bal (65 / 183 / 305).
Entradas: <tag>_masa_destino_resumen.csv y <tag>_M8_union.csv (r4_t2b_post.py). Salida: 02_CAVIDAD_N1/<tag>_dosis_balistica.csv
Uso: python -I -B r4_t2e_dosis_balistica.py --tag d2400
"""
import argparse
import csv

OUT = "D:/CFD_Redosado/CORRIDA_4_PRIMER_LAVADO/02_CAVIDAD_N1"
T = 35.294
ap = argparse.ArgumentParser()
ap.add_argument("--tag", default="base")
a = ap.parse_args()
MD = list(csv.DictReader(open(OUT + "/%s_masa_destino_resumen.csv" % a.tag, encoding="utf-8")))
M8 = [r for r in csv.DictReader(open(OUT + "/%s_M8_union.csv" % a.tag, encoding="utf-8")) if r["subconjunto"] == "todas"]


def masa(ven, dest, prof=None):
    return sum(float(r["kg_por_vuelta"]) for r in MD if r["ventana"] == ven and r["destino"] == dest and (prof is None or r["prof_mm"] == prof))


def area(sup, fila, prof):
    r = [q for q in M8 if q["superficie"] == sup and q["fila_o_mitad"] == fila and q["prof_mm"] == prof][0]
    return float(r["area_total_m2"]), float(r["frac_N1_media"])


REG = [("ventana sup", "extremo de rodillo (lado cara), hilera sup", masa("sup", "rodillo_extremo_cara"),
        area("rodillo_extremo_cara", "hilera_sup", "extremo"))]
for p in ("0-25", "25-50", "50-100", "100-150"):
    REG.append(("ventana sup", "flanco de rodillo %s mm, hilera sup" % p, masa("sup", "rodillo_flanco", p), area("rodillo_flanco", "hilera_sup", p)))
REG.append(("ventana sup", "pista exterior, mitad sup (todas las prof.)", masa("sup", "pista_exterior"), area("pista_exterior", "mitad_sup", "todo")))
REG.append(("ventana sup", "pista interior, mitad sup (todas las prof.)", masa("sup", "pista_interior"), area("pista_interior", "mitad_sup", "todo")))
REG.append(("ventana sup", "extremo interior de rodillo, hilera inf", masa("sup", "rodillo_extremo_interior"),
            area("rodillo_extremo_interior", "hilera_inf", "extremo")))
REG.append(("ventana inf", "extremo de rodillo (lado cara), hilera inf", masa("inf", "rodillo_extremo_cara"),
            area("rodillo_extremo_cara", "hilera_inf", "extremo")))
REG.append(("ventana inf", "resalte del aro interior, mitad inf", masa("inf", "resalte_interior"), area("resalte_interior", "mitad_inf", "todo")))
REG.append(("ventana inf", "pista exterior 0-50 mm, mitad inf", masa("inf", "pista_exterior", "0-25") + masa("inf", "pista_exterior", "25-50"),
            (area("pista_exterior", "mitad_inf", "0-25")[0] + area("pista_exterior", "mitad_inf", "25-50")[0],
             (area("pista_exterior", "mitad_inf", "0-25")[0] * area("pista_exterior", "mitad_inf", "0-25")[1] +
              area("pista_exterior", "mitad_inf", "25-50")[0] * area("pista_exterior", "mitad_inf", "25-50")[1]) /
             (area("pista_exterior", "mitad_inf", "0-25")[0] + area("pista_exterior", "mitad_inf", "25-50")[0]))))
filas = []
for ven, nom, m, (A, f) in REG:
    Ail = A * f
    D = m / Ail if Ail > 0 else 0.0
    fila = [ven, nom, "%.4g" % m, "%.4f" % A, "%.4f" % f, "%.3f" % D]
    for Dr in (65, 183, 305):
        fila.append("%.1f" % (Dr / D * T / 60) if D > 0 else "inf")
    filas.append(fila)
with open(OUT + "/%s_dosis_balistica.csv" % a.tag, "w", newline="", encoding="utf-8") as fo:
    w = csv.writer(fo)
    w.writerow(["ventana", "region", "kg_por_vuelta", "area_m2", "frac_N1", "D_bal_kg_m2_vuelta_en_area_visible",
                "min_D65", "min_D183", "min_D305"])
    w.writerows(filas)
for r in filas:
    print(r)
