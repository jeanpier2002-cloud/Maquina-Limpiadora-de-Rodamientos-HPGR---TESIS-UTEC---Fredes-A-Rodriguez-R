#!/usr/bin/env python3
"""
Posproceso del piloto F2: lee los archivos de impactos de particlePostProcessing
y produce los CSV de decision (balance de masa, huella, indicadores, diametros).

Se ejecuta con el Python de Windows (tiene numpy) sobre una copia local de los
.dat; no lee directamente de \\wsl.localhost (no funciona de forma fiable).

Uso:
    python post_F2.py --raiz <carpeta con V*/impactos/*/placa.dat> --salida <carpeta>
"""
import argparse
import csv
import glob
import math
import os
import re

import numpy as np

P = argparse.ArgumentParser()
P.add_argument("--raiz", required=True, help="carpeta con una subcarpeta por variante")
P.add_argument("--salida", required=True, help="carpeta donde escribir los CSV")
P.add_argument("--t-estable", type=float, default=0.03,
               help="se promedia solo con impactos de t >= este valor (regimen estacionario)")
P.add_argument("--t-fin", type=float, default=0.05)
P.add_argument("--bin-mm", type=float, default=2.0, help="tamano del bin del mapa, mm")
A = P.parse_args()

# ---- datos del caso (deben coincidir con los del piloto) -------------------
Q_LMIN = 9.11766505450028
RHO_L = 982.1203530851709
V_SAL = 27.11354121556065
MDOT_OBJ = Q_LMIN / 60000.0 * RHO_L          # kg/s
SIGMA = 0.0662                                # N/m, agua a 62 C
DIST_PARED = 0.1433                           # m, punta -> pared
Y_PLACA = 0.1478                              # m
SEMIANG = math.radians(25.0)
OMEGA = 0.1780235837034216                    # rad/s
R_PARED = 0.450                               # m
R_PUNTA = 0.3067                              # m

LIN = re.compile(r"^\s*([0-9.eE+-]+)\s+(\d+)\s+\(([^)]*)\)\s+(\d+)\s+"
                 r"([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+\(([^)]*)\)\s+"
                 r"([0-9.eE+-]+)\s+([0-9.eE+-]+)")


def leer(variante_dir):
    """devuelve dict de arrays con todos los impactos de una variante"""
    t, px, py, pz, oid, npart, d, ux, uy, uz, rho, age = ([] for _ in range(12))
    archivos = sorted(glob.glob(os.path.join(variante_dir, "**", "placa.dat"), recursive=True))
    for f in archivos:
        with open(f) as fh:
            for ln in fh:
                if ln.startswith("#"):
                    continue
                m = LIN.match(ln)
                if not m:
                    continue
                t.append(float(m.group(1)))
                p = [float(v) for v in m.group(3).split()]
                px.append(p[0]); py.append(p[1]); pz.append(p[2])
                oid.append(int(m.group(4)))
                npart.append(float(m.group(5)))
                d.append(float(m.group(6)))
                u = [float(v) for v in m.group(7).split()]
                ux.append(u[0]); uy.append(u[1]); uz.append(u[2])
                rho.append(float(m.group(8)))
                age.append(float(m.group(9)))
    out = dict(t=np.array(t), x=np.array(px), y=np.array(py), z=np.array(pz),
               origId=np.array(oid), nParticle=np.array(npart), d=np.array(d),
               U=np.column_stack([ux, uy, uz]) if t else np.zeros((0, 3)),
               rho=np.array(rho), age=np.array(age), archivos=len(archivos))
    out["masa"] = out["rho"] * out["nParticle"] * math.pi / 6.0 * out["d"] ** 3
    return out


variantes = sorted(d for d in os.listdir(A.raiz) if os.path.isdir(os.path.join(A.raiz, d)))
os.makedirs(A.salida, exist_ok=True)
print("variantes encontradas: %s" % ", ".join(variantes))

fila_ind = []
fila_bal = []
huella_rows = []
acum_rows = []
diam_rows = []

for v in variantes:
    D = leer(os.path.join(A.raiz, v))
    n = D["t"].size
    if n == 0:
        print("  %-16s sin impactos" % v)
        continue

    # ------------------------------------------------ ventana estacionaria
    # ventana SEMIABIERTA [t_estable, t_fin): si se incluyen los dos extremos se
    # cuenta un paso de mas y el caudal sale +1/n_pasos alto (era el +0,25 % inicial)
    sel = (D["t"] >= A.t_estable) & (D["t"] < A.t_fin)
    dt_v = A.t_fin - A.t_estable
    m_sel = D["masa"][sel]
    mdot = m_sel.sum() / dt_v

    # ------------------------------------------------ huella en la direccion del abanico
    # x es la direccion de apertura del abanico (= Z global, vertical, axial en la pared)
    xb = D["x"][sel]
    zb = D["z"][sel]
    paso = A.bin_mm * 1e-3
    xi = np.floor(xb / paso).astype(int)
    zi = np.floor(zb / paso).astype(int)
    # extremos por masa acumulada
    orden = np.argsort(xb)
    cum = np.cumsum(m_sel[orden]) / m_sel.sum()
    x05 = xb[orden][np.searchsorted(cum, 0.05)]
    x95 = xb[orden][np.searchsorted(cum, 0.95)]
    largo_total = xb.max() - xb.min()
    largo_90 = x95 - x05
    ancho_total = zb.max() - zb.min()
    largo_geom = 2 * Y_PLACA * math.tan(SEMIANG)

    # mapa phi(x, z) en kg/m2/s
    ux_, inv_x = np.unique(xi, return_inverse=True)
    uz_, inv_z = np.unique(zi, return_inverse=True)
    M = np.zeros((ux_.size, uz_.size))
    np.add.at(M, (inv_x, inv_z), m_sel)
    phi = M / (paso * paso) / dt_v
    # perfil por bin de x (integrado en z): es lo que alimenta D(Z)
    perfil = M.sum(axis=1) / dt_v            # kg/s por bin de x
    for k, ix in enumerate(ux_):
        huella_rows.append([v, "%.4f" % ((ix + 0.5) * paso * 1e3),
                            "%.6e" % perfil[k],
                            "%.6e" % (perfil[k] / (paso * max(ancho_total, paso)))])

    # ------------------------------------------------ impacto
    Usel = D["U"][sel]
    vmag = np.linalg.norm(Usel, axis=1)
    vnorm = np.abs(Usel[:, 1])                       # normal a la placa (y)
    vtan = np.linalg.norm(Usel[:, [0, 2]], axis=1)
    ang_inc = np.degrees(np.arctan2(vtan, vnorm))    # 0 = perpendicular
    dsel = D["d"][sel]
    We = RHO_L * vnorm ** 2 * dsel / SIGMA
    edad = D["age"][sel]

    # ---- masa acumulada frente a x, y su prediccion analitica ----------------
    # Si la masa es uniforme por unidad de angulo, la fraccion acumulada hasta x
    # vale F(x) = (atan(x/Y) + semiangulo) / (2*semiangulo). Es una comprobacion
    # de la geometria del abanico inmune al aliasing de los rayos discretos.
    q = np.linspace(0.0, 1.0, 201)
    xq = np.interp(q, cum, xb[orden])
    Fteo = (np.arctan(xq / Y_PLACA) + SEMIANG) / (2 * SEMIANG)
    for k in range(q.size):
        acum_rows.append([v, "%.4f" % (xq[k] * 1e3), "%.6f" % q[k], "%.6f" % Fteo[k]])
    err_acum = float(np.abs(q - Fteo).max())

    # ------------------------------------------------ hipotesis de una posicion de lanza
    t_vuelo = float(np.median(edad))
    arco_pared = OMEGA * R_PARED * t_vuelo * 1e3     # mm que recorre la pared
    arco_punta = OMEGA * R_PUNTA * t_vuelo * 1e3     # mm que recorre la boquilla
    desliz = abs(arco_pared - arco_punta)

    fila_ind.append(dict(
        variante=v, n_impactos=n, n_ventana=int(sel.sum()),
        mdot_kg_s="%.9g" % mdot, mdot_objetivo_kg_s="%.9g" % MDOT_OBJ,
        error_mdot_pct="%.4f" % (100 * (mdot - MDOT_OBJ) / MDOT_OBJ),
        huella_total_mm="%.2f" % (largo_total * 1e3),
        huella_90pct_mm="%.2f" % (largo_90 * 1e3),
        huella_geometrica_mm="%.2f" % (largo_geom * 1e3),
        error_huella_pct="%.2f" % (100 * (largo_total - largo_geom) / largo_geom),
        ancho_mm="%.3f" % (ancho_total * 1e3),
        t_vuelo_ms="%.4f" % (t_vuelo * 1e3),
        v_impacto_media_m_s="%.4f" % vmag.mean(),
        v_impacto_min_m_s="%.4f" % vmag.min(),
        v_impacto_max_m_s="%.4f" % vmag.max(),
        perdida_v_pct="%.2f" % (100 * (V_SAL - vmag.mean()) / V_SAL),
        ang_incidencia_max_deg="%.2f" % ang_inc.max(),
        We_media="%.1f" % We.mean(), We_max="%.1f" % We.max(),
        d_media_um="%.2f" % (dsel.mean() * 1e6),
        d32_um="%.2f" % ((dsel ** 3).sum() / (dsel ** 2).sum() * 1e6),
        d_min_um="%.2f" % (dsel.min() * 1e6), d_max_um="%.2f" % (dsel.max() * 1e6),
        giro_arco_pared_mm="%.4f" % arco_pared,
        giro_desliz_relativo_mm="%.4f" % desliz,
        giro_desliz_vs_ancho_pct="%.2f" % (100 * desliz * 1e-3 / max(ancho_total, 1e-9)),
        err_max_acumulada="%.5f" % err_acum,
        paso_entre_rayos_mm="%.3f" % (1e3 * largo_total / 59.0),
    ))

    # distribucion de diametros en el impacto (ponderada en masa)
    bins = np.linspace(0, 700e-6, 36)
    hm, _ = np.histogram(dsel, bins=bins, weights=m_sel)
    hm = hm / hm.sum()
    for k in range(len(bins) - 1):
        diam_rows.append([v, "%.1f" % (0.5 * (bins[k] + bins[k + 1]) * 1e6), "%.6f" % hm[k]])

    print("  %-16s %7d impactos | mdot=%.6g kg/s (%.3f %%) | huella=%.1f mm | vuelo=%.2f ms | v_imp=%.1f m/s"
          % (v, n, mdot, 100 * (mdot - MDOT_OBJ) / MDOT_OBJ, largo_total * 1e3,
             t_vuelo * 1e3, vmag.mean()))

# ------------------------------------------------------------------ escritura
def escribir(nombre, cabecera, filas):
    p = os.path.join(A.salida, nombre)
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cabecera)
        w.writerows(filas)
    print("escrito %s (%d filas)" % (p, len(filas)))


if fila_ind:
    cab = list(fila_ind[0].keys())
    escribir("F2_indicadores.csv", cab, [[r[k] for k in cab] for r in fila_ind])
escribir("F2_huella.csv", ["variante", "x_mm", "mdot_bin_kg_s", "phi_kg_m2_s"], huella_rows)
escribir("F2_huella_acumulada.csv",
         ["variante", "x_mm", "fraccion_masa_acumulada", "prediccion_uniforme_por_angulo"], acum_rows)
escribir("F2_diametros_impacto.csv", ["variante", "d_um", "fraccion_de_masa"], diam_rows)
