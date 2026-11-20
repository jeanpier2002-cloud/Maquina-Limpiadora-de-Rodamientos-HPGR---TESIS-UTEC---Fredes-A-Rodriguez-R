# -*- coding: utf-8 -*-
"""Figura explicativa (12/11/2026): la reacción REAL de cada boquilla del brazo A, dibujada como un solo vector.
Lee geometria/cargas_brazo_A.csv (F = m·v del CFD O7+C2, ya usada en s03). Sistema del STEP: x a lo largo del transversal desde la cara
de la brida, y vertical, z fuera del plano. El brazo se dibuja como esquema (eje del DN40 en x ≈ 599, como el golpe de s02).
En SOLIDWORKS la carga remota se definió con sus tres componentes (s03: SetForceOrTranslationValues2 con X, Y y Z activas), por eso el
símbolo muestra flechas en los tres ejes aunque varias valgan cero. Escribe resultados/fig_reacciones_reales_brazo.png."""
import math
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Rectangle

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
filas = [l.strip().split(";") for l in open(os.path.join(D, "geometria", "cargas_brazo_A.csv"), encoding="utf-8")][1:]
ch = [(f[0].replace("CHORRO_", "").replace("_A", ""), *map(float, f[1:])) for f in filas if f[0].startswith("CHORRO")]
plt.rcParams.update({"font.size": 8.5, "font.family": "DejaVu Sans"})
fig, ax = plt.subplots(figsize=(9.5, 8.2))
XB, R = 599.25, 76.0                                         # eje del brazo DN40 y radio del codo (esquema)
ax.add_patch(Rectangle((-12, -82), 12, 164, fc="0.75", ec="k"))
ax.plot([0, XB - R], [0, 0], color="0.55", lw=9, solid_capstyle="butt")
ax.add_patch(Arc((XB - R, -R), 2 * R, 2 * R, theta1=0, theta2=90, color="0.55", lw=8))
ax.plot([XB, XB], [-R, -850], color="0.55", lw=7, solid_capstyle="butt")
ax.text(-20, 95, "brida (empotrada)", fontsize=8, ha="left")
ax.text(250, 18, "transversal DN50", fontsize=8)
ax.text(XB + 22, -430, "brazo DN40", fontsize=8, rotation=-90, va="center")
E = 18.0                                                     # escala: mm de dibujo por N
for nom, x, y, z, fx, fy, fz in ch:
    F = math.hypot(fx, fy); ang = math.degrees(math.atan2(fy, fx))
    ux, uy = fx / F, fy / F
    ax.annotate("", (x - ux * 55, y - uy * 55), (x, y), arrowprops=dict(arrowstyle="->", color="#5dade2", lw=1.0, ls="--"))   # chorro
    ax.annotate("", (x + fx * E, y + fy * E), (x, y), arrowprops=dict(arrowstyle="-|>", color="#c0392b", lw=2.0))        # reacción
    ax.plot(x, y, "o", color="k", ms=3)
    if abs(fy) < 0.01 or abs(fx) < 0.01:
        txt = "%s: %.2f N" % (nom, F)
    else:
        txt = "%s: %.2f N a %+.0f°\n(Fx %.2f, Fy %+.2f)" % (nom, F, ang, fx, fy)
    if nom.startswith("SUP"):
        izq = nom.endswith("1")
        ax.text(x + (-8 if izq else 8), y + fy * E + 8, txt, fontsize=7.4, ha="right" if izq else "left", va="bottom", color="#922b21")
    else:
        dy = {"INF_EXT": -34, "C2": 34, "LAT_1": 16, "LAT_5": -22}.get(nom, 0)
        ax.text(x + fx * E + 75, y + fy * E + dy, txt, fontsize=7.4, va="center", color="#922b21")
ax.plot([], [], color="#c0392b", lw=2, label="reacción del chorro sobre el brazo (F = ṁ·v, opuesta al chorro)")
ax.plot([], [], color="#5dade2", lw=1, ls="--", label="sentido del chorro")
ax.legend(loc="lower left", fontsize=8, frameon=False)
sx = sum(c[4] for c in ch); sy = sum(c[5] for c in ch)
ax.plot([XB, 560], [-850, -884], color="0.55", lw=3)      # pie DN15 (esquema)
ax.text(10, -470, "Una sola fuerza por boquilla, en el eje del chorro.\n"
                  "Si la boquilla está inclinada, esa misma fuerza\n"
                  "tiene dos componentes (Fx, Fy): no son fuerzas extra.\n"
                  "Fz = 0 en todas: los chorros están en el plano de la U\n"
                  "(C2 está 60 mm fuera del plano, pero también con Fz = 0).\n\n"
                  "Suma del brazo: %.2f N hacia afuera y %.2f N hacia arriba.\n"
                  "El brazo opuesto da lo mismo en espejo: se anulan en el cubo." % (sx, sy), fontsize=7.1, va="top",
        bbox=dict(boxstyle="round", fc="white", ec="0.7"))
ax.set_xlim(-40, 930); ax.set_ylim(-960, 160); ax.set_aspect("equal")
ax.set_xlabel("x a lo largo del transversal (mm)"); ax.set_ylabel("y vertical (mm)")
ax.set_title("Brazo A de la U: reacción de cada boquilla (escala de flechas: 1 N = %.0f mm)" % E, loc="left", fontsize=9.5)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(D, "resultados", "fig_reacciones_reales_brazo.png"), dpi=200)
print("ok", round(sx, 2), round(sy, 2))
