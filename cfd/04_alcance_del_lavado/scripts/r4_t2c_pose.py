#!/usr/bin/env python3
"""
CORRIDA 4 · T2c · Barrido de pose de UNA boquilla generica sobre la ventana superior (PROPUESTA, no cambio; [INTERFAZ ISMAEL]).
N1 de cavidad (COTA SUPERIOR: sin jaula; rodillos abombados del STEP), mismo trazador que r4_t2_cavidad_n1.py.
Boquilla VeeJet de 50 grados (como SUP_1/SUP_2), 3 planos en +-1 grado, n_plano rayos, barrido del rotor 360 grados (dphi).
Pose: radio del vertice r_n, altura h sobre la cara superior, inclinacion radial a_r (+ = el eje apunta hacia r creciente),
inclinacion tangencial a_t (+ = hacia theta creciente), abanico «radial» (plano del abanico = plano meridiano, como SUP) o
«tangencial» (plano del abanico perpendicular al radio).
Metrica: fraccion de area con N1 > 0 de (rodillos de la hilera superior: flanco + extremos) + (pistas exterior e interior de
la mitad superior), y por separado flanco de rodillo y pistas. La matriz completa se informa; el maximo es solo propuesta.
Salida: 02_CAVIDAD_N1/T2c_pose.csv, figuras/T2c_pose_*.png. Uso: python -I -B r4_t2c_pose.py [--rapido]
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
from r4_estilo_kevin import C, ejes_coma, guardar, plt  # noqa: E402


def boquilla(rn, h, ar, at, fan):
    """Vertice en (rn, 0, Z_TOP + h); eje: -z inclinado ar hacia +x (radial) y at hacia +y (tangencial)."""
    e = np.array([math.tan(math.radians(ar)), math.tan(math.radians(at)), -1.0]); e /= np.linalg.norm(e)
    if fan == "radial":
        nrm = np.array([0.0, 1.0, 0.0])      # abanico en el plano x-z (meridiano)
    else:
        nrm = np.array([1.0, 0.0, 0.0])      # abanico en el plano y-z (tangencial)
    nrm = nrm - (nrm @ e) * e; nrm /= np.linalg.norm(nrm)
    return {"vertice_m": [rn / 1000.0, 0.0, T.Z_TOP + h / 1000.0], "eje": list(e), "normal_abanico": list(nrm),
            "q_Lmin": 9.19, "angulo_deg": 50.0}


def n1(b, n_plano, dphi):
    P0, D0, m0 = T.abanico(b, n_plano)
    nphi = int(round(360.0 / dphi))
    U_fl = np.zeros((T.NROD, T.NS, T.NPSI), bool)
    U_end = np.zeros((T.NROD, 2, len(T.A_END), 12), bool)
    U_out = np.zeros((T.NXP, T.NTH), bool); U_in = np.zeros((T.NXP, T.NTH), bool)
    m_ent = 0.0
    for j0 in range(0, nphi, 48):
        js = np.arange(j0, min(j0 + 48, nphi))
        Ps, Us = [], []
        for j in js:
            ph = math.radians(j * dphi); c, s = math.cos(ph), math.sin(ph)
            Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
            Ps.append(P0 @ Rz.T); Us.append(D0 @ Rz.T)
        Pm = np.vstack(Ps); Um = np.vstack(Us)
        dest, tt, H = T.RR.trazar(Pm, Um, obst=False)
        rH = np.hypot(H[:, 0], H[:, 1]) * 1000.0
        w_ = np.where((dest == "sup") & (rH >= T.W_IN) & (rH <= T.W_OUT))[0]
        m_ent += len(w_)
        if not len(w_):
            continue
        Pb, Ub = T.a_marco_rodamiento(H[w_], Um[w_]); Pb = Pb - Ub
        cod, tc = T.marchar(Pb, Ub, 0.0, False, True)
        Q = Pb + tc[:, None] * Ub
        sr = cod == 1
        if sr.any():
            dr, fil, kk, ss, dd = T.prueba_rodillos(Q[sr] + 1e-3 * Ub[sr], 0.0, False)
            ss = np.clip(ss, 0, T.L_ROD); psi = np.zeros(sr.sum())
            for k in np.unique(kk[fil == 0]):
                mk = (fil == 0) & (kk == k)
                c1, ax_, eo, et = T.ejes_rodillo(0, k, 0.0)
                V = Q[sr][mk] - c1
                psi[mk] = np.degrees(np.arctan2(V @ et, V @ eo)) % 360
            f0 = fil == 0
            ext0 = ss < 0.05; ext1 = ss > T.L_ROD - 0.05; fl = ~(ext0 | ext1) & f0
            isb = np.minimum((ss / T.DS).astype(int), T.NS - 1); ip = np.minimum((psi / T.DPSI).astype(int), T.NPSI - 1)
            U_fl[kk[fl], isb[fl], ip[fl]] = True
            irf = np.minimum((dd / T.DRF).astype(int), len(T.A_END) - 1); ipf = np.minimum((psi / T.DPSIF).astype(int), 11)
            for e_, me in ((0, ext0 & f0), (1, ext1 & f0)):
                U_end[kk[me], e_, irf[me], ipf[me]] = True
        x = Q[:, 0]; th = np.degrees(np.arctan2(Q[:, 2], Q[:, 1])) % 360
        for cval, UU in ((2, U_in), (3, U_out)):
            sc_ = (cod == cval) & (x < T.LB / 2)
            ix = np.clip((x[sc_] / T.DXP).astype(int), 0, T.NXP - 1); itt = np.minimum((th[sc_] / T.DTH).astype(int), T.NTH - 1)
            UU[ix, itt] = True
    npsi = T.NPSI
    A_fl = T.A_FL.sum() * npsi * T.NROD
    f_fl = (U_fl * T.A_FL[None, :, None]).sum() / A_fl
    A_e = T.A_END.sum() * 12 * T.NROD * 2
    f_e = (U_end * T.A_END[None, None, :, None]).sum() / A_e
    msk_o = T.XC < T.LB / 2
    msk_i = msk_o & (T.XC > T.X_RES_T)
    A_o = T.A_OUT[msk_o].sum() * T.NTH; A_i = T.A_IN[msk_i].sum() * T.NTH
    f_o = (U_out[msk_o] * T.A_OUT[msk_o][:, None]).sum() / A_o
    f_i = (U_in[msk_i] * T.A_IN[msk_i][:, None]).sum() / A_i
    f_tot = (f_fl * A_fl + f_e * A_e + f_o * A_o + f_i * A_i) / (A_fl + A_e + A_o + A_i)
    return dict(tot=f_tot, flanco=f_fl, extremos=f_e, pista_ext=f_o, pista_int=f_i,
                frac_entra=m_ent / (len(m0) * nphi))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--n-plano", type=int, default=150)
    ap.add_argument("--dphi", type=float, default=0.5)
    ap.add_argument("--fan", default="radial,tangencial")
    a = ap.parse_args()
    t0 = time.time()
    RN = (545.0, 570.0, 595.0)
    HH = (100.0, 190.0)
    AR = (-20.0, -10.0, 0.0, 10.0, 20.0)
    AT = (0.0, 20.0, 40.0)
    FAN = tuple(a.fan.split(","))
    filas = []
    # referencia: SUP_1_A y SUP_2_A reales (h = 189,3 mm, eje vertical, abanico radial)
    for rn, h, ar, at, fan in itertools.product(RN, HH, AR, AT, FAN):
        if a.rapido and (fan == "tangencial" or h == 100.0):
            continue
        r = n1(boquilla(rn, h, ar, at, fan), a.n_plano, a.dphi)
        filas.append([rn, h, ar, at, fan] + ["%.5f" % r[k] for k in ("tot", "flanco", "extremos", "pista_ext", "pista_int", "frac_entra")])
        print("r %5.0f h %4.0f ar %+4.0f at %3.0f %-10s -> tot %.4f flanco %.4f ext %.4f pe %.4f pi %.4f entra %.3f (%.0f s)" % (
            rn, h, ar, at, fan, r["tot"], r["flanco"], r["extremos"], r["pista_ext"], r["pista_int"], r["frac_entra"], time.time() - t0), flush=True)
    with open(T.OUT + "/T2c_pose_%s.csv" % "_".join(FAN), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["r_vertice_mm", "h_sobre_cara_mm", "incl_radial_deg", "incl_tangencial_deg", "abanico", "frac_N1_total",
                    "frac_N1_flanco", "frac_N1_extremos", "frac_N1_pista_ext", "frac_N1_pista_int", "frac_rayos_entran_ventana"])
        w.writerows(filas)
    # figura: frac total frente a inclinacion radial, una curva por inclinacion tangencial (r 570, h 190, abanico radial)
    for fan in FAN:
        sel = [r for r in filas if r[0] == 570.0 and r[1] == 190.0 and r[4] == fan]
        if not sel:
            continue
        fig, ax = plt.subplots()
        datos = []
        for i, at in enumerate(AT):
            s = sorted([r for r in sel if r[3] == at], key=lambda r: r[2])
            ax.plot([r[2] for r in s], [100 * float(r[5]) for r in s], "o-", color=C[i], label="inclinación tangencial %g°" % at)
            datos += [[r[2], at, r[5], r[6], r[8], r[9]] for r in s]
        ax.set_xlabel("inclinación radial del eje (grados; + hacia afuera)")
        ax.set_ylabel("rodillos + pistas con N1 (% del área)")
        ejes_coma(ax)
        ax.legend(fontsize=10)
        guardar(fig, T.OUT + "/figuras", "T2c_pose_r570_h190_" + fan, ["incl_radial", "incl_tang", "frac_tot", "frac_flanco",
                                                                     "frac_pe", "frac_pi"], datos)
    print("listo en %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
