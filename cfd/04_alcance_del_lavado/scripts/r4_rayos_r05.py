#!/usr/bin/env python3
"""
N1 con obstaculos de R05: trazado de rayos rectos de cada abanico durante UNA VUELTA del rotor frente a los
obstaculos FIJOS de la mesa (PAD, topes de retencion, vigas), medidos en R05_GEOMETRICO_DETALLADO (G1/G2).
[INTERFAZ ISMAEL: contexto de mesa copiado de R04 en R05]

Rayos: posicion y velocidad de cada parcela de la tabla de inyeccion (abanico_*.csv de gen_abanico.py), sin
gravedad ni arrastre (N1). Para cada angulo del rotor phi (paso --dphi) se rotan los rayos alrededor de Z y se
busca el PRIMER impacto entre:
  objetivos : od (cilindro R 0,710, z 0,890-1,405, desde fuera), sup (z 1,405, r 0,45858-0,710, desde arriba),
              cara_inf (z 0,890, r 0,450-0,710, desde abajo), agujero (cono 1:30 de la rama B, desde dentro)
  obstaculos: PAD cap+liner (sector anular r 0,638-0,688, +-12 grados, z 0,850-0,890) y base (caja), en 0/120/240;
              topes (caja radial 0,710-0,780 x +-0,040 x z 0,800-0,920) en 60/180/300; vigas W6x9 (z <= 0,805).
Acumula por vuelta la masa de cada rayo (m_i * dphi/omega) en celdas (superficie, s, theta).

Salidas (--salida, --caso):
  <caso>_reparto.csv   : por boquilla, % del caudal a cada objetivo/obstaculo/escape (libre y con obstaculos)
  <caso>_K1.csv        : K1 por superficie (bandas de 10 mm): libre y con obstaculos (celdas de 10 mm x 0,5 grados)
  <caso>_mascaras.npz  : por boquilla y superficie, masa por vuelta en (banda de 2 mm, theta 0,5 grados), con y sin
                         obstaculos -> mascaras de sombra para combinar con la dosis CFD del sector libre.
Uso: python rayos_r05.py --tablas a.csv b.csv ... --salida DIR --caso NOMBRE [--dphi 0.5] [--sin-obstaculos]
"""
import argparse
import csv
import math
import os

import numpy as np

OMEGA = 0.1780235837034216
R_OD, Z0, Z1 = 0.710, 0.890, 1.405
R_AGI, R_AGS = 0.450, 0.450 + (Z1 - Z0) / 60.0
SUPS = {  # nombre: (coordenada s, limites)
    "od": ("z", (Z0, Z1)), "sup": ("r", (R_AGS, R_OD)), "cara_inf": ("r", (R_AGI, R_OD)), "agujero": ("z", (Z0, Z1))}
DB = 0.002                  # banda fina de las mascaras (2 mm); las de 10 mm se agregan
NTH = 720                   # celdas de 0,5 grados


def r_cono(z):
    return R_AGI + (np.clip(z, Z0, Z1) - Z0) / 60.0


# ------------------------------------------------------------------ primitivas (t de entrada, inf si no)
def t_cil_fuera(P, U, R, z1, z2):
    a = U[:, 0] ** 2 + U[:, 1] ** 2
    b = 2 * (P[:, 0] * U[:, 0] + P[:, 1] * U[:, 1])
    c = P[:, 0] ** 2 + P[:, 1] ** 2 - R ** 2
    d = b * b - 4 * a * c
    ok = (d >= 0) & (a > 1e-14)
    sq = np.sqrt(np.where(ok, d, 0))
    t = np.where(ok, (-b - sq) / (2 * np.where(a > 1e-14, a, 1)), np.inf)
    z = P[:, 2] + t * U[:, 2]
    return np.where((t > 1e-9) & (z >= z1) & (z <= z2) & (c > 0), t, np.inf)


def t_plano(P, U, z0, r1, r2, desde_abajo):
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (z0 - P[:, 2]) / U[:, 2]
    H = P + np.where(np.isfinite(t), t, 0)[:, None] * U
    r = np.hypot(H[:, 0], H[:, 1])
    lado = (U[:, 2] > 0) if desde_abajo else (U[:, 2] < 0)
    return np.where(np.isfinite(t) & (t > 1e-9) & lado & (r >= r1) & (r <= r2), t, np.inf)


def t_cono_dentro(P, U):
    """Impacto en el agujero conico desde dentro (el rayo sale hacia r creciente)."""
    a = U[:, 0] ** 2 + U[:, 1] ** 2
    b = 2 * (P[:, 0] * U[:, 0] + P[:, 1] * U[:, 1])
    best = np.full(len(P), np.inf)
    R = np.full(len(P), R_AGI)
    for _ in range(6):
        c = P[:, 0] ** 2 + P[:, 1] ** 2 - R ** 2
        d = b * b - 4 * a * c
        ok = (d >= 0) & (a > 1e-14)
        t2 = np.where(ok, (-b + np.sqrt(np.where(ok, d, 0))) / (2 * np.where(a > 1e-14, a, 1)), np.inf)
        z = P[:, 2] + np.where(np.isfinite(t2), t2, 0) * U[:, 2]
        R = r_cono(z)
    val = np.isfinite(t2) & (t2 > 1e-9) & (z >= Z0) & (z <= Z1)
    return np.where(val, t2, best)


def t_caja(P, U, tc_deg, lo, hi):
    """Caja en ejes locales (x' radial en tc, y' tangencial, z). lo/hi = (x', y', z)."""
    c, s = math.cos(math.radians(tc_deg)), math.sin(math.radians(tc_deg))
    Pl = np.column_stack([c * P[:, 0] + s * P[:, 1], -s * P[:, 0] + c * P[:, 1], P[:, 2]])
    Ul = np.column_stack([c * U[:, 0] + s * U[:, 1], -s * U[:, 0] + c * U[:, 1], U[:, 2]])
    t0 = np.zeros(len(P)); t1 = np.full(len(P), np.inf)
    for k in range(3):
        with np.errstate(divide="ignore", invalid="ignore"):
            ta = (lo[k] - Pl[:, k]) / Ul[:, k]
            tb = (hi[k] - Pl[:, k]) / Ul[:, k]
        par = np.abs(Ul[:, k]) < 1e-14
        dentro = (Pl[:, k] >= lo[k]) & (Pl[:, k] <= hi[k])
        tmin = np.where(par, np.where(dentro, -np.inf, np.inf), np.minimum(ta, tb))
        tmax = np.where(par, np.where(dentro, np.inf, -np.inf), np.maximum(ta, tb))
        t0 = np.maximum(t0, tmin); t1 = np.minimum(t1, tmax)
    return np.where((t0 <= t1) & (t0 > 1e-9), t0, np.inf)


def t_sector(P, U, tc_deg, hw_deg, r1, r2, z1, z2):
    """Entrada en el solido {r1<=r<=r2, |theta-tc|<=hw, z1<=z<=z2}: candidatos en las 6 caras + prueba."""
    a = U[:, 0] ** 2 + U[:, 1] ** 2
    b = 2 * (P[:, 0] * U[:, 0] + P[:, 1] * U[:, 1])
    cands = []
    for R in (r1, r2):
        c = P[:, 0] ** 2 + P[:, 1] ** 2 - R ** 2
        d = b * b - 4 * a * c
        ok = (d >= 0) & (a > 1e-14)
        sq = np.sqrt(np.where(ok, d, 0))
        for sg in (-1, 1):
            cands.append(np.where(ok, (-b + sg * sq) / (2 * np.where(a > 1e-14, a, 1)), np.inf))
    for zz in (z1, z2):
        with np.errstate(divide="ignore", invalid="ignore"):
            cands.append(np.where(np.abs(U[:, 2]) > 1e-14, (zz - P[:, 2]) / U[:, 2], np.inf))
    for ang in (tc_deg - hw_deg, tc_deg + hw_deg):
        n = np.array([-math.sin(math.radians(ang)), math.cos(math.radians(ang))])
        den = U[:, 0] * n[0] + U[:, 1] * n[1]
        with np.errstate(divide="ignore", invalid="ignore"):
            cands.append(np.where(np.abs(den) > 1e-14, -(P[:, 0] * n[0] + P[:, 1] * n[1]) / den, np.inf))
    best = np.full(len(P), np.inf)
    for t in cands:
        t = np.where(np.isfinite(t) & (t > 1e-9), t, np.inf)
        tt = np.where(np.isfinite(t), t, 0) + 1e-7
        H = P + tt[:, None] * U
        r = np.hypot(H[:, 0], H[:, 1]); z = H[:, 2]
        dth = (np.degrees(np.arctan2(H[:, 1], H[:, 0])) - tc_deg + 180.0) % 360.0 - 180.0
        ins = (r >= r1) & (r <= r2) & (z >= z1) & (z <= z2) & (np.abs(dth) <= hw_deg)
        best = np.where(np.isfinite(t) & ins, np.minimum(best, t), best)
    return best


OBST = []
for k, tc in enumerate((0.0, 120.0, 240.0)):
    OBST.append(("PAD_%d" % (k + 1), "pad", lambda P, U, tc=tc: t_sector(P, U, tc, 12.0, 0.638, 0.688, 0.850, 0.890)))
    OBST.append(("PAD_%d_base" % (k + 1), "pad", lambda P, U, tc=tc: t_caja(P, U, tc, (0.583, -0.070, 0.805), (0.743, 0.070, 0.850))))
for k, tc in enumerate((60.0, 180.0, 300.0)):
    OBST.append(("TOPE_%d" % (k + 1), "tope", lambda P, U, tc=tc: t_caja(P, U, tc, (0.710, -0.040, 0.800), (0.780, 0.040, 0.920))))
VIGAS = [((-0.980038, -0.950, 0.65514), (-0.879962, 0.950, 0.805)), ((0.879962, -0.950, 0.65514), (0.980038, 0.950, 0.805)),
         ((-0.930, -1.000038, 0.65514), (0.930, -0.899962, 0.805)), ((-0.930, 0.899962, 0.65514), (0.930, 1.000038, 0.805)),
         ((-0.930, -0.624213, 0.65514), (0.930, -0.524137, 0.805)), ((-0.930, 0.524137, 0.65514), (0.930, 0.624213, 0.805)),
         ((0.612962, -0.574175, 0.65514), (0.713038, 0.574175, 0.805))]
for k, (lo, hi) in enumerate(VIGAS):
    OBST.append(("VIGA_M%02d" % (k + 1), "mesa", lambda P, U, lo=lo, hi=hi: t_caja(P, U, 0.0, lo, hi)))


def trazar(P, U, obst=True):
    """Primer impacto: devuelve (destino (str array), t, punto)."""
    ts = {"od": t_cil_fuera(P, U, R_OD, Z0, Z1), "sup": t_plano(P, U, Z1, R_AGS, R_OD, False),
          "cara_inf": t_plano(P, U, Z0, R_AGI, R_OD, True), "agujero": t_cono_dentro(P, U)}
    if obst:
        for nom, tipo, f in OBST:
            ts[nom] = f(P, U)
    nombres = list(ts)
    T = np.vstack([ts[n] for n in nombres])
    i = np.argmin(T, axis=0)
    tmin = T[i, np.arange(len(P))]
    dest = np.array(nombres, dtype=object)[i]
    dest[~np.isfinite(tmin)] = "escape"
    H = P + np.where(np.isfinite(tmin), tmin, 0)[:, None] * U
    return dest, tmin, H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tablas", nargs="+", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--caso", required=True)
    ap.add_argument("--dphi", type=float, default=0.5)
    a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)
    nphi = int(round(360.0 / a.dphi))
    dt_phi = math.radians(a.dphi) / OMEGA                # s de rotor por paso
    edges = {s: np.append(np.arange(lo, hi - 1e-12, DB), hi) for s, (_, (lo, hi)) in SUPS.items()}
    masc, rep = {}, []
    for tb in a.tablas:
        nombre = os.path.basename(tb).replace("abanico_", "").replace(".csv", "")
        rows = list(csv.DictReader(open(tb)))
        P0 = np.array([[float(r["Px_m"]), float(r["Py_m"]), float(r["Pz_m"])] for r in rows])
        U0 = np.array([[float(r["Ux_m_s"]), float(r["Uy_m_s"]), float(r["Uz_m_s"])] for r in rows])
        m = np.array([float(r["mDot_kg_s"]) for r in rows])
        tot = {"libre": {}, "obst": {}}
        acc = {(s, o): np.zeros((len(edges[s]) - 1, NTH)) for s in SUPS for o in (0, 1)}
        for k in range(nphi):
            ph = math.radians(k * a.dphi)
            c, s_ = math.cos(ph), math.sin(ph)
            Rz = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
            P, U = P0 @ Rz.T, U0 @ Rz.T
            for o in (0, 1):
                if o == 0 and k > 0:
                    # sin obstaculos el resultado es el de phi = 0 rotado: se reutiliza con desplazamiento en theta
                    pass
                dest, t, H = trazar(P, U, obst=bool(o))
                clave = "obst" if o else "libre"
                for d_ in set(dest.tolist()):
                    tot[clave][d_] = tot[clave].get(d_, 0.0) + m[dest == d_].sum() * dt_phi
                th = (np.degrees(np.arctan2(H[:, 1], H[:, 0])) % 360.0)
                jt = np.minimum((th / 0.5).astype(int), NTH - 1)
                for sname, (coord, (lo, hi)) in SUPS.items():
                    sel = dest == sname
                    if not sel.any():
                        continue
                    sc = H[sel, 2] if coord == "z" else np.hypot(H[sel, 0], H[sel, 1])
                    ib = np.clip(np.searchsorted(edges[sname], sc, side="right") - 1, 0, len(edges[sname]) - 2)
                    np.add.at(acc[(sname, o)], (ib, jt[sel]), m[sel] * dt_phi)
        vuelta = m.sum() * nphi * dt_phi
        for s in SUPS:
            masc["%s|%s|libre" % (nombre, s)] = acc[(s, 0)]
            masc["%s|%s|obst" % (nombre, s)] = acc[(s, 1)]
        fila = {"boquilla": nombre, "mdot_kg_s": "%.6f" % m.sum()}
        for clave in ("libre", "obst"):
            for d_, v in sorted(tot[clave].items()):
                fila["%s_%s_pct" % (clave, d_)] = "%.3f" % (100 * v / vuelta)
        rep.append(fila)
        print(nombre, {k: v for k, v in fila.items() if k.endswith("pct") and float(v) > 0.05})
    claves = sorted({k for f in rep for k in f})
    claves = ["boquilla", "mdot_kg_s"] + [k for k in claves if k not in ("boquilla", "mdot_kg_s")]
    with open(os.path.join(a.salida, a.caso + "_reparto.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=claves, restval="0.000")
        w.writeheader(); w.writerows(rep)
    np.savez_compressed(os.path.join(a.salida, a.caso + "_mascaras.npz"),
                        **{k.replace("|", "__"): v for k, v in masc.items()},
                        **{"edges__" + s: e for s, e in edges.items()})
    # K1 por superficie (suma de todas las boquillas)
    #  libre: bandas de 10 mm alcanzadas (definicion de CFD02/rama B)
    #  con obstaculos: celdas de 2 mm x 0,5 grados alcanzadas, sobre el area MOJABLE (sin contacto de PAD ni
    #  la franja del OD tapada por los topes, que no cuentan en KPI-1)
    filas = []
    thc = (np.arange(NTH) + 0.5) * 0.5
    for sname, (coord, (lo, hi)) in SUPS.items():
        L = sum(masc["%s|%s|libre" % (os.path.basename(t).replace("abanico_", "").replace(".csv", ""), sname)] for t in a.tablas)
        O = sum(masc["%s|%s|obst" % (os.path.basename(t).replace("abanico_", "").replace(".csv", ""), sname)] for t in a.tablas)
        if L.sum() == 0:
            continue
        e = edges[sname]
        sc = 0.5 * (e[:-1] + e[1:])
        Acel = area_celdas(sname, e)
        excl = contacto(sname, sc, thc)
        nb = int(math.ceil((hi - lo) / 0.010 - 1e-9))
        b10 = np.minimum(((sc - lo) / 0.010).astype(int), nb - 1)
        alc10 = np.zeros(nb, bool)
        alc10[np.unique(b10[L.sum(1) > 0])] = True
        A10 = np.bincount(b10, weights=Acel.sum(1), minlength=nb)
        k1_libre = 100 * A10[alc10].sum() / A10.sum()
        # con obstaculos: celdas de 10 mm x 0,5 grados (con 2 mm la densidad de rayos deja huecos artificiales:
        # INF_INT llega rasante y 150 rayos en el plano quedan a ~8 mm en r)
        O10 = np.zeros((nb, NTH)); A10c = np.zeros((nb, NTH)); E10 = np.zeros((nb, NTH))
        np.add.at(O10, b10, O); np.add.at(A10c, b10, Acel); np.add.at(E10, b10, Acel * excl)
        moj10 = A10c - E10                       # area mojable de cada celda de 10 mm
        k1_obst = 100 * moj10[O10 > 0].sum() / moj10.sum()
        filas.append([a.caso, sname, "%.3f" % k1_libre, "%.3f" % k1_obst, "%.3f" % (100 - k1_obst),
                      "%.3f" % (100 * Acel[excl].sum() / Acel.sum())])
        print("K1 %-8s libre %.3f %% | con obstaculos %.3f %% del area mojable (contacto excluido %.3f %%)"
              % (sname, k1_libre, k1_obst, 100 * Acel[excl].sum() / Acel.sum()))
    with open(os.path.join(a.salida, a.caso + "_K1.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["caso", "superficie", "K1_libre_pct", "K1_con_obstaculos_pct", "sin_impacto_directo_pct",
                    "area_contacto_excluida_pct"])
        w.writerows(filas)


def area_celdas(sname, e):
    """Area de cada celda (banda fina x 0,5 grados)."""
    dth = 2 * math.pi / NTH
    if sname == "od":
        a = R_OD * np.diff(e) * dth
    elif sname == "agujero":
        a = r_cono(0.5 * (e[:-1] + e[1:])) * np.diff(e) * dth / math.cos(math.atan(1 / 60))
    else:
        a = 0.5 * (e[1:] ** 2 - e[:-1] ** 2) * dth
    return np.repeat(a[:, None], NTH, 1)


def contacto(sname, sc, thc):
    """Celdas no mojables en E1: techo del liner de los PAD (cara_inf) y franja del OD tapada por los topes."""
    ex = np.zeros((len(sc), len(thc)), bool)
    if sname == "cara_inf":
        for tc in (0.0, 120.0, 240.0):
            d = np.abs((thc - tc + 180) % 360 - 180)
            ex |= ((sc >= 0.638) & (sc <= 0.688))[:, None] & (d <= 12.0)[None, :]
    if sname == "od":
        hw = math.degrees(math.atan(0.040 / R_OD))      # +-40 mm de la cara del tope sobre R 710 = +-3,22 grados
        for tc in (60.0, 180.0, 300.0):
            d = np.abs((thc - tc + 180) % 360 - 180)
            ex |= ((sc >= Z0) & (sc <= 0.920))[:, None] & (d <= hw)[None, :]
    return ex


if __name__ == "__main__":
    main()
