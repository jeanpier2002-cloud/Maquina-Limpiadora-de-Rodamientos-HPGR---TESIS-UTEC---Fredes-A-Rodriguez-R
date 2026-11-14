#!/usr/bin/env python3
"""
CORRIDA 2 · T3/T2 · Posproceso de E1-OD (lamina 2D de 0,049 mm sobre la pared, interFoam) y regresion V0.
Lee las copias ligeras en 02_VOF_v3/logs/<etapa>/<caso>/ (meta.json, resumen.txt, log.checkMesh, log.interFoam.gz,
postProcessing/{fuerzas,paredSup,lineas}). Todo se calcula con las constantes de meta.json (e0, S, LX, B, v), asi
que vale para cualquier espesor. Ventanas: 0,3-0,5 ms * S (comun a todos) y 1,0-1,2 ms * S (si el caso llega).
Teoria (lamina plana intacta, sin viscosidad; se deduce a mano, ver TABLA_REFERENCIAS_TEORICAS_v3.md):
  p0 = 1/2 rho v^2 ; F/b = rho v^2 e0 (lamina completa) ; por lado: q0 = rho v e0/2 , M0 = rho v^2 e0/2.
Salidas (02_VOF_v3/datos/): E1OD_metricas.csv, E1OD_convergencia.csv, E1OD_M_lineas.csv, E1OD_dt.csv,
  E1OD_gravedad.csv, E1OD_perfiles_pared.csv, V0_regresion.csv (si hay V0).
Uso: python -I v3_e1od_post.py [--etapa e1od] [--ventana t0 t1]   (ventana en s, para pruebas)
"""
import argparse
import csv
import glob
import gzip
import json
import math
import os
import re

import numpy as np

BASE = "D:/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3"
T1_E1 = "D:/CFD_Redosado/CORRIDA_1_13a21oct/06_VOF/logs/e1"
DAT = BASE + "/datos"
HIEMENZ = 1.2326


def raw(p):
    return np.loadtxt(p, comments="#", ndmin=2)


def log_dt(d):
    t, dt, co, aco, clock = [], [], [], [], []
    f = d + "/log.interFoam.gz"
    if not os.path.exists(f):
        return [np.zeros(0)] * 5
    with gzip.open(f, "rt", errors="ignore") as fh:
        cur = {}
        for ln in fh:
            if ln.startswith("Courant Number mean"):
                cur["co"] = float(ln.split()[-1])
            elif ln.startswith("Interface Courant Number"):
                cur["aco"] = float(ln.split()[-1])
            elif ln.startswith("deltaT = "):
                cur["dt"] = float(ln.split()[2])
            elif ln.startswith("Time = "):
                cur["t"] = float(ln.split()[2])
            elif ln.startswith("ExecutionTime"):
                if "t" in cur and "dt" in cur:
                    t.append(cur["t"]); dt.append(cur["dt"]); co.append(cur.get("co", np.nan))
                    aco.append(cur.get("aco", np.nan)); clock.append(float(ln.split()[-2]))
    return [np.array(v) for v in (t, dt, co, aco, clock)]


def checkmesh(d):
    p = d + "/log.checkMesh"
    if not os.path.exists(p):
        return {}
    t = open(p).read()
    f = lambda pat: float(re.search(pat, t).group(1)) if re.search(pat, t) else np.nan
    return dict(AR_max=f(r"Max aspect ratio = ([0-9.eE+-]+)"), nonorth_max=f(r"non-orthogonality Max: ([0-9.eE+-]+)"),
                skew_max=f(r"Max skewness = ([0-9.eE+-]+)"), mesh_ok="Mesh OK" in t)


def perfil(path, m):
    """h, q, M (agua) y tau de la primera celda de un perfil normal a la pared (y, alpha, p, Ux, Uy, Uz)."""
    a = np.loadtxt(path, ndmin=2)
    y = np.concatenate([[0.0], a[:, 0]])
    al = np.clip(np.concatenate([[a[0, 1]], a[:, 1]]), 0, 1)
    ux = np.concatenate([[0.0], a[:, 3]])
    rw = m["rho_w"]
    h = np.trapezoid(al, y)
    q = np.trapezoid(al * rw * np.abs(ux), y)
    M = np.trapezoid(al * rw * ux ** 2, y)
    mu1 = a[0, 1] * m["mu_w"] + (1 - a[0, 1]) * m["mu_a"]
    return h, q, M, mu1 * abs(a[0, 3]) / a[0, 0]


def analizar(d, ventana=None):
    m = json.load(open(d + "/meta.json"))
    S = m.get("S", 1.0)
    E0, V, B, LX = m["E0"], m["V0"], m["B"], m["LX"]
    RHO, MU = m["rho_w"], m["mu_w"]
    NU = MU / RHO
    comp = m.get("completo", False)
    fac = 1.0 if comp else 2.0
    T0, T1 = ventana if ventana else (3e-4 * S, 5e-4 * S)
    F_TEO, P0_TEO, M0, Q0 = RHO * V ** 2 * E0, 0.5 * RHO * V ** 2, 0.5 * RHO * V ** 2 * E0, 0.5 * RHO * V * E0
    r = dict(caso=os.path.basename(d.rstrip("/")), N=m["N"], Co=m["co"], g=" ".join("%g" % v for v in m.get("g", [0, 0, 0])),
             completo=int(comp), celdas=m["malla"]["celdas"], e0_mm=E0 * 1e3, S=S, delta_um=E0 / m["N"] * 1e6,
             Re_lamina=RHO * V * E0 / MU, t0_ventana=T0, t1_ventana=T1)
    r.update(checkmesh(d))
    fd = raw(glob.glob(d + "/postProcessing/fuerzas/0/force.dat")[0])
    w = (fd[:, 0] >= T0 - 1e-15) & (fd[:, 0] <= T1 + 1e-15)
    Fy = -fac * fd[w, 2] / B
    r.update(F_Nm=Fy.mean(), F_std=Fy.std(), F_err_teo=Fy.mean() / F_TEO - 1, F_teo=F_TEO)
    if not comp:
        r["Fcort_Nm"] = float(2 * np.abs(fd[w, 7]).mean() / B)
    w2 = (fd[:, 0] >= 1.0e-3 * S) & (fd[:, 0] <= 1.2e-3 * S)
    if w2.sum() > 5 and not ventana:
        r["F_estac_Nm"] = float((-fac * fd[w2, 2] / B).mean())
        r["F_estac_err_teo"] = r["F_estac_Nm"] / F_TEO - 1
    # pared
    ps, taus, als = [], [], []
    xs = dxs = None
    for td in sorted(glob.glob(d + "/postProcessing/paredSup/*"), key=lambda s: float(os.path.basename(s))):
        t = float(os.path.basename(td))
        if not (T0 - 1e-15 <= t <= T1 + 1e-15):
            continue
        a = raw(td + "/alpha.water_pared.raw")
        o = np.argsort(a[:, 0]); x = a[o, 0]
        lo = -LX if comp else 0.0
        dx = np.diff(np.concatenate([[lo], 0.5 * (x[1:] + x[:-1]), [LX]]))
        p = raw(td + "/p_pared.raw")[o, 3]; rho = raw(td + "/rho_pared.raw")[o, 3]
        ws = raw(td + "/wallShearStress_pared.raw")[o]
        ps.append(p); taus.append(rho * np.hypot(ws[:, 3], ws[:, 4])); als.append(a[o, 3]); xs, dxs = x, dx
    P, TAU, AL = np.mean(ps, 0), np.mean(taus, 0), np.mean(als, 0)
    ax = np.abs(xs)
    for xr in (1.0, 2.0):
        sel = ax <= xr * 1e-3 * S
        r[f"F_loc{xr:g}_Nm"] = float(fac * (P[sel] * dxs[sel]).sum())
        r[f"F_loc{xr:g}_err_teo"] = r[f"F_loc{xr:g}_Nm"] / F_TEO - 1
    i0 = np.argsort(ax)[:2] if comp else [0]
    r.update(p0_Pa=float(P[i0].mean()), p0_err_teo=float(P[i0].mean()) / P0_TEO - 1, p0_teo=P0_TEO,
             tau_max_Pa=TAU.max(), x_tau_max_um=xs[TAU.argmax()] * 1e6)
    pos = xs > 0
    for xr in (0.5, 1, 2, 4):
        r[f"tau_xr{xr:g}"] = float(np.interp(xr * 1e-3 * S, xs[pos], TAU[pos]))
        if comp:
            neg = xs < 0
            r[f"tau_mxr{xr:g}"] = float(np.interp(xr * 1e-3 * S, -xs[neg][::-1], TAU[neg][::-1]))
    near = (ax < (0.06e-3 if m["N"] >= 20 else 0.15e-3) * S) & pos
    if near.sum() >= 2:
        c = np.linalg.lstsq(np.vstack([np.ones(near.sum()), xs[near] ** 2]).T, P[near], rcond=None)[0]
        a_h = math.sqrt(max(-2 * c[1] / RHO, 0))
        r.update(a_Hiemenz=a_h, dtaudx_Hiemenz=HIEMENZ * MU * a_h ** 1.5 / math.sqrt(NU),
                 dtaudx_VOF=float(np.polyfit(xs[near], TAU[near], 1)[0]))
        r["dtaudx_err"] = r["dtaudx_VOF"] / r["dtaudx_Hiemenz"] - 1 if r["dtaudx_Hiemenz"] else np.nan
    # perfiles normales: h, q/q0, M/M0 por lado, en las dos ventanas
    filasM = []
    for lab, (a0, a1) in (("v1", (T0, T1)), ("v2", (1.0e-3 * S, 1.2e-3 * S))):
        acc = {}
        for td in glob.glob(d + "/postProcessing/lineas/*"):
            t = float(os.path.basename(td))
            if not (a0 - 1e-15 <= t <= a1 + 1e-15):
                continue
            for f in glob.glob(td + "/*_alpha.water_p_U.xy"):
                nom = os.path.basename(f).split("_alpha")[0]
                if nom == "eje":
                    continue
                acc.setdefault(nom, []).append(perfil(f, m))
        for nom, v in sorted(acc.items()):
            v = np.array(v)
            xr = float(nom.lstrip("m").replace("xr", "").replace("p", "."))
            lado = "-" if nom.startswith("m") else "+"
            h, q, M, t1 = v.mean(0)
            filasM.append([r["caso"], lab, lado, xr, xr * S, len(v), h * 1e6, q / Q0, M, v[:, 2].std(), M / M0, t1])
            if lab == "v1":
                k = ("m" if lado == "-" else "") + f"xr{xr:g}"
                r[f"h_{k}_um"], r[f"q_{k}_q0"], r[f"M_{k}_Nm"], r[f"M_{k}_M0"] = h * 1e6, q / Q0, M, M / M0
    r["M0_Nm"] = M0
    t, dt, co, aco, clock = log_dt(d)
    if t.size:
        wt = (t >= T0) & (t <= T1)
        r.update(dt_medio_ventana=dt[wt].mean() if wt.any() else np.nan,
                 Co_max_ventana=co[wt].max() if wt.any() else np.nan, pasos=len(t), t_fin=t[-1], pared_s=clock[-1],
                 np=m.get("np", 1))
    perf = dict(x=xs, p=P, tau=TAU, alpha=AL)
    return r, filasM, perf


def orden(a, b, c):
    try:
        return math.log(abs((a - b) / (b - c))) / math.log(2)
    except (ValueError, ZeroDivisionError):
        return np.nan


def escribir(nombre, filas, cab=None):
    os.makedirs(DAT, exist_ok=True)
    with open(f"{DAT}/{nombre}", "w", newline="") as f:
        if isinstance(filas[0], dict):
            cab = cab or sorted({k for x in filas for k in x}, key=lambda k: list(filas[0]).index(k) if k in filas[0] else 999)
            w = csv.DictWriter(f, fieldnames=cab)
            w.writeheader()
            for x in filas:
                w.writerow({k: (f"{v:.6g}" if isinstance(v, (float, np.floating)) else v) for k, v in x.items()})
        else:
            w = csv.writer(f)
            w.writerow(cab)
            for x in filas:
                w.writerow([f"{v:.6g}" if isinstance(v, (float, np.floating)) else v for v in x])


def regresion_v0():
    """V0: E1 N5 corrido desde la ruta v3 frente a la tanda 1 (mismos archivos de entrada -> mismo resultado)."""
    a, b = BASE + "/logs/e1/N5_Co0.5_lam", T1_E1 + "/N5_Co0.5_lam"
    if not os.path.exists(a + "/FIN"):
        return None
    fa = raw(glob.glob(a + "/postProcessing/fuerzas/0/force.dat")[0])
    fb = raw(glob.glob(b + "/postProcessing/fuerzas/0/force.dat")[0])
    n = min(len(fa), len(fb))
    filas = [["force.dat filas (v3, tanda 1)", len(fa), len(fb)],
             ["max |dt| entre tiempos (s)", float(np.abs(fa[:n, 0] - fb[:n, 0]).max()), ""],
             ["max |dFy| / max|Fy|", float(np.abs(fa[:n, 2] - fb[:n, 2]).max() / np.abs(fb[:n, 2]).max()), ""]]
    for tt in ("0.0003", "0.0005", "0.001"):
        pa, pb = glob.glob(f"{a}/postProcessing/paredSup/{tt}*/p_pared.raw"), glob.glob(f"{b}/postProcessing/paredSup/{tt}*/p_pared.raw")
        if pa and pb:
            A, Bv = raw(pa[0])[:, 3], raw(pb[0])[:, 3]
            filas.append([f"max |dp| pared t={tt} s (Pa)", float(np.abs(A - Bv).max()), float(np.abs(Bv).max())])
    ra, rb = open(a + "/resumen.txt").read().split("\n")[0], open(b + "/resumen.txt").read().split("\n")[0]
    filas.append(["resumen v3 / tanda 1", ra, rb])
    escribir("V0_regresion.csv", filas, ["comprobacion", "valor", "referencia"])
    return filas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--etapa", default="e1od")
    ap.add_argument("--ventana", type=float, nargs=2)
    a = ap.parse_args()
    res, Ms, perfs = [], [], {}
    for d in sorted(glob.glob(f"{BASE}/logs/{a.etapa}/*/")):
        d = d.rstrip("/\\")
        if not (os.path.exists(d + "/FIN") or a.ventana) or not os.path.exists(d + "/meta.json"):
            continue
        try:
            r, fm, pf = analizar(d, a.ventana)
        except Exception as e:  # noqa: BLE001  (un caso roto no tumba el resto; queda registrado)
            print("ERROR", d, e)
            continue
        res.append(r); Ms += fm; perfs[r["caso"]] = pf
        print(f"{r['caso']:36s} F={r['F_Nm']:.3f} N/m ({100 * r['F_err_teo']:+.2f} %)  p0={r['p0_Pa'] / 1e3:.1f} kPa "
              f"({100 * r['p0_err_teo']:+.2f} %)  tau_max={r['tau_max_Pa']:.0f} Pa  M(xr2)={r.get('M_xr2_Nm', np.nan):.2f} N/m "
              f"({r.get('M_xr2_M0', np.nan):.3f} M0)  pared={r.get('pared_s', np.nan):.0f} s")
    if not res:
        print("sin casos terminados"); return
    suf = "" if not a.ventana else "_prueba"
    escribir(f"E1OD_metricas{suf}.csv", res)
    escribir(f"E1OD_M_lineas{suf}.csv", Ms, ["caso", "ventana", "lado", "x_E1_mm", "x_mm", "n_instantes", "h_agua_um",
                                              "q_sobre_q0", "M_agua_Nm", "M_std", "M_sobre_M0", "tau1celda_Pa"])
    fil = []
    for c, p in perfs.items():
        for i in range(len(p["x"])):
            fil.append([c, p["x"][i], p["p"][i], p["tau"][i], p["alpha"][i]])
    escribir(f"E1OD_perfiles_pared{suf}.csv", fil, ["caso", "x_m", "p_Pa", "tau_w_Pa", "alpha_pared"])
    if a.ventana:
        return
    R = {r["caso"]: r for r in res}
    # convergencia (laminar, Co 0,5, sin gravedad, medio dominio)
    base = sorted([r for r in res if r["Co"] == 0.5 and r["g"] == "0 0 0" and not r["completo"]], key=lambda r: r["N"])
    mags = ["p0_Pa", "F_Nm", "F_loc1_Nm", "F_loc2_Nm", "tau_max_Pa", "tau_xr0.5", "tau_xr1", "tau_xr2", "dtaudx_VOF",
            "h_xr1_um", "h_xr2_um", "h_xr4_um", "M_xr1_Nm", "M_xr2_Nm", "M_xr5_Nm", "q_xr2_q0"]
    teo = {"p0_Pa": base[0]["p0_teo"] if base else np.nan, "F_Nm": base[0]["F_teo"] if base else np.nan,
           "F_loc1_Nm": base[0]["F_teo"] if base else np.nan, "F_loc2_Nm": base[0]["F_teo"] if base else np.nan}
    filas = []
    if len(base) >= 2:
        fino = base[-1]
        for mg in mags:
            vals = [r.get(mg, np.nan) for r in base]
            p1 = orden(*vals[0:3]) if len(vals) >= 3 else np.nan
            p2 = orden(*vals[1:4]) if len(vals) >= 4 else np.nan
            for r, v in zip(base, vals):
                ef = abs(v - fino.get(mg, np.nan)) / abs(fino.get(mg, np.nan)) if fino.get(mg) else np.nan
                et = abs(v - teo[mg]) / abs(teo[mg]) if mg in teo else np.nan
                filas.append([mg, r["N"], r["celdas"], r["delta_um"], v, fino["N"], fino.get(mg, np.nan), ef,
                              teo.get(mg, ""), et, p1, p2, r.get("pared_s", np.nan), r.get("np", "")])
        escribir("E1OD_convergencia.csv", filas, ["magnitud", "N", "celdas", "delta_um", "valor", "N_fino", "valor_fino",
                                                  "error_rel_fino", "teoria", "error_rel_teoria", "orden_5-10-20",
                                                  "orden_10-20-40", "pared_s", "np"])
    # paso de tiempo (N20, Co 0,25 / 0,5 / 1; ventana comun 0,3-0,5 ms*S)
    dtc = [R.get(f"OD_N20_Co{c}") for c in ("0.25", "0.5", "1")]
    if dtc[0]:
        ref = dtc[0]
        fil = []
        for r in [x for x in dtc if x]:
            fil.append([r["caso"], r["Co"], r.get("dt_medio_ventana", np.nan)] +
                       [r.get(k, np.nan) / ref.get(k, np.nan) - 1 for k in ("p0_Pa", "F_loc1_Nm", "tau_xr2", "h_xr2_um", "M_xr2_Nm")] +
                       [r.get("pared_s", np.nan)])
        escribir("E1OD_dt.csv", fil, ["caso", "Co", "dt_medio_s", "dp0", "dF_loc1", "dtau_xr2", "dh_xr2", "dM_xr2", "pared_s"])
    # gravedad
    pares = [("OD_N10_Co0.5", "OD_N10_Co0.5_g0_-9.81_0", "hacia la pared (cara superior)"),
             ("OD_N10_Co0.5", "OD_N10_Co0.5_g0_9.81_0", "alejandose de la pared (cara inferior)"),
             ("OD_N20_Co0.5", "OD_N20_Co0.5_g0_-9.81_0", "hacia la pared, N20"),
             ("OD_N10_Co0.5_completo", "OD_N10_Co0.5_g-9.81_0_0_completo", "a lo largo de la pared (I3 falso)"),
             ("OD_N10_Co0.5", "OD_N10_Co0.5_completo", "control: medio dominio frente a completo, sin g")]
    fil = []
    for c0, c1, lab in pares:
        if c0 in R and c1 in R:
            for k in ("p0_Pa", "F_Nm", "F_loc1_Nm", "tau_max_Pa", "tau_xr2", "h_xr2_um", "M_xr2_Nm", "M_xr5_Nm"):
                v0, v1 = R[c0].get(k, np.nan), R[c1].get(k, np.nan)
                fil.append([lab, c0, c1, k, v0, v1, v1 / v0 - 1 if v0 else np.nan])
            if R[c1]["completo"]:   # asimetria entre los dos lados
                for k in ("h_xr2_um", "M_xr2_Nm", "M_xr5_Nm", "tau_xr2"):
                    km = k.replace("xr", "mxr")
                    vp, vm = R[c1].get(k, np.nan), R[c1].get(km, np.nan)
                    fil.append([lab + " (lado -x frente a +x)", c1, c1, k, vp, vm, vm / vp - 1 if vp else np.nan])
    if fil:
        escribir("E1OD_gravedad.csv", fil, ["caso_gravedad", "sin_g", "con_g", "magnitud", "valor_sin_g", "valor_con_g", "cambio_rel"])
    v0 = regresion_v0()
    if v0:
        for f in v0:
            print("V0", f)


if __name__ == "__main__":
    main()
