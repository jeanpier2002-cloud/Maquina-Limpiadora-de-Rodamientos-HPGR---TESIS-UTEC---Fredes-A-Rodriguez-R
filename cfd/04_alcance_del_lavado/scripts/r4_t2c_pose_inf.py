#!/usr/bin/env python3
"""
CORRIDA 4 · T2c (ventana INFERIOR) · Barrido de pose de UNA boquilla generica bajo la cara inferior (PROPUESTA; [INTERFAZ ISMAEL]).
N1 de cavidad (COTA SUPERIOR: sin jaula; rodillos abombados), con los obstaculos de la mesa (PAD, topes, vigas de rayos_r05).
Restriccion geometrica (no es resultado): bajo la cara inferior, las bases de PAD ocupan r 583-743 mm (z 805-850) y los
casquetes r 638-688 (z 850-890); los topes llegan a r 780 (z 800-920). Una boquilla que gira con el rotor solo cabe por
DENTRO (r < 583 mm, bajo el aro interior) o por FUERA (r > 780 mm, como INF_EXT a 840 mm).
Pose: r_n, z_n (altura del vertice), elevacion del eje sobre la horizontal (hacia la ventana), inclinacion tangencial,
abanico radial (plano meridiano) o tangencial.
Metrica: rodillos de la hilera INFERIOR (flanco + extremos) + pistas exterior e interior de la mitad inferior con N1 > 0.
Salida: 02_CAVIDAD_N1/T2c_pose_inf_<grupo>.csv. Uso: python -I -B r4_t2c_pose_inf.py --grupo interior|exterior [--fan radial]
"""
import argparse
import csv
import itertools
import math
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import r4_t2_cavidad_n1 as T  # noqa: E402


def boquilla(rn, zn, el, at, fan, hacia_afuera):
    sr = 1.0 if hacia_afuera else -1.0
    e = np.array([sr * math.cos(math.radians(el)), math.tan(math.radians(at)) * math.cos(math.radians(el)), math.sin(math.radians(el))])
    e /= np.linalg.norm(e)
    nrm = np.array([0.0, 1.0, 0.0]) if fan == "radial" else np.array([e[2], 0.0, -e[0]])
    nrm = nrm - (nrm @ e) * e; nrm /= np.linalg.norm(nrm)
    return {"vertice_m": [rn / 1000.0, 0.0, zn / 1000.0], "eje": list(e), "normal_abanico": list(nrm), "q_Lmin": 9.19, "angulo_deg": 50.0}


def n1_inf(b, n_plano, dphi):
    P0, D0, m0 = T.abanico(b, n_plano)
    nphi = int(round(360.0 / dphi))
    U_fl = np.zeros((T.NROD, T.NS, T.NPSI), bool)
    U_end = np.zeros((T.NROD, 2, len(T.A_END), 12), bool)
    U_out = np.zeros((T.NXP, T.NTH), bool); U_in = np.zeros((T.NXP, T.NTH), bool)
    n_ent = 0
    for j0 in range(0, nphi, 48):
        js = np.arange(j0, min(j0 + 48, nphi))
        Ps, Us = [], []
        for j in js:
            ph = math.radians(j * dphi); c, s = math.cos(ph), math.sin(ph)
            Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
            Ps.append(P0 @ Rz.T); Us.append(D0 @ Rz.T)
        Pm = np.vstack(Ps); Um = np.vstack(Us)
        dest, tt, H = T.RR.trazar(Pm, Um, obst=True)
        rH = np.hypot(H[:, 0], H[:, 1]) * 1000.0
        w_ = np.where((dest == "cara_inf") & (rH >= T.W_IN) & (rH <= T.W_OUT))[0]
        n_ent += len(w_)
        if not len(w_):
            continue
        Pb, Ub = T.a_marco_rodamiento(H[w_], Um[w_]); Pb = Pb - Ub
        cod, tc = T.marchar(Pb, Ub, 0.0, False, True)
        Q = Pb + tc[:, None] * Ub
        sr = cod == 1
        if sr.any():
            dr, fil, kk, ss, dd = T.prueba_rodillos(Q[sr] + 1e-3 * Ub[sr], 0.0, False)
            ss = np.clip(ss, 0, T.L_ROD); psi = np.zeros(sr.sum())
            for k in np.unique(kk[fil == 1]):
                mk = (fil == 1) & (kk == k)
                c1, ax_, eo, et = T.ejes_rodillo(1, k, 0.0)
                V = Q[sr][mk] - c1
                psi[mk] = np.degrees(np.arctan2(V @ et, V @ eo)) % 360
            f1 = fil == 1
            ext0 = ss < 0.05; ext1 = ss > T.L_ROD - 0.05; fl = ~(ext0 | ext1) & f1
            isb = np.minimum((ss / T.DS).astype(int), T.NS - 1); ip = np.minimum((psi / T.DPSI).astype(int), T.NPSI - 1)
            U_fl[kk[fl], isb[fl], ip[fl]] = True
            irf = np.minimum((dd / T.DRF).astype(int), len(T.A_END) - 1); ipf = np.minimum((psi / T.DPSIF).astype(int), 11)
            for e_, me in ((0, ext0 & f1), (1, ext1 & f1)):
                U_end[kk[me], e_, irf[me], ipf[me]] = True
        x = Q[:, 0]; th = np.degrees(np.arctan2(Q[:, 2], Q[:, 1])) % 360
        for cval, UU in ((2, U_in), (3, U_out)):
            sc_ = (cod == cval) & (x >= T.LB / 2)
            ix = np.clip((x[sc_] / T.DXP).astype(int), 0, T.NXP - 1); itt = np.minimum((th[sc_] / T.DTH).astype(int), T.NTH - 1)
            UU[ix, itt] = True
    A_fl = T.A_FL.sum() * T.NPSI * T.NROD
    f_fl = (U_fl * T.A_FL[None, :, None]).sum() / A_fl
    A_e = T.A_END.sum() * 12 * T.NROD * 2
    f_e = (U_end * T.A_END[None, None, :, None]).sum() / A_e
    msk_o = T.XC >= T.LB / 2
    msk_i = msk_o & (T.XC < T.X_RES_B)
    A_o = T.A_OUT[msk_o].sum() * T.NTH; A_i = T.A_IN[msk_i].sum() * T.NTH
    f_o = (U_out[msk_o] * T.A_OUT[msk_o][:, None]).sum() / A_o
    f_i = (U_in[msk_i] * T.A_IN[msk_i][:, None]).sum() / A_i
    f_tot = (f_fl * A_fl + f_e * A_e + f_o * A_o + f_i * A_i) / (A_fl + A_e + A_o + A_i)
    return dict(tot=f_tot, flanco=f_fl, extremos=f_e, pista_ext=f_o, pista_int=f_i, frac_entra=n_ent / (len(m0) * nphi))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grupo", required=True, choices=["interior", "exterior", "referencia"])
    ap.add_argument("--fan", default="radial,tangencial")
    ap.add_argument("--n-plano", type=int, default=150)
    ap.add_argument("--dphi", type=float, default=0.5)
    a = ap.parse_args()
    t0 = time.time()
    if a.grupo == "interior":
        conf = list(itertools.product((500.0, 540.0), (855.0, 870.0), (30.0, 45.0, 60.0, 75.0), (0.0, 20.0, 40.0), a.fan.split(",")))
        afuera = True
    elif a.grupo == "exterior":
        conf = list(itertools.product((800.0, 840.0), (855.0, 870.0), (5.0, 10.0, 15.0, 20.0), (0.0, 20.0, 40.0), a.fan.split(",")))
        afuera = False
    else:   # pose parecida a INF_EXT (r 840, z 853,8, eje 15 grados, abanico 50 grados aqui) como referencia
        conf = [(840.0, 853.8, 15.0, 0.0, "radial")]
        afuera = False
    filas = []
    for rn, zn, el, at, fan in conf:
        r = n1_inf(boquilla(rn, zn, el, at, fan, afuera), a.n_plano, a.dphi)
        filas.append([a.grupo, rn, zn, el, at, fan] + ["%.5f" % r[k] for k in ("tot", "flanco", "extremos", "pista_ext", "pista_int", "frac_entra")])
        print("%s r %4.0f z %4.0f el %3.0f at %3.0f %-10s -> tot %.4f flanco %.4f ext %.4f pe %.4f pi %.4f entra %.3f (%.0f s)" % (
            a.grupo, rn, zn, el, at, fan, r["tot"], r["flanco"], r["extremos"], r["pista_ext"], r["pista_int"], r["frac_entra"],
            time.time() - t0), flush=True)
    suf = a.grupo + ("" if a.fan == "radial,tangencial" else "_" + a.fan.replace(",", "_"))
    with open(T.OUT + "/T2c_pose_inf_%s.csv" % suf, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["grupo", "r_vertice_mm", "z_vertice_mm", "elevacion_deg", "incl_tangencial_deg", "abanico", "frac_N1_total",
                    "frac_N1_flanco", "frac_N1_extremos", "frac_N1_pista_ext", "frac_N1_pista_int", "frac_rayos_entran_ventana"])
        w.writerows(filas)
    print("listo en %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
