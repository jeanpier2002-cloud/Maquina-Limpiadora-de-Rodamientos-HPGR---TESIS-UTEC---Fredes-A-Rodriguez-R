#!/usr/bin/env python3
"""
Malla hexaedrica de un sector cilindrico para los estudios exteriores (F6, F7 E-OD).

Superficies analiticas desde R05 (decision D3 de MODO_AUTONOMO.md):
  OD del aro = cilindro R = 0,710 m, Z 0,890-1,405 m. Sin PAD, topes, mesa ni tubos del rotor.

Dominio: r en [R_OD, r_ext], theta en [th0, th1] (grados; theta = 0 en +X, antihorario),
z en [z0, z1]. La frontera interior r = R_OD es pared 'od' (trap) donde 0,890 <= z <= 1,405
y abierta ('abierto_interior') fuera de ese tramo (debajo: mesa/PAD no modelados; encima: aire
sobre la cara superior). Resto de fronteras: abiertas (pressure-outlet).

Uso: python malla_sector.py --salida s.msh --th -15 15 --z 0.85 1.50 --r-ext 0.95
       [--dr 0.004] [--dth 0.5] [--dz 0.005] [--dr-crec 1.0]
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from msh_writer import write_hex_cells  # noqa: E402

R_OD, Z0, Z1 = 0.710, 0.890, 1.405
R_AG = 0.450 + (1.405 - 0.890) / 60.0     # radio del agujero en la cara superior (0,45858 m)


def tramo(a, b, h):
    n = max(1, int(round((b - a) / h)))
    return np.linspace(a, b, n + 1)


def nodos_z(z0, z1, h):
    """Nodos en z que contienen exactamente 0,890 y 1,405 si caen en el rango."""
    cortes = sorted({z0, z1} | {q for q in (Z0, Z1) if z0 < q < z1})
    return np.concatenate([tramo(cortes[i], cortes[i + 1], h)[(1 if i else 0):] for i in range(len(cortes) - 1)])


def nodos_r(r0, r1, h):
    cortes = sorted({r0, r1} | {q for q in (R_AG, R_OD) if r0 < q < r1})
    return np.concatenate([tramo(cortes[i], cortes[i + 1], h)[(1 if i else 0):] for i in range(len(cortes) - 1)])


def construir(a):
    if a.tipo == "sup":
        return construir_sup(a)
    r = tramo(R_OD, a.r_ext, a.dr)
    if a.dr_crec != 1.0:   # crecimiento geometrico desde la pared
        n = len(r) - 1
        g = a.dr_crec
        w = g ** np.arange(n)
        r = R_OD + (a.r_ext - R_OD) * np.concatenate([[0], np.cumsum(w) / w.sum()])
    th = np.radians(tramo(a.th[0], a.th[1], a.dth))
    z = nodos_z(a.z[0], a.z[1], a.dz)
    ni, nj, nk = len(r), len(th), len(z)
    I, J, K = np.meshgrid(np.arange(ni), np.arange(nj), np.arange(nk), indexing="ij")
    nodes = np.stack([r[I] * np.cos(th[J]), r[I] * np.sin(th[J]), z[K]], -1).transpose(2, 1, 0, 3).reshape(-1, 3)
    nid = lambda i, j, k: i + ni * (j + nj * k)
    ci, cj, ck = [q.ravel() for q in np.meshgrid(np.arange(ni - 1), np.arange(nj - 1), np.arange(nk - 1), indexing="ij")]
    cells = np.stack([nid(ci, cj, ck), nid(ci + 1, cj, ck), nid(ci + 1, cj + 1, ck), nid(ci, cj + 1, ck),
                      nid(ci, cj, ck + 1), nid(ci + 1, cj, ck + 1), nid(ci + 1, cj + 1, ck + 1),
                      nid(ci, cj + 1, ck + 1)], -1)
    info = dict(ni=ni, nj=nj, nk=nk, celdas=int(len(cells)), dr_pared_m=float(r[1] - r[0]),
                dth_deg=float(np.degrees(th[1] - th[0])), dz_m=float(z[1] - z[0]),
                th_deg=list(a.th), z_m=list(a.z), r_ext_m=a.r_ext)
    return nodes, cells, info


def construir_sup(a):
    """E-SUP: aire sobre la cara superior del aro. r en [r_in, r_ext], z en [Z1, z1]."""
    r = nodos_r(a.r_in, a.r_ext, a.dr)
    th = np.radians(tramo(a.th[0], a.th[1], a.dth))
    z = tramo(Z1, a.z[1], a.dz)
    ni, nj, nk = len(r), len(th), len(z)
    I, J, K = np.meshgrid(np.arange(ni), np.arange(nj), np.arange(nk), indexing="ij")
    nodes = np.stack([r[I] * np.cos(th[J]), r[I] * np.sin(th[J]), z[K]], -1).transpose(2, 1, 0, 3).reshape(-1, 3)
    nid = lambda i, j, k: i + ni * (j + nj * k)
    ci, cj, ck = [q.ravel() for q in np.meshgrid(np.arange(ni - 1), np.arange(nj - 1), np.arange(nk - 1), indexing="ij")]
    cells = np.stack([nid(ci, cj, ck), nid(ci + 1, cj, ck), nid(ci + 1, cj + 1, ck), nid(ci, cj + 1, ck),
                      nid(ci, cj, ck + 1), nid(ci + 1, cj, ck + 1), nid(ci + 1, cj + 1, ck + 1),
                      nid(ci, cj + 1, ck + 1)], -1)
    info = dict(tipo="sup", ni=ni, nj=nj, nk=nk, celdas=int(len(cells)), dr_m=float(np.diff(r).max()),
                dth_deg=float(np.degrees(th[1] - th[0])), dz_m=float(z[1] - z[0]), th_deg=list(a.th),
                z_m=[Z1, a.z[1]], r_m=[a.r_in, a.r_ext])
    return nodes, cells, info


def clasificador_sup(a):
    def f(c, n):
        r = np.hypot(c[:, 0], c[:, 1])
        z = c[:, 2]
        nr = (n[:, 0] * c[:, 0] + n[:, 1] * c[:, 1]) / r
        out = np.full(len(c), "SIN_CLASIFICAR", dtype=object)
        abajo = (n[:, 2] < -0.99) & (z < Z1 + 1e-7)
        out[abajo] = "abierto_inferior"
        out[abajo & (r > R_AG) & (r < R_OD)] = "sup"
        out[(n[:, 2] > 0.99)] = "abierto_superior"
        out[(np.abs(nr) < 0.1) & (np.abs(n[:, 2]) < 0.1)] = "abierto_lateral"
        out[(nr > 0.9) & (r > 0.99 * a.r_ext)] = "abierto_exterior"
        out[(nr < -0.9) & (r < a.r_in * 1.001)] = "abierto_interior"
        if (out == "SIN_CLASIFICAR").any():
            raise ValueError("caras sin clasificar: %d" % (out == "SIN_CLASIFICAR").sum())
        return out
    return f


def clasificador(a):
    if a.tipo == "sup":
        return clasificador_sup(a)
    th0, th1 = np.radians(a.th)

    def f(c, n):
        r = np.hypot(c[:, 0], c[:, 1])
        th = np.arctan2(c[:, 1], c[:, 0])
        z = c[:, 2]
        nr = (n[:, 0] * c[:, 0] + n[:, 1] * c[:, 1]) / r
        out = np.full(len(c), "SIN_CLASIFICAR", dtype=object)
        tol = 1e-7
        out[np.abs(n[:, 2]) > 0.99] = np.where(z[np.abs(n[:, 2]) > 0.99] < 0.5 * (a.z[0] + a.z[1]),
                                               "abierto_inferior", "abierto_superior")
        lat = (np.abs(nr) < 0.1) & (np.abs(n[:, 2]) < 0.1)
        out[lat] = "abierto_lateral"
        out[(nr > 0.9) & (r > 0.99 * a.r_ext)] = "abierto_exterior"
        inner = (nr < -0.9) & (r < R_OD * 1.001)
        out[inner] = "abierto_interior"
        out[inner & (z > Z0 - tol) & (z < Z1 + tol)] = "od"
        if (out == "SIN_CLASIFICAR").any():
            raise ValueError("caras sin clasificar: %d" % (out == "SIN_CLASIFICAR").sum())
        return out
    return f


TIPOS = {"od": "wall", "sup": "wall", "abierto_interior": "pressure-outlet", "abierto_exterior": "pressure-outlet",
         "abierto_lateral": "pressure-outlet", "abierto_inferior": "pressure-outlet",
         "abierto_superior": "pressure-outlet"}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--th", nargs=2, type=float, required=True)
    ap.add_argument("--z", nargs=2, type=float, required=True)
    ap.add_argument("--r-ext", type=float, default=0.95)
    ap.add_argument("--r-in", type=float, default=0.40, help="solo tipo sup")
    ap.add_argument("--tipo", choices=["od", "sup"], default="od")
    ap.add_argument("--dr", type=float, default=0.004)
    ap.add_argument("--dr-crec", type=float, default=1.0)
    ap.add_argument("--dth", type=float, default=0.5)
    ap.add_argument("--dz", type=float, default=0.005)
    a = ap.parse_args()
    nodes, cells, info = construir(a)
    if info["celdas"] >= 1048576:
        raise SystemExit("excede el limite Student: %d celdas" % info["celdas"])
    info.update(write_hex_cells(a.salida, nodes, cells, clasificador(a), TIPOS, title="sector " + a.tipo))
    json.dump(info, open(os.path.splitext(a.salida)[0] + "_info.json", "w"), indent=1)
    print(json.dumps(info, indent=1))
