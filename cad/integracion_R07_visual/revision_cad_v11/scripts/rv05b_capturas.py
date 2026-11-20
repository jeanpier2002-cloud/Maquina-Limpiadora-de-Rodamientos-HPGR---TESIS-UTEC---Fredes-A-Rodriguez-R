# -*- coding: utf-8 -*-
"""Revision del CAD R07 V11, fase 5b (Python + matplotlib): capturas de los hallazgos principales a partir de
rv05_teselas.json. Volumen comun en rojo. La vista se recorta a la zona del hallazgo (las piezas grandes, como el piso, se
filtran por triangulo). Salida: revision_cad_v11/capturas/H0x_*.png."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

BASE = r"C:\Users\<usuario>\Documents\Codex\2026-07-06\ho\01_DISENO_VIGENTE\integracion_R07_visual\revision_cad_v11"
datos = json.load(open(BASE + r"\resultados\rv05_teselas.json", encoding="utf-8"))
COL = ["#4C78A8", "#9C9C9C", "#F2A93B", "#54A24B", "#B279A2", "#72B7B2"]
GRANDES = ("Floor", "CTX_CABIN", "R06_PISO", "R06_DELANTAL")
os.makedirs(BASE + r"\capturas", exist_ok=True)
for k, h in datos.items():
    piezas = h["piezas"]
    foco = [p for n, p in piezas.items() if not n.startswith(GRANDES)] or list(piezas.values())
    pts = np.array([v for p in foco for v in p["v"]])
    lo, hi = pts.min(0), pts.max(0)
    m = max(150.0, 0.25 * float((hi - lo).max()))
    lo, hi = lo - m, hi + m
    fig = plt.figure(figsize=(8, 6.2), dpi=130)
    ax = fig.add_subplot(111, projection="3d")
    for i, (n, p) in enumerate(piezas.items()):
        v = np.array(p["v"]); tri = v[np.array(p["f"])]
        c = tri.mean(1)
        ok = np.all((c >= lo) & (c <= hi), axis=1)
        if not ok.any():
            continue
        ax.add_collection3d(Poly3DCollection(tri[ok], facecolor=COL[i % len(COL)], edgecolor="k", linewidths=0.05, alpha=0.55, label=n))
    for n, p in h["comunes"].items():
        v = np.array(p["v"]); tri = v[np.array(p["f"])]
        ax.add_collection3d(Poly3DCollection(tri, facecolor="#E45756", edgecolor="#8B0000", linewidths=0.2, alpha=0.95))
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(hi - lo)
    ax.view_init(elev=22, azim=-58)
    ax.set_xlabel("X (mm)"); ax.set_ylabel("Y (mm)"); ax.set_zlabel("Z (mm)")
    ax.tick_params(labelsize=6)
    titulo = h["titulo"]
    if h["comunes"]:
        titulo += "\nRojo: volumen comun " + ", ".join(f"{p['mm3']:,.0f} mm3".replace(",", " ") for p in h["comunes"].values())
    ax.set_title(titulo, fontsize=9)
    leg = [plt.Rectangle((0, 0), 1, 1, fc=COL[i % len(COL)], alpha=0.6) for i in range(len(piezas))]
    ax.legend(leg, list(piezas.keys()), loc="upper left", fontsize=6, frameon=False)
    fig.tight_layout()
    fig.savefig(BASE + rf"\capturas\{k}.png")
    plt.close(fig)
    print("captura", k)
