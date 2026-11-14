#!/usr/bin/env python3
# v3 (CORRIDA 2, 24/10/2026): copia de CORRIDA_1_13a21oct/06_VOF/scripts/v2_e1_b3_b4.py con rutas cambiadas a 02_VOF_v3 y /home/piermoto/vof3 (sed); sin otros cambios.
"""VOF v2 - E1: tareas B3 (error frente a dt) y B4 (empuje de la pelicula M = int rho u_t^2 dy).

B3: datos/E1_metricas.csv (barrido Co 0,25/0,5/1/2 en N20; ventana 0,3-0,5 ms). Eje x = dt medio en la ventana
    (columna dt_medio_ventana); eje y = |valor/valor(Co 0,25) - 1| para p0, F/b local (|x| < 2 mm), espesor y
    tau_w en x = 2 mm, y velocidad del frente.
B4: perfiles normales a la pared en x = 1, 2, 5, 10 mm (logs/v2_b4/<caso>/lineasB4/<t>/x*mm_alpha.water_p_U.xy,
    columnas y, alpha, p, Ux, Uy, Uz; v2_b4_lineas.sh). Por perfil:
      q   = int alpha rho_w u_x dy          caudal de agua por unidad de ancho (kg/(s m)); teoria q0 = rho v e0/2
      M_w = int alpha rho_w u_x^2 dy        empuje (flujo de cantidad de movimiento) del agua (N/m)
      M   = int rho_mezcla u_x^2 dy         idem con la densidad de la mezcla (agua + aire)
      h   = int alpha dy                    espesor equivalente de agua
    Integracion trapezoidal con el punto de pared (y = 0, u = 0). Teoria sin viscosidad (medio dominio):
    M0 = rho v^2 e0 / 2 = 111,2 N/m. Balance de momento de la pelicula: M_w(x1) - M_w(x2) ~ int tau_w dx
    (tau_w de datos/E1_perfiles_tau.csv), sin presion ni arrastre del aire.
Salidas: datos/B3_E1_error_dt.csv, datos/B4_E1_empuje_pelicula.csv, figuras/VOF2-FIG-B3_E1_error_dt.png,
         figuras/VOF2-FIG-B4_E1_empuje_pelicula.png (+ CSV).
Uso: python -I v2_e1_b3_b4.py"""
import csv, glob, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from v3_estilo import plt, guardar, pie, csv_escribir, CAT, INK2, GRAY, DAT2  # noqa: E402

B = "D:/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3"
RHO_W, RHO_A, V0, E0 = 982.12, 0.9061, 27.4711, 0.30e-3
Q0, M0 = RHO_W * V0 * E0 / 2, RHO_W * V0 ** 2 * E0 / 2
PIE = "Fuente: 06_VOF (E1, lámina 2D, interFoam v2606), v2 17/10/2026. Estado: CANDIDATO; verificado ≠ validado."

# ------------------------------------------------------------------ B3
E1 = {r["caso"]: r for r in csv.DictReader(open(f"{B}/datos/E1_metricas.csv"))}
co_casos = [("N20_Co0.25_lam", 0.25), ("N20_Co0.5_lam", 0.5), ("N20_Co1_lam", 1.0), ("N20_Co2_lam", 2.0)]
mags = [("p0_Pa", "p₀ (estancamiento)"), ("F_loc2mm_Nm", "F/b local (|x| < 2 mm)"),
        ("h_x2mm_um", "espesor en x = 2 mm"), ("tau_x2mm", "τ_w en x = 2 mm"), ("v_frente_m_s", "velocidad del frente")]
ref = E1["N20_Co0.25_lam"]
filas = []
for c, co in co_casos:
    for k, lab in mags:
        v, v0 = float(E1[c][k]), float(ref[k])
        filas.append([c, co, float(E1[c]["dt_medio_ventana"]), k, v, v0, abs(v / v0 - 1)])
cab = ["caso", "maxCo", "dt_medio_s", "magnitud", "valor", "valor_Co0.25", "error_rel"]
csv_escribir(f"{DAT2}/B3_E1_error_dt.csv", cab, filas)
fig, ax = plt.subplots(figsize=(9.2, 4.3))
PISO = 1e-5
for i, (k, lab) in enumerate(mags):
    F = [f for f in filas if f[3] == k and f[1] > 0.25]
    dt = [f[2] for f in F]; e = [max(f[6], PISO) for f in F]
    ax.plot(dt, e, "o-", color=CAT[i], ms=5, label=lab)
dts = np.array([float(E1[c]["dt_medio_ventana"]) for c, _ in co_casos])
ax.plot(dts[1:], 0.05 * dts[1:] / dts[1], ":", color=GRAY, lw=1.2, label="pendiente 1 (error ∝ Δt)")
ax.axhline(0.01, color=GRAY, ls="--", lw=0.9); ax.text(dts[1] * 1.02, 0.0106, "1 %", fontsize=7, color=INK2)
for c, co in co_casos:
    ax.annotate(f"Co {co:g}", (float(E1[c]["dt_medio_ventana"]), PISO), textcoords="offset points", xytext=(0, -14),
                ha="center", fontsize=7, color=INK2)
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(PISO * 0.5, 0.3)
ax.set_xlabel("Δt medio en la ventana 0,3-0,5 ms (s)"); ax.set_ylabel("error relativo frente a Co = 0,25 (−)")
ax.set_title("E1 (N20): error frente al paso de tiempo (barrido maxCo = maxAlphaCo)", fontsize=10)
ax.legend(fontsize=7.5, loc="center left", bbox_to_anchor=(1.01, 0.5))
pie(fig, PIE + f"\nDatos: datos/E1_metricas.csv (ventana 0,3-0,5 ms). Referencia: Co 0,25, Δt = {dts[0]:.2e} s.")
fig.tight_layout(rect=(0, 0.05, 1, 1))
guardar(fig, "VOF2-FIG-B3_E1_error_dt", filas, cab)

# ------------------------------------------------------------------ B4
tau = {}
for r in csv.DictReader(open(f"{B}/datos/E1_perfiles_tau.csv")):
    tau.setdefault(r["caso"], []).append((float(r["x_m"]), float(r["tau_w_Pa"])))
filas, res = [], {}
for caso in ("N20_Co0.5_lam", "N40_Co0.5_lam"):
    for d in sorted(glob.glob(f"{B}/logs/v2_b4/{caso}/lineasB4/*")):
        t = float(os.path.basename(d))
        for xmm in (1, 2, 5, 10):
            p = glob.glob(f"{d}/x{xmm}mm_*.xy")
            if not p:
                continue
            a = np.loadtxt(p[0])
            y = np.concatenate([[0.0], a[:, 0]]); al = np.concatenate([[a[0, 1]], a[:, 1]])
            ux = np.concatenate([[0.0], a[:, 3]])
            al = np.clip(al, 0, 1); rho = al * RHO_W + (1 - al) * RHO_A
            q = np.trapezoid(al * RHO_W * ux, y); Mw = np.trapezoid(al * RHO_W * ux ** 2, y)
            Mm = np.trapezoid(rho * ux ** 2, y); h = np.trapezoid(al, y)
            filas.append([caso, t, xmm, h * 1e6, q, q / Q0, Mw, Mm, Mw / M0])
            res.setdefault((caso, t), {})[xmm] = (h, q, Mw, Mm)
cab = ["caso", "t_s", "x_mm", "h_agua_um", "q_kg_s_m", "q_sobre_q0", "M_agua_N_m", "M_mezcla_N_m", "M_agua_sobre_M0"]
csv_escribir(f"{DAT2}/B4_E1_empuje_pelicula.csv", cab, filas)
# medias por ventana
ven = {"N20 0,3-0,5 ms": ("N20_Co0.5_lam", (3e-4, 5e-4)), "N40 0,3-0,5 ms": ("N40_Co0.5_lam", (3e-4, 5e-4)),
       "N20 1,0-1,2 ms": ("N20_Co0.5_lam", (1e-3, 1.2e-3))}
resumen = []
for lab, (caso, (t0, t1)) in ven.items():
    for xmm in (1, 2, 5, 10):
        F = [f for f in filas if f[0] == caso and t0 - 1e-9 <= f[1] <= t1 + 1e-9 and f[2] == xmm]
        if not F:
            continue
        Mw = np.array([f[6] for f in F]); q = np.array([f[4] for f in F]); h = np.array([f[3] for f in F])
        resumen.append([lab, xmm, len(F), h.mean(), q.mean(), q.mean() / Q0, Mw.mean(), Mw.std(), Mw.mean() / M0])
# balance de momento con tau_w (ventana 0,3-0,5 ms de E1_perfiles_tau)
bal = []
for caso, lab in (("N20_Co0.5_lam", "N20 0,3-0,5 ms"), ("N40_Co0.5_lam", "N40 0,3-0,5 ms")):
    T = np.array(sorted(tau[caso])); R = {r[1]: r for r in resumen if r[0] == lab}
    for x1, x2 in ((1, 2), (2, 5), (1, 5)):
        if x1 in R and x2 in R:
            s = (T[:, 0] >= x1 * 1e-3) & (T[:, 0] <= x2 * 1e-3)
            it = np.trapezoid(T[s, 1], T[s, 0])
            bal.append([lab, x1, x2, R[x1][6] - R[x2][6], it])
cabr = ["ventana", "x_mm", "n_instantes", "h_agua_um", "q_kg_s_m", "q_sobre_q0", "M_agua_N_m", "M_agua_std", "M_sobre_M0"]
csv_escribir(f"{DAT2}/B4_E1_empuje_resumen.csv", cabr, resumen)
csv_escribir(f"{DAT2}/B4_E1_balance_momento.csv", ["ventana", "x1_mm", "x2_mm", "M1_menos_M2_N_m", "int_tau_w_dx_N_m"], bal)
fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.0))
for i, lab in enumerate(ven):
    R = [r for r in resumen if r[0] == lab]
    ax[0].errorbar([r[1] for r in R], [r[6] for r in R], yerr=[r[7] for r in R], fmt="o-", color=CAT[i], ms=5,
                   capsize=3, label=lab)
    ax[1].plot([r[1] for r in R], [r[5] for r in R], "o-", color=CAT[i], ms=5, label=lab)
ax[0].axhline(M0, color=GRAY, ls="--", lw=1); ax[0].text(10, M0 * 1.01, "ρv²e₀/2 = %.1f N/m (sin viscosidad)" % M0,
                                                      ha="right", va="bottom", fontsize=7, color=INK2)
ax[0].axvspan(9.3, 10.7, color="#eb6834", alpha=0.12, lw=0)
ax[0].text(9.2, 8, "x = 10 mm a 0,3-0,5 ms:\nes el frente de la película\n(poco fiable)", ha="right", fontsize=6.8, color="#a3441d")
ax[0].set_xlabel("distancia al eje del impacto x (mm)"); ax[0].set_ylabel("M = ∫ α ρ_w u_x² dy (N/m)")
ax[0].set_title("Empuje de la película (por unidad de ancho)", fontsize=10); ax[0].set_ylim(0, 130)
ax[0].legend(fontsize=7.5, loc="lower left")
ax[1].axhline(1, color=GRAY, ls="--", lw=1)
ax[1].set_xlabel("distancia al eje del impacto x (mm)"); ax[1].set_ylabel("q / (ρ v e₀/2) (−)")
ax[1].set_title("Comprobación: caudal de agua por la línea", fontsize=10); ax[1].set_ylim(0, 1.3)
pie(fig, PIE + " Datos: logs/v2_b4 (v2_b4_lineas.sh, copia de los campos), datos/B4_E1_*.csv. Medio dominio (plano de simetría).")
fig.tight_layout(rect=(0, 0.03, 1, 1))
guardar(fig, "VOF2-FIG-B4_E1_empuje_pelicula", resumen, cabr)
for r in resumen: print("B4", r[0], "x=%d" % r[1], "n=%d" % r[2], "h=%.0f um" % r[3], "q/q0=%.3f" % r[5], "M=%.1f+-%.1f N/m" % (r[6], r[7]), "M/M0=%.3f" % r[8])
for b in bal: print("balance", b)
for k, lab in mags:
    print("B3", k, ["%.2e" % f[6] for f in filas if False])
