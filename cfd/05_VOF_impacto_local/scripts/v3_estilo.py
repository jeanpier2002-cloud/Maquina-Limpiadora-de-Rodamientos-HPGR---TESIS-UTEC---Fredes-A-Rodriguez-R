"""VOF v2 - estilo comun de figuras (mismos colores y formato que e1_figuras.py, sin importarlo) y guardado en
# v3 (CORRIDA 2, 24/10/2026): copia de CORRIDA_1_13a21oct/06_VOF/scripts/v2_estilo.py con rutas cambiadas a 02_VOF_v3 y /home/piermoto/vof3 (sed); sin otros cambios.
figuras/ con su CSV al lado."""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

FIG = "D:/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3/figuras"
DAT2 = "D:/CFD_Redosado/CORRIDA_2_desde24oct/02_VOF_v3/datos"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
SEQ = {"M0": "#86b6ef", "M1": "#3987e5", "M2": "#1c5cab", "M3": "#0d366b", "M4": "#06172e"}
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#6250d6", "#c2338a", "#8a8985"]
GRAY = "#8a8985"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "axes.facecolor": SURF, "figure.facecolor": SURF, "lines.linewidth": 2,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False})


def pie(fig, texto):
    fig.text(0.01, 0.005, texto, fontsize=6.3, color=INK2, ha="left", va="bottom")


def guardar(fig, nombre, filas=None, cab=None):
    fig.savefig(f"{FIG}/{nombre}.png", dpi=200)
    plt.close(fig)
    if filas is not None:
        with open(f"{FIG}/{nombre}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(cab); w.writerows(filas)
    print("figura", nombre)


def csv_escribir(ruta, cab, filas):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cab); w.writerows(filas)
