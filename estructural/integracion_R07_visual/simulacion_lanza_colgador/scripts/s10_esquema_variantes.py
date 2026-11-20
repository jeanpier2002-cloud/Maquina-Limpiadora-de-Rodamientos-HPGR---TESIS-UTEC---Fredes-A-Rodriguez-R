# -*- coding: utf-8 -*-
"""Esquema acotado de la unión transversal–tambor (W5) y de las variantes de refuerzo de s07 (12/11/2026).
Cotas tomadas de la copia del CAD R07 V18D (cubo R200, placa inferior de 15 mm, anillo de 26 mm; transversal DN50 tangente bajo
la placa; bridas a x = 279,25–299,25) y de las variantes de s07 (propuestas, no salen de ningún plano).
Escribe resultados/union_variantes/fig_esquema_variantes.png."""
import math
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle, Wedge

RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultados", "union_variantes")
plt.rcParams.update({"font.size": 8.5, "font.family": "DejaVu Sans"})
fig, ax = plt.subplots(1, 3, figsize=(12, 4.2), gridspec_kw={"width_ratios": [1.25, 1.25, 0.9]})
gris, acero, rojo, morado = "0.82", "0.55", "#d62728", "#9467bd"

# (a) vista lateral, plano de la U (y = 0)
a = ax[0]
a.add_patch(Rectangle((120, 1770), 80, 15, fc=gris, ec="k", lw=0.8))            # placa inferior del cubo
a.add_patch(Rectangle((174, 1785), 26, 75, fc=gris, ec="k", lw=0.8))            # anillo (pared) del cubo
a.add_patch(Rectangle((120, 1845), 54, 15, fc=gris, ec="k", lw=0.8))            # placa superior
a.add_patch(Rectangle((120, 1709.85), 159.25, 60.3, fc="white", ec="k", lw=0.8))  # tubo DN50
a.add_patch(Rectangle((279.25, 1657.5), 20, 165, fc=gris, ec="k", lw=0.8))      # brida A
a.add_patch(Polygon([(200, 1830), (260, 1777), (266, 1777), (266, 1770.15), (200, 1770.15)], fc=morado, alpha=0.55, ec=morado, lw=0.8))
a.add_patch(Rectangle((200, 1770.15), 55, 8, fc=rojo, alpha=0.55, ec=rojo, lw=0.8))
a.plot([120, 200], [1770, 1770], color="k", lw=2.2)
a.annotate("W5 (a4) bajo la placa,\nde borde a borde", (160, 1770), (125, 1735), fontsize=7.5, arrowprops=dict(arrowstyle="-", lw=0.6))
a.annotate("fin de W5\n(x = 200)", (200, 1770), (212, 1700), fontsize=7.5, arrowprops=dict(arrowstyle="->", lw=0.6))
a.text(229, 1808, "cartela\n8 mm", color=morado, fontsize=7.5)
a.text(205, 1781, "lengüeta 8 mm", color=rojo, fontsize=7.5)
a.text(135, 1812, "tambor (cubo)", fontsize=7.5)
a.text(282, 1830, "brida A", fontsize=7.5)
a.text(150, 1690, "transversal DN50 (Ø60,3)", fontsize=7.5)
a.text(205, 1612, "→ brazo A a x = 900; golpe de 1 000 N\n   a Z1400 (fuera del plano: hacia el lector)", fontsize=7.2)
a.text(214, 1842, "cartela y lengüeta son alternativas", fontsize=7.2, style="italic")
a.set_xlim(118, 312); a.set_ylim(1595, 1870); a.set_aspect("equal")
a.set_xlabel("x (mm)"); a.set_ylabel("z (mm)"); a.set_title("(a) Vista lateral (plano de la U)", loc="left", fontsize=9)

# (b) vista en planta (desde abajo, z = 1770)
b = ax[1]
b.add_patch(Wedge((0, 0), 200, -35, 35, width=26, fc=gris, ec="k", lw=0.8))
b.add_patch(Wedge((0, 0), 174, -35, 35, fc="0.93", ec="k", lw=0.5))
b.add_patch(Rectangle((120, -30.15), 159.25, 60.3, fc="white", ec="k", lw=0.8))
b.add_patch(Rectangle((279.25, -82.5), 20, 165, fc=gris, ec="k", lw=0.8))
b.add_patch(Polygon([(193.2, -51.7), (200, -50), (255, -14), (255, 14), (200, 50), (193.2, 51.7)], fc=rojo, alpha=0.45, ec=rojo, lw=0.8))
b.add_patch(Rectangle((200, -4), 66, 8, fc=morado, alpha=0.6, ec=morado, lw=0.8))
for s in (1, -1):
    b.plot([120, 200], [s * 10.3, s * 10.3], color="k", lw=1.4)
b.text(203, 54, "lengüeta: semiancho 50 → 14 mm,\npunta a x = 255", color=rojo, fontsize=7.3)
b.text(203, -16, "cartela (t 8)", color=morado, fontsize=7.3)
b.text(125, 13, "pies de W5", fontsize=7.3)
b.text(150, -110, "borde del tambor R200", fontsize=7.3)
b.set_xlim(118, 312); b.set_ylim(-125, 125); b.set_aspect("equal")
b.set_xlabel("x (mm)"); b.set_ylabel("y (mm)"); b.set_title("(b) Planta: la lengüeta prolonga la placa del tambor", loc="left", fontsize=9)

# (c) sección del tubo
c = ax[2]
c.add_patch(Rectangle((-45, 30.15 - 0.15), 90, 15, fc=gris, ec="k", lw=0.8))
for t, ls, nom in ((2.77, "-", "Sch 10S, t 2,77 (actual)"), (3.91, "--", "Sch 40S, t 3,91"), (5.54, ":", "Sch 80S, t 5,54")):
    c.add_patch(Circle((0, 0), 30.15 - t, fill=False, ls=ls, lw=1.0))
    c.plot([], [], color="k", ls=ls, label=nom)
c.add_patch(Circle((0, 0), 30.15, fill=False, lw=1.2))
for s in (1, -1):
    c.add_patch(Polygon([(s * 2.9, 30.0), (s * 12, 30.0), (s * 10.33, 28.33), (s * 2.9, 29.85)], fc="k"))
th = math.radians(20.03)
c.annotate("pie del cordón (θ ≈ 20°)", (30.15 * math.sin(th), 30.15 * math.cos(th)), (31, 20), fontsize=7.3, arrowprops=dict(arrowstyle="->", lw=0.6))
c.annotate("", (40, 0), (55, 0), arrowprops=dict(arrowstyle="<-", lw=1.2))
c.text(36, -9, "golpe fuera\ndel plano", fontsize=7.2)
c.text(-44, 47, "placa inferior del tambor (15 mm)", fontsize=7.3)
c.legend(fontsize=7, frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.38))
c.set_xlim(-48, 62); c.set_ylim(-36, 50); c.set_aspect("equal"); c.axis("off")
c.set_title("(c) Sección del transversal", loc="left", fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(RES, "fig_esquema_variantes.png"), dpi=200)
