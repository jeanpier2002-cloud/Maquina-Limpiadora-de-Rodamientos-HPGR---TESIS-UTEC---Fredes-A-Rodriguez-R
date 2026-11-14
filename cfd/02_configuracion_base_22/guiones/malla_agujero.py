#!/usr/bin/env python3
"""
Malla hexaedrica polar del caso puente F5 (interior de la rama B en Fluent).

Dominio (equivalente al de la rama B, F4_S2, ver ESTADO.md supuestos S4-S6):
  - Agujero conico 1:30: r_cono(z) = 0,450 + (z - 0,890)/60, z en [0,890; 1,405]
    (misma ley que post_kpi.py --superficie cono y post_F4.py).
  - Franjas abiertas bajo (z 0,790-0,890) y sobre (z 1,405-1,445) el aro, hasta
    R_ext = 0,55 m. La rama B usa una caja de 1,0 x 1,0 m (|x|,|y| <= 0,5); aqui un
    cilindro de 0,55 m (SUPUESTO S5: las esquinas de la caja no reciben gotas).
  - Nucleo r < r_in abierto (frontera pressure-outlet 'nucleo_abierto', SUPUESTO S4):
    evita la singularidad del eje en una malla polar.
  - Lanza: celdas cuyo centro cae dentro de lanza.stl de la rama B se eliminan
    (pared escalonada 'lanza').
  - Direcciones: i = radio, j = acimut (cerrado, 360 grados), k = z.
    Acimut refinado alrededor de theta = 90 grados (plano de la lanza, x = 0, y > 0).

Uso: python malla_agujero.py --salida caso.msh [--nivel base|fina|gruesa] [--stl lanza.stl]
"""
import argparse
import json
import os
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from msh_writer import write_hex_cells  # noqa: E402

Z0, Z1 = 0.890, 1.405           # caras del aro
ZB, ZT = 0.790, 1.445           # extremos del dominio (rama B, blockMeshDict)
R_EXT = 0.55


def r_cono(z):
    return 0.450 + (np.clip(z, Z0, Z1) - Z0) / 60.0


NIVELES = {
    # dth_fino (grados), semiancho_fino, crecimiento, dth_max; dr fino (m); dz (m)
    "gruesa": dict(dth=1.0, th_fino=10.0, g=1.18, dth_max=12.0, dr=0.0065, dz=0.0075, r_in=0.10),
    "base":   dict(dth=0.8, th_fino=10.0, g=1.15, dth_max=10.0, dr=0.0050, dz=0.0060, r_in=0.10),
    "fina":   dict(dth=0.63, th_fino=10.0, g=1.12, dth_max=8.0, dr=0.0040, dz=0.0048, r_in=0.10),
}


def dist_theta(p):
    """Nodos de acimut en grados, simetricos respecto de 90, cerrados (sin repetir 360)."""
    half = [0.0]
    while half[-1] < p["th_fino"] - 1e-9:
        half.append(half[-1] + p["dth"])
    d = p["dth"]
    while half[-1] < 180.0:
        d = min(d * p["g"], p["dth_max"])
        half.append(half[-1] + d)
    half = np.array(half)
    half = half * (180.0 / half[-1])            # ajusta para cerrar exactamente en 180
    ang = np.concatenate([90.0 - half[::-1], 90.0 + half[1:-1]])
    return np.sort(np.mod(ang, 360.0))


def tramo(a, b, h):
    n = max(1, int(round((b - a) / h)))
    return np.linspace(a, b, n + 1)


def lee_stl(path):
    b = open(path, "rb").read()
    if b[:5] == b"solid" and b"facet" in b[:300]:
        v = np.array([list(map(float, l.split()[1:4])) for l in b.decode().splitlines()
                      if l.strip().startswith("vertex")])
        return v.reshape(-1, 3, 3)
    n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + 50 * n], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(float)


def dentro_stl(pts, tri):
    """Paridad de cruces de un rayo +x (prueba punto-en-solido cerrado)."""
    inside = np.zeros(len(pts), bool)
    A, B, C = tri[:, 0], tri[:, 1], tri[:, 2]
    for s in range(0, len(pts), 256):
        p = pts[s:s + 256]
        py, pz = p[:, 1:2], p[:, 2:3]
        # coordenadas baricentricas en el plano yz
        d = (B[:, 1] - A[:, 1]) * (C[:, 2] - A[:, 2]) - (C[:, 1] - A[:, 1]) * (B[:, 2] - A[:, 2])
        ok = np.abs(d) > 1e-18
        u = ((py - A[:, 1]) * (C[:, 2] - A[:, 2]) - (C[:, 1] - A[:, 1]) * (pz - A[:, 2])) / np.where(ok, d, 1)
        w = ((B[:, 1] - A[:, 1]) * (pz - A[:, 2]) - (py - A[:, 1]) * (B[:, 2] - A[:, 2])) / np.where(ok, d, 1)
        hit = ok & (u >= 0) & (w >= 0) & (u + w <= 1)
        x = A[:, 0] + u * (B[:, 0] - A[:, 0]) + w * (C[:, 0] - A[:, 0])
        hit &= x > p[:, 0:1]
        inside[s:s + 256] = (hit.sum(1) % 2) == 1
    return inside


def construir(nivel, stl):
    p = NIVELES[nivel]
    th = np.radians(dist_theta(p))
    nj = len(th)
    # radios "de referencia" (en z donde r_cono = 0,450); por encima de 0,30 se escalan con r_cono(z)
    r_a = tramo(p["r_in"], 0.22, 2.5 * p["dr"])
    r_b = tramo(0.22, 0.30, p["dr"])
    s_c = tramo(0.0, 1.0, p["dr"] / 0.15)[1:]           # fraccion entre 0,30 y r_cono
    s_d = tramo(0.0, 1.0, 2.0 * p["dr"] / 0.10)[1:]     # fraccion entre r_cono y R_EXT
    ni_fix = len(r_a) + len(r_b) - 1
    zs = np.concatenate([tramo(ZB, Z0, p["dz"]), tramo(Z0, Z1, p["dz"])[1:], tramo(Z1, ZT, 1.4 * p["dz"])[1:]])
    nk = len(zs)
    ni = ni_fix + len(s_c) + len(s_d)
    rfix = np.concatenate([r_a, r_b[1:]])
    R = np.zeros((ni, nk))
    for k, z in enumerate(zs):
        rc = r_cono(z)
        R[:, k] = np.concatenate([rfix, 0.30 + (rc - 0.30) * s_c, rc + (R_EXT - rc) * s_d])
    i_cono = ni_fix + len(s_c) - 1          # indice del anillo de nodos sobre r_cono
    # nodos (i, j, k) -> id
    I, J, K = np.meshgrid(np.arange(ni), np.arange(nj), np.arange(nk), indexing="ij")
    nid = lambda i, j, k: i + ni * ((j % nj) + nj * k)
    Rr = R[I, K]
    nodes = np.stack([Rr * np.cos(th[J]), Rr * np.sin(th[J]), zs[K]], -1).transpose(2, 1, 0, 3).reshape(-1, 3)
    # celdas
    ci, cj, ck = np.meshgrid(np.arange(ni - 1), np.arange(nj), np.arange(nk - 1), indexing="ij")
    ci, cj, ck = ci.ravel(), cj.ravel(), ck.ravel()
    cells = np.stack([nid(ci, cj, ck), nid(ci + 1, cj, ck), nid(ci + 1, cj + 1, ck), nid(ci, cj + 1, ck),
                      nid(ci, cj, ck + 1), nid(ci + 1, cj, ck + 1), nid(ci + 1, cj + 1, ck + 1),
                      nid(ci, cj + 1, ck + 1)], -1)
    zc = 0.5 * (zs[ck] + zs[ck + 1])
    solido_aro = (ci >= i_cono) & (zc > Z0) & (zc < Z1)
    cen = nodes[cells].mean(1)
    lanza = np.zeros(len(cells), bool)
    if stl:
        tri = lee_stl(stl)
        lo, hi = tri.reshape(-1, 3).min(0) - 1e-3, tri.reshape(-1, 3).max(0) + 1e-3
        cand = np.where(np.all((cen >= lo) & (cen <= hi), 1) & ~solido_aro)[0]
        jit = np.array([0.0, 1.3e-7, 0.7e-7])
        lanza[cand] = dentro_stl(cen[cand] + jit, tri)
    keep = ~(solido_aro | lanza)
    cells = cells[keep]
    used = np.unique(cells)
    remap = -np.ones(len(nodes), np.int64)
    remap[used] = np.arange(len(used))
    nodes = nodes[used]
    cells = remap[cells]
    info = dict(nivel=nivel, ni=ni, nj=nj, nk=nk, celdas=int(len(cells)), celdas_lanza=int(lanza.sum()),
                dth_min_deg=float(np.degrees(np.diff(th).min())), dth_max_deg=float(np.degrees(np.diff(th).max())),
                dr_fino_m=p["dr"], dz_m=p["dz"], r_in_m=p["r_in"], R_ext_m=R_EXT)
    return nodes, cells, info


def clasificar(c, n):
    r = np.hypot(c[:, 0], c[:, 1])
    z = c[:, 2]
    nr = (n[:, 0] * c[:, 0] + n[:, 1] * c[:, 1]) / np.maximum(r, 1e-12)
    nz = n[:, 2]
    out = np.full(len(c), "SIN_CLASIFICAR", dtype=object)
    # lanza: caras dentro de la caja envolvente de lanza.stl (|x| < 0,02; 0,22 < y < 0,41)
    out[(np.abs(c[:, 0]) < 0.02) & (c[:, 1] > 0.22) & (c[:, 1] < 0.41) & (z > 0.80)] = "lanza"
    tol = 1e-6
    out[(np.abs(nz) > 0.99) & (np.abs(z - ZB) < tol)] = "abierto_inferior"
    out[(np.abs(nz) > 0.99) & (np.abs(z - ZT) < tol)] = "abierto_superior"
    out[(np.abs(nr) > 0.9) & (r > 0.99 * R_EXT)] = "lateral_abierto"   # el centro de cara cae en la cuerda
    out[(np.abs(nr) > 0.9) & (r < 0.101) & (nr < 0)] = "nucleo_abierto"
    out[(np.abs(nz) > 0.99) & (np.abs(z - Z0) < tol) & (r > 0.449)] = "cara_inf_rodamiento"
    out[(np.abs(nz) > 0.99) & (np.abs(z - Z1) < tol) & (r > 0.449)] = "cara_sup_rodamiento"
    en_cono = (z > Z0 - tol) & (z < Z1 + tol) & (r > 0.99 * r_cono(z)) & (r < r_cono(z) + 1e-6) & (nr > 0.9)
    out[en_cono] = "pared_agujero"
    if (out == "SIN_CLASIFICAR").any():
        raise ValueError("caras de frontera sin clasificar: %d" % (out == "SIN_CLASIFICAR").sum())
    return out


TIPOS = {"abierto_inferior": "pressure-outlet", "abierto_superior": "pressure-outlet",
         "lateral_abierto": "pressure-outlet", "nucleo_abierto": "pressure-outlet",
         "cara_inf_rodamiento": "wall", "cara_sup_rodamiento": "wall",
         "pared_agujero": "wall", "lanza": "wall"}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--nivel", default="base", choices=list(NIVELES))
    ap.add_argument("--stl", default=None, help="lanza.stl de la rama B (m)")
    a = ap.parse_args()
    nodes, cells, info = construir(a.nivel, a.stl)
    res = write_hex_cells(a.salida, nodes, cells, clasificar, TIPOS, title=f"F5 agujero {a.nivel}")
    info.update(res)
    # area de la pared del agujero (control): superficie lateral del cono
    json.dump(info, open(os.path.splitext(a.salida)[0] + "_info.json", "w"), indent=1)
    print(json.dumps(info, indent=1))
