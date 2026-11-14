#!/usr/bin/env python3
"""Graficos de KPIs de CFD03 (22 boquillas) para la tesis. Estilo y paleta de CFD02 (graficos_kpi.py; paleta de
referencia dataviz, slots categoricos validados en orden fijo). Los KPIs NO se recalculan aqui: los perfiles por
boquilla se reconstruyen de los impactos con la misma aritmetica de post_kpi.py y se cotejan con su total.

Uso: python graficos_cfd03.py <figura> [opciones]   (ver funciones fig_*)
"""
import argparse
import csv
import math
import os

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURF, INK, INK2, MUTED, GRID, BASE = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
SLOT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": BASE, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10.5,
    "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlecolor": INK, "legend.frameon": False,
    "text.color": INK,
})
T_VUELTA = 2 * math.pi / 0.1780235837034216
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(RAIZ, "07_FIGURAS", "graficos_KPI")
NOMBRE = {"lat_1_a": "LAT_1", "lat_2_a": "LAT_2", "lat_3_a": "LAT_3", "lat_4_a": "LAT_4", "lat_5_a": "LAT_5",
          "inf_ext_a": "INF_EXT"}


def guardar(fig, nombre):
    os.makedirs(FIG, exist_ok=True)
    fig.savefig(os.path.join(FIG, nombre), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("->", nombre)


def nota(fig, texto):
    fig.text(0.01, -0.02, texto, fontsize=8.5, color=MUTED, ha="left", va="top", wrap=True)


def impactos(path, t0, t1):
    R = list(csv.DictReader(open(path)))
    t = np.array([float(r["t"]) for r in R]); s = (t >= t0) & (t < t1)
    return (np.array([float(r["z"]) for r in R])[s], np.array([float(r["masa"]) for r in R])[s] / (t1 - t0),
            np.array([r["boquilla"] for r in R])[s])


def dosis_banda(z, m, db, lo=0.890, hi=1.405, R=0.710):
    nb = int(math.ceil((hi - lo) / db - 1e-9))
    e = np.minimum(lo + db * np.arange(nb + 1), hi)
    A = 2 * math.pi * R * np.diff(e)
    d = (z >= lo) & (z <= hi)
    ib = np.clip(np.searchsorted(e, z[d], side="right") - 1, 0, nb - 1)
    return e, np.bincount(ib, weights=m[d], minlength=nb) * T_VUELTA / A


def fig_od_por_boquilla(caso_dir, t0, t1, nombre, titulo, franja=(1.0308, 1.0399), cotejo=None):
    z, m, b = impactos(os.path.join(caso_dir, "od.csv"), t0, t1)
    orden = [k for k in NOMBRE if k in set(b)]
    fig, (ax, az) = plt.subplots(1, 2, figsize=(11.5, 6.2), gridspec_kw=dict(width_ratios=[1.35, 1], wspace=0.28))
    for axx, db, lim in ((ax, 0.010, (0.890, 1.405)), (az, 0.002, (1.000, 1.070))):
        izq = None
        tot = None
        for i, k in enumerate(orden):
            e, D = dosis_banda(z[b == k], m[b == k], db)
            c = 0.5 * (e[:-1] + e[1:]) * 1e3
            izq = np.zeros_like(D) if izq is None else izq
            axx.barh(c, D, height=db * 1e3 * 0.86, left=izq, color=SLOT[i], edgecolor=SURF, linewidth=0.6,
                     label=NOMBRE[k])
            izq = izq + D
            tot = D if tot is None else tot + D
        axx.axhspan(franja[0] * 1e3, franja[1] * 1e3, color=MUTED, alpha=0.18, lw=0)
        axx.set_ylim(lim[0] * 1e3, lim[1] * 1e3)
        axx.set_xlabel("Dosis por vuelta D (kg·m⁻²·vuelta⁻¹), ramal A")
        if db == 0.010:
            axx.set_ylabel("Altura Z (mm, sistema global R05)")
            axx.set_title("Bandas de 10 mm (definición oficial)", loc="left")
            if cotejo:
                ref = np.array([float(r["D_kg_m2_vuelta"]) for r in csv.DictReader(open(cotejo))])
                print("  cotejo con post_kpi (10 mm): max |dif| = %.2e" % np.abs(ref - tot).max())
        else:
            axx.set_title("Zoom de la franja, bandas de 2 mm", loc="left")
            secas = c[(tot <= 1e-9) & (c > lim[0] * 1e3) & (c < lim[1] * 1e3)]
            if len(secas):
                axx.text(axx.get_xlim()[1] * 0.97, secas.mean(), "sin impacto directo\n%.0f-%.0f mm" %
                         (secas.min() - 1, secas.max() + 1), ha="right", va="center", fontsize=9, color=INK2)
    ax.legend(ncol=6, loc="lower left", bbox_to_anchor=(0.0, 1.07), fontsize=9, handlelength=1.2, columnspacing=1.0)
    fig.suptitle(titulo, x=0.01, y=1.04, ha="left", fontsize=12.5, fontweight="bold")
    nota(fig, "Barras apiladas por boquilla (misma aritmética que post_kpi.py; ventana %.0f-%.0f ms). Franja gris: entre el "
              "borde superior de la huella de INF_EXT y el inferior de LAT_1 (CFD). Pared trap: no incluye escorrentía." %
         (t0 * 1e3, t1 * 1e3))
    guardar(fig, nombre)


def dosis_anillo(r, m, db, lo=0.450, hi=0.710):
    nb = int(math.ceil((hi - lo) / db - 1e-9))
    e = np.minimum(lo + db * np.arange(nb + 1), hi)
    A = math.pi * (e[1:] ** 2 - e[:-1] ** 2)
    d = (r >= lo) & (r <= hi)
    ib = np.clip(np.searchsorted(e, r[d], side="right") - 1, 0, nb - 1)
    return e, np.bincount(ib, weights=m[d], minlength=nb) * T_VUELTA / A


def fig_cara_inf_por_aporte(aportes, nombre, titulo, t0=0.025, t1=0.050):
    """aportes: lista de (csv de impactos en cara_inf, boquilla, factor, etiqueta). Barras apiladas por r (10 mm) y
    linea del total con bandas de 2 mm. Sombreado: zona de contacto de los PAD (r 638-688 mm, solo en 3 x 24 grados)."""
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    izq = None; tot2 = None
    for i, (p, bq, fac, lab) in enumerate(aportes):
        R = list(csv.DictReader(open(p)))
        t = np.array([float(x["t"]) for x in R]); s = (t >= t0) & (t < t1) & np.array([x["boquilla"] == bq for x in R])
        r = np.hypot(np.array([float(x["x"]) for x in R])[s], np.array([float(x["y"]) for x in R])[s])
        m = np.array([float(x["masa"]) for x in R])[s] / (t1 - t0) * fac
        e, D = dosis_anillo(r, m, 0.010)
        c = 0.5 * (e[:-1] + e[1:]) * 1e3
        izq = np.zeros_like(D) if izq is None else izq
        ax.bar(c, D, width=8.6, bottom=izq, color=SLOT[i], edgecolor=SURF, linewidth=0.6, label=lab)
        izq = izq + D
        e2, D2 = dosis_anillo(r, m, 0.002)
        tot2 = D2 if tot2 is None else tot2 + D2
    c2 = 0.5 * (e2[:-1] + e2[1:]) * 1e3
    ax.plot(c2, tot2, color=INK, lw=1.0, label="Total, bandas de 2 mm")
    ax.axvspan(638, 688, color=MUTED, alpha=0.15, lw=0)
    ax.text(663, ax.get_ylim()[1] * 0.95, "PAD\n(contacto en 3 × 24°)", ha="center", va="top", fontsize=8.5, color=INK2)
    ax.set_xlim(450, 710)
    ax.set_xlabel("Radio r en la cara inferior (mm)")
    ax.set_ylabel("Dosis por vuelta D (kg·m⁻²·vuelta⁻¹)")
    ax.legend(ncol=4, loc="lower left", bbox_to_anchor=(0.0, 1.02), fontsize=9)
    fig.suptitle(titulo, x=0.01, y=1.05, ha="left", fontsize=12.5, fontweight="bold")
    nota(fig, "Sector libre (sin PAD ni topes; su efecto se aplica con las máscaras de rayos, ver mapa). Barras: bandas de 10 mm "
              "apiladas por aporte; línea: total con bandas de 2 mm. Ventana %.0f-%.0f ms; pared trap." % (t0 * 1e3, t1 * 1e3))
    guardar(fig, nombre)


def fig_mapa_polar(npz, nombre, titulo, rango=None, radial=True):
    """Mapa D(s, theta) por vuelta con obstaculos (salida _mapa10mm.npz de combinar_kpi.py). Escala secuencial de un solo
    tono (magnitud); celdas no mojables (contacto) en gris."""
    from matplotlib.colors import LinearSegmentedColormap
    Z = np.load(npz)
    D, A, e, th = Z["D"], Z["A"], Z["edges"], Z["th"]
    cmap = LinearSegmentedColormap.from_list("azul", ["#eef4fc", "#9cc3ef", "#2a78d6", "#123f78"])
    Dm = np.ma.masked_where(A <= 0, D)
    fig = plt.figure(figsize=(7.6, 7.2))
    ax = fig.add_subplot(111, projection="polar")
    T, Rr = np.meshgrid(np.radians(np.append(th - 0.25, th[-1] + 0.25)), e * 1e3)
    pc = ax.pcolormesh(T, Rr, Dm, cmap=cmap, vmin=0, vmax=rango or np.percentile(D[A > 0], 99), shading="flat")
    ax.pcolormesh(T, Rr, np.ma.masked_where(A > 0, np.ones_like(D)), cmap=LinearSegmentedColormap.from_list("g", [BASE, BASE]),
                  shading="flat")
    ax.set_ylim(0, e[-1] * 1e3); ax.set_yticks([450, 550, 650, 710]); ax.set_rorigin(0)
    ax.set_theta_zero_location("E"); ax.set_theta_direction(1)
    ax.set_xticks(np.radians([30, 90, 150, 210, 270, 330]))          # entre obstaculos: no chocan con sus etiquetas
    ax.set_rlabel_position(150); ax.tick_params(axis="y", labelsize=8, colors=MUTED)
    ax.grid(color=GRID, lw=0.5)
    for tc in (0, 120, 240):
        ax.annotate("PAD", (np.radians(tc), 740), ha="center", va="center", fontsize=8.5, color=INK2, annotation_clip=False)
    for tc in (60, 180, 300):
        ax.annotate("tope", (np.radians(tc), 760), ha="center", va="center", fontsize=8.5, color=INK2, annotation_clip=False)
    cb = fig.colorbar(pc, ax=ax, shrink=0.7, pad=0.08)
    cb.set_label("D por vuelta (kg·m⁻²·vuelta⁻¹)", color=INK2)
    fig.suptitle(titulo, x=0.01, ha="left", fontsize=12, fontweight="bold")
    nota(fig, "Marco fijo del rodamiento (θ = 0 en +X, antihorario). Dosis CFD del sector libre por boquilla × máscara de "
              "sombra por rayos de PAD, topes y vigas de R05 [INTERFAZ ISMAEL]. Gris: contacto no mojable.")
    guardar(fig, nombre)


def fig_g8_opciones(nombre="G19_G8_opciones_rediseno.png"):
    """Pequenos multiplos: un panel por KPI (cada uno con su escala), barras horizontales por variante.
    Base en gris, opciones recomendadas en azul (slot 1), alternativas en gris claro."""
    R = os.path.join(RAIZ, "06_RESULTADOS", "G8")
    od = {r["variante"]: r for r in csv.DictReader(open(os.path.join(R, "cribado_hibrido_OD_v3.csv")))}
    su = {r["variante"]: r for r in csv.DictReader(open(os.path.join(R, "cribado_hibrido_SUP_v2.csv")))}
    filas_od = [("Base R05", od["C0 base R05 (CFD v3)"], "base"), ("A: LAT_1 −4°", od["A: LAT_1 -4 grados"], "rec"),
                ("C: A + LAT_2-4 paso 88", od["B: LAT_1 -4 + paso 88 (LAT_2-4 sube)"], "alt")]
    filas_su = [("Base R05", su["S0 base R05 (CFD v2)"], "base"), ("B: SUP_2 +15 mm", su["S5: SUP_2 +15 solo"], "rec"),
                ("SUP_1 −15 / SUP_2 +15", su["S2: SUP_1 -15 / SUP_2 +15"], "alt")]
    col = {"base": MUTED, "rec": SLOT[0], "alt": BASE}
    fig, axs = plt.subplots(2, 4, figsize=(13, 5.6), gridspec_kw=dict(hspace=0.75, wspace=0.55))
    paneles_od = [("CV_10mm", "CV (10 mm) ↓"), ("Dmin_10mm", "D_min 10 mm ↑"), ("seca_2mm_pct", "Zona seca 2 mm (%) ↓"),
                  ("eta_pct", "η OD (%) ↑")]
    paneles_su = [("CV_10mm", "CV (10 mm) ↓"), ("Dmin_10mm", "D_min 10 mm ↑"), ("seca_2mm_pct", "Zona seca 2 mm (%) ↓"),
                  ("eta_pct", "η cara superior (%) ↑")]
    for fila, (filas, paneles, titulo) in enumerate(((filas_od, paneles_od, "OD (ramal A)"),
                                                      (filas_su, paneles_su, "Cara superior (ramal A)"))):
        for j, (k, lab) in enumerate(paneles):
            ax = axs[fila, j]
            vals = [float(f[k]) for _, f, _ in filas]
            ys = np.arange(len(filas))[::-1]
            ax.barh(ys, vals, height=0.6, color=[col[t] for _, _, t in filas], edgecolor=SURF)
            for y, v in zip(ys, vals):
                ax.text(v, y, " %.3g" % v, va="center", ha="left", fontsize=8.5, color=INK2)
            ax.set_yticks(ys)
            ax.set_yticklabels([n for n, _, _ in filas] if j == 0 else [], fontsize=8.5)
            ax.set_title(lab, loc="left", fontsize=9.5)
            ax.set_xlim(0, max(vals) * 1.35 if max(vals) > 0 else 1)
            ax.grid(axis="y", visible=False)
        axs[fila, 0].text(-0.9, 1.30, titulo, transform=axs[fila, 0].transAxes, fontsize=11, fontweight="bold", color=INK)
    fig.suptitle("G8: efecto de las opciones de rediseño (criba híbrida CFD + rayos)", x=0.01, y=1.10, ha="left",
                 fontsize=12.5, fontweight="bold")
    nota(fig, "Azul: opción recomendada (Caso 2 = A; Caso 3 = A + B). Ruido de corrida (par A/B con S18): CV del OD ±0,0007; "
              "CV de la cara superior ±0,006. Criba: impactos CFD del Caso Base desplazados (cotas) + rayos (ángulos); los "
              "valores definitivos salen del CFD de cada caso.")
    guardar(fig, nombre)


def fig_comparacion_casos(nombre="G18_comparacion_CasoBase_C2_C3.png"):
    """Caso Base / Caso 2 / Caso 3 (totales con obstaculos, base ramal A x 2) por superficie y KPI: pequenos multiplos.
    Color por caso (identidad, slots fijos 1-3); el valor va rotulado en cada barra."""
    R = os.path.join(RAIZ, "06_RESULTADOS", "G8", "comparacion")
    casos = [("Caso Base", "CB"), ("Caso 2", "C2"), ("Caso 3", "C3")]
    sup_lab = [("od", "OD"), ("sup", "Cara superior"), ("cara_inf", "Cara inferior")]
    kpis = [("seca_pct", "obst_2mm", "Zona seca 2 mm (%) ↓"), ("CV", "obst_10mm", "CV 10 mm ↓"),
            ("D_min", "obst_10mm", "D_min 10 mm ↑"), ("eta_pct", "obst_10mm", "η (%) ↑")]
    val = {}
    for _, c in casos:
        for s, _ in sup_lab:
            for r in csv.DictReader(open(os.path.join(R, c, "G7_%s_indicadores.csv" % s))):
                val[(c, s, r["variante"])] = r
    fig, axs = plt.subplots(len(sup_lab), len(kpis), figsize=(13, 7.2), gridspec_kw=dict(hspace=0.8, wspace=0.5))
    for i, (s, slab) in enumerate(sup_lab):
        for j, (k, var, klab) in enumerate(kpis):
            ax = axs[i, j]
            v = [float(val[(c, s, var)][k]) for _, c in casos]
            ys = np.arange(len(casos))[::-1]
            ax.barh(ys, v, height=0.62, color=SLOT[:3], edgecolor=SURF)
            for y, x in zip(ys, v):
                ax.text(x, y, " %.3g" % x, va="center", ha="left", fontsize=8.5, color=INK2)
            ax.set_yticks(ys); ax.set_yticklabels([n for n, _ in casos] if j == 0 else [], fontsize=8.5)
            ax.set_xlim(0, max(max(v) * 1.35, 0.05)); ax.grid(axis="y", visible=False)
            ax.set_title(klab, loc="left", fontsize=9.5)
        axs[i, 0].text(-0.75, 1.32, slab, transform=axs[i, 0].transAxes, fontsize=11, fontweight="bold", color=INK)
    fig.suptitle("Caso Base / Caso 2 / Caso 3: KPIs con PAD, topes y vigas de R05 (22 boquillas)", x=0.01, y=1.06,
                 ha="left", fontsize=12.5, fontweight="bold")
    nota(fig, "Caso 2: LAT_1 A/B inclinada −4°. Caso 3: Caso 2 + SUP_2 A/B +15 mm hacia fuera. Totales = ramal A x 2 (S9, "
              "verificado en el OD ±0,09 %); cara inferior y agujero no cambian entre casos. Regla lexicográfica: 1) zona seca 0 %, "
              "2) mayor D_min y menor CV, 3) mayor η. Ruido de corrida del CV del OD ±0,0007.")
    guardar(fig, nombre)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("figura")
    ap.add_argument("--caso", default="D:/CFD03_run/G3/G3_A_base")
    ap.add_argument("--t0", type=float, default=0.025)
    ap.add_argument("--t1", type=float, default=0.050)
    ap.add_argument("--nombre", default="G11_OD_dosis_por_boquilla.png")
    ap.add_argument("--titulo", default="OD: dosis por vuelta por boquilla (LAT_1-5 + INF_EXT, ramal A)")
    ap.add_argument("--cotejo", default=None)
    a = ap.parse_args()
    if a.figura == "od_por_boquilla":
        fig_od_por_boquilla(a.caso, a.t0, a.t1, a.nombre, a.titulo, cotejo=a.cotejo)
