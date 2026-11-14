#!/usr/bin/env python3
"""
CORRIDA 4 · T1 · Dosis por banda unificada de las cuatro superficies externas (solo lectura de la Corrida 3 y CFD03).

Fuentes (preregistro §9: OD y cara inferior = O7+C2 + Caso 2, A+B explicito; cara superior Caso 3 y agujero base, G7):
  OD, cara inferior : CORRIDA_3_O7C2/03_FLUENT/resultados/KPI/R3_02_03_AB/R3_02_03_AB_{od,cara_inf}_bandas_{10,2}mm.csv
  cara superior     : CFD03_ANSYS_COMPLETO/06_RESULTADOS/G8/comparacion/C3/G7_sup_bandas_{10,2}mm.csv
  agujero           : CFD03_ANSYS_COMPLETO/06_RESULTADOS/G7/G7_agujero_bandas_{10,2}mm.csv
Columnas de origen: s_centro_mm, area_banda_m2, area_mojable_m2, D_libre, D_obst_media_theta, D_obst_min_celda, J_libre, J_obst
Zonas de las caras (preregistro §3): Z1 r 450,1-521,5 mm; Z2 ventana r 521,5-617,5 mm; Z3 r 617,5-710 mm (por centro de
banda). OD: bajo z 890-1000 / alto z 1000-1405 (como R3). Agujero: una zona.
Aceptacion (prompt T1): reproducir D_media, D_min (peor banda de 10 mm, media theta) y minutos de T10 con +-0,5 %.
  t = D_req * T_vuelta / D, T_vuelta = 35,294 s.
Salidas: 03_DOSIS_TIEMPO/dosis_por_banda_unificada.csv (10 mm, oficial), dosis_por_banda_unificada_2mm.csv,
         T1_aceptacion_T10.csv. Uso: python -I -B r4_t1_dosis_unificada.py
"""
import csv
import os

B4 = "D:/CFD_Redosado/CORRIDA_4_PRIMER_LAVADO"
OUT = B4 + "/03_DOSIS_TIEMPO"
K3 = "D:/CFD_Redosado/CORRIDA_3_O7C2/03_FLUENT/resultados/KPI/R3_02_03_AB/R3_02_03_AB_"
G = "G:/Mi unidad/Semestre X/TESIS II/Sistema de aspersión/CFD03_ANSYS_COMPLETO/06_RESULTADOS"
T10 = "D:/CFD_Redosado/CORRIDA_3_O7C2/03_FLUENT/resultados/T10_tiempo_lavado.csv"
T = 35.294
FUENTES = {
    "OD": (K3 + "od_bandas_%s.csv", "O7+C2 + Caso 2 (R3_02_03_AB)"),
    "Cara inferior": (K3 + "cara_inf_bandas_%s.csv", "O7+C2 + Caso 2 (R3_02_03_AB)"),
    "Cara superior": (G + "/G8/comparacion/C3/G7_sup_bandas_%s.csv", "Caso 3 (G7; no cambia)"),
    "Agujero": (G + "/G7/G7_agujero_bandas_%s.csv", "Base = Caso 3 (G7; no cambia)"),
}


def zona(sup, s_mm):
    if sup in ("Cara inferior", "Cara superior"):
        if s_mm < 521.5:
            return "Z1_aro_interior"
        if s_mm < 617.5:
            return "Z2_ventana_proyectada"
        return "Z3_aro_exterior"
    if sup == "OD":
        return "OD_bajo_z890-1000" if s_mm < 1000 else "OD_alto_z1000-1405"
    return "agujero"


def cargar(res):
    filas = []
    for sup, (pat, caso) in FUENTES.items():
        for r in csv.DictReader(open(pat % res, encoding="utf-8")):
            s = float(r["s_centro_mm"])
            Ab, Aw = float(r["area_banda_m2"]), float(r["area_mojable_m2"])
            Dm = float(r["D_obst_media_theta"])
            Dc = float(r["D_obst_min_celda"]) if r["D_obst_min_celda"] not in ("", None) else 0.0
            filas.append(dict(superficie=sup, caso=caso, zona=zona(sup, s), s_centro_mm=s, area_banda_m2=Ab,
                              area_mojable_m2=Aw, frac_sombra_E1=(1 - Aw / Ab) if Ab > 0 else 0.0,
                              D1_media_theta=Dm, D1_peor_celda=Dc, D1_libre=float(r["D_libre"]),
                              J_obst=float(r["J_obst"]), fuente=pat % res))
    return filas


CAB = ["superficie", "caso", "zona", "s_centro_mm", "area_banda_m2", "area_mojable_m2", "frac_sombra_E1",
       "D1_media_theta", "D1_peor_celda", "D1_libre", "J_obst", "fuente"]


def escribir(filas, ruta):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CAB)
        for r in filas:
            w.writerow([("%.6g" % r[c]) if isinstance(r[c], float) else r[c] for c in CAB])


def main():
    os.makedirs(OUT, exist_ok=True)
    f10, f2 = cargar("10mm"), cargar("2mm")
    escribir(f10, OUT + "/dosis_por_banda_unificada.csv")
    escribir(f2, OUT + "/dosis_por_banda_unificada_2mm.csv")
    # aceptacion contra T10
    ref = [r for r in csv.DictReader(open(T10, encoding="utf-8")) if r["superficie"] in FUENTES]
    out, peor = [], 0.0
    for r in ref:
        sup, Dr = r["superficie"], float(r["D_req"])
        sel = [x for x in f10 if x["superficie"] == sup and x["area_mojable_m2"] > 0]
        A = sum(x["area_mojable_m2"] for x in sel)
        Dm = sum(x["area_mojable_m2"] * x["D1_media_theta"] for x in sel) / A
        Dmin = min(x["D1_media_theta"] for x in sel)
        tm, tp = Dr * T / Dm / 60, Dr * T / Dmin / 60
        e = [100 * (Dm / float(r["D_media"]) - 1), 100 * (Dmin / float(r["D_min_10mm"]) - 1),
             100 * (tm / float(r["min_media"]) - 1), 100 * (tp / float(r["min_peor_celda"]) - 1)]
        peor = max(peor, max(abs(v) for v in e))
        out.append([sup, int(Dr), "%.4f" % Dm, r["D_media"], "%.4f" % Dmin, r["D_min_10mm"], "%.3f" % tm, r["min_media"],
                    "%.3f" % tp, r["min_peor_celda"]] + ["%.3f" % v for v in e])
    with open(OUT + "/T1_aceptacion_T10.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["superficie", "D_req", "D_media_R4", "D_media_T10", "D_min_banda_R4", "D_min_T10", "min_media_R4",
                    "min_media_T10", "min_peor_banda_R4", "min_peor_T10", "err_Dmedia_pct", "err_Dmin_pct",
                    "err_tmedia_pct", "err_tpeor_pct"])
        w.writerows(out)
    for o in out:
        print(o)
    print("maximo error relativo frente a T10: %.3f %%  -> %s" % (peor, "ACEPTADO (<= 0,5 %)" if peor <= 0.5 else "NO REPRODUCE"))
    # resumen de areas
    for sup in FUENTES:
        sel = [x for x in f10 if x["superficie"] == sup]
        Ab = sum(x["area_banda_m2"] for x in sel); Aw = sum(x["area_mojable_m2"] for x in sel)
        print("%-14s S_ref %.4f m2  S_acc %.4f m2  sombra/contacto %.2f %%  peor celda min %.3f" % (
            sup, Ab, Aw, 100 * (1 - Aw / Ab), min(x["D1_peor_celda"] for x in sel)))


if __name__ == "__main__":
    main()
