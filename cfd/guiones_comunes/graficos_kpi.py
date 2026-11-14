#!/usr/bin/env python3
"""Gráficos de KPIs K1-K6 (Caso Base F7, puente F5, verificación F8) para la tesis.

Lee SOLO los CSV de 06_RESULTADOS (salida de post_kpi.py) y, para los mapas de huella,
los archivos de muestreo DPM de Fluent (D:/CFD02_run/F7/*/od.dpm y sup.dpm).
No recalcula ningún KPI: los mapas de huella son una vista complementaria y su caudal
se contrasta con el de post_kpi.py (se imprime el cotejo).

Convención: los CSV "_A_" son del ramal A. Totales A+B = 2 × ramal A para D y J (supuesto S9);
CV, zona seca, η y p_huella no cambian.

Uso: python graficos_kpi.py --salida <carpeta>
"""
import argparse, csv, math, os, re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

P = argparse.ArgumentParser()
P.add_argument("--salida", required=True)
P.add_argument("--res", default=os.path.join(os.path.dirname(__file__), "..", "06_RESULTADOS"))
P.add_argument("--sin-huella", action="store_true")
a = P.parse_args()
OUT = a.salida; os.makedirs(OUT, exist_ok=True)
R = a.res

# ---- estilo (paleta de referencia dataviz, modo claro) ----
SURF, INK, INK2, MUTED, GRID, BASE = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
C_OD, C_RB, C_SUP, C_AMB = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": BASE, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10.5,
    "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlecolor": INK, "legend.frameon": False,
    "text.color": INK,
})
T_VUELTA = 35.294

def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f))
def col(filas, k): return np.array([float(r[k]) for r in filas])
def fila(ruta): return leer(ruta)[0]
def guardar(fig, nombre):
    fig.savefig(os.path.join(OUT, nombre), dpi=200, bbox_inches="tight"); plt.close(fig); print("->", nombre)
def nota(fig, texto):
    fig.text(0.01, -0.02, texto, fontsize=8.5, color=MUTED, ha="left", va="top", wrap=True)

eod = leer(f"{R}/F7/F7_EOD_A_v2_dosis_por_banda.csv")
eod2 = leer(f"{R}/F7/sens_banda/F7_EOD_A_v2_banda2mm_dosis_por_banda.csv")
esup = leer(f"{R}/F7/F7_ESUP_A_v2_dosis_por_banda.csv")
ind_eod = fila(f"{R}/F7/F7_EOD_A_v2_indicadores.csv")
ind_esup = fila(f"{R}/F7/F7_ESUP_A_v2_indicadores.csv")
ind_f5 = fila(f"{R}/F5/F5_base_v1_indicadores.csv")
boq_eod = leer(f"{R}/F7/F7_EOD_A_v2_por_boquilla.csv")
boq_esup = leer(f"{R}/F7/F7_ESUP_A_v2_por_boquilla.csv")

# ================= G01: perfil D(z) en el OD (K2, K3, K4) =================
z = col(eod, "s_centro_mm"); D = 2 * col(eod, "D_kg_m2_vuelta")
z2 = col(eod2, "s_centro_mm"); D2 = 2 * col(eod2, "D_kg_m2_vuelta")
fig, ax = plt.subplots(figsize=(7.2, 7.6))
ax.barh(z, D, height=8.6, color=C_OD, alpha=0.85, label="Bandas de 10 mm (KPI oficial)")
ax.plot(D2, z2, color=INK, lw=1.0, label="Bandas de 2 mm (KPI complementario)")
seco2 = z2[D2 <= 1e-9]
if len(seco2):
    ax.axhspan(seco2.min() - 1, seco2.max() + 1, color=C_RB, alpha=0.25, lw=0)
    ax.annotate(f"Franja sin impacto directo\nZ ≈ {seco2.min()-1:.0f}–{seco2.max()+1:.0f} mm\n(entre LAT_5 y LAT_1)",
                xy=(0.5, (seco2.min() + seco2.max()) / 2), xytext=(27, 960), fontsize=9, color=INK,
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
Dm = 2 * float(ind_eod["K2_D_media_kg_m2_vuelta"])
ax.axvline(Dm, color=INK2, ls="--", lw=1)
ax.text(Dm + 0.5, 1406, f"D̄ = {Dm:.2f}", color=INK2, fontsize=9, va="bottom")
for i, b in enumerate(boq_eod):  # huellas por boquilla, en el margen derecho (alternadas)
    x0 = 46 if i % 2 == 0 else 49.5
    ax.plot([x0, x0], [float(b["s_min_mm"]), float(b["s_max_mm"])], color=MUTED, lw=3, solid_capstyle="butt")
    ax.text(x0 + 0.6, (float(b["s_min_mm"]) + float(b["s_max_mm"])) / 2, b["boquilla"].upper(), fontsize=7.5, va="center", color=INK2, rotation=90)
ax.set_xlim(0, 52); ax.set_ylim(885, 1418)
ax.set_xlabel("Dosis por vuelta D  [kg·m⁻²·vuelta⁻¹]  (ramal A + B)")
ax.set_ylabel("Altura Z sobre el OD  [mm]")
ax.set_title("K2–K4 · Dosis por vuelta a lo largo del OD (Caso Base E-OD)", loc="left")
ax.legend(loc="lower right", fontsize=9)
nota(fig, f"CV (10 mm) = {float(ind_eod['K3_CV']):.3f} · zona seca: 0 % con 10 mm, 1,55 % con 2 mm · "
          "barras grises: huella de cada boquilla (ramal A). Fuente: 06_RESULTADOS/F7 (post_kpi.py).")
guardar(fig, "G01_EOD_dosis_por_altura.png")

# ================= G02: perfil D(r) en la cara superior =================
r = col(esup, "s_centro_mm"); Ds = 2 * col(esup, "D_kg_m2_vuelta")
fig, ax = plt.subplots(figsize=(7.6, 4.6))
ax.bar(r, Ds, width=8.6, color=C_SUP, alpha=0.9, label="Bandas de 10 mm")
Dms = 2 * float(ind_esup["K2_D_media_kg_m2_vuelta"])
ax.axhline(Dms, color=INK2, ls="--", lw=1); ax.text(712, Dms + 0.6, f"D̄ = {Dms:.2f}", color=INK2, fontsize=9, ha="right")
for i, b in enumerate(boq_esup):
    y0 = 44 + 2.2 * i
    ax.plot([float(b["s_min_mm"]), float(b["s_max_mm"])], [y0, y0], color=MUTED, lw=3, solid_capstyle="butt")
    ax.text(float(b["s_max_mm"]) + 3, y0, b["boquilla"].upper(), fontsize=8, va="center", color=INK2)
ax.set_ylim(0, 50); ax.set_xlim(455, 735)
ax.set_xlabel("Radio r sobre la cara superior  [mm]"); ax.set_ylabel("D  [kg·m⁻²·vuelta⁻¹]  (ramal A + B)")
ax.set_title("K2–K4 · Dosis por vuelta en la cara superior (Caso Base E-SUP)", loc="left")
nota(fig, f"CV = {float(ind_esup['K3_CV']):.3f} · zona seca 0 % · D_min = {2*float(ind_esup['K2_D_min']):.2f}. Fuente: 06_RESULTADOS/F7.")
guardar(fig, "G02_ESUP_dosis_por_radio.png")

# ================= G03: curva de cobertura C(Dmin) (K4) =================
fig, ax = plt.subplots(figsize=(7.6, 4.8))
for ruta, fac, c, lab in [(f"{R}/F7/F7_EOD_A_v2_cobertura.csv", 2, C_OD, "OD exterior (E-OD)"),
                          (f"{R}/F7/F7_ESUP_A_v2_cobertura.csv", 2, C_SUP, "Cara superior (E-SUP)"),
                          (f"{R}/F5/F5_base_v1_cobertura.csv", 1, C_RB, "Agujero interior (Fluent F5)")]:
    cc = leer(ruta)
    ax.plot(fac * col(cc, "D_min_kg_m2_vuelta"), col(cc, "cobertura_pct"), color=c, lw=2, label=lab)
ax.set_xscale("log"); ax.set_ylim(0, 102); ax.set_xlim(0.02, 100)
ax.set_xlabel("Umbral de dosis D_min  [kg·m⁻²·vuelta⁻¹]  (escala log)")
ax.set_ylabel("Área con D ≥ D_min  [%]")
ax.set_title("K4 · Curva de cobertura: qué fracción del área supera cada dosis", loc="left")
ax.legend(loc="lower left")
nota(fig, "Sin umbral de dosis con respaldo para grasa [SIN FUENTE]: la curva se usa para comparar casos, no como pasa/no pasa. "
          "Exterior: total ramal A + B.")
guardar(fig, "G03_cobertura_vs_umbral.png")

# ================= G04: resumen de KPIs (small multiples, un eje cada uno) =================
casos = ["Interior\nOpenFOAM (rama B)", "Interior\nFluent (F5)", "OD\n(E-OD)", "Cara sup.\n(E-SUP)"]
colores = [C_RB, C_RB, C_OD, C_SUP]
vals = {
    "K2 · D̄  [kg·m⁻²·vuelta⁻¹]": [18.81, float(ind_f5["K2_D_media_kg_m2_vuelta"]), Dm, Dms],
    "K3 · CV  [–] (menor = más uniforme)": [0.340, float(ind_f5["K3_CV"]), float(ind_eod["K3_CV"]), float(ind_esup["K3_CV"])],
    "K5 · η  [%] (llega a la pared objetivo)": [87.2, float(ind_f5["K5_eta_pct"]), float(ind_eod["K5_eta_pct"]), float(ind_esup["K5_eta_pct"])],
    "K6 · p_huella  [kPa]": [float("nan"), float(ind_f5["K6_p_huella_Pa"]) / 1e3, float(ind_eod["K6_p_huella_Pa"]) / 1e3, float(ind_esup["K6_p_huella_Pa"]) / 1e3],
}
fig, axs = plt.subplots(2, 2, figsize=(10, 7))
for ax, (tit, v) in zip(axs.flat, vals.items()):
    x = np.arange(len(casos))
    bars = ax.bar(x, [0 if math.isnan(t) else t for t in v], color=colores, width=0.62)
    for i, t in enumerate(v):
        ax.text(i, (0 if math.isnan(t) else t), "n/d" if math.isnan(t) else (f"{t:.3f}" if t < 1 else f"{t:.2f}" if t < 10 else f"{t:.1f}"),
                ha="center", va="bottom", fontsize=9, color=INK)
    ax.set_xticks(x, casos, fontsize=8.5); ax.set_title(tit, loc="left", fontsize=10.5)
    ax.set_ylim(0, max(t for t in v if not math.isnan(t)) * 1.18); ax.grid(axis="x", visible=False)
fig.suptitle("Resumen de KPIs del Caso Base frente al caso interior (referencia)", x=0.01, ha="left", fontweight="bold")
fig.legend(handles=[Patch(color=C_RB, label="Agujero interior (6 boquillas de lanza)"), Patch(color=C_OD, label="OD exterior (10 laterales)"),
                    Patch(color=C_SUP, label="Cara superior (4 superiores)")], loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.03))
fig.tight_layout(rect=(0, 0.04, 1, 0.97))
nota(fig, "K1 (acceso por rayos) = 100 % en las tres superficies. Zona seca con bandas de 10 mm = 0 % en todas. "
          "p_huella de la rama B no calculada (n/d). Exterior: ramal A + B (S9).")
guardar(fig, "G04_resumen_KPIs.png")

# ================= G05: impulso J(z) en el OD (K6) =================
J = 2 * col(eod, "J_N_s_m2_vuelta")
fig, ax = plt.subplots(figsize=(7.2, 6.0))
ax.barh(z, J, height=8.6, color=C_OD, alpha=0.85)
Jm = 2 * float(ind_eod["K6_J_media_N_s_m2_vuelta"])
ax.axvline(Jm, color=INK2, ls="--", lw=1); ax.text(Jm + 10, 1398, f"J̄ = {Jm:.0f}", color=INK2, fontsize=9, va="top")
ax.set_ylim(885, 1410); ax.set_xlabel("Impulso de impacto J  [N·s·m⁻²·vuelta⁻¹]  (ramal A + B)")
ax.set_ylabel("Altura Z sobre el OD  [mm]")
ax.set_title("K6 · Impulso normal de las gotas a lo largo del OD", loc="left")
nota(fig, f"p_huella = {float(ind_eod['K6_p_huella_Pa']):.0f} Pa · v_n medio = {float(ind_eod['K6_vn_medio_m_s']):.1f} m/s. "
          "Mide la intensidad mecánica que llega, no la remoción de grasa [SIN FUENTE para grasa]. J̄ con GCI 21 % (F8).")
guardar(fig, "G05_EOD_impulso_por_altura.png")

# ================= G06: verificación F8 (malla, Δt, dominio) =================
cv = leer(f"{R}/F8/F8_convergencia.csv")
base = [r for r in cv if r["caso"] == "base"][0]
kpis = [("K2_D_media_kg_m2_vuelta", "K2 D̄"), ("K3_CV", "K3 CV"), ("K5_eta_pct", "K5 η"),
        ("K6_J_media_N_s_m2_vuelta", "K6 J̄"), ("K6_p_huella_Pa", "K6 p_huella")]
variantes = [("gruesa", "Malla gruesa (173 k)", "#86b6ef"), ("fina", "Malla fina (689 k)", "#184f95"),
             ("dt25", "Δt / 2", C_AMB), ("dominio", "Dominio ampliado", C_SUP)]
fig, ax = plt.subplots(figsize=(8.6, 4.6))
w = 0.19; x = np.arange(len(kpis))
for j, (k, lab, c) in enumerate(variantes):
    rr = [r for r in cv if r["caso"] == k][0]
    d = [100 * (float(rr[kk]) / float(base[kk]) - 1) for kk, _ in kpis]
    ax.bar(x + (j - 1.5) * w, d, width=w * 0.9, color=c, label=lab)
ax.axhspan(-5, 5, color="#f0efec", lw=0, zorder=0)
ax.axhline(0, color=BASE, lw=1)
ax.set_xticks(x, [l for _, l in kpis]); ax.set_ylim(-6, 6)
ax.set_ylabel("Cambio respecto a la malla base  [%]")
ax.set_title("Verificación (F8, E-OD): sensibilidad de los KPIs", loc="left")
ax.legend(ncol=2, fontsize=9, loc="lower left")
nota(fig, "Franja gris: objetivo de trabajo ±5 % entre las dos mallas finas (CLAUDE.md, checklist). Todos los cambios ≤ 1,4 % (mayor: p_huella con malla gruesa, −1,3 %). "
          "Verificado ≠ validado. Fuente: 06_RESULTADOS/F8/F8_convergencia.csv.")
guardar(fig, "G06_verificacion_F8.png")

# ================= G07: caso puente F5 (Fluent vs OpenFOAM) =================
pf = leer(f"{R}/F5/F5_perfil_Dz.csv")
zz = col(pf, "z_mm")
fig, ax = plt.subplots(figsize=(7.2, 6.6))
ax.plot(col(pf, "D_rama_B"), zz, color=C_RB, lw=2, marker="o", ms=4, label="OpenFOAM (rama B, S2_seis)")
ax.plot(col(pf, "D_Fluent"), zz, color=C_OD, lw=2, marker="s", ms=4, label="Fluent 2026 R1 (F5)")
ax.set_xlabel("D  [kg·m⁻²·vuelta⁻¹]"); ax.set_ylabel("Altura Z en el agujero  [mm]")
ax.set_title("Caso puente · mismo caso interior en dos solvers", loc="left")
ax.legend(loc="lower right")
nota(fig, "D̄: 18,81 vs 18,76 (−0,27 %) · CV: 0,340 vs 0,336 · zona seca 0 % en ambos · balance +0,06 %. "
          "Verificación cruzada entre solvers, no validación experimental. Fuente: 06_RESULTADOS/F5.")
guardar(fig, "G07_puente_OpenFOAM_vs_Fluent.png")

# ================= G08: reparto por boquilla (K5) =================
fig, axs = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [5, 2]})
for ax, boq, c, iny, tit in [(axs[0], boq_eod, C_OD, 0.149244, "OD (ramal A)"), (axs[1], boq_esup, C_SUP, 0.149244, "Cara sup. (ramal A)")]:
    nom = [b["boquilla"].upper() for b in boq]; eta = [100 * float(b["mdot_kg_s"]) / iny for b in boq]
    ax.bar(nom, eta, color=c, width=0.6)
    for i, e in enumerate(eta): ax.text(i, e + 1, f"{e:.1f} %", ha="center", fontsize=9)
    ax.set_ylim(0, 110); ax.set_title(tit, loc="left", fontsize=10.5); ax.grid(axis="x", visible=False)
axs[0].set_ylabel("Caudal que llega a la pared objetivo  [%]")
fig.suptitle("K5 · Eficiencia de transferencia por boquilla", x=0.01, ha="left", fontweight="bold")
fig.tight_layout()
nota(fig, "LAT_5: 10,7 % de su caudal pasa bajo Z 890 mm (fuera del OD). SUP_1: ~4 % cae hacia el agujero. "
          "Con trap, η es cota superior (sin rebote ni salpicadura).")
guardar(fig, "G08_eficiencia_por_boquilla.png")

# ================= G09-G10: mapas de huella desde el muestreo DPM =================
def leer_dpm(ruta, t0=0.020, t1=0.040):
    num = re.compile(r"^\(\(\s*(.*?)\)\s*(\S+)\)")
    xs = []
    with open(ruta, encoding="utf-8", errors="ignore") as f:
        for ln in f:
            if not ln.startswith("(("): continue
            m = num.match(ln)
            if not m: continue
            v = m.group(1).split()
            t = float(v[12])
            if t0 <= t < t1:
                xs.append((float(v[0]), float(v[1]), float(v[2]), float(v[3]), float(v[4]), float(v[5]), float(v[8])))
    return np.array(xs)

if not a.sin_huella:
    dur = 0.020
    # OD: mapa (arco s = R·θ, z) del flujo de masa instantáneo, ramal A, rotor congelado
    A = leer_dpm("D:/CFD02_run/F7/F7_EOD_tr_v2/od.dpm")
    mdot = A[:, 6].sum() / dur
    print(f"cotejo OD: Σmasa/Δt = {mdot:.6f} kg/s  vs post_kpi {float(ind_eod['mdot_depositado_kg_s']):.6f}")
    Rr = 0.710; th = np.degrees(np.arctan2(A[:, 1], A[:, 0])); s = np.radians(th) * Rr * 1000
    zb = np.arange(890, 1405 + 2, 2.0); sb = np.arange(-8, 10 + 0.5, 0.5)
    H, _, _ = np.histogram2d(A[:, 2] * 1000, s, bins=[zb, sb], weights=A[:, 6] / dur)
    flux = H / ((zb[1] - zb[0]) * (sb[1] - sb[0]) * 1e-6)  # kg/(m2 s)
    fig, ax = plt.subplots(figsize=(6.4, 8.0))
    im = ax.pcolormesh(sb, zb, np.ma.masked_less_equal(flux, 0), cmap="Blues", shading="flat",
                       vmin=0, vmax=np.percentile(flux[flux > 0], 99))
    ax.set_facecolor("#f0efec")
    ax.set_xlabel("Arco sobre el OD  s = R·θ  [mm]"); ax.set_ylabel("Z  [mm]")
    ax.set_title("Huella instantánea de las 5 laterales\nsobre el OD (rotor congelado)", loc="left")
    cb = fig.colorbar(im, ax=ax, shrink=0.8); cb.set_label("Flujo de masa depositado  [kg·m⁻²·s⁻¹]")
    ax.grid(False)
    nota(fig, "Celdas de 0,5 mm (arco) × 2 mm (Z); gris = sin impacto. Las 3 líneas verticales son los 3 rayos de espesor de la tabla de inyección (150 × 3, espesor 2° SUPUESTO), no un efecto físico. Ramal A. Al girar el rotor, cada franja de Z barre toda la "
              "circunferencia: la dosis por vuelta (G01) integra esta huella en θ. Fuente: od.dpm (F7_EOD_tr_v2), ventana 20–40 ms.")
    guardar(fig, "G09_EOD_huella_instantanea.png")
    del A
    B = leer_dpm("D:/CFD02_run/F7/F7_ESUP_tr_v2/sup.dpm")
    print(f"cotejo SUP: Σmasa/Δt = {B[:, 6].sum()/dur:.6f} kg/s  vs post_kpi {float(ind_esup['mdot_depositado_kg_s']):.6f}")
    xb = np.arange(440, 720 + 2, 2.0); yb = np.arange(-10, 10 + 0.5, 0.5)
    H, _, _ = np.histogram2d(B[:, 0] * 1000, B[:, 1] * 1000, bins=[xb, yb], weights=B[:, 6] / dur)
    flux = H / ((xb[1] - xb[0]) * (yb[1] - yb[0]) * 1e-6)
    fig, ax = plt.subplots(figsize=(8.4, 3.6))
    im = ax.pcolormesh(xb, yb, np.ma.masked_less_equal(flux, 0).T, cmap="Greens", shading="flat",
                       vmin=0, vmax=np.percentile(flux[flux > 0], 99))
    ax.axvline(458.58, color=INK2, lw=0.8, ls=":"); ax.axvline(710, color=INK2, lw=0.8, ls=":")
    ax.set_facecolor("#f0efec"); ax.grid(False)
    ax.set_xlabel("Radio  x ≈ r  [mm]"); ax.set_ylabel("y  [mm]")
    ax.set_title("Huella instantánea de SUP_1 y SUP_2 sobre la cara superior", loc="left")
    cb = fig.colorbar(im, ax=ax); cb.set_label("[kg·m⁻²·s⁻¹]")
    nota(fig, "Líneas punteadas: borde interior (r 458,6 mm) y exterior (r 710 mm) del aro. Ramal A. Fuente: sup.dpm (F7_ESUP_tr_v2).")
    guardar(fig, "G10_ESUP_huella_instantanea.png")
