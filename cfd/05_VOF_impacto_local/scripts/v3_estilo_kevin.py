"""CORRIDA 2 - estilo de figuras pedido por Kevin (21/10): una grafica por figura, letra grande, sin titulo ni texto
de control dentro de la imagen, colores estandar, referencias a trazos y COMA DECIMAL. Cada figura se guarda con su
CSV al lado (mismo nombre). Lo usan los scripts de 02_VOF_v3 y 03_FLUENT."""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter, NullFormatter  # noqa: E402
import sys  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")   # la consola de Windows (cp1252) no imprime subindices

C = plt.rcParams["axes.prop_cycle"].by_key()["color"]      # colores estandar de matplotlib (tab10)
plt.rcParams.update({"font.size": 13, "axes.labelsize": 14, "legend.fontsize": 11, "xtick.labelsize": 12,
                     "ytick.labelsize": 12, "lines.linewidth": 2, "lines.markersize": 7, "axes.grid": True,
                     "grid.alpha": 0.35, "legend.frameon": False, "figure.figsize": (6.4, 4.6),
                     "savefig.bbox": "tight", "axes.spines.top": False, "axes.spines.right": False})


def coma(v, _pos=None):
    if v == 0:
        return "0"
    s = ("%.6g" % v)
    if "e" in s:
        m, e = s.split("e")
        return "%s·10$^{%d}$" % (m.replace(".", ","), int(e)) if m != "1" else "10$^{%d}$" % int(e)
    return s.replace(".", ",")


def ejes_coma(ax, x=True, y=True):
    if x:
        ax.xaxis.set_major_formatter(FuncFormatter(coma))
    if y:
        ax.yaxis.set_major_formatter(FuncFormatter(coma))
    # sin etiquetas en las marcas menores de los ejes logaritmicos (salian «6×10⁰»)
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_minor_formatter(NullFormatter())


def guardar(fig, carpeta, nombre, cab, filas):
    os.makedirs(carpeta, exist_ok=True)
    fig.savefig(os.path.join(carpeta, nombre + ".png"), dpi=200)
    plt.close(fig)
    with open(os.path.join(carpeta, nombre + ".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cab)
        w.writerows(filas)
    print("figura", nombre)
