#!/usr/bin/env python3
"""G10 - Graficos de KPIs del Caso Base de 22 boquillas (R05) y del rediseno (Caso 3) para la memoria de figuras.
Mismo estilo y paleta que graficos_cfd03.py (slots categoricos en orden fijo, validados en CFD02).
Los KPIs NO se recalculan: se leen de los CSV de caso_base_22.py / combinar_kpi.py (G7, G8/comparacion) y de
procesar_caso.py (G3-G6). Solo G12 reconstruye perfiles desde los impactos, con la aritmetica de post_kpi.py, y los
coteja con los aportes de G7.

Uso: python graficos_g10.py [--g7 06_RESULTADOS/G7] g12 g13 g14 g15 g17 g21 g22 g24 [g20]
Salida: 07_FIGURAS/graficos_KPI/G12_... G24_...
"""
import argparse
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from graficos_cfd03 import (BASE, FIG, GRID, INK, INK2, MUTED, RAIZ, SLOT, SURF, dosis_anillo, fig_mapa_polar,  # noqa: E402
                            guardar, nota, plt)

RES = os.path.join(RAIZ, "06_RESULTADOS")
SUPERF = [("od", "OD (R 710 mm)", "Altura Z (mm)"),
          ("sup", "Cara superior (z 1405 mm)", "Radio r (mm)"),
          ("cara_inf", "Cara inferior (z 890 mm)", "Radio r (mm)"),
          ("agujero", "Agujero (cono 1:30, ID 900 mm)", "Altura Z (mm)")]
COLOR_SUP = {"od": SLOT[0], "sup": SLOT[1], "cara_inf": SLOT[2], "agujero": SLOT[3]}
LIM = {"od": (890.0, 1405.0), "sup": (458.58, 710.0), "cara_inf": (450.0, 710.0), "agujero": (890.0, 1405.0)}  # mm


def leer(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def col(filas, k):
    return np.array([float(r[k]) for r in filas])


def indicadores(carpeta, s):
    return {r["variante"]: r for r in leer(os.path.join(carpeta, "G7_%s_indicadores.csv" % s))}


def fmt(x, nd=2):
    """Coma decimal (texto de la memoria en espanol)."""
    return ("%%.%df" % nd % x).replace(".", ",")


# ---------------------------------------------------------------------------------------------------------------
def g14(g7):
    """Dosis por vuelta en las 4 superficies (Caso Base, con obstaculos R05): pequenos multiplos con la MISMA escala
    vertical para que la comparacion entre superficies sea directa. Barras: 10 mm (KPI oficial); linea: 2 mm."""
    fig, axs = plt.subplots(2, 2, figsize=(12.8, 8.4), sharey=True, gridspec_kw=dict(hspace=0.5, wspace=0.08))
    for ax, (s, tit, xl) in zip(axs.flat, SUPERF):
        b10 = leer(os.path.join(g7, "G7_%s_bandas_10mm.csv" % s))
        b2 = leer(os.path.join(g7, "G7_%s_bandas_2mm.csv" % s))
        ind = indicadores(g7, s)
        c10, D10 = col(b10, "s_centro_mm"), col(b10, "D_obst_media_theta")
        c2, D2 = col(b2, "s_centro_mm"), col(b2, "D_obst_media_theta")
        lo, hi = LIM[s]
        e10 = np.minimum(lo + 10.0 * np.arange(len(c10) + 1), hi)
        ax.bar(0.5 * (e10[:-1] + e10[1:]), D10, width=0.84 * np.diff(e10), color=SLOT[0], edgecolor=SURF, linewidth=0.6,
               label="Bandas de 10 mm (KPI oficial)")
        ax.plot(c2, D2, color=INK, lw=0.9, label="Bandas de 2 mm (complementario)")
        secas = c2[D2 <= 1e-9]
        for z in secas:
            ax.axvspan(z - 1, z + 1, color=SLOT[7], alpha=0.35, lw=0)
        if s == "cara_inf":
            ax.axvspan(638, 688, color=MUTED, alpha=0.13, lw=0)
            ax.text(663, 43.5, "PAD\n(contacto 3 × 24°)", ha="center", va="top", fontsize=8, color=INK2)
        o10, o2 = ind["obst_10mm"], ind["obst_2mm"]
        Dm = float(o10["D_media"])
        ax.hlines(Dm, lo, hi, color=INK2, ls="--", lw=0.9)
        ax.text(hi + 4, Dm, "D̄ = %s" % fmt(Dm, 1), va="center", ha="left", fontsize=8.5, color=INK2)
        ax.set_title(tit, loc="left")
        txt = ("CV %s · D_min %s · zona seca %s / %s %% (10 / 2 mm) · η %s %%"
               % (fmt(float(o10["CV"])), fmt(float(o10["D_min"]), 1), fmt(float(o10["seca_pct"]), 1),
                  fmt(float(o2["seca_pct"]), 2), fmt(float(o10["eta_pct"]), 1)))
        ax.text(0.0, 1.0, txt, transform=ax.transAxes, va="bottom", ha="left", fontsize=8.3, color=INK2,
                bbox=dict(boxstyle="square,pad=0.15", fc=SURF, ec="none"))
        ax.set_title(tit, loc="left", pad=16)
        ax.set_xlabel(xl)
        ax.set_xlim(lo - 6, hi + 44)
        ax.set_ylim(0, 45)
    for ax in axs[:, 0]:
        ax.set_ylabel("D por vuelta (kg·m⁻²·vuelta⁻¹)")
    h, l = axs[0, 0].get_legend_handles_labels()
    orden = sorted(range(len(l)), key=lambda i: "10 mm" not in l[i])
    h, l = [h[i] for i in orden], [l[i] for i in orden]
    fig.legend(h, l, ncol=2, loc="upper left", bbox_to_anchor=(0.01, 0.995), fontsize=9)
    fig.suptitle("Caso Base R05 (22 boquillas): dosis por vuelta en las cuatro superficies", x=0.01, y=1.035, ha="left",
                 fontsize=12.5, fontweight="bold")
    nota(fig, "Dosis media en θ con las sombras de PAD, topes y vigas de R05 (máscaras de rayos, [INTERFAZ ISMAEL]); misma "
              "escala vertical en los cuatro paneles. OD y cara inferior: ramales A y B explícitos (G3 v3 + G4 v2) + INF_INT "
              "(G5 v2). Cara superior: ramal A × 2 (S9). Agujero: lanza (INT_1-5 + INF_INT). Rojo: bandas de 2 mm sin impacto "
              "directo. η = fracción del caudal de las boquillas dirigidas a esa superficie que llega a ella (cara inferior: "
              "INF_EXT A/B e INF_INT, que también moja el agujero). Pared trap (sin escorrentía): D y η son cotas superiores; "
              "la zona seca es conservadora. 1,7 rpm (HIPÓTESIS): D escala con T_vuelta; CV y zona seca no.")
    guardar(fig, "G14_CasoBase_dosis_4_superficies.png")


def cobertura(npz, x):
    Z = np.load(npz)
    D, A = Z["D"], Z["A"]
    m = A > 0
    Dv, Av = D[m].ravel(), A[m].ravel()
    orden = np.argsort(Dv)
    Dv, Av = Dv[orden], Av[orden]
    acum = np.cumsum(Av[::-1])[::-1] / Av.sum()          # fraccion de area con D >= Dv[i]
    idx = np.searchsorted(Dv, x, side="left")
    return 100 * np.where(idx < len(Dv), acum[np.minimum(idx, len(Dv) - 1)], 0.0)


def g15(g7):
    """Curva de cobertura C(D) = % del area mojable con dosis >= D, por celdas de 10 mm x 0,5 grados con sombras de
    obstaculos. (a) Caso Base, 4 superficies. (b) OD y cara superior: Caso Base frente a Caso 3 (misma base A x 2)."""
    x = np.linspace(0, 45, 901)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.8, 4.9), sharey=True, gridspec_kw=dict(wspace=0.08))
    for s, tit, _ in SUPERF:
        C = cobertura(os.path.join(g7, "G7_%s_mapa10mm.npz" % s), x)
        a1.plot(x, C, color=COLOR_SUP[s], lw=2, label=tit.split(" (")[0])
    a1.set_title("(a) Caso Base: cuatro superficies", loc="left")
    a1.legend(loc="lower left", fontsize=9)
    comp = os.path.join(RES, "G8", "comparacion")
    for s, lab in (("od", "OD"), ("sup", "Cara superior")):
        for caso, ls, nom in (("CB", "-", "Caso Base"), ("C3", "--", "Caso 3")):
            C = cobertura(os.path.join(comp, caso, "G7_%s_mapa10mm.npz" % s), x)
            a2.plot(x, C, color=COLOR_SUP[s], lw=2, ls=ls, label="%s, %s" % (lab, nom))
    a2.set_title("(b) Rediseño: Caso Base frente a Caso 3", loc="left")
    a2.legend(loc="lower left", fontsize=9)
    for ax in (a1, a2):
        ax.set_xlim(0, 45)
        ax.set_ylim(0, 102)
        ax.set_xlabel("Umbral de dosis D (kg·m⁻²·vuelta⁻¹)")
    a1.set_ylabel("Área mojable con dosis ≥ D (%)")
    fig.suptitle("Curva de cobertura C(D): cuánto del área recibe al menos una dosis dada", x=0.01, y=1.03, ha="left",
                 fontsize=12.5, fontweight="bold")
    nota(fig, "Celdas de 10 mm × 0,5° con sombras de obstáculos (más exigente que las bandas axisimétricas del K4 oficial). "
              "No hay umbral de dosis con respaldo para grasa sobre acero [SIN FUENTE]: la curva ordena casos, no dice "
              "'limpia'. Panel (b): ramal A × 2 en ambos casos (G8/comparacion), la misma base de G18.")
    guardar(fig, "G15_cobertura_vs_umbral.png")


def g17(g7):
    """Destino del caudal de cada boquilla (fraccion de su caudal), con obstaculos de R05, y total de las 22.
    Destinos: OD, cara superior, cara inferior, agujero, interceptado por PAD/topes/vigas, escape del dominio."""
    bal = leer(os.path.join(g7, "G7_balance_por_boquilla.csv"))
    # depositos por boquilla y superficie (libre, con obstaculos); los aportes ya traen aplicado su factor
    dep = {}
    for s in ("od", "sup", "cara_inf", "agujero"):
        for r in leer(os.path.join(g7, "G7_%s_aportes.csv" % s)):
            for b in r["boquillas"].split(","):
                li, ob = dep.get((b, s), (0.0, 0.0))
                dep[(b, s)] = (li + float(r["mdot_dep_libre_kg_s"]), ob + float(r["mdot_dep_obst_kg_s"]))
    # fila por tipo de boquilla: (nombre, claves de aportes, nombre en el balance)
    tipos = [("LAT_%d" % i, ["lat_%d_a" % i, "lat_%d_b" % i], "LAT_%d_A" % i) for i in range(1, 6)]
    tipos += [("INF_EXT", ["inf_ext_a", "inf_ext_b"], "INF_EXT_A"), ("SUP_1", ["sup_1_a"], "SUP_1_A"),
              ("SUP_2", ["sup_2_a"], "SUP_2_A")]
    tipos += [("INT_%d" % i, ["int_%d" % i], "INT_%d" % i) for i in range(1, 6)] + [("INF_INT", ["inf_int"], "INF_INT")]
    destinos = [("od", "OD", SLOT[0]), ("sup", "Cara superior", SLOT[1]), ("cara_inf", "Cara inferior", SLOT[2]),
                ("agujero", "Agujero", SLOT[3]), ("obst", "PAD, topes y vigas", SLOT[6]), ("esc", "Escape", BASE)]
    filas = []
    for nom, ks, kb in tipos:
        tot = sum(float(r["inyectado_kg_s"]) for r in bal if r["boquilla"] == kb)      # A + B (factor incluido)
        v = {d: 0.0 for d, _, _ in destinos}
        libre = 0.0
        for k in ks:
            for s in ("od", "sup", "cara_inf", "agujero"):
                li, ob = dep.get((k, s), (0.0, 0.0))
                v[s] += ob
                v["obst"] += li - ob
                libre += li
        v["esc"] = max(tot - libre, 0.0)
        filas.append((nom, tot, {d: 100 * v[d] / tot for d in v}))
        print("%-8s iny %.6f kg/s | %s" % (nom, tot, " ".join("%s %.1f" % (d, filas[-1][2][d]) for d in v)))
    fig, ax = plt.subplots(figsize=(11.5, 7.0))
    ys = np.arange(len(filas))[::-1]
    for (nom, tot, pc), y in zip(filas, ys):
        izq = 0.0
        for d, lab, c in destinos:
            w = pc[d]
            if w <= 0:
                continue
            ax.barh(y, w, left=izq, height=0.66, color=c, edgecolor=SURF, linewidth=1.0)
            if w >= 7:
                ax.text(izq + w / 2, y, "%d" % round(w), ha="center", va="center", fontsize=8,
                        color="white" if d not in ("esc", "agujero") else INK)
            izq += w
    ax.set_yticks(ys)
    ax.set_yticklabels(["%s%s" % (n, " (A y B)" if n.startswith(("LAT", "INF_EXT")) else
                                   (" (A; B = A)" if n.startswith("SUP") else "")) for n, _, _ in filas], fontsize=9)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Destino del caudal de la boquilla (%)")
    ax.grid(axis="y", visible=False)
    from matplotlib.patches import Patch
    ax.legend([Patch(color=c) for _, _, c in destinos], [l for _, l, _ in destinos], ncol=6, loc="lower left",
              bbox_to_anchor=(0.0, 1.0), fontsize=9)
    fig.suptitle("¿A dónde va el líquido de cada boquilla? (Caso Base R05, con obstáculos)", x=0.01, y=1.0, ha="left",
                 fontsize=12.5, fontweight="bold")
    gl = leer(os.path.join(g7, "G7_balance_global.csv"))
    tg = {r["destino"]: r for r in gl}
    import json
    q = [v["q_Lmin"] for v in json.load(open(os.path.join(RAIZ, "03_GEOMETRIA", "boquillas_22.json")))["boquillas"].values()]
    pg = [fmt(float(tg[k]["pct_del_inyectado"]), 1) for k in ("OD", "cara superior", "cara inferior", "agujero", "escape")]
    cierre = fmt(float(gl[-1]["pct_del_inyectado"]), 3)
    txt = ("Barra = 100 % del caudal de la boquilla (red de 22: {0}-{1} L/min por boquilla; total {2} L/min). Total de las "
           "22 sin obstáculos: OD {3} %, cara superior {4} %, cara inferior {5} %, agujero {6} %, escape {7} %; cierre del "
           "balance {8} %. 'PAD, topes y vigas' = líquido interceptado según las máscaras de rayos. Pared trap: lo que llega "
           "se queda (η es cota superior).").format(fmt(min(q)), fmt(max(q)), fmt(sum(q)), *pg, cierre)
    nota(fig, txt)
    guardar(fig, "G17_destino_del_caudal_por_boquilla.png")


def g21():
    """S9 y ruido de corrida: ramal A (G3_A_base_v3) frente a ramal B (G4_B_base_v2), geometricamente identicos."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.8, 4.8), gridspec_kw=dict(wspace=0.22))
    s9 = {(r["zona"], r["caso"].split("/")[0]): r for r in leer(os.path.join(RES, "G4", "G4_S9_A_vs_B_S18.csv"))}
    for ax, z, xl, tit in ((a1, "od", "Altura Z (mm)", "OD: LAT_1-5 + INF_EXT"),
                           (a2, "cara_inf", "Radio r (mm)", "Cara inferior: INF_EXT")):
        for caso, c, lab in (("G3/G3_A_base_v3", SLOT[0], "Ramal A (θ = 0°)"), ("G4/G4_B_base_v2", SLOT[1], "Ramal B (θ = 180°)")):
            b = leer(os.path.join(RES, "%s_%s_dosis_por_banda.csv" % (caso, z)))
            ax.plot(col(b, "s_centro_mm"), col(b, "D_kg_m2_vuelta"), color=c, lw=1.6, label=lab)
        rb = s9[(z, "G4")]
        ax.set_title(tit, loc="left", pad=16)
        ax.text(0.0, 1.0, "B frente a A: D̄ %+.2f %% · CV %+.4f · J̄ %+.2f %%" % (
            float(rb["d_K2_D_media_kg_m2_vuelta_pct"]), float(rb["d_K3_CV"]), float(rb["d_K6_J_media_N_s_m2_vuelta_pct"])),
            transform=ax.transAxes, va="bottom", fontsize=8.5, color=INK2)
        ax.set_xlabel(xl)
        ax.set_ylim(bottom=0)
    a1.set_ylabel("D por vuelta de un ramal (kg·m⁻²·vuelta⁻¹)")
    a1.legend(loc="lower right", fontsize=9)
    fig.suptitle("S9 (ramal B = ramal A) y ruido de corrida del CFD acoplado", x=0.01, y=1.04, ha="left",
                 fontsize=12.5, fontweight="bold")
    nota(fig, "Mismas tablas de inyección (600/1200 rayos, S18) y la malla rotada 180°: la diferencia mide el ruido de una "
              "realización del flujo de aire acoplado (ventana 25-50 ms). OD: S9 se cumple (< 1 %). Cara inferior: ±1,5 % en "
              "D̄ y ±0,05 en CV (incidencia rasante, flujo caótico bajo el aro). El Caso Base usa A y B explícitos.")
    guardar(fig, "G21_S9_ramal_A_vs_B.png")


def g22():
    """Verificacion del metodo de mascaras: PAD modelado en la malla (G5_PAD_base) frente a la prediccion por rayos."""
    v = {r["boquilla"]: r for r in leer(os.path.join(RES, "G5", "G5_verificacion_PAD.csv"))}
    ie, l5 = v["INF_EXT_A"], v["LAT_5_A"]
    cats = [("INF_EXT → PAD", ie["PAD_rayos_pct"], ie["PAD_CFD_pct"]),
            ("INF_EXT → cara inf.\nsin PAD", ie["cara_inf_rayos_libre_pct"], ie["cara_inf_CFD_libre_pct"]),
            ("INF_EXT → cara inf.\ncon PAD", ie["cara_inf_rayos_PAD_pct"], ie["cara_inf_CFD_PAD_pct"]),
            ("LAT_5 → PAD", l5["PAD_rayos_pct"], l5["PAD_CFD_pct"])]
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    x = np.arange(len(cats))
    w = 0.36
    for i, (lab, c, k) in enumerate((("Rayos (máscara)", MUTED, 1), ("CFD con el PAD en la malla", SLOT[0], 2))):
        vals = [float(cv[k]) for cv in cats]
        ax.bar(x + (i - 0.5) * w, vals, width=w - 0.03, color=c, edgecolor=SURF, label=lab)
        for xi, vv in zip(x, vals):
            ax.text(xi + (i - 0.5) * w, vv + 0.4, fmt(vv, 1), ha="center", va="bottom", fontsize=8.5, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels([c[0] for c in cats], fontsize=9)
    ax.set_ylabel("% del caudal de la boquilla")
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_ylim(0, 25)
    fig.suptitle("Verificación del método de máscaras: el PAD en la malla frente a los rayos (rotor sobre el PAD 1)",
                 x=0.01, y=1.0, ha="left", fontsize=12.5, fontweight="bold")
    nota(fig, "G5_PAD_base (G3_A_base + PAD 1 mallado, 150 rayos). Sombra en la cara inferior r < 638 mm: %s %% del caudal "
              "de INF_EXT sin PAD → %s %% con PAD (total, como predicen los rayos). OD sin cambio (D̄ 13,2392 frente a "
              "13,2394). La diferencia en LAT_5 → PAD (gotas que de todos modos no llegan al OD) no afecta a ningún KPI."
         % (fmt(float(ie["cara_inf_r638_CFD_libre_pct"]), 2), fmt(float(ie["cara_inf_r638_CFD_PAD_pct"]), 3)))
    guardar(fig, "G22_verificacion_PAD_mascaras.png")


def g24():
    """Rediseno: perfiles de dosis (2 mm) Caso Base frente a Caso 3 en el OD (completo y zoom de la franja) y en la
    cara superior (base A x 2, G8/comparacion)."""
    comp = os.path.join(RES, "G8", "comparacion")
    fig, axs = plt.subplots(1, 3, figsize=(14.5, 4.9), gridspec_kw=dict(wspace=0.22, width_ratios=[1.35, 0.75, 1.15]))
    paneles = ((axs[0], "od", "Altura Z (mm)", "OD", None), (axs[1], "od", "Altura Z (mm)", "OD: franja LAT_5-LAT_1",
                                                            (995, 1075)),
               (axs[2], "sup", "Radio r (mm)", "Cara superior", None))
    for ax, s, xl, tit, zoom in paneles:
        for caso, c, nom in (("CB", SLOT[0], "Caso Base"), ("C3", SLOT[2], "Caso 3")):
            b = leer(os.path.join(comp, caso, "G7_%s_bandas_2mm.csv" % s))
            ind = indicadores(os.path.join(comp, caso), s)
            o10, o2 = ind["obst_10mm"], ind["obst_2mm"]
            lab = ("%s: CV %s · D_min %s · seca 2 mm %s %%" % (nom, fmt(float(o10["CV"])), fmt(float(o10["D_min"]), 1),
                                                                fmt(float(o2["seca_pct"]), 2)))
            ax.plot(col(b, "s_centro_mm"), col(b, "D_obst_media_theta"), color=c, lw=1.3 if zoom else 1.1, label=lab)
        ax.set_title(tit, loc="left", pad=40 if not zoom else 6)
        ax.set_xlabel(xl)
        ax.set_ylim(0, 50)
        if zoom:
            ax.set_xlim(*zoom)
            ax.set_ylim(0, 35)
        else:
            ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), fontsize=8.5)
    axs[0].set_ylabel("D por vuelta, bandas de 2 mm (kg·m⁻²·vuelta⁻¹)")
    fig.suptitle("Rediseño: Caso 3 (LAT_1 −4° y SUP_2 +15 mm) frente al Caso Base", x=0.01, y=1.10, ha="left",
                 fontsize=12.5, fontweight="bold")
    nota(fig, "Ramal A × 2 (S9) en ambos casos, con obstáculos de R05 (G8/comparacion, base de G18). En el OD, la huella de "
              "LAT_1 baja ≈ 11 mm y solapa con la de LAT_5: la franja sin impacto directo del Caso Base (Z ≈ 1032-1038 mm) "
              "desaparece. En la cara superior, SUP_2 más afuera reparte mejor la dosis. CV y D_min con bandas de 10 mm. "
              "La remoción de grasa no se simula (N4).")
    guardar(fig, "G24_rediseno_perfiles_CasoBase_vs_Caso3.png")


def g20():
    """Verificacion G6: cambio de cada KPI frente a la corrida base (malla gruesa / fina, dt/2, dominio, parcelas).
    Pequenos multiplos por superficie; barras por estudio (color = estudio, orden fijo). Se omite lo que aun no existe.
    Cambio relativo (%) para D, J, p_huella y eta; para CV se grafica el cambio relativo tambien (|dCV|/CV)."""
    paneles = [
        ("od", "OD (LAT_1-5 + INF_EXT, ramal A)", "G3/G3_A_base_v3",
         [("Malla gruesa", "G6/G6_G3_gruesa"), ("Malla fina", "G6/G6_G3_fina"), ("Dominio ampliado", "G6/G6_G3_dominio"),
          ("150 rayos", "G3/G3_A_base")]),
        ("cara_inf", "Cara inferior: INF_EXT (ramal A)", "G3/G3_A_base_v3",
         [("Malla gruesa", "G6/G6_G3_gruesa"), ("Malla fina", "G6/G6_G3_fina"), ("Dominio ampliado", "G6/G6_G3_dominio"),
          ("150 rayos", "G3/G3_A_base")]),
        ("sup", "Cara superior (SUP_1-2, ramal A)", "G6/G6_ESUP_base_v2",
         [("Malla gruesa", "G6/G6_ESUP_gruesa"), ("Malla fina", "G6/G6_ESUP_fina"), ("150 rayos", "G6/G6_ESUP_base")]),
        ("cara_inf", "Cara inferior: INF_INT", "G5/G5_INT_base_v2",
         [("Malla gruesa", "G6/G6_INT_gruesa"), ("Malla fina", "G6/G6_INT_fina"), ("Δt / 2", "G6/G6_INT_dt25"),
          ("150 rayos", "G6/G6_INT_n150")]),
    ]
    kpis = [("K2_D_media_kg_m2_vuelta", "D̄"), ("K3_CV", "CV"), ("K6_J_media_N_s_m2_vuelta", "J̄"),
            ("K6_p_huella_Pa", "p_huella"), ("K5_eta_pct", "η")]
    color = {"Malla gruesa": SLOT[0], "Malla fina": SLOT[1], "Dominio ampliado": SLOT[2], "Δt / 2": SLOT[3],
             "150 rayos": BASE}
    fig, axs = plt.subplots(2, 2, figsize=(13, 8), sharey=True, gridspec_kw=dict(hspace=0.55, wspace=0.08))
    filas_csv = []
    for ax, (zona, tit, base, est) in zip(axs.flat, paneles):
        pb = os.path.join(RES, "%s_%s_indicadores.csv" % (base, zona))
        b = leer(pb)[0]
        presentes = [(n, c) for n, c in est if os.path.exists(os.path.join(RES, "%s_%s_indicadores.csv" % (c, zona)))]
        w = 0.8 / max(len(presentes), 1)
        for j, (n, c) in enumerate(presentes):
            r = leer(os.path.join(RES, "%s_%s_indicadores.csv" % (c, zona)))[0]
            d = [100 * (float(r[k]) / float(b[k]) - 1) for k, _ in kpis]
            x = np.arange(len(kpis)) + (j - (len(presentes) - 1) / 2) * w
            ax.bar(x, d, width=w * 0.92, color=color[n], edgecolor=SURF, label=n)
            for xi, di in zip(x, d):           # barras recortadas: se rotula su valor real
                if abs(di) > 12:
                    ax.text(xi, 11.3 if di > 0 else -11.3, ("%+.0f %%" % di).replace(".", ","), ha="center",
                            va="top" if di > 0 else "bottom", fontsize=7.5, color=INK, rotation=90)
            filas_csv.append([tit, n, c] + ["%.3f" % v for v in d])
        ax.axhspan(-5, 5, color=MUTED, alpha=0.10, lw=0)
        ax.axhline(0, color=BASE, lw=0.8)
        ax.set_xticks(np.arange(len(kpis)))
        ax.set_xticklabels([l for _, l in kpis])
        ax.set_title(tit, loc="left", fontsize=10.5)
        ax.grid(axis="x", visible=False)
        ax.legend(fontsize=8, loc="lower left", ncol=2)
        ax.set_ylim(-12, 12)
    for ax in axs[:, 0]:
        ax.set_ylabel("Cambio frente a la corrida base (%)")
    fig.suptitle("Verificación (G6): sensibilidad de los KPIs a la malla, el paso de tiempo, el dominio y las parcelas",
                 x=0.01, y=1.0, ha="left", fontsize=12.5, fontweight="bold")
    nota(fig, "Franja gris: ±5 %, objetivo de trabajo del checklist (cambio < 5 % entre las dos mallas finas; no es una norma). "
              "Base: G3_A_base_v3 (430 560 celdas), G6_ESUP_base_v2 (237 552) y G5_INT_base_v2 (197 280), todas con S18. "
              "'150 rayos' = sensibilidad al número de parcelas. Barras fuera de escala recortadas en ±12 %; valores en "
              "06_RESULTADOS/G6/G20_variaciones.csv. Esto es verificación, no validación.")
    with open(os.path.join(RES, "G6", "G20_variaciones.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["superficie", "estudio", "corrida"] + ["d_%s_pct" % k for k, _ in kpis])
        wr.writerows(filas_csv)
    guardar(fig, "G20_verificacion_G6.png")


def g12():
    """Cara inferior por aporte (definitivo): INF_EXT A (G3 v3), INF_EXT B (G4 v2) e INF_INT (G5 v2), cada uno con su
    ventana. Sector libre (sin PAD); cotejo de la masa con G7_cara_inf_aportes (libre)."""
    from lector_impactos import leer as leer_imp
    aportes = [("D:/CFD03_run/G3/G3_A_base_v3/cara_inf.csv", "inf_ext_a", 0.025, 0.050, "INF_EXT A"),
               ("D:/CFD03_run/G4/G4_B_base_v2/cara_inf.csv", "inf_ext_b", 0.025, 0.050, "INF_EXT B"),
               ("D:/CFD03_run/G5/G5_INT_base_v2/cara_inf.csv", "inf_int", 0.070, 0.100, "INF_INT (lanza)")]
    ref = {r["boquillas"]: float(r["mdot_dep_libre_kg_s"]) for r in
           leer(os.path.join(RES, "G7_preliminar", "G7_cara_inf_aportes.csv"))}
    fig, ax = plt.subplots(figsize=(10.8, 5.6))
    izq = None
    tot2 = None
    cotejo = []
    for i, (p, bq, t0, t1, lab) in enumerate(aportes):
        R = leer_imp(p, ["x", "y", "masa", "t"], texto=("boquilla",), filtro_t=(t0, t1))
        s = R["boquilla"] == bq
        r = np.hypot(R["x"][s], R["y"][s])
        m = R["masa"][s] / (t1 - t0)
        cotejo.append("%s %.6f (G7 %.6f)" % (lab, m[(r >= 0.45) & (r <= 0.71)].sum(), ref.get(bq, float("nan"))))
        e, D = dosis_anillo(r, m, 0.010)
        c = 0.5 * (e[:-1] + e[1:]) * 1e3
        izq = np.zeros_like(D) if izq is None else izq
        ax.bar(c, D, width=8.4, bottom=izq, color=SLOT[i], edgecolor=SURF, linewidth=0.6, label=lab)
        izq = izq + D
        e2, D2 = dosis_anillo(r, m, 0.002)
        tot2 = D2 if tot2 is None else tot2 + D2
    print("cotejo de masa en la cara inferior (kg/s):", "; ".join(cotejo))
    c2 = 0.5 * (e2[:-1] + e2[1:]) * 1e3
    ax.plot(c2, tot2, color=INK, lw=0.9, label="Total, bandas de 2 mm")
    ax.axvspan(638, 688, color=MUTED, alpha=0.13, lw=0)
    ax.text(663, ax.get_ylim()[1] * 0.97, "PAD\n(contacto 3 × 24°)", ha="center", va="top", fontsize=8.5, color=INK2)
    ax.set_xlim(450, 710)
    ax.set_xlabel("Radio r en la cara inferior (mm)")
    ax.set_ylabel("D por vuelta (kg·m⁻²·vuelta⁻¹)")
    ax.legend(ncol=4, loc="lower left", bbox_to_anchor=(0.0, 1.0), fontsize=9)
    fig.suptitle("Cara inferior: quién la moja (Caso Base, sector libre)", x=0.01, y=1.06, ha="left", fontsize=12.5,
                 fontweight="bold")
    nota(fig, "Barras apiladas: bandas de 10 mm por aporte; línea: total con bandas de 2 mm. Sin PAD ni topes (su efecto se "
              "aplica con las máscaras, ver G13 y G14). INF_EXT A y B: ventana 25-50 ms; INF_INT: 70-100 ms (escape lento, "
              "S16). INF_INT concentra la dosis junto al agujero (r < 520 mm); INF_EXT reparte hacia el borde exterior. "
              "La cara mira hacia abajo: con pared trap no se modela el goteo, así que la dosis es una cota superior.")
    guardar(fig, "G12_cara_inferior_por_aporte.png")


def g13(g7):
    fig_mapa_polar(os.path.join(g7, "G7_cara_inf_mapa10mm.npz"), "G13_mapa_cara_inferior.png",
                   "Cara inferior: dosis por vuelta con PAD, topes y vigas (Caso Base)", rango=18)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("figuras", nargs="*", default=["g12", "g13", "g14", "g15", "g17", "g21", "g22", "g24"])
    ap.add_argument("--g7", default=os.path.join(RES, "G7"))
    a = ap.parse_args()
    g7 = a.g7 if os.path.isabs(a.g7) else os.path.join(RAIZ, a.g7)
    print("datos del Caso Base:", g7)
    for f in a.figuras:
        fn = globals()[f]
        fn(g7) if fn.__code__.co_argcount else fn()
