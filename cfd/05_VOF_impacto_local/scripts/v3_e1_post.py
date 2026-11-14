#!/usr/bin/env python3
# v3 (CORRIDA 2, 24/10/2026): copia de CORRIDA_1_13a21oct/06_VOF/scripts/e1_post.py con rutas cambiadas a 02_VOF_v3 y /home/piermoto/vof3 (sed); sin otros cambios.
"""
Etapa 1 - posproceso de la lamina 2D (interFoam). Lee las copias ligeras en 06_VOF/logs/e1/<caso>/
(postProcessing de fuerzas y pared, perfiles 'lineas', meta.json, log.interFoam.gz, log.checkMesh)
y escribe:
  06_VOF/datos/E1_metricas.csv          una fila por caso, magnitudes promediadas en la ventana comun
  06_VOF/datos/E1_mojado_t.csv          longitud mojada frente al tiempo (alpha_pared >= 0,5 y >= 0,01)
  06_VOF/datos/E1_perfiles_tau.csv      perfiles de tau_w y p en la pared (ventana comun) por caso
  06_VOF/datos/E1_convergencia.csv      error relativo frente a la malla fina N40
Ventana comun: 0,3-0,5 ms (N40 se corrio hasta 0,5 ms; el resto hasta 0,6 o 1,2 ms).
Teoria (lamina plana intacta, invisicida): F/b = rho*v^2*e0 ; p0 = 1/2*rho*v^2.
Uso: python e1_post.py
"""
import csv
import glob
import gzip
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v3_e1_generar as g  # noqa: E402

BASE = "D:/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3"
L1 = f"{BASE}/logs/e1"
DAT = f"{BASE}/datos"
os.makedirs(DAT, exist_ok=True)
T0, T1 = 3e-4, 5e-4
RHO, MU, V, E0, B = g.RHO_W, g.MU_W, g.V0, g.E0, g.B
NU = MU / RHO
F_TEO = RHO * V ** 2 * E0              # N/m, lamina completa
P0_TEO = 0.5 * RHO * V ** 2            # Pa
CASOS = ["N5_Co0.5_lam", "N10_Co0.5_lam", "N20_Co0.5_lam", "N40_Co0.5_lam",
         "N20_Co0.25_lam", "N20_Co1_lam", "N20_Co2_lam", "N20_Co0.5_kOmegaSST"]


def raw(path):
    return np.loadtxt(path, comments="#", ndmin=2)


def tiempos_pared(caso):
    ds = glob.glob(f"{L1}/{caso}/postProcessing/paredSup/*")
    return sorted(((float(os.path.basename(d)), d) for d in ds), key=lambda t: t[0])


def checkmesh(caso):
    t = open(f"{L1}/{caso}/log.checkMesh").read()
    f = lambda pat: float(re.search(pat, t).group(1))
    return dict(AR_max=f(r"Max aspect ratio = ([0-9.eE+-]+)"),
                nonorth_max=f(r"non-orthogonality Max: ([0-9.eE+-]+)"),
                nonorth_med=f(r"average: ([0-9.eE+-]+)"),
                skew_max=f(r"Max skewness = ([0-9.eE+-]+)"),
                mesh_ok="Mesh OK" in t)


def log_dt(caso):
    t, dt, co, aco, clock = [], [], [], [], []
    with gzip.open(f"{L1}/{caso}/log.interFoam.gz", "rt", errors="ignore") as f:
        cur = {}
        for ln in f:
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


def perfil_lineas(caso, N):
    """Espesor y velocidad media de la pelicula, tau de la primera celda, por x y tiempo de la ventana."""
    _, yn = g.nodos(N)
    out = {}
    for tdir in sorted(glob.glob(f"{L1}/{caso}/lineas/*")):
        t = float(os.path.basename(tdir))
        if not (T0 - 1e-9 <= t <= T1 + 1e-9):
            continue
        for f in glob.glob(f"{tdir}/*_alpha.water_p_U.xy"):
            nom = os.path.basename(f).split("_")[0]
            d = raw(f)
            y, a, p, ux = d[:, 0], d[:, 1], d[:, 2], d[:, 3]
            j = np.clip(np.searchsorted(yn, y) - 1, 0, len(yn) - 2)
            dy = yn[j + 1] - yn[j]
            h = float((a * dy).sum())
            uf = float((a * ux * dy).sum() / max(h, 1e-30))
            mu1 = a[0] * MU + (1 - a[0]) * g.MU_A
            tau1 = mu1 * ux[0] / y[0]                 # mu_mezcla * u / distancia del centro a la pared
            out.setdefault(nom, []).append((t, h, uf, tau1, float(p[0])))
    return {k: np.array(v) for k, v in out.items()}


def analizar(caso):
    meta = json.load(open(f"{L1}/{caso}/meta.json"))
    N = meta["N"]
    res = dict(caso=caso, N=N, Co=meta["co"], modelo=meta["modelo"], celdas=meta["malla"]["celdas"],
               delta_um=E0 / N * 1e6, dy_pared_um=meta["malla"]["dy_pared"] * 1e6)
    res.update(checkmesh(caso))
    # fuerza
    fd = raw(glob.glob(f"{L1}/{caso}/postProcessing/fuerzas/0/force.dat")[0])
    w = (fd[:, 0] >= T0) & (fd[:, 0] <= T1)
    Fy = -2 * fd[w, 2] / B                           # lamina completa (x2 por la simetria), N/m
    Fp = -2 * fd[w, 5] / B
    Fx_visc = 2 * np.abs(fd[w, 7]) / B               # fuerza cortante total en la pared (dos lados), N/m
    res.update(F_Nm=Fy.mean(), F_std=Fy.std(), F_pres_Nm=Fp.mean(), Fcort_Nm=Fx_visc.mean(),
               F_err_teo=Fy.mean() / F_TEO - 1)
    # pared: p, tau, alpha en la ventana
    ps, taus, als, xs = [], [], [], None
    moj = []
    for t, d in tiempos_pared(caso):
        a = raw(f"{d}/alpha.water_pared.raw")
        x = a[:, 0]
        o = np.argsort(x)
        x, al = x[o], a[o, 3]
        dx = np.diff(np.concatenate([[0.0], 0.5 * (x[1:] + x[:-1]), [g.LX]]))
        for thr, key in ((0.5, "L05"), (0.01, "L001")):
            pass
        mojado05 = float(dx[al >= 0.5].sum())
        mojado001 = float(dx[al >= 0.01].sum())
        moj.append((t, mojado05, mojado001))
        if T0 - 1e-9 <= t <= T1 + 1e-9:
            p = raw(f"{d}/p_pared.raw")[o, 3]
            rho = raw(f"{d}/rho_pared.raw")[o, 3]
            ws = raw(f"{d}/wallShearStress_pared.raw")[o]
            tau = rho * np.hypot(ws[:, 3], ws[:, 4])
            ps.append(p); taus.append(tau); als.append(al); xs = x; dxs = dx
    P = np.mean(ps, 0); TAU = np.mean(taus, 0); AL = np.mean(als, 0)
    # fuerza local: integral de p sobre |x| < 1 y 2 mm (lamina completa), estacionaria antes que la total
    for xc in (1.0, 2.0):
        sel = xs <= xc * 1e-3
        res[f"F_loc{xc:g}mm_Nm"] = float(2 * (P[sel] * dxs[sel]).sum())
        res[f"F_loc{xc:g}mm_err_teo"] = res[f"F_loc{xc:g}mm_Nm"] / F_TEO - 1
    w2 = (fd[:, 0] >= 1.0e-3) & (fd[:, 0] <= 1.2e-3)
    if w2.sum() > 5:                                  # tras salir el frente del dominio (solo corridas a 1,2 ms)
        res["F_estac_1.0-1.2ms_Nm"] = float((-2 * fd[w2, 2] / B).mean())
        res["F_estac_err_teo"] = res["F_estac_1.0-1.2ms_Nm"] / F_TEO - 1
    res.update(p0_Pa=P[0], x_p0_um=xs[0] * 1e6, p0_err_teo=P[0] / P0_TEO - 1,
               tau_max_Pa=TAU.max(), x_tau_max_mm=xs[TAU.argmax()] * 1e3)
    for xm in (0.5, 1.0, 2.0, 4.0, 8.0):
        res[f"tau_x{xm:g}mm"] = float(np.interp(xm * 1e-3, xs, TAU))
    # Hiemenz: p = p0 - 1/2 rho a^2 x^2 cerca del eje -> a; tau = 1,2326 mu a^1,5 nu^-0,5 x
    near = xs < 0.06e-3 if N >= 20 else xs < 0.15e-3
    if near.sum() >= 2:
        A = np.vstack([np.ones(near.sum()), xs[near] ** 2]).T
        c = np.linalg.lstsq(A, P[near], rcond=None)[0]
        a_h = math.sqrt(max(-2 * c[1] / RHO, 0))
        res.update(a_Hiemenz_1s=a_h, dtaudx_Hiemenz=1.2326 * MU * a_h ** 1.5 / math.sqrt(NU),
                   dtaudx_VOF=float(np.polyfit(xs[near], TAU[near], 1)[0]))
    # perfiles de linea
    pl = perfil_lineas(caso, N)
    for nom, arr in pl.items():
        res[f"h_{nom}_um"] = arr[:, 1].mean() * 1e6
        res[f"uf_{nom}"] = arr[:, 2].mean()
        res[f"tau1celda_{nom}"] = arr[:, 3].mean()
    # mojado
    moj = np.array(moj)
    res["L_moj05_t0.5ms_mm"] = float(np.interp(5e-4, moj[:, 0], moj[:, 1])) * 1e3
    sel = (moj[:, 0] >= 1.5e-4) & (moj[:, 0] <= 4.5e-4)
    res["v_frente_m_s"] = float(np.polyfit(moj[sel, 0], moj[sel, 1], 1)[0]) if sel.sum() > 3 else np.nan
    # Courant y costo
    t, dt, co, aco, clock = log_dt(caso)
    w = (t >= T0) & (t <= T1)
    res.update(dt_medio_ventana=dt[w].mean(), Co_max_ventana=co[w].max(), alphaCo_max_ventana=aco[w].max(),
               pasos=len(t), t_fin=t[-1], pared_s=clock[-1], np=meta.get("np", 1))
    res["nucleo_h_por_ms"] = res["pared_s"] / 3600 * res["np"] / (res["t_fin"] * 1e3)
    perf = dict(x=xs, p=P, tau=TAU, alpha=AL)
    return res, moj, perf


def main():
    filas, mojs, perfs = [], {}, {}
    for c in CASOS:
        if not os.path.exists(f"{L1}/{c}/resumen.txt"):
            print("falta", c); continue
        r, m, p = analizar(c)
        filas.append(r); mojs[c] = m; perfs[c] = p
        print(f"{c:22s} F={r['F_Nm']:.2f} N/m ({100*r['F_err_teo']:+.2f} %)  p0={r['p0_Pa']/1e3:.1f} kPa "
              f"({100*r['p0_err_teo']:+.2f} %)  tau_max={r['tau_max_Pa']:.0f} Pa @ {r['x_tau_max_mm']:.3f} mm  "
              f"h2mm={r.get('h_x2mm_um', np.nan):.1f} um  dt={r['dt_medio_ventana']:.3g}  Co={r['Co_max_ventana']:.2f}")
    claves = sorted({k for f in filas for k in f}, key=lambda k: list(filas[0]).index(k) if k in filas[0] else 999)
    with open(f"{DAT}/E1_metricas.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=claves); w.writeheader()
        for r in filas:
            w.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()})
    with open(f"{DAT}/E1_mojado_t.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["caso", "t_s", "L_mojada_alpha05_m", "L_mojada_alpha001_m", "pct_alpha05"])
        for c, m in mojs.items():
            for t, a, b in m:
                w.writerow([c, f"{t:.6g}", f"{a:.6g}", f"{b:.6g}", f"{100 * a / g.LX:.4g}"])
    with open(f"{DAT}/E1_perfiles_tau.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["caso", "x_m", "p_Pa", "tau_w_Pa", "alpha_pared"])
        for c, p in perfs.items():
            for i in range(len(p["x"])):
                w.writerow([c, f"{p['x'][i]:.6g}", f"{p['p'][i]:.6g}", f"{p['tau'][i]:.6g}", f"{p['alpha'][i]:.4g}"])
    # convergencia frente a N40
    fino = next(r for r in filas if r["caso"] == "N40_Co0.5_lam")
    mags = ["F_loc1mm_Nm", "F_loc2mm_Nm", "F_Nm", "p0_Pa", "dtaudx_VOF", "tau_max_Pa", "tau_x0.5mm", "tau_x1mm", "tau_x2mm", "tau_x4mm", "h_x1mm_um",
            "h_x2mm_um", "h_x4mm_um", "uf_x2mm", "L_moj05_t0.5ms_mm", "v_frente_m_s", "Fcort_Nm"]
    with open(f"{DAT}/E1_convergencia.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["magnitud", "N", "celdas", "delta_um", "valor", "valor_N40", "error_rel",
                                       "orden_observado_5-10-20", "orden_observado_10-20-40"])
        base = [r for r in filas if r["Co"] == 0.5 and r["modelo"] == "laminar"]
        base.sort(key=lambda r: r["N"])
        for m in mags:
            vals = [r.get(m, np.nan) for r in base]
            def orden(a, b, c):
                try:
                    return math.log(abs((a - b) / (b - c))) / math.log(2)
                except (ValueError, ZeroDivisionError):
                    return np.nan
            p1 = orden(*vals[0:3]) if len(vals) >= 3 else np.nan
            p2 = orden(*vals[1:4]) if len(vals) >= 4 else np.nan
            for r, v in zip(base, vals):
                w.writerow([m, r["N"], r["celdas"], f"{r['delta_um']:.4g}", f"{v:.6g}", f"{fino.get(m, np.nan):.6g}",
                            f"{abs(v - fino.get(m, np.nan)) / abs(fino.get(m, np.nan)):.4g}", f"{p1:.3g}", f"{p2:.3g}"])
    print("teoria F/b =", F_TEO, "N/m ; p0 =", P0_TEO, "Pa")


if __name__ == "__main__":
    main()
