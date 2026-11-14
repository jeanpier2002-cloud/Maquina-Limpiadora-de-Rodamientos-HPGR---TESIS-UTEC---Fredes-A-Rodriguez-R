#!/usr/bin/env python3
"""
Posproceso de F4: de la lista de impactos en la pared del agujero a los
indicadores del plan maestro (seccion 4).

  1. phi(Z, theta)  flujo de deposicion, kg/(m2 s)
  2. D(Z)           dosis por vuelta, kg/m2, = integral de phi en theta dividida por omega
  3. cobertura(D_min) como CURVA, que es lo que pidio el usuario
  4. uniformidad: coeficiente de variacion de D(Z); zonas secas y con exceso
  5. solape: masa por boquilla, usando typeId (injectorID)

Geometria de la pared: cono 1:30 con r(z) = 0,450 + (z - 0,890)/60 m, z de 0,890
a 1,405 m. El elemento de area es dA = r(z) dtheta ds, con ds = dz/cos(alfa) y
alfa = atan(1/60) = 0,9548 grados, de modo que cos(alfa) = 0,99986.

Uso:
    python post_F4.py --raiz <carpeta con <caso>/impactos/*/pared_agujero.dat> --salida <carpeta>
"""
import argparse
import csv
import glob
import math
import os
import re

import numpy as np

P = argparse.ArgumentParser()
P.add_argument("--raiz", required=True)
P.add_argument("--salida", required=True)
P.add_argument("--t-estable", type=float, default=0.020,
               help="solo se promedia con impactos de t >= este valor")
P.add_argument("--t-fin", type=float, default=0.035)
P.add_argument("--dz-mm", type=float, default=5.0, help="bin en la cota Z, mm")
P.add_argument("--dtheta-deg", type=float, default=0.25, help="bin en acimut, grados")
A = P.parse_args()

Z_INF, Z_SUP = 0.890, 1.405
R_INF, CONIC = 0.450, 1.0 / 60.0        # radial
COS_ALFA = math.cos(math.atan(CONIC))
OMEGA = 0.1780235837034216              # rad/s, giro del distribuidor
T_VUELTA = 2 * math.pi / OMEGA          # 35,29 s
RHO_L = 982.1203530851709
SIGMA = 0.0662
TAGS = {1: "INT_1", 2: "INT_2", 3: "INT_3", 4: "INT_4", 5: "INT_5", 6: "INF_INT"}

# Orden real de las columnas, leido de la cabecera del propio archivo:
#   Time currentProc (position) origId typeId nParticle d (U) rho age
LIN = re.compile(r"^\s*([0-9.eE+-]+)\s+(\d+)\s+\(([^)]*)\)\s+(\d+)\s+(\d+)\s+"
                 r"([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+\(([^)]*)\)\s+"
                 r"([0-9.eE+-]+)\s+([0-9.eE+-]+)")


def r_pared(z):
    return R_INF + (z - Z_INF) * CONIC


def leer(d):
    t, px, py, pz, npart, dd, ux, uy, uz, rho, age, tid = ([] for _ in range(12))
    for f in sorted(glob.glob(os.path.join(d, "**", "pared_agujero.dat"), recursive=True)):
        for ln in open(f):
            if ln.startswith("#"):
                continue
            m = LIN.match(ln)
            if not m:
                continue
            t.append(float(m.group(1)))
            p = [float(v) for v in m.group(3).split()]
            px.append(p[0]); py.append(p[1]); pz.append(p[2])
            tid.append(int(m.group(5)))
            npart.append(float(m.group(6))); dd.append(float(m.group(7)))
            u = [float(v) for v in m.group(8).split()]
            ux.append(u[0]); uy.append(u[1]); uz.append(u[2])
            rho.append(float(m.group(9))); age.append(float(m.group(10)))
    o = dict(t=np.array(t), x=np.array(px), y=np.array(py), z=np.array(pz),
             nParticle=np.array(npart), d=np.array(dd),
             U=np.column_stack([ux, uy, uz]) if t else np.zeros((0, 3)),
             rho=np.array(rho), age=np.array(age), typeId=np.array(tid))
    o["masa"] = o["rho"] * o["nParticle"] * math.pi / 6.0 * o["d"] ** 3
    return o


casos = sorted(c for c in os.listdir(A.raiz) if os.path.isdir(os.path.join(A.raiz, c)))
os.makedirs(A.salida, exist_ok=True)
print("casos: %s" % ", ".join(casos))

res, dz_rows, cob_rows, boq_rows, mapa_rows, dzb_rows = [], [], [], [], [], []

for caso in casos:
    D = leer(os.path.join(A.raiz, caso))
    if D["t"].size == 0:
        print("  %-16s sin impactos" % caso)
        continue
    sel = (D["t"] >= A.t_estable) & (D["t"] < A.t_fin)
    dtv = A.t_fin - A.t_estable
    if sel.sum() == 0:
        print("  %-16s sin impactos en la ventana" % caso)
        continue
    m = D["masa"][sel]
    z = D["z"][sel]
    # acimut medido desde el plano de la lanza (+y), positivo hacia +x
    th = np.degrees(np.arctan2(D["x"][sel], D["y"][sel]))
    tid = D["typeId"][sel]
    mdot_dep = m.sum() / dtv

    # ---------------------------------------------------------- D(Z)
    dz = A.dz_mm * 1e-3
    # el ultimo borde se RECORTA en Z_SUP. Sin esto, cuando 515 mm no es multiplo
    # del bin, el ultimo bin sobresale del agujero, se le asigna area de mas y la
    # dosis minima y la cobertura salen falsamente bajas
    nb = int(math.ceil((Z_SUP - Z_INF) / dz))
    bordes = np.minimum(Z_INF + dz * np.arange(nb + 1), Z_SUP)
    anchos = np.diff(bordes)
    idx = np.clip(np.digitize(z, bordes) - 1, 0, bordes.size - 2)
    mband = np.zeros(bordes.size - 1)
    np.add.at(mband, idx, m)
    zc = 0.5 * (bordes[:-1] + bordes[1:])
    rc = r_pared(zc)
    area_band = 2 * math.pi * rc * anchos / COS_ALFA       # area real de cada banda
    mdot_band = mband / dtv                                # kg/s en cada banda
    # dosis por vuelta: toda la masa de la banda se reparte sobre la banda entera
    # al cabo de una vuelta, de modo que D(Z) = mdot_banda * T_vuelta / area_banda
    Dz = mdot_band * T_VUELTA / area_band                  # kg/m2 por vuelta
    phi_media = mdot_band / area_band                      # kg/(m2 s) promediada en acimut

    for k in range(zc.size):
        dz_rows.append([caso, "%.2f" % (zc[k] * 1e3), "%.6e" % mdot_band[k],
                        "%.6e" % phi_media[k], "%.6f" % Dz[k], "%.6f" % area_band[k]])

    # ---------------------------------------------------------- cobertura(D_min)
    area_tot = area_band.sum()
    for Dm in np.concatenate([np.logspace(-2, 1.4, 60), [0.1, 1.0, 5.0]]):
        cub = area_band[Dz >= Dm].sum()
        cob_rows.append([caso, "%.4f" % Dm, "%.4f" % (100 * cub / area_tot)])

    # ---------------------------------------------------------- uniformidad
    conmasa = Dz > 0
    cv = float(np.std(Dz[conmasa]) / np.mean(Dz[conmasa])) if conmasa.sum() > 1 else float("nan")
    media_pond = float((Dz * area_band).sum() / area_tot)
    secas = area_band[Dz <= 1e-9].sum() / area_tot
    exceso = area_band[Dz > 2 * media_pond].sum() / area_tot

    # ---------------------------------------------------------- por boquilla
    for t_ in sorted(set(tid.tolist())):
        s = tid == t_
        zz = z[s]
        boq_rows.append([caso, TAGS.get(t_, str(t_)), int(s.sum()),
                         "%.6e" % (m[s].sum() / dtv),
                         "%.2f" % (100 * m[s].sum() / m.sum()),
                         "%.2f" % (zz.min() * 1e3), "%.2f" % (zz.max() * 1e3)])

    # ------------------------------------------- D(Z) descompuesta por boquilla
    # Es el indicador 5 del plan (solape): cuanto pone cada boquilla en cada cota.
    for t_ in sorted(set(tid.tolist())):
        s_ = tid == t_
        mb = np.zeros(bordes.size - 1)
        np.add.at(mb, idx[s_], m[s_])
        Dzb = mb / dtv * T_VUELTA / area_band
        for k in range(zc.size):
            if Dzb[k] > 0:
                dzb_rows.append([caso, TAGS.get(t_, str(t_)), "%.2f" % (zc[k] * 1e3),
                                 "%.6f" % Dzb[k]])

    # ---------------------------------------------------------- mapa phi(Z,theta)
    dth = A.dtheta_deg
    tb = np.arange(-6.0, 6.0 + dth, dth)
    ti = np.clip(np.digitize(th, tb) - 1, 0, tb.size - 2)
    M2 = np.zeros((bordes.size - 1, tb.size - 1))
    np.add.at(M2, (idx, ti), m)
    thc = 0.5 * (tb[:-1] + tb[1:])
    for i in range(zc.size):
        dA = rc[i] * math.radians(dth) * anchos[i] / COS_ALFA
        for j in range(thc.size):
            if M2[i, j] > 0:
                mapa_rows.append([caso, "%.2f" % (zc[i] * 1e3), "%.3f" % thc[j],
                                  "%.6e" % (M2[i, j] / dtv / dA)])

    # ---------------------------------------------------------- impacto
    U = D["U"][sel]
    n = np.column_stack([D["x"][sel], D["y"][sel], np.zeros_like(z)])
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    vn = np.abs((U * n).sum(axis=1))
    We = RHO_L * vn ** 2 * D["d"][sel] / SIGMA

    res.append(dict(
        caso=caso, n_impactos=int(D["t"].size), n_ventana=int(sel.sum()),
        mdot_depositado_kg_s="%.6f" % mdot_dep,
        dosis_media_kg_m2_vuelta="%.4f" % media_pond,
        dosis_max_kg_m2_vuelta="%.4f" % Dz.max(),
        dosis_min_kg_m2_vuelta="%.4f" % Dz.min(),
        CV_de_Dz="%.4f" % cv,
        area_seca_pct="%.3f" % (100 * secas),
        area_exceso_pct="%.3f" % (100 * exceso),
        cobertura_Dmin_0p1_pct="%.2f" % (100 * area_band[Dz >= 0.1].sum() / area_tot),
        cobertura_Dmin_1_pct="%.2f" % (100 * area_band[Dz >= 1.0].sum() / area_tot),
        cobertura_Dmin_5_pct="%.2f" % (100 * area_band[Dz >= 5.0].sum() / area_tot),
        z_min_mojado_mm="%.2f" % (z.min() * 1e3), z_max_mojado_mm="%.2f" % (z.max() * 1e3),
        ancho_acimutal_deg="%.3f" % (th.max() - th.min()),
        v_impacto_media="%.3f" % np.linalg.norm(U, axis=1).mean(),
        We_media="%.1f" % We.mean(), We_max="%.1f" % We.max(),
        t_vuelo_ms="%.3f" % (np.median(D["age"][sel]) * 1e3),
        area_pared_m2="%.6f" % area_tot,
    ))
    print("  %-16s %8d impactos | mdot=%.6f kg/s | D media=%.2f kg/m2 vuelta | CV=%.3f | seca=%.2f %%"
          % (caso, D["t"].size, mdot_dep, media_pond, cv, 100 * secas))


def esc(nombre, cab, filas):
    p = os.path.join(A.salida, nombre)
    with open(p, "w", newline="") as f:
        w = csv.writer(f); w.writerow(cab); w.writerows(filas)
    print("escrito %s (%d filas)" % (p, len(filas)))


if res:
    cab = list(res[0].keys())
    esc("F4_indicadores.csv", cab, [[r[k] for k in cab] for r in res])
esc("F4_dosis_por_Z.csv",
    ["caso", "z_mm", "mdot_banda_kg_s", "phi_medio_kg_m2_s", "D_kg_m2_vuelta", "area_banda_m2"], dz_rows)
esc("F4_cobertura.csv", ["caso", "D_min_kg_m2_vuelta", "cobertura_pct"], cob_rows)
esc("F4_por_boquilla.csv",
    ["caso", "boquilla", "impactos", "mdot_kg_s", "porcentaje_de_la_masa", "z_min_mm", "z_max_mm"], boq_rows)
esc("F4_dosis_por_Z_boquilla.csv",
    ["caso", "boquilla", "z_mm", "D_kg_m2_vuelta"], dzb_rows)
esc("F4_mapa_phi.csv", ["caso", "z_mm", "theta_deg", "phi_kg_m2_s"], mapa_rows)
