#!/usr/bin/env python3
# v3 (CORRIDA 2, 24/10/2026): copia de CORRIDA_1_13a21oct/06_VOF/scripts/e1_figuras.py con rutas cambiadas a 02_VOF_v3 y /home/piermoto/vof3 (sed); sin otros cambios.
"""
Etapa 1 - figuras VOF-FIG-01..08 y 10 de la lamina 2D, a partir de 06_VOF/datos/E1_*.csv (e1_post.py)
y de los cortes de alpha (logs/e1/<caso>/corte). PNG a 200 dpi en 06_VOF/figuras/ con su CSV.
Paleta: la de referencia del skill dataviz (azul secuencial para niveles de malla; categoricos
azul/naranja/aqua/violeta en orden fijo), etiquetas directas, tinta de texto neutra.
Uso: python e1_figuras.py
"""
import csv
import glob
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v3_e1_generar as g  # noqa: E402

BASE = "D:/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3"
DAT, FIG = f"{BASE}/datos", f"{BASE}/figuras"
os.makedirs(FIG, exist_ok=True)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
SEQ = {5: "#86b6ef", 10: "#3987e5", 20: "#1c5cab", 40: "#0d366b"}
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#6250d6"]
GRAY = "#8a8985"
PIE = "Fuente: 06_VOF (etapa 1, lámina 2D, interFoam v2606). Estado: CANDIDATO, verificado ≠ validado."
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "axes.facecolor": SURF, "figure.facecolor": SURF, "lines.linewidth": 2,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False})


def leer(nombre):
    return list(csv.DictReader(open(f"{DAT}/{nombre}")))


def pie(fig, extra=""):
    fig.text(0.01, 0.005, PIE + (" " + extra if extra else ""), fontsize=6.5, color=INK2, ha="left", va="bottom")


def guardar(fig, nombre, filas=None, cab=None):
    fig.savefig(f"{FIG}/{nombre}.png", dpi=200)
    plt.close(fig)
    if filas is not None:
        with open(f"{FIG}/{nombre}.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(cab); w.writerows(filas)
    print("figura", nombre)


M = {r["caso"]: r for r in leer("E1_metricas.csv")}
BASEC = [f"N{n}_Co0.5_lam" for n in (5, 10, 20, 40)]
f_ = lambda c, k: float(M[c][k]) if M[c].get(k, "") not in ("", "nan") else np.nan
F_TEO = g.RHO_W * g.V0 ** 2 * g.E0
P0_TEO = 0.5 * g.RHO_W * g.V0 ** 2

# ------------------------------------------------------------------ VOF-FIG-08 teoria
fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.4))
Ns = [5, 10, 20, 40]
filas = []
for i, (k, teo, lab, esc) in enumerate((("F_loc2mm_Nm", F_TEO, "Fuerza por ancho en |x| < 2 mm (N/m)", 1),
                                        ("p0_Pa", P0_TEO, "Presión de estancamiento en la pared (kPa)", 1e-3),
                                        ("dtaudx_VOF", None, "Pendiente dτ_w/dx junto al eje (Pa/mm)", 1e-3))):
    v = [f_(c, k) * esc for c in BASEC]
    ax[i].plot(Ns, v, "o-", color=SEQ[20], ms=6)
    if teo is not None:
        ax[i].axhline(teo * esc, color=GRAY, ls="--", lw=1.2)
        ax[i].text(5, teo * esc, "teoría" if i else "teoría ρv²e₀ = %.1f" % (teo * esc), color=INK2, va="bottom", fontsize=8)
    else:
        th = [f_(c, "dtaudx_Hiemenz") * esc for c in BASEC]
        ax[i].plot(Ns, th, "s--", color=GRAY, lw=1.2, ms=4)
        ax[i].text(5.2, th[0] * 1.02, "Hiemenz con la a medida", color=INK2, fontsize=8, va="bottom")
    if i == 0:
        ax[i].plot(Ns, [f_(c, "F_Nm") for c in BASEC], "o", mfc="none", color=CAT[1], ms=6)
        ax[i].text(10.5, f_("N10_Co0.5_lam", "F_Nm") + 1, "pared completa (0,3-0,5 ms)", color=CAT[1], fontsize=7.5)
    ax[i].set_xscale("log", base=2); ax[i].set_xticks(Ns); ax[i].set_xticklabels(Ns)
    ax[i].set_xlabel("N = celdas a través del espesor e₀"); ax[i].set_title(lab, fontsize=9, color=INK, loc="left")
    for n, c, val in zip(Ns, BASEC, v):
        filas.append([k, n, val, teo * esc if teo else f_(c, "dtaudx_Hiemenz") * esc])
fig.suptitle("VOF-FIG-08 · Lámina 2D intacta (e₀ = 0,30 mm, v = 27,47 m/s) frente a la teoría", x=0.01, ha="left", fontsize=10)
fig.tight_layout(rect=(0, 0.04, 1, 0.95)); pie(fig)
guardar(fig, "VOF-FIG-08_E1_teoria", filas, ["magnitud", "N", "valor", "teoria"])

# ------------------------------------------------------------------ VOF-FIG-01 error relativo
conv = leer("E1_convergencia.csv")
def serie(m):
    s = [r for r in conv if r["magnitud"] == m and r["N"] != "40"]
    return np.array([float(r["delta_um"]) for r in s]), np.array([float(r["celdas"]) for r in s]), \
        np.array([float(r["error_rel"]) for r in s])
grupos = [("Convergen (cambio N20→N40 < 2 %)", [("p0_Pa", "p₀ estancamiento"), ("F_loc2mm_Nm", "F/b local"),
                                                 ("h_x2mm_um", "espesor película x=2 mm"), ("tau_x2mm", "τ_w en x=2 mm")]),
          ("No convergen o lentas", [("tau_max_Pa", "τ_w máximo"), ("dtaudx_VOF", "dτ_w/dx junto al eje"),
                                     ("v_frente_m_s", "velocidad del frente"), ("tau_x1mm", "τ_w en x=1 mm")])]
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.8), sharey=True)
filas = []
for a_, (tit, mags) in zip(ax, grupos):
    for i, (m, lab) in enumerate(mags):
        d, cel, e = serie(m)
        e = np.maximum(e, 1e-5)
        a_.plot(cel, e, "o-", color=CAT[i], ms=5, label=lab)
        filas += [[m, int(c), dd, ee] for c, dd, ee in zip(cel, d, e)]
    a_.axhline(0.05, color=GRAY, ls="--", lw=1); a_.text(5e3, 0.055, "5 %", color=INK2, fontsize=7.5)
    a_.axvline(76960, color=GRAY, lw=1, ls=":"); a_.text(76960 * 1.08, 1.2, "malla elegida N20", color=INK2, fontsize=7.5)
    a_.set_xscale("log"); a_.set_yscale("log"); a_.set_xlim(3e3, 2e5); a_.set_ylim(3e-4, 2.5)
    a_.legend(loc="lower left", fontsize=7.5)
    a_.set_xlabel("celdas (2D, medio dominio)"); a_.set_title(tit, fontsize=9, loc="left", color=INK)
ax[0].set_ylabel("error relativo |φᵢ − φ_N40| / |φ_N40|")
fig.suptitle("VOF-FIG-01 · Etapa 1: error relativo frente a la malla fina N40 (N = 5, 10, 20; Δ = e₀/N)", x=0.01, ha="left", fontsize=10)
fig.tight_layout(rect=(0, 0.04, 1, 0.94)); pie(fig, "Ventana 0,3-0,5 ms.")
guardar(fig, "VOF-FIG-01_E1_error_malla", filas, ["magnitud", "celdas", "delta_um", "error_rel"])

# ------------------------------------------------------------------ VOF-FIG-02 costo
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.6))
cel = np.array([f_(c, "celdas") for c in BASEC]); ch = np.array([f_(c, "nucleo_h_por_ms") for c in BASEC])
ax[0].plot(cel, ch, "o-", color=SEQ[20])
for n, x, y in zip(Ns, cel, ch):
    ax[0].text(x * 1.1, y, f"N{n}", fontsize=8, color=INK, va="top")
ax[0].set_xscale("log"); ax[0].set_yscale("log"); ax[0].set_xlabel("celdas"); ax[0].set_ylabel("núcleo·h por ms simulado")
ax[0].set_title("Costo medido (incluye la contención por corridas simultáneas)", fontsize=9, loc="left")
filas = [[c, int(x), y] for c, x, y in zip(BASEC, cel, ch)]
for i, (m, lab) in enumerate((("tau_max_Pa", "τ_w máximo"), ("h_x2mm_um", "espesor x=2 mm"), ("v_frente_m_s", "frente"))):
    d, cc, e = serie(m)
    ax[1].plot(ch[:3], np.maximum(e, 1e-5), "o-", color=CAT[i])
    ax[1].text(ch[2] * 1.15, max(e[-1], 1e-5), lab, fontsize=7.5, color=INK, va="center")
ax[1].set_xscale("log"); ax[1].set_yscale("log"); ax[1].set_xlabel("núcleo·h por ms simulado"); ax[1].set_ylabel("error relativo frente a N40")
ax[1].set_title("Error frente a costo: el codo está en N20", fontsize=9, loc="left")
ax[1].set_xlim(right=ch[2] * 6)
fig.suptitle("VOF-FIG-02 · Etapa 1: costo frente a celdas y error frente a costo", x=0.01, ha="left", fontsize=10)
fig.tight_layout(rect=(0, 0.04, 1, 0.94)); pie(fig, "N40: 2,7 h de pared con 4 rangos hasta 0,5 ms.")
guardar(fig, "VOF-FIG-02_E1_costo", filas, ["caso", "celdas", "nucleo_h_por_ms"])

# ------------------------------------------------------------------ VOF-FIG-03 Courant
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.7))
dx = np.logspace(-6, -4, 50)
for co, ls in ((0.25, ":"), (0.5, "--"), (1, "-."), (2, "-")):
    ax[0].plot(dx * 1e6, co * dx / g.V0, color=GRAY, ls=ls, lw=1)
    ax[0].text(100, co * 1e-4 / g.V0, f"Co = {co:g}", fontsize=7.5, color=INK2, va="bottom", ha="right")
filas = []
for c in M:
    d = f_(c, "delta_um") * 1e-6; dt = f_(c, "dt_medio_ventana")
    col = SEQ.get(int(M[c]["N"]), CAT[0]) if M[c]["modelo"] == "laminar" else CAT[1]
    ax[0].plot(d * 1e6, dt, "o", color=col, ms=6 if "Co0.5" in c else 4)
    filas.append([c, d, dt, g.V0 * dt / d, f_(c, "Co_max_ventana")])
ax[0].set_xscale("log"); ax[0].set_yscale("log"); ax[0].set_xlabel("Δ = e₀/N (µm)"); ax[0].set_ylabel("Δt medio en 0,3-0,5 ms (s)")
ax[0].set_title("Δt frente a Δx: Co con U₀ = 0,31-0,41 en N5-N40 (paso adaptable)", fontsize=9, loc="left")
ax[0].text(1.1, 4e-6, "azules: N5-N40 (oscuro = fino); puntos pequeños: barrido N20;\nnaranja: k-ω SST", fontsize=7, color=INK2)
cos = [0.25, 0.5, 1, 2]; cs = ["N20_Co0.25_lam", "N20_Co0.5_lam", "N20_Co1_lam", "N20_Co2_lam"]
for i, (k, lab) in enumerate((("p0_Pa", "p₀"), ("tau_x2mm", "τ_w x=2 mm"), ("h_x2mm_um", "espesor x=2 mm"),
                              ("v_frente_m_s", "velocidad del frente"))):
    v = np.array([f_(c, k) for c in cs]); v = v / v[0]
    ax[1].plot(cos, v, "o-", color=CAT[i], ms=5)
    ax[1].text(2.15, v[-1], lab, fontsize=7.5, color=INK, va="center")
ax[1].set_xscale("log", base=2); ax[1].set_xticks(cos); ax[1].set_xticklabels([str(c) for c in cos])
ax[1].set_xlim(0.2, 4.5); ax[1].set_xlabel("maxCo = maxAlphaCo (malla N20)"); ax[1].set_ylabel("valor / valor con Co = 0,25")
ax[1].set_title("Barrido de Courant: solo el frente transitorio cambia", fontsize=9, loc="left")
fig.suptitle("VOF-FIG-03 · Etapa 1: Courant (Co = U·Δt/Δx, U = 27,47 m/s)", x=0.01, ha="left", fontsize=10)
fig.tight_layout(rect=(0, 0.04, 1, 0.94)); pie(fig)
guardar(fig, "VOF-FIG-03_E1_courant", filas, ["caso", "delta_m", "dt_medio_s", "Co_con_U0", "Co_max_log"])

# ------------------------------------------------------------------ VOF-FIG-05 mojado frente a tiempo
moj = leer("E1_mojado_t.csv")
fig, ax = plt.subplots(figsize=(7.2, 3.8))
for n in Ns:
    c = f"N{n}_Co0.5_lam"
    t = np.array([float(r["t_s"]) for r in moj if r["caso"] == c]); p = np.array([float(r["pct_alpha05"]) for r in moj if r["caso"] == c])
    ax.plot(t * 1e3, p, color=SEQ[n], lw=1.8)
    ax.text(t[-1] * 1e3 + 0.01, p[-1], f"N{n}", color=INK, fontsize=8, va="center")
ax.set_xlabel("tiempo (ms); el chorro toca la pared a ≈ 0,07 ms"); ax.set_ylabel("% de la pared mojada (α ≥ 0,5)")
ax.set_ylim(0, 105); ax.set_xlim(0, 1.3)
ax.set_title("VOF-FIG-05 · Etapa 1: % de pared mojada frente al tiempo (100 % = 15 mm modelados)", fontsize=9.5, loc="left")
fig.tight_layout(rect=(0, 0.05, 1, 1)); pie(fig, "Meseta = el frente sale del dominio.")
guardar(fig, "VOF-FIG-05_E1_mojado_t", [[r["caso"], r["t_s"], r["pct_alpha05"]] for r in moj], ["caso", "t_s", "pct_alpha05"])

# ------------------------------------------------------------------ perfiles de pared
perf = leer("E1_perfiles_tau.csv")
def prof(c):
    s = [r for r in perf if r["caso"] == c]
    return [np.array([float(r[k]) for r in s]) for k in ("x_m", "p_Pa", "tau_w_Pa", "alpha_pared")]

BANDAS_TAU = [(20, "20 Pa (bajo)"), (300, "300 Pa (central)"), (1000, "1000 Pa (alto)")]
def bandas_tau(a_, xmax):
    a_.axhspan(230, 320, color="#86b6ef", alpha=0.35, lw=0)
    a_.axhspan(170, 410, color="#eda100", alpha=0.18, lw=0)
    for v, lab in BANDAS_TAU:
        a_.axhline(v, color=GRAY, ls="--", lw=0.9)
        a_.text(xmax, v * 1.06, "τ₀ " + lab, fontsize=7, color=INK2, ha="right", va="bottom")
    a_.text(xmax, 235, "LGHP 2 (analogía buena) 230-320 Pa", fontsize=6.5, color="#1c5cab", ha="right", va="bottom")
    a_.text(xmax, 172, "LGEV 2 (analogía débil) 170-410 Pa", fontsize=6.5, color="#8a5a00", ha="right", va="bottom")

# ------------------------------------------------------------------ VOF-FIG-07 tau_w
fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.0))
filas = []
for n in Ns:
    x, p, tau, al = prof(f"N{n}_Co0.5_lam")
    ax[0].plot(x * 1e3, tau, color=SEQ[n], lw=1.6, label=f"N{n}")
xb = np.linspace(0.3e-3, 8e-3, 100)
ax[0].plot(xb * 1e3, 0.332 * g.RHO_W * g.V0 ** 2 / np.sqrt(g.V0 * xb / (g.MU_W / g.RHO_W)), color=GRAY, ls="--", lw=1)
ax[0].text(5, 0.332 * g.RHO_W * g.V0 ** 2 / np.sqrt(g.V0 * 5e-3 / (g.MU_W / g.RHO_W)) * 1.1, "Blasius 0,332ρU²/√Re_x (referencia)", fontsize=7, color=INK2)
x40, _, t40, _ = prof("N40_Co0.5_lam")
xs_ = np.linspace(0, 0.3e-3, 20)
ax[0].plot(xs_ * 1e3, float(M["N40_Co0.5_lam"]["dtaudx_Hiemenz"]) * xs_, color=CAT[1], lw=1, ls="-.")
ax[0].text(0.35, 6500, "Hiemenz (pendiente junto al eje)", fontsize=7, color=CAT[1])
ax[0].legend(loc="upper right", fontsize=7.5, ncol=4)
ax[0].set_xlim(0, 8); ax[0].set_yscale("log"); ax[0].set_ylim(10, 2e4)
bandas_tau(ax[0], 8)
ax[0].set_xlabel("x desde el eje del chorro (mm)"); ax[0].set_ylabel("τ_w (Pa)")
ax[0].set_title("Perfil de τ_w en la pared (media 0,3-0,5 ms)", fontsize=9, loc="left")
for n in (20, 40):
    x, p, tau, al = prof(f"N{n}_Co0.5_lam")
    dx_ = np.diff(np.concatenate([[0], 0.5 * (x[1:] + x[:-1]), [g.LX]]))
    m = al >= 0.5
    o = np.argsort(-tau[m]); frac = np.cumsum(dx_[m][o]) / dx_[m].sum() * 100
    ax[1].plot(frac, tau[m][o], color=SEQ[n], lw=1.8, label=f"N{n}")
    filas += [[f"N{n}", ff, tt] for ff, tt in zip(frac, tau[m][o])]
ax[1].set_yscale("log"); ax[1].set_ylim(10, 2e4); ax[1].set_xlim(0, 100)
bandas_tau(ax[1], 100); ax[1].legend(loc="upper right", fontsize=7.5)
ax[1].set_xlabel("% de la longitud mojada (α ≥ 0,5) con τ_w ≥ Y"); ax[1].set_ylabel("τ_w (Pa)")
ax[1].set_title("Curva de excedencia τ_w-área (a 0,5 ms la película cubre ≈ 11 mm)", fontsize=9, loc="left")
fig.suptitle("VOF-FIG-07 · Etapa 1: esfuerzo cortante en la pared con las bandas τ₀ de U9 (identidad de la grasa: DATO EXTERNO PENDIENTE)", x=0.01, ha="left", fontsize=9.5)
fig.tight_layout(rect=(0, 0.04, 1, 0.94)); pie(fig, "τ₀: U9_UMBRAL_ANALOGICO.md (CANDIDATO).")
guardar(fig, "VOF-FIG-07_E1_tau_area", filas, ["malla", "pct_longitud_mojada", "tau_w_Pa"])

# ------------------------------------------------------------------ VOF-FIG-06 presion-area
fig, ax = plt.subplots(figsize=(7.4, 4.0))
filas = []
for n in (5, 10, 20, 40):
    x, p, tau, al = prof(f"N{n}_Co0.5_lam")
    dx_ = np.diff(np.concatenate([[0], 0.5 * (x[1:] + x[:-1]), [g.LX]]))
    m = al >= 0.5
    o = np.argsort(-p[m]); frac = np.cumsum(dx_[m][o]) / dx_[m].sum() * 100
    pp = np.maximum(p[m][o], 1.0)
    ax.plot(frac, pp / 1e3, color=SEQ[n], lw=1.6)
    filas += [[f"N{n}", ff, v] for ff, v in zip(frac, pp)]
ax.text(1.2, 200, "N5-N40: picos de 365-371 kPa\nen los primeros 0,1-0,2 mm", fontsize=7.5, color=INK)
for v in (10, 50, 100):
    ax.axhline(v, color=GRAY, ls="--", lw=0.9); ax.text(99, v * 1.07, f"σ_c = {v} kPa", fontsize=7, color=INK2, ha="right")
ax.axhline(P0_TEO / 1e3, color=CAT[1], lw=1, ls="-."); ax.text(99, P0_TEO / 1e3 * 1.07, "½ρv² = 370,6 kPa", fontsize=7, color=CAT[1], ha="right")
ax.set_yscale("log"); ax.set_ylim(0.1, 800); ax.set_xlim(0, 100)
ax.set_xlabel("% de la longitud mojada (α ≥ 0,5) con p ≥ Y"); ax.set_ylabel("presión en la pared (kPa)")
ax.set_title("VOF-FIG-06 · Etapa 1: curva de excedencia presión-área (σ_c de U4 [TRANSFERENCIA])", fontsize=9.5, loc="left")
fig.tight_layout(rect=(0, 0.05, 1, 1)); pie(fig, "Media 0,3-0,5 ms.")
guardar(fig, "VOF-FIG-06_E1_presion_area", filas, ["malla", "pct_longitud_mojada", "p_Pa"])

# ------------------------------------------------------------------ VOF-FIG-10 instantaneas de alpha
fig, ax = plt.subplots(2, 3, figsize=(10.5, 4.6), sharex="col")
for i, n in enumerate((20, 40)):
    for j, t in enumerate(("0.0001", "0.0003", "0.0005")):
        f = f"{BASE}/logs/e1/N{n}_Co0.5_lam/corte/{t}/alpha.water_plano.raw"
        a_ = ax[i, j]
        if os.path.exists(f):
            d = np.loadtxt(f, comments="#")
            s = (d[:, 0] < 12e-3) & (d[:, 1] < 1.5e-3)
            a_.tricontourf(d[s, 0] * 1e3, d[s, 1] * 1e3, d[s, 3], levels=[0, 0.05, 0.5, 0.95, 1.0001],
                           colors=[SURF, "#cde2fb", "#3987e5", "#0d366b"])
        a_.set_ylim(0, 1.5); a_.set_xlim(0, 12); a_.grid(False)
        a_.set_title(f"N{n}, t = {float(t) * 1e3:.1f} ms", fontsize=8.5, loc="left")
        if i == 1: a_.set_xlabel("x (mm)")
        if j == 0: a_.set_ylabel("y (mm)")
fig.suptitle("VOF-FIG-10 · Etapa 1: fracción de agua α (0 aire · 0,05 · 0,5 · 0,95 · 1 agua). Apoyo cualitativo, no es prueba", x=0.01, ha="left", fontsize=9.5)
fig.tight_layout(rect=(0, 0.04, 1, 0.94)); pie(fig, "Vista de 0-12 mm × 0-1,5 mm; el chorro entra por arriba en x < 0,15 mm.")
guardar(fig, "VOF-FIG-10_E1_alpha")
