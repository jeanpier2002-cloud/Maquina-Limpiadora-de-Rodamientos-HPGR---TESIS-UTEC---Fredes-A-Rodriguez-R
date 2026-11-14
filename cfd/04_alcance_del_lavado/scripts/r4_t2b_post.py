#!/usr/bin/env python3
"""
CORRIDA 4 · T2b · Post-proceso del N1 de cavidad (M8) a partir de <tag>_union.npz y <tag>_masa_destino.csv.
COTA SUPERIOR (sin jaula; rodillos abombados del STEP, o cilindros en la variante «cil»: HIPOTESIS). N1 = linea de vista.

M8 = fraccion de AREA con N1 > 0 (union sobre el barrido del rotor de 360 grados y sobre las boquillas del subconjunto).
  Rodillos: por rodillo (23 por hilera) -> media, minimo y maximo entre rodillos; flanco por profundidad s desde el extremo
  del lado de la cara (0-25, 25-50, 50-100, 100-150, 150-214 mm); extremos (cara / interior) aparte.
  Pistas: exterior (esfera) e interior (aro interior sin resaltes); resaltes aparte. Mitad superior (x < 257,5) e inferior;
  profundidad axial desde su cara (0-25 ... 150-214, 214-257,5).
Gate de T6: rodillos + pistas con N1 > 0 en >= 5 % de su area.
Uso: python -I -B r4_t2b_post.py --tag base [--tag2 sinrod ...]
Salidas: 02_CAVIDAD_N1/<tag>_M8_*.csv y figuras (solo para el tag base).
"""
import argparse
import csv
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from r4_estilo_kevin import C, ejes_coma, guardar, plt  # noqa: E402

OUT = "D:/CFD_Redosado/CORRIDA_4_PRIMER_LAVADO/02_CAVIDAD_N1"
FIG = OUT + "/figuras"
PROF = [0, 25, 50, 100, 150, 214, 257.5]
LB = 515.0
SUP = ["SUP_1_A", "SUP_2_A", "SUP_1_B", "SUP_2_B"]
INF = ["INF_EXT_A", "INF_EXT_B", "C2_A", "C2_B", "INF_INT"]


def cargar(tag):
    """tag simple, o 'nombre=tag1+tag2+...' para unir corridas por boquilla (se concatenan las boquillas)."""
    if "=" not in tag:
        Z = np.load(OUT + "/%s_union.npz" % tag)
        return {k: Z[k] for k in Z.files}
    partes = tag.split("=", 1)[1].split("+")
    Zs = [np.load(OUT + "/%s_union.npz" % t) for t in partes]
    Z = {k: Zs[0][k] for k in Zs[0].files}
    for k in ("U_fl", "U_end", "U_out", "U_in", "U_win", "boqs", "inst"):
        Z[k] = np.concatenate([z[k] for z in Zs], axis=0)
    return Z


def sub(Z, nombres):
    b = [str(x) for x in Z["boqs"]]
    idx = [b.index(n) for n in nombres if n in b]
    if not idx:
        return None
    return {k: Z[k][idx].any(axis=0) for k in ("U_fl", "U_end", "U_out", "U_in", "U_win")}


def fracciones(Z, U):
    """Lista de (superficie, fila/mitad, prof, area_total_m2, frac_media, frac_min, frac_max)."""
    A_FL, A_END, A_OUT, A_IN, XC, SC = Z["A_FL"], Z["A_END"], Z["A_OUT"], Z["A_IN"], Z["XC"], Z["SC"]
    XR = Z["X_RES"]
    fil = []
    npsi = U["U_fl"].shape[-1]
    for f, nomf in ((0, "hilera_sup"), (1, "hilera_inf")):
        Ufl = U["U_fl"][f]                                    # (23, NS, NPSI)
        for ip in range(len(PROF) - 1):
            if PROF[ip] >= 214:
                continue
            m = (SC >= PROF[ip]) & (SC < PROF[ip + 1])
            At = A_FL[m].sum() * npsi
            per = (Ufl[:, m, :] * A_FL[m][None, :, None]).sum(axis=(1, 2)) / At
            fil.append(["rodillo_flanco", nomf, "%g-%g" % (PROF[ip], PROF[ip + 1]), At * 23 * 1e-6, per.mean(), per.min(), per.max()])
        At = A_FL.sum() * npsi
        per = (Ufl * A_FL[None, :, None]).sum(axis=(1, 2)) / At
        fil.append(["rodillo_flanco", nomf, "todo", At * 23 * 1e-6, per.mean(), per.min(), per.max()])
        for e_, nome in ((0, "rodillo_extremo_cara"), (1, "rodillo_extremo_interior")):
            Ue = U["U_end"][f, :, e_]                         # (23, NRF, 12)
            At = A_END.sum() * Ue.shape[-1]
            per = (Ue * A_END[None, :, None]).sum(axis=(1, 2)) / At
            fil.append([nome, nomf, "extremo", At * 23 * 1e-6, per.mean(), per.min(), per.max()])
    nth = U["U_out"].shape[-1]
    for UU, AA, nom in ((U["U_out"], A_OUT, "pista_exterior"), (U["U_in"], A_IN, "aro_interior")):
        for mitad, msk in (("mitad_sup", XC < LB / 2), ("mitad_inf", XC >= LB / 2)):
            prof = np.where(XC < LB / 2, XC, LB - XC)
            clases = [("pista_exterior", msk)] if nom == "pista_exterior" else [
                ("pista_interior", msk & (XC > XR[0]) & (XC < XR[1])), ("resalte_interior", msk & ((XC <= XR[0]) | (XC >= XR[1])))]
            for nc, mc in clases:
                for ip in range(len(PROF) - 1):
                    m = mc & (prof >= PROF[ip]) & (prof < PROF[ip + 1])
                    if not m.any():
                        continue
                    At = AA[m].sum() * nth
                    fr = (UU[m] * AA[m][:, None]).sum() / At
                    fil.append([nc, mitad, "%g-%g" % (PROF[ip], PROF[ip + 1]), At * 1e-6, fr, fr, fr])
                At = AA[mc].sum() * nth
                fr = (UU[mc] * AA[mc][:, None]).sum() / At if At > 0 else 0.0
                fil.append([nc, mitad, "todo", At * 1e-6, fr, fr, fr])
    return fil


def gate(fil):
    """Rodillos (flanco + extremos, ambas hileras) + pistas (exterior + interior, ambas mitades)."""
    sel = [r for r in fil if r[2] in ("todo", "extremo") and r[0] in (
        "rodillo_flanco", "rodillo_extremo_cara", "rodillo_extremo_interior", "pista_exterior", "pista_interior")]
    A = sum(r[3] for r in sel)
    return sum(r[3] * r[4] for r in sel) / A, A


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="base")
    ap.add_argument("--figuras", action="store_true")
    a = ap.parse_args()
    os.makedirs(FIG, exist_ok=True)
    Z = cargar(a.tag)
    partes = a.tag.split("=", 1)[1].split("+") if "=" in a.tag else [a.tag]
    a.tag = a.tag.split("=", 1)[0]
    b = [str(x) for x in Z["boqs"]]
    subconj = [("todas", b), ("SUP (ventana sup)", [x for x in b if x in SUP]), ("INF (ventana inf)", [x for x in b if x in INF]),
               ("ramal A", [x for x in b if x.endswith("_A")]), ("ramal B", [x for x in b if x.endswith("_B")])] + [(x, [x]) for x in b]
    filas, gates = [], []
    RES = {}
    for nom, lista in subconj:
        U = sub(Z, lista)
        if U is None:
            continue
        fil = fracciones(Z, U)
        RES[nom] = fil
        g, A = gate(fil)
        gates.append([a.tag, nom, "%.5f" % g, "%.4f" % A, "ABIERTO" if g >= 0.05 else "CERRADO"])
        for r in fil:
            filas.append([a.tag, nom] + r[:3] + ["%.5f" % r[3], "%.5f" % r[4], "%.5f" % r[5], "%.5f" % r[6]])
    with open(OUT + "/%s_M8_union.csv" % a.tag, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tag", "subconjunto", "superficie", "fila_o_mitad", "prof_mm", "area_total_m2", "frac_N1_media",
                    "frac_N1_min_rodillo", "frac_N1_max_rodillo"])
        w.writerows(filas)
    with open(OUT + "/%s_M8_gate.csv" % a.tag, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tag", "subconjunto", "frac_area_rodillos_mas_pistas_N1", "area_m2", "gate_T6_5pct"])
        w.writerows(gates)
    # prueba (a): ventana en el plano de la cara
    pa = []
    for nom, lista, iv in (("SUP", [x for x in b if x in SUP], 0), ("INF", [x for x in b if x in INF], 1)):
        U = sub(Z, lista)
        if U is None:
            continue
        cov = U["U_win"][iv].mean()
        pa.append([a.tag, nom, "%.4f" % (100 * cov)])
    with open(OUT + "/%s_prueba_a_ventana.csv" % a.tag, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["tag", "ventana", "pct_celdas_ventana_con_N1"]); w.writerows(pa)
    # instantaneo (por boquilla): area de flanco iluminada en una posicion del rotor / area de flanco de la hilera
    A_fl_tot = Z["A_FL"].sum() * Z["U_fl"].shape[-1] * 23
    ins = [[a.tag, n, "%.5f" % (Z["inst"][i, 0] / (int(Z["nphi"]) * A_fl_tot)), "%.5f" % (Z["inst"][i, 1] / (int(Z["nphi"]) * A_fl_tot))]
           for i, n in enumerate(b)]
    with open(OUT + "/%s_instantaneo.csv" % a.tag, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["tag", "boquilla", "frac_flanco_hilera_sup_instant_media", "frac_flanco_hilera_inf_instant_media"])
        w.writerows(ins)
    # destino de la masa que entra por cada ventana (N1 balistico)
    M = []
    for t_ in partes:
        M += list(csv.DictReader(open(OUT + "/%s_masa_destino.csv" % t_, encoding="utf-8")))
    md = []
    for ven in ("sup", "inf"):
        sel = [r for r in M if r["ventana"] == ven]
        tot = sum(float(r["kg_por_vuelta"]) for r in sel)
        agg = {}
        for r in sel:
            k = (r["destino"], r["prof_rango_mm"])
            agg[k] = agg.get(k, 0.0) + float(r["kg_por_vuelta"])
        for (d_, p_), v in sorted(agg.items()):
            md.append([a.tag, ven, d_, p_, "%.5e" % v, "%.4f" % (100 * v / tot if tot else 0)])
    with open(OUT + "/%s_masa_destino_resumen.csv" % a.tag, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["tag", "ventana", "destino", "prof_mm", "kg_por_vuelta", "pct_de_lo_que_entra"])
        w.writerows(md)
    # impresion
    print("GATE:", gates[:5])
    print("prueba a:", pa)
    for nom in ("todas",):
        for r in RES[nom]:
            print("%-26s %-11s %-10s A %.4f m2  N1 media %.4f  [min %.4f max %.4f]" % (r[0], r[1], r[2], r[3], r[4], r[5], r[6]))
    print("instantaneo:", ins)
    for r in md:
        print(r)
    if not a.figuras:
        return
    # figuras: N1 por profundidad (todas las boquillas), una por ventana
    for f_, (fila, mitad, nomfig) in enumerate((("hilera_sup", "mitad_sup", "T2_M8_prof_ventana_sup"),
                                                ("hilera_inf", "mitad_inf", "T2_M8_prof_ventana_inf"))):
        R = RES["todas"]
        bins = ["0-25", "25-50", "50-100", "100-150", "150-214"]
        series = [("rodillo_flanco", fila, "flanco de rodillo"), ("pista_exterior", mitad, "pista exterior"),
                  ("pista_interior", mitad, "pista interior")]
        fig, ax = plt.subplots()
        xs = np.arange(len(bins)); wbar = 0.26
        datos = []
        for i, (sn, fm, lab) in enumerate(series):
            v = []
            for bb in bins:
                r = [q for q in R if q[0] == sn and q[1] == fm and q[2] == bb]
                v.append(100 * r[0][4] if r else 0.0)
            ax.bar(xs + (i - 1) * wbar, v, wbar, color=C[i], label=lab)
            for xx, vv in zip(xs + (i - 1) * wbar, v):
                ax.text(xx, vv + 1, ("%.0f" % vv).replace(".", ","), ha="center", fontsize=9)
            datos += [[lab, bb, "%.3f" % vv] for bb, vv in zip(bins, v)]
        ax.set_xticks(xs); ax.set_xticklabels([x.replace("-", "–") for x in bins])
        ax.set_xlabel("profundidad desde la cara (mm)")
        ax.set_ylabel("área con línea de vista N1 (%)")
        ax.set_ylim(0, 105)
        ejes_coma(ax, x=False)
        ax.legend(fontsize=10, loc="upper right")
        guardar(fig, FIG, nomfig, ["superficie", "prof_mm", "pct_area_N1"], datos)


if __name__ == "__main__":
    main()
