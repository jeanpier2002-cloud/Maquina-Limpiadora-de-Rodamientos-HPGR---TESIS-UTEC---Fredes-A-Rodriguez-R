#!/usr/bin/env python3
"""
CFD03 - Dosis por vuelta de una superficie sumando aportes de varias corridas/boquillas, sin y con los obstaculos
fijos de R05 (PAD, topes, vigas). Misma aritmetica de bandas que post_kpi.py (rama B):
  D_n(b) = mdot_n,banda * T_vuelta / A_banda        (sector libre, rotor congelado -> axisimetrico)
Con obstaculos, por celda (banda de 10 mm x 0,5 grados) del marco FIJO:
  D(b, th) = sum_n D_n(b) * M_n(b, th),   M_n = F_obst / F_libre de rayos_r05.py (misma celda y mismo muestreo:
  el ruido de muestreo se cancela). Las bandas de 2 mm heredan la mascara de su banda de 10 mm.
Area que cuenta = area mojable (sin el contacto de PAD en cara_inf ni la franja del OD tapada por los topes).

KPIs (bandas de 10 mm y 2 mm): D media (ponderada por area), CV sobre bandas con masa (no ponderado, rama B),
zona seca por bandas (D <= 1e-9), D_min/D_max, C(1) y C(5), J media; con obstaculos ademas la zona sin
deposito por CELDAS (10 mm x 0,5 grados) y D_min por celdas.

Uso:
  python combinar_kpi.py --superficie cara_inf --caso G7_INF --salida DIR --mascaras K1_22boq_mascaras.npz \
     --aporte "G3_A_cara_inf.csv|inf_ext_a|2|0.025|0.050|INF_EXT_A" \
     --aporte "G5_INT_cara_inf.csv|inf_int|1|0.025|0.050|INF_INT" [--mdot-inyectado 0.4536]
  aporte = csv_impactos(dpm2csv, transitorio) | boquillas (coma) | factor | t0 | t1 | clave(s) de mascara (coma)
"""
import argparse
import csv
import math
import os

import numpy as np

OMEGA = 0.1780235837034216
T_VUELTA = 2 * math.pi / OMEGA
R_OD, Z0, Z1 = 0.710, 0.890, 1.405
R_AGI, R_AGS = 0.450, 0.450 + (Z1 - Z0) / 60.0
LIM = {"od": (Z0, Z1), "sup": (R_AGS, R_OD), "cara_inf": (R_AGI, R_OD), "agujero": (Z0, Z1)}
NTH = 720
SECO = 1e-9


def area_banda(sup, b0, b1):
    if sup == "od":
        return 2 * math.pi * R_OD * (b1 - b0)
    if sup == "agujero":
        rz = R_AGI + (0.5 * (b0 + b1) - Z0) / 60.0
        return 2 * math.pi * rz * (b1 - b0) / math.cos(math.atan(1 / 60.0))
    return math.pi * (b1 ** 2 - b0 ** 2)


def solape_theta(thc, tc, hw):
    """Fraccion exacta de cada celda de 0,5 grados (centro thc) dentro de [tc - hw, tc + hw]."""
    d = (thc - tc + 180) % 360 - 180
    return np.clip(np.minimum(d + 0.25, hw) - np.maximum(d - 0.25, -hw), 0, None) / 0.5


def contacto(sup, sc, thc):
    ex = np.zeros((len(sc), len(thc)), float)
    if sup == "cara_inf":
        for tc in (0.0, 120.0, 240.0):
            ex = np.maximum(ex, ((sc >= 0.638) & (sc <= 0.688))[:, None] * solape_theta(thc, tc, 12.0)[None, :])
    if sup == "od":
        hw = math.degrees(math.atan(0.040 / R_OD))
        for tc in (60.0, 180.0, 300.0):
            ex = np.maximum(ex, ((sc >= Z0) & (sc <= 0.920))[:, None] * solape_theta(thc, tc, hw)[None, :])
    return ex


def bandas(sup, db):
    lo, hi = LIM[sup]
    nb = int(math.ceil((hi - lo) / db - 1e-9))
    e = np.minimum(lo + db * np.arange(nb + 1), hi)
    return e


_CACHE = {}


def _cargar(path):
    """Lee una vez cada CSV de impactos (columnas de dpm2csv) y lo guarda en memoria como arreglos."""
    if path not in _CACHE:
        import sys as _s
        _s.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from lector_impactos import leer as _leer       # por columnas: archivos de varios GB (S18)
        cols = ("x", "y", "z", "u", "v", "w", "masa", "t")
        R = _leer(path, cols, texto=("boquilla",))
        n = R["x"].size if "x" in R else 0
        num = np.column_stack([R[c] for c in cols]) if n else np.zeros((0, 8))
        bq = np.array([str(b).lower() for b in R["boquilla"]], dtype=object) if n else np.array([], dtype=object)
        _CACHE[path] = (num, bq)
    return _CACHE[path]


def leer(path, boqs, t0, t1, sup):
    num, bq = _cargar(path)
    q = {b.lower() for b in boqs}
    s = np.isin(bq, list(q)) & (num[:, 7] >= t0) & (num[:, 7] < t1)
    if not s.any():
        return np.zeros(0), np.zeros(0), np.zeros(0)
    x, y, z, u, v, w = (num[s, k] for k in range(6))
    m = num[s, 6] / (t1 - t0)
    rr = np.hypot(x, y)
    if sup == "od":
        s, vn = z, -(u * x + v * y) / rr
    elif sup == "agujero":
        s, vn = z, (u * x + v * y) / rr
    elif sup == "sup":
        s, vn = rr, -w
    else:
        s, vn = rr, w
    return s, m, np.clip(vn, 0, None)


def kpis(D, Aw, cuenta):
    """D (n,), Aw area mojable (n,): indicadores por bandas (definicion rama B)."""
    ok = cuenta & (Aw > 0)
    At = Aw[ok].sum()
    cm = ok & (D > 0)
    return dict(D_media=(D * Aw)[ok].sum() / At,
                CV=float(np.std(D[cm]) / np.mean(D[cm])) if cm.sum() > 1 else float("nan"),
                seca_pct=100 * Aw[ok & (D <= SECO)].sum() / At,
                D_min=D[ok].min(), D_max=D[ok].max(),
                cob1_pct=100 * Aw[ok & (D >= 1.0)].sum() / At, cob5_pct=100 * Aw[ok & (D >= 5.0)].sum() / At,
                area_m2=At)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--superficie", choices=list(LIM), required=True)
    ap.add_argument("--caso", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--mascaras", default=None)
    ap.add_argument("--aporte", action="append", required=True)
    ap.add_argument("--mdot-inyectado", type=float, default=None)
    a = ap.parse_args()
    sup = a.superficie
    os.makedirs(a.salida, exist_ok=True)
    thc = (np.arange(NTH) + 0.5) * 0.5
    Z = np.load(a.mascaras) if a.mascaras else None
    res, filas_b, porb = {}, {}, []
    for db in (0.010, 0.002):
        e = bandas(sup, db)
        nb = len(e) - 1
        sc = 0.5 * (e[:-1] + e[1:])
        Ab = np.array([area_banda(sup, e[k], e[k + 1]) for k in range(nb)])
        # fraccion mojable por celda (contacto excluido), a la resolucion de la banda
        fin = np.linspace(0, 1, 11)[:-1] + 0.05
        exc = np.mean([contacto(sup, e[:-1] + f * np.diff(e), thc) for f in fin], axis=0)   # (nb, NTH)
        Acel = Ab[:, None] / NTH * (1 - exc)
        Aw = Acel.sum(1)
        Dl = np.zeros(nb); Jl = np.zeros(nb); Do = np.zeros((nb, NTH)); Jo = np.zeros((nb, NTH))
        mt_l = 0.0; mt_o = 0.0
        for ap_ in a.aporte:
            path, boq, fac, t0, t1, *mk = ap_.split("|")
            s, m, vn = leer(path, boq.split(","), float(t0), float(t1), sup)
            m = m * float(fac)
            lo, hi = LIM[sup]
            den = (s >= lo) & (s <= hi)
            ib = np.clip(np.searchsorted(e, s[den], side="right") - 1, 0, nb - 1)
            mb = np.bincount(ib, weights=m[den], minlength=nb)
            jb = np.bincount(ib, weights=(m * vn)[den], minlength=nb)
            Dn, Jn = mb * T_VUELTA / Ab, jb * T_VUELTA / Ab
            Dl += Dn; Jl += Jn; mt_l += mb.sum()
            M = np.ones((nb, NTH))
            if Z is not None and mk and mk[0]:
                M = mascara(Z, mk[0].split(","), sup, e)
            Do += Dn[:, None] * M; Jo += Jn[:, None] * M
            mt_o += (mb[:, None] / NTH * M).sum()
            if db == 0.010:
                porb.append([os.path.basename(path), boq, fac, "%.6e" % mb.sum(), "%.6e" % (mb[:, None] / NTH * M).sum()])
        cuenta = Aw > 0
        Dob = np.where(Aw > 0, (Do * Acel).sum(1) / np.where(Aw > 0, Aw, 1), 0.0)
        Job = np.where(Aw > 0, (Jo * Acel).sum(1) / np.where(Aw > 0, Aw, 1), 0.0)
        kl = kpis(Dl, Aw, cuenta); ko = kpis(Dob, Aw, cuenta)
        kl["J_media"] = (Jl * Aw)[cuenta].sum() / Aw[cuenta].sum()
        ko["J_media"] = (Job * Aw)[cuenta].sum() / Aw[cuenta].sum()
        celda_ok = Acel > 0
        ko["seca_celdas_pct"] = 100 * Acel[celda_ok & (Do <= SECO)].sum() / Acel[celda_ok].sum()
        ko["D_min_celdas"] = Do[celda_ok].min()
        kl["mdot_dep"] = mt_l; ko["mdot_dep"] = mt_o
        if a.mdot_inyectado:
            kl["eta_pct"] = 100 * mt_l / a.mdot_inyectado; ko["eta_pct"] = 100 * mt_o / a.mdot_inyectado
        tag = "%dmm" % round(db * 1000)
        res["libre_" + tag] = kl; res["obst_" + tag] = ko
        filas_b[tag] = [["%.2f" % (1e3 * sc[k]), "%.6f" % Ab[k], "%.6f" % Aw[k], "%.6f" % Dl[k], "%.6f" % Dob[k],
                         "%.6f" % Do[k][Acel[k] > 0].min() if (Acel[k] > 0).any() else "", "%.5e" % Jl[k],
                         "%.5e" % Job[k]] for k in range(nb)]
        if db == 0.010:
            np.savez_compressed(os.path.join(a.salida, a.caso + "_mapa10mm.npz"), D=Do, J=Jo, A=Acel, edges=e, th=thc)
    for tag, F in filas_b.items():
        with open(os.path.join(a.salida, "%s_bandas_%s.csv" % (a.caso, tag)), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["s_centro_mm", "area_banda_m2", "area_mojable_m2", "D_libre", "D_obst_media_theta",
                        "D_obst_min_celda", "J_libre", "J_obst"])
            w.writerows(F)
    with open(os.path.join(a.salida, a.caso + "_indicadores.csv"), "w", newline="") as f:
        w = csv.writer(f)
        claves = sorted({k for v in res.values() for k in v})
        w.writerow(["variante"] + claves)
        for kk, v in res.items():
            w.writerow([kk] + ["%.6g" % v[c] if c in v else "" for c in claves])
    with open(os.path.join(a.salida, a.caso + "_aportes.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["csv", "boquillas", "factor", "mdot_dep_libre_kg_s", "mdot_dep_obst_kg_s"])
        w.writerows(porb)
    for kk in ("libre_10mm", "obst_10mm", "libre_2mm", "obst_2mm"):
        v = res[kk]
        print("%-11s D %.4f | CV %.4f | seca %.3f %% | Dmin %.4f | J %.3f | eta %s%s" % (
            kk, v["D_media"], v["CV"], v["seca_pct"], v["D_min"], v["J_media"],
            ("%.2f %%" % v["eta_pct"]) if "eta_pct" in v else "-",
            (" | seca celdas %.3f %% Dmin celdas %.4f" % (v["seca_celdas_pct"], v["D_min_celdas"])) if "seca_celdas_pct" in v else ""))


def mascara(Z, claves, sup, e):
    """M(b, th) = F_obst / F_libre agregando las bandas finas (2 mm) de rayos a las bandas e."""
    ef = Z["edges__" + sup]
    scf = 0.5 * (ef[:-1] + ef[1:])
    Fl = sum(Z["%s__%s__libre" % (k, sup)] for k in claves)
    Fo = sum(Z["%s__%s__obst" % (k, sup)] for k in claves)
    # a bandas de 10 mm (evita huecos de rayos) y luego a las bandas pedidas
    lo = LIM[sup][0]
    b10 = ((scf - lo) / 0.010).astype(int)
    n10 = b10.max() + 1
    L10 = np.zeros((n10, NTH)); O10 = np.zeros((n10, NTH))
    np.add.at(L10, b10, Fl); np.add.at(O10, b10, Fo)
    M10 = np.where(L10 > 0, O10 / np.where(L10 > 0, L10, 1), np.nan)
    # bandas de 10 mm sin rayos: mascara de la banda mas cercana con rayos (misma boquilla)
    con = np.where(np.isfinite(M10).all(1))[0]
    for k in range(n10):
        if not np.isfinite(M10[k]).all():
            M10[k] = M10[con[np.argmin(np.abs(con - k))]] if len(con) else 1.0
    sc = 0.5 * (e[:-1] + e[1:])
    return M10[np.clip(((sc - lo) / 0.010).astype(int), 0, n10 - 1)]


if __name__ == "__main__":
    main()
