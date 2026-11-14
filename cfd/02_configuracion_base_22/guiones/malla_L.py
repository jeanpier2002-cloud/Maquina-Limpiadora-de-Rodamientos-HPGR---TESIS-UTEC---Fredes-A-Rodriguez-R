#!/usr/bin/env python3
"""
Mallas hexaedricas de sector polar con celdas enmascaradas (CFD03): OD + cara inferior (E-OD completo con
INF_EXT), sector de INF_INT bajo el aro, y variante con PAD de la mesa (G5).

Superficies analiticas del rodamiento (R05 CTX_BEARING_REFERENCE, medido en G1: OD cilindro R 710,
agujero cilindro R 450, caras planas Z 890 y 1405; mm). Las celdas cuyo centro cae dentro de un solido
(aro o PAD) se eliminan; cada cara de frontera se clasifica sondeando un punto justo fuera de ella:
  dentro del aro  -> 'od' (r = 0,710), 'cara_inf' (z = 0,890; 'inf' no: Fluent lo renombra 'zone-inf'), 'agujero' (r = 0,450)   [pared, trap]
  dentro de un PAD -> 'pad'                                                        [pared, trap]
  en otro caso     -> fronteras abiertas (pressure-outlet), por posicion.
Ejes: i = r, j = theta (grados, 0 en +X, antihorario, sector [tc - semi, tc + semi]), k = z.

Tipos:
  odinf : r [r_in, r_ext], z [z_bot, z_top]; aire en r >= 0,710 (todo z) y bajo el aro (z < 0,890).
          Sobre la cara superior (r < 0,710, z > 1,405) no se malla: 'abierto_interior' (igual que CFD02).
  int   : sector de INF_INT: r [r_in, r_ext], z [z_bot, z_top]; aro enmascarado (0,450 <= r <= 0,710,
          z >= 0,890); el aire del agujero (r < 0,450) si se malla.
PAD (opcional, --pad tc_deg, repetible): cap+liner = sector anular r 0,638-0,688, theta tc +- 12, z 0,850-0,890;
base = caja local x' 0,583-0,743, y' +-0,070, z 0,805-0,850 (R05 CTX_PAD_01, medido en G1). [INTERFAZ ISMAEL]

Uso: python malla_L.py --tipo odinf --salida m.msh --tc 0 --semi 12 --r 0.45 0.95 --z 0.80 1.45 \
        [--dr 0.004 --dth 0.5 --dz 0.005] [--pad 0]
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from msh_writer import write_hex_cells  # noqa: E402

R_OD, R_AG, Z0, Z1 = 0.710, 0.450, 0.890, 1.405
PAD_R, PAD_Z, PAD_HW = (0.638, 0.688), (0.850, 0.890), 12.0
BASE_X, BASE_Y, BASE_Z = (0.583, 0.743), 0.070, (0.805, 0.850)


def tramo(a, b, h):
    n = max(1, int(round((b - a) / h)))
    return np.linspace(a, b, n + 1)


def nodos(a, b, h, cortes):
    c = sorted({a, b} | {q for q in cortes if a + 1e-9 < q < b - 1e-9})
    return np.concatenate([tramo(c[i], c[i + 1], h)[(1 if i else 0):] for i in range(len(c) - 1)])


def en_aro(r, z, tipo):
    if tipo == "odinf":
        return (r < R_OD) & (z > Z0)
    return (r > R_AG) & (r < R_OD) & (z > Z0) & (z < Z1)


def en_pad(x, y, z, pads):
    r = np.hypot(x, y)
    th = np.degrees(np.arctan2(y, x))
    out = np.zeros(len(r), bool)
    for tc in pads:
        d = (th - tc + 180.0) % 360.0 - 180.0
        out |= (r > PAD_R[0]) & (r < PAD_R[1]) & (np.abs(d) < PAD_HW) & (z > PAD_Z[0]) & (z < PAD_Z[1])
        c, s = np.cos(np.radians(tc)), np.sin(np.radians(tc))
        xl, yl = c * x + s * y, -s * x + c * y
        out |= (xl > BASE_X[0]) & (xl < BASE_X[1]) & (np.abs(yl) < BASE_Y) & (z > BASE_Z[0]) & (z < BASE_Z[1])
    return out


def construir(a):
    cr = [R_AG, R_OD] + ([PAD_R[0], PAD_R[1], BASE_X[0], BASE_X[1]] if a.pad else [])
    cz = [Z0, Z1] + ([PAD_Z[0], BASE_Z[0]] if a.pad else [])
    r = nodos(a.r[0], a.r[1], a.dr, cr)
    z = nodos(a.z[0], a.z[1], a.dz, cz)
    ct = [p + s * PAD_HW for p in a.pad for s in (-1, 1)]
    th = np.radians(nodos(a.tc - a.semi, a.tc + a.semi, a.dth, ct))
    ni, nj, nk = len(r), len(th), len(z)
    I, J, K = np.meshgrid(np.arange(ni), np.arange(nj), np.arange(nk), indexing="ij")
    nodes = np.stack([r[I] * np.cos(th[J]), r[I] * np.sin(th[J]), z[K]], -1).transpose(2, 1, 0, 3).reshape(-1, 3)
    nid = lambda i, j, k: i + ni * (j + nj * k)
    ci, cj, ck = [q.ravel() for q in np.meshgrid(np.arange(ni - 1), np.arange(nj - 1), np.arange(nk - 1), indexing="ij")]
    cells = np.stack([nid(ci, cj, ck), nid(ci + 1, cj, ck), nid(ci + 1, cj + 1, ck), nid(ci, cj + 1, ck),
                      nid(ci, cj, ck + 1), nid(ci + 1, cj, ck + 1), nid(ci + 1, cj + 1, ck + 1),
                      nid(ci, cj + 1, ck + 1)], -1)
    rc = 0.5 * (r[ci] + r[ci + 1])
    zc = 0.5 * (z[ck] + z[ck + 1])
    tcen = 0.5 * (th[cj] + th[cj + 1])
    # motivo de enmascarado por celda de la rejilla: 0 aire, 1 aro, 2 PAD (lo usa el clasificador)
    motivo = np.where(en_aro(rc, zc, a.tipo), 1, 0)
    if a.pad:
        motivo = np.where((motivo == 0) & en_pad(rc * np.cos(tcen), rc * np.sin(tcen), zc, a.pad), 2, motivo)
    REJILLA.update(r=r, th=th, z=z, motivo=motivo.reshape(ni - 1, nj - 1, nk - 1))
    fuera = motivo > 0
    cells = cells[~fuera]
    used = np.unique(cells)
    remap = -np.ones(len(nodes), np.int64)
    remap[used] = np.arange(len(used))
    nodes, cells = nodes[used], remap[cells]
    info = dict(tipo=a.tipo, tc_deg=a.tc, semi_deg=a.semi, r_m=list(a.r), z_m=list(a.z), pad_deg=a.pad,
                ni=ni, nj=nj, nk=nk, celdas=int(len(cells)), celdas_enmascaradas=int(fuera.sum()),
                dr_max_m=float(np.diff(r).max()), dth_max_deg=float(np.degrees(np.diff(th).max())),
                dz_max_m=float(np.diff(z).max()))
    return nodes, cells, info


REJILLA = {}


def clasificador(a):
    def f(c, n):
        g = REJILLA
        # celda vecina al otro lado de la cara: sonda a 1/4 de la celda mas pequena, en (r, theta, z)
        h = 0.25 * min(np.diff(g["r"]).min(), np.diff(g["z"]).min())
        p = c + h * n
        rp, zp = np.hypot(p[:, 0], p[:, 1]), p[:, 2]
        tp = np.radians(a.tc + ((np.degrees(np.arctan2(p[:, 1], p[:, 0])) - a.tc + 180.0) % 360.0 - 180.0))
        ii = np.searchsorted(g["r"], rp) - 1
        jj = np.searchsorted(g["th"], tp) - 1
        kk = np.searchsorted(g["z"], zp) - 1
        M = g["motivo"]
        dentro = (ii >= 0) & (ii < M.shape[0]) & (jj >= 0) & (jj < M.shape[1]) & (kk >= 0) & (kk < M.shape[2])
        mot = np.full(len(c), -1)
        mot[dentro] = M[ii[dentro], jj[dentro], kk[dentro]]
        rc, zc = np.hypot(c[:, 0], c[:, 1]), c[:, 2]
        out = np.full(len(c), "SIN_CLASIFICAR", dtype=object)
        # fuera de la rejilla: fronteras del dominio por la direccion de la normal saliente
        nr = (n[:, 0] * c[:, 0] + n[:, 1] * c[:, 1]) / rc
        fr = mot == -1
        out[fr & (n[:, 2] < -0.9)] = "abierto_inferior"
        out[fr & (n[:, 2] > 0.9)] = "abierto_superior"
        out[fr & (np.abs(nr) < 0.1) & (np.abs(n[:, 2]) < 0.1)] = "abierto_lateral"
        out[fr & (nr > 0.9)] = "abierto_exterior"
        out[fr & (nr < -0.9)] = "abierto_interior" if a.tipo == "int" else "abierto_agujero"
        # paredes del aro (tolerancia 0,1 mm: la cara plana queda dentro del arco por la flecha de la cuerda)
        aro = mot == 1
        out[aro & (np.abs(rc - R_OD) < 1e-4)] = "od"
        out[aro & (np.abs(zc - Z0) < 1e-7)] = "cara_inf"
        out[aro & (np.abs(rc - R_AG) < 1e-4)] = "agujero"
        if a.tipo == "odinf":           # sobre la cara superior no se malla (CFD02: abierto_interior)
            out[aro & (np.abs(rc - R_OD) < 1e-4) & (zc > Z1)] = "abierto_interior"
        out[mot == 2] = "pad"
        if (out == "SIN_CLASIFICAR").any():
            bad = c[out == "SIN_CLASIFICAR"][:5]
            raise ValueError("caras sin clasificar: %d, p. ej. %s" % ((out == "SIN_CLASIFICAR").sum(), bad))
        return out
    return f


TIPOS = {"od": "wall", "cara_inf": "wall", "agujero": "wall", "pad": "wall",
         "abierto_inferior": "pressure-outlet", "abierto_superior": "pressure-outlet",
         "abierto_lateral": "pressure-outlet", "abierto_exterior": "pressure-outlet",
         "abierto_interior": "pressure-outlet", "abierto_agujero": "pressure-outlet"}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tipo", choices=["odinf", "int"], required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--tc", type=float, default=0.0, help="centro del sector (grados)")
    ap.add_argument("--semi", type=float, default=12.0, help="semiancho del sector (grados)")
    ap.add_argument("--r", nargs=2, type=float, required=True)
    ap.add_argument("--z", nargs=2, type=float, required=True)
    ap.add_argument("--dr", type=float, default=0.004)
    ap.add_argument("--dth", type=float, default=0.5)
    ap.add_argument("--dz", type=float, default=0.005)
    ap.add_argument("--pad", type=float, action="append", default=[], help="centro de un PAD (grados)")
    a = ap.parse_args()
    nodes, cells, info = construir(a)
    if info["celdas"] >= 1048576:
        raise SystemExit("excede el limite Student: %d celdas" % info["celdas"])
    info.update(write_hex_cells(a.salida, nodes, cells, clasificador(a), TIPOS, title="CFD03 " + a.tipo))
    json.dump(info, open(os.path.splitext(a.salida)[0] + "_info.json", "w"), indent=1)
    print(json.dumps(info, indent=1))
