#!/usr/bin/env python3
"""
CORRIDA 4 · T2 · Acceso N1 a la cavidad (rodillos y pistas) a traves de las dos ventanas, en E1 (M8).
ETIQUETA: COTA SUPERIOR (sin jaula; rodillos con el perfil abombado medido del STEP o como cilindros: HIPOTESIS).
N1 = linea de vista balistica (rayos rectos, sin gravedad ni arrastre, sin rebote ni pelicula). NO es dosis ni limpieza.

Geometria (02_CAVIDAD_N1/step_medicion.json y step_rodillo.json, medidos con freecadcmd del STEP de SKF):
  marco del rodamiento: x axial en mm (0 = cara superior z 1,405 m; 515 = cara inferior z 0,890 m; O900 abajo, HIPOTESIS),
  r, theta del marco de la maquina. Aro exterior: r_oi(x) (esfera R 669,04 mm); aro interior: r_io(x) (perfil medido).
  2 hileras x 23 rodillos, L 214,0 mm, eje a 13,0 grados; perfil rho(s) = sqrt(669,04^2-(s-107)^2) - 601,04 (59,4-68,0 mm);
  hilera superior (T): extremo del lado de la cara en x 18,04 / r 561,56; hilera inferior (B) especular, desfasada medio paso.
  Jaula: NO esta en el STEP -> no se modela (cota superior).
Rayos: abanicos como gen_abanico.py (vertice, eje, normal del plano del kit; 50 grados o el de la boquilla; 3 planos en
  +-1 grado; n rayos por plano), boquillas de boquillas_O7_C2_LAT1m4.json (O7+C2 + Caso 2). Barrido del rotor 360 grados
  con paso dphi. Antes de la cara: trazar() de r4_rayos_r05.py (copia sin cambios de rayos_r05.py) con PAD, topes y vigas.
  Rayos que llegan al plano de una cara con r en la ventana (521,5-617,5 mm) entran a la cavidad: marcha de 1 mm +
  biseccion (12 iteraciones) contra aros y rodillos.
Salidas en 02_CAVIDAD_N1/<tag>_*.csv/.npz. Uso:
  python -I -B r4_t2_cavidad_n1.py --tag base [--boq SUP_1_A,...] [--n-plano 150] [--dphi 0.25] [--sin-rodillos]
         [--cilindro] [--fase0 0] [--prueba-cilindro]
"""
import argparse
import csv
import json
import math
import os
import sys
import time

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import r4_rayos_r05 as RR  # noqa: E402

B4 = "D:/CFD_Redosado/CORRIDA_4_PRIMER_LAVADO"
OUT = B4 + "/02_CAVIDAD_N1"
JSON_BOQ = "D:/CFD_Redosado/CORRIDA_3_O7C2/01_ENTRADA/boquillas_O7_C2_LAT1m4.json"
RHO = 982.1203530851709
OMEGA = RR.OMEGA
Z_TOP, Z_BOT = 1.405, 0.890
W_IN, W_OUT = 521.5, 617.5          # ventana (mm)
LB = 515.0
# rodillos (STEP)
L_ROD = 214.0
AX, AR = 0.974370, 0.224951         # direccion del eje en (axial, radial), 13,0 grados
X1_T, R1 = 18.04, 561.56
X1_B = LB - X1_T
RT, RM = 669.04, 601.04             # toroide del abombado
RHO_CIL = 68.0                      # variante cilindro (diametro maximo medido)
NROD = 23
PASO = 360.0 / NROD
# discretizacion de superficies
DS, DPSI = 5.0, 10.0
NS, NPSI = int(math.ceil(L_ROD / DS)), int(360 / DPSI)
DRF, DPSIF = 10.0, 30.0
DXP, DTH = 5.0, 0.5
NXP, NTH = int(math.ceil(LB / DXP)), int(360 / DTH)
PROF = [0, 25, 50, 100, 150, 214, 257.5]


def rho_s(s, cil=False):
    if cil:
        return np.full_like(s, RHO_CIL, dtype=float)
    return np.sqrt(np.maximum(RT ** 2 - (s - 107.0) ** 2, 0.0)) - RM


# ------------------------------------------------------------------ aros: perfiles medidos
def perfiles():
    R = json.load(open(OUT + "/step_medicion.json"))
    def bins(k, fun, rmin, rmax):
        # filtro por radio (corregido ≈ 01:20): sin el, bins de 0,25 mm con solo puntos del OD (r 704-710) o del agujero
        # (r 450-466) abrian huecos falsos en las superficies de la cavidad. Aro interior: r > 480 (sin agujero);
        # aro exterior: r < 690 (sin OD ni ranura W33). Bins de 0,5 mm; los vacios se interpolan.
        P = np.vstack([np.array(e) for e in R["perfiles"][k]])
        P = P[(P[:, 2] > 0)]
        P = P[(P[:, 2] > rmin) & (P[:, 2] < rmax)]
        x, r = P[:, 0], P[:, 2]
        xb = np.arange(0, LB + 0.5, 0.5)
        idx = np.clip(np.round(x / 0.5).astype(int), 0, len(xb) - 1)
        val = np.full(len(xb), np.nan)
        for i in np.unique(idx):
            v = r[idx == i]
            val[i] = fun(v)
        ok = np.isfinite(val)
        return xb, np.interp(xb, xb[ok], val[ok])
    xb, r_io = bins("0", np.max, 480.0, 600.0)   # aro interior: radio exterior (incluye resaltes)
    _, r_oi = bins("1", np.min, 600.0, 690.0)    # aro exterior: radio interior (pista esferica)
    return xb, r_io, r_oi


XB, R_IO, R_OI = perfiles()


def r_io(x):
    return np.interp(x, XB, R_IO)


def r_oi(x):
    return np.interp(x, XB, R_OI)


# limites de los resaltes del aro interior (zona plana r >= 521 junto a cada cara)
_fl = XB[(R_IO >= 521.0) & (XB < 100)]
X_RES_T = float(_fl.max()) if len(_fl) else 20.0
X_RES_B = LB - X_RES_T


# ------------------------------------------------------------------ rodillos
def ejes_rodillo(fila, k, fase0):
    th = math.radians(fase0 + (0.0 if fila == 0 else PASO / 2) + k * PASO)
    c, s = math.cos(th), math.sin(th)
    x1, ax = (X1_T, AX) if fila == 0 else (X1_B, -AX)
    c1 = np.array([x1, R1 * c, R1 * s])
    a = np.array([ax, AR * c, AR * s])
    eo = np.array([-AR if fila == 0 else AR, AX * c, AX * s])          # perpendicular a a, hacia r creciente
    eo = eo - (eo @ a) * a; eo /= np.linalg.norm(eo)
    et = np.cross(a, eo)
    return c1, a, eo, et


def prueba_rodillos(Q, fase0, cil):
    """Q (n,3) en (x, y, z) del marco del rodamiento [mm]. Devuelve (dentro, fila, k, s, d)."""
    n = len(Q)
    dentro = np.zeros(n, bool); fila = np.full(n, -1); kk = np.full(n, -1)
    ss = np.zeros(n); dd = np.zeros(n)
    th = np.degrees(np.arctan2(Q[:, 2], Q[:, 1]))
    for f in (0, 1):
        off = fase0 + (0.0 if f == 0 else PASO / 2)
        k0 = np.round((th - off) / PASO).astype(int)
        for dk in (-1, 0, 1):
            k = (k0 + dk) % NROD
            thk = np.radians(off + k * PASO)
            c, s = np.cos(thk), np.sin(thk)
            x1, ax = (X1_T, AX) if f == 0 else (X1_B, -AX)
            dx = Q[:, 0] - x1; dy = Q[:, 1] - R1 * c; dz = Q[:, 2] - R1 * s
            sl = dx * ax + dy * AR * c + dz * AR * s
            d2 = dx * dx + dy * dy + dz * dz - sl * sl
            rr = rho_s(np.clip(sl, 0, L_ROD), cil)
            ins = (~dentro) & (sl >= 0) & (sl <= L_ROD) & (d2 <= rr * rr)
            dentro |= ins; fila[ins] = f; kk[ins] = k[ins]; ss[ins] = sl[ins]; dd[ins] = np.sqrt(np.maximum(d2[ins], 0))
    return dentro, fila, kk, ss, dd


def solido(Q, fase0, cil, con_rodillos):
    """0 = hueco, 1 = rodillo, 2 = aro interior, 3 = aro exterior (dentro de 0 <= x <= 515)."""
    x = Q[:, 0]; r = np.hypot(Q[:, 1], Q[:, 2])
    enx = (x >= 0) & (x <= LB)
    cod = np.zeros(len(Q), int)
    cod[enx & (r <= r_io(x))] = 2
    cod[enx & (r >= r_oi(x))] = 3
    if con_rodillos:
        dr, *_ = prueba_rodillos(Q, fase0, cil)
        cod[(cod == 0) & enx & dr] = 1
    return cod


def marchar(P, U, fase0, cil, con_rodillos, h=1.0, nmax=900, nbis=12):
    """P (n,3) punto 1 mm antes de la cara, U unitario, marco del rodamiento [mm]. Devuelve (cod, t)."""
    n = len(P)
    t = np.zeros(n); cod = np.zeros(n, int); vivo = np.ones(n, bool)
    tpre = np.zeros(n)
    for it in range(nmax):
        idx = np.where(vivo)[0]
        if not len(idx):
            break
        tn = t[idx] + h
        Q = P[idx] + tn[:, None] * U[idx]
        c = solido(Q, fase0, cil, con_rodillos)
        x = Q[:, 0]
        fuera = ((x < -2.0) | (x > LB + 2.0)) & (tn > 3.0)
        golpe = c > 0
        tpre[idx] = t[idx]; t[idx] = tn
        gi = idx[golpe]; cod[gi] = -1           # marca de biseccion
        fi = idx[fuera & ~golpe]; cod[fi] = 9   # sale
        vivo[gi] = False; vivo[fi] = False
    sel = np.where(cod == -1)[0]
    lo, hi = tpre[sel].copy(), t[sel].copy()
    for _ in range(nbis):
        mid = 0.5 * (lo + hi)
        c = solido(P[sel] + mid[:, None] * U[sel], fase0, cil, con_rodillos)
        g = c > 0
        hi = np.where(g, mid, hi); lo = np.where(g, lo, mid)
    cf = solido(P[sel] + hi[:, None] * U[sel], fase0, cil, con_rodillos)
    cod[sel] = cf; t[sel] = hi
    cod[vivo] = 8                               # sin resolver en nmax pasos
    return cod, t


# ------------------------------------------------------------------ abanicos (formula de gen_abanico.py, muestreo extremos)
def abanico(b, n_plano, n_fuera=3, ang_fuera=2.0):
    eje = np.array(b["eje"], float); eje /= np.linalg.norm(eje)
    npl = np.array(b["normal_abanico"], float); npl /= np.linalg.norm(npl)
    ef = npl - (npl @ eje) * eje; ef /= np.linalg.norm(ef)
    ea = np.cross(ef, eje); ea /= np.linalg.norm(ea)
    hi = math.radians(b.get("angulo_deg", 50.0)) / 2; ho = math.radians(ang_fuera) / 2
    al = np.linspace(-hi, hi, n_plano); be = np.linspace(-ho, ho, n_fuera)
    AL, BE = np.meshgrid(al, be, indexing="ij")
    D = eje[None, :] + np.tan(AL.ravel())[:, None] * ea[None, :] + np.tan(BE.ravel())[:, None] * ef[None, :]
    D /= np.linalg.norm(D, axis=1, keepdims=True)
    V = np.array(b["vertice_m"], float)
    P = V[None, :] + (4.5e-3 / (D @ eje))[:, None] * D          # plano de la punta a 4,5 mm (como gen_abanico)
    m = b["q_Lmin"] * RHO / 60000.0 / len(D)
    return P, D, np.full(len(D), m)


# ------------------------------------------------------------------ areas de los parches
def areas():
    sc = (np.arange(NS) + 0.5) * DS
    s0 = np.arange(NS) * DS; s1 = np.minimum(s0 + DS, L_ROD)
    rr = rho_s(0.5 * (s0 + s1))
    A_fl = rr * (s1 - s0) * math.radians(DPSI)          # por (is, ipsi), mm2
    rf = np.arange(0, 60, DRF); rf1 = np.minimum(rf + DRF, rho_s(np.array([0.0]))[0])
    A_end = 0.5 * (rf1 ** 2 - rf ** 2) * math.radians(DPSIF)
    x0 = np.arange(NXP) * DXP; x1 = np.minimum(x0 + DXP, LB)
    def anillo(rfun):
        A = np.zeros(NXP)
        for i in range(NXP):
            xs = np.linspace(x0[i], x1[i], 21); rs = rfun(xs)
            A[i] = (0.5 * (rs[1:] + rs[:-1]) * np.hypot(np.diff(xs), np.diff(rs))).sum() * math.radians(DTH)
        return A
    return sc, A_fl, A_end, anillo(r_oi), anillo(r_io), 0.5 * (x0 + x1)


SC, A_FL, A_END, A_OUT, A_IN, XC = areas()


def a_marco_rodamiento(Pm, Um):
    """De la maquina [m] (X, Y, Z) al rodamiento [mm] (x axial hacia abajo desde la cara superior, y, z)."""
    P = np.column_stack([(Z_TOP - Pm[:, 2]) * 1000.0, Pm[:, 0] * 1000.0, Pm[:, 1] * 1000.0])
    U = np.column_stack([-Um[:, 2], Um[:, 0], Um[:, 1]])
    return P, U / np.linalg.norm(U, axis=1, keepdims=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--boq", default="SUP_1_A,SUP_2_A,SUP_1_B,SUP_2_B,INF_EXT_A,INF_EXT_B,C2_A,C2_B,INF_INT")
    ap.add_argument("--n-plano", type=int, default=150)
    ap.add_argument("--dphi", type=float, default=0.25)
    ap.add_argument("--fase0", type=float, default=0.0)
    ap.add_argument("--sin-rodillos", action="store_true")
    ap.add_argument("--cilindro", action="store_true")
    ap.add_argument("--sin-obstaculos", action="store_true")
    ap.add_argument("--lote-phi", type=int, default=24)
    a = ap.parse_args()
    t0 = time.time()
    B = json.load(open(JSON_BOQ, encoding="utf-8"))["boquillas"]
    boqs = a.boq.split(",")
    nphi = int(round(360.0 / a.dphi)); dtp = math.radians(a.dphi) / OMEGA
    con_rod = not a.sin_rodillos
    # acumuladores
    U_fl = np.zeros((len(boqs), 2, NROD, NS, NPSI), bool)
    U_end = np.zeros((len(boqs), 2, NROD, 2, len(A_END), int(360 / DPSIF)), bool)
    U_out = np.zeros((len(boqs), NXP, NTH), bool)
    U_in = np.zeros((len(boqs), NXP, NTH), bool)
    U_win = np.zeros((len(boqs), 2, 10, NTH), bool)       # ventana en el plano de la cara (prueba a)
    M_tipo = {}                                           # (boq, ventana, tipo, prof) -> kg/vuelta
    inst = np.zeros((len(boqs), 2))                      # area de flanco iluminada instantanea (suma sobre phi) por boquilla y fila
    rep = []
    for ib, nb in enumerate(boqs):
        P0, D0, m0 = abanico(B[nb], a.n_plano)
        mtot = m0.sum() * nphi * dtp
        ent = {"sup": 0.0, "cara_inf": 0.0}
        for j0 in range(0, nphi, a.lote_phi):
            js = np.arange(j0, min(j0 + a.lote_phi, nphi))
            Ps, Us, Ms, Js = [], [], [], []
            for j in js:
                ph = math.radians(j * a.dphi); c, s = math.cos(ph), math.sin(ph)
                Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
                Ps.append(P0 @ Rz.T); Us.append(D0 @ Rz.T); Ms.append(m0); Js.append(np.full(len(m0), j))
            Pm = np.vstack(Ps); Um = np.vstack(Us); Mm = np.concatenate(Ms) * dtp; Jm = np.concatenate(Js)
            dest, tt, H = RR.trazar(Pm, Um, obst=not a.sin_obstaculos)
            rH = np.hypot(H[:, 0], H[:, 1]) * 1000.0
            win = np.isin(dest, ["sup", "cara_inf"]) & (rH >= W_IN) & (rH <= W_OUT)
            if not win.any():
                continue
            for d_ in ("sup", "cara_inf"):
                ent[d_] += Mm[win & (dest == d_)].sum()
            # prueba (a): celdas de la ventana en el plano de la cara
            w_ = np.where(win)[0]
            iv = (dest[w_] == "cara_inf").astype(int)
            ir = np.clip(((rH[w_] - W_IN) / 9.6).astype(int), 0, 9)
            it = np.minimum(((np.degrees(np.arctan2(H[w_, 1], H[w_, 0])) % 360) / DTH).astype(int), NTH - 1)
            U_win[ib, iv, ir, it] = True
            # cavidad
            Pb, Ub = a_marco_rodamiento(H[w_], Um[w_])
            Pb = Pb - 1.0 * Ub
            cod, tc = marchar(Pb, Ub, a.fase0, a.cilindro, con_rod)
            Q = Pb + tc[:, None] * Ub
            mw = Mm[w_]; jw = Jm[w_]
            x = Q[:, 0]; r = np.hypot(Q[:, 1], Q[:, 2]); th = np.degrees(np.arctan2(Q[:, 2], Q[:, 1])) % 360
            ven = np.where(iv == 1, "inf", "sup")
            # rodillos
            sr = cod == 1
            if sr.any():
                dr, fil, kk, ss, dd = prueba_rodillos(Q[sr] + 1e-3 * Ub[sr], a.fase0, a.cilindro)
                ss = np.clip(ss, 0, L_ROD)
                psi = np.zeros(sr.sum())
                for f in (0, 1):
                    for k in np.unique(kk[fil == f]):
                        mk = (fil == f) & (kk == k)
                        c1, ax_, eo, et = ejes_rodillo(f, k, a.fase0)
                        V = Q[sr][mk] - c1
                        psi[mk] = np.degrees(np.arctan2(V @ et, V @ eo)) % 360
                ext0 = ss < 0.05; ext1 = ss > L_ROD - 0.05; fl = ~(ext0 | ext1) & (fil >= 0)
                isb = np.minimum((ss / DS).astype(int), NS - 1); ip = np.minimum((psi / DPSI).astype(int), NPSI - 1)
                U_fl[ib, fil[fl], kk[fl], isb[fl], ip[fl]] = True
                irf = np.minimum((dd / DRF).astype(int), len(A_END) - 1); ipf = np.minimum((psi / DPSIF).astype(int), 11)
                for e_, me in ((0, ext0 & (fil >= 0)), (1, ext1 & (fil >= 0))):
                    U_end[ib, fil[me], kk[me], e_, irf[me], ipf[me]] = True
                # instantaneo: area de flanco por (phi, parche) distinto
                gid = ((jw[sr][fl] * 2 + fil[fl]) * NROD + kk[fl]) * (NS * NPSI) + isb[fl] * NPSI + ip[fl]
                u = np.unique(gid)
                fu = (u // (NS * NPSI)) // NROD % 2
                isu = (u % (NS * NPSI)) // NPSI
                for f in (0, 1):
                    inst[ib, f] += A_FL[isu[fu == f]].sum()
                tipo = np.where(ext0, "extremo_cara", np.where(ext1, "extremo_interior", "flanco"))
                prof = np.digitize(ss, PROF[1:-1])
                for tp, pr, mm, vv in zip(tipo, prof, mw[sr], ven[sr]):
                    M_tipo[(nb, vv, "rodillo_" + tp, pr)] = M_tipo.get((nb, vv, "rodillo_" + tp, pr), 0.0) + mm
            for cval, nom, UU in ((2, "aro_interior", U_in), (3, "pista_exterior", U_out)):
                sc_ = cod == cval
                if not sc_.any():
                    continue
                ix = np.clip((x[sc_] / DXP).astype(int), 0, NXP - 1)
                itt = np.minimum((th[sc_] / DTH).astype(int), NTH - 1)
                UU[ib, ix, itt] = True
                xd = np.where(x[sc_] < LB / 2, x[sc_], LB - x[sc_])
                prof = np.digitize(xd, PROF[1:-1])
                if cval == 2:
                    nomv = np.where((x[sc_] <= X_RES_T) | (x[sc_] >= X_RES_B), "resalte_interior", "pista_interior")
                else:
                    nomv = np.full(sc_.sum(), nom)
                for nn, pr, mm, vv in zip(nomv, prof, mw[sc_], ven[sc_]):
                    M_tipo[(nb, vv, nn, pr)] = M_tipo.get((nb, vv, nn, pr), 0.0) + mm
            for cval, nom in ((9, "sale"), (8, "sin_resolver")):
                sc_ = cod == cval
                for mm, vv in zip(mw[sc_], ven[sc_]):
                    M_tipo[(nb, vv, nom, -1)] = M_tipo.get((nb, vv, nom, -1), 0.0) + mm
        rep.append([nb, "%.6f" % (m0.sum()), "%.4f" % (100 * ent["sup"] / mtot), "%.4f" % (100 * ent["cara_inf"] / mtot)])
        print("%-10s entra ventana sup %.3f %% | inf %.3f %%  (%.0f s)" % (nb, 100 * ent["sup"] / mtot,
                                                                     100 * ent["cara_inf"] / mtot, time.time() - t0), flush=True)
    os.makedirs(OUT, exist_ok=True)
    tag = a.tag
    np.savez_compressed(OUT + "/%s_union.npz" % tag, U_fl=U_fl, U_end=U_end, U_out=U_out, U_in=U_in, U_win=U_win,
                        boqs=np.array(boqs), A_FL=A_FL, A_END=A_END, A_OUT=A_OUT, A_IN=A_IN, XC=XC, SC=SC,
                        inst=inst, nphi=nphi, X_RES=np.array([X_RES_T, X_RES_B]))
    with open(OUT + "/%s_entrada_ventana.csv" % tag, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["boquilla", "mdot_kg_s", "pct_caudal_entra_ventana_sup", "pct_caudal_entra_ventana_inf"])
        w.writerows(rep)
    with open(OUT + "/%s_masa_destino.csv" % tag, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["boquilla", "ventana", "destino", "prof_bin", "prof_rango_mm", "kg_por_vuelta"])
        for (nb, vv, nn, pr), mm in sorted(M_tipo.items()):
            rng = "" if pr < 0 else "%g-%g" % (PROF[pr], PROF[pr + 1])
            w.writerow([nb, vv, nn, pr, rng, "%.6e" % mm])
    print("listo %s en %.0f s" % (tag, time.time() - t0))


if __name__ == "__main__":
    main()
