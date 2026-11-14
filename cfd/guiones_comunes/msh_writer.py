#!/usr/bin/env python3
"""
Escritor de mallas hexaedricas estructuradas en formato ASCII de Fluent (.msh).

Motivo: la sesion autonoma no puede usar la GUI de Fluent Meshing. Una malla
estructurada (caja o sector cilindrico) se escribe directamente y Fluent la lee
con /file/read-case. La orientacion de caras (regla de la mano derecha respecto
a c0) se verifico empiricamente con /mesh/check en F4 (ver ESTADO.md).

Uso como modulo:
    from msh_writer import write_structured
    write_structured(path, X, Y, Z, bc, normal_to_c0=True)
X, Y, Z: arrays (ni, nj, nk) de coordenadas de nodos (m).
bc: dict con claves 'imin','imax','jmin','jmax','kmin','kmax'. Cada valor es
    (nombre, tipo) o una funcion f(a, b) -> (nombre, tipo) evaluada en los
    indices de celda de la cara (para partir un lado en varias zonas).
    tipo en {'wall','pressure-outlet','pressure-inlet','velocity-inlet','symmetry'}.
"""
import numpy as np

BC_HEX = {"interior": 0x2, "wall": 0x3, "pressure-inlet": 0x4,
          "pressure-outlet": 0x5, "symmetry": 0x7, "velocity-inlet": 0xA}


def _quads(ni, nj, nk, side):
    """Caras de un lado: devuelve (nodos Nx4 con normal +eje, celda N, (a,b) N)."""
    def nid(i, j, k):
        return 1 + i + ni * (j + nj * k)

    def cid(i, j, k):
        return 1 + i + (ni - 1) * (j + (nj - 1) * k)

    if side[0] == "i":
        i = 0 if side == "imin" else ni - 1
        ic = 0 if side == "imin" else ni - 2
        j, k = np.meshgrid(np.arange(nj - 1), np.arange(nk - 1), indexing="ij")
        n = np.stack([nid(i, j, k), nid(i, j + 1, k), nid(i, j + 1, k + 1), nid(i, j, k + 1)], -1)
        c = cid(ic, j, k)
        ab = (j, k)
    elif side[0] == "j":
        jj = 0 if side == "jmin" else nj - 1
        jc = 0 if side == "jmin" else nj - 2
        i, k = np.meshgrid(np.arange(ni - 1), np.arange(nk - 1), indexing="ij")
        # e_k x e_i = +e_j
        n = np.stack([nid(i, jj, k), nid(i, jj, k + 1), nid(i + 1, jj, k + 1), nid(i + 1, jj, k)], -1)
        c = cid(i, jc, k)
        ab = (i, k)
    else:
        kk = 0 if side == "kmin" else nk - 1
        kc = 0 if side == "kmin" else nk - 2
        i, j = np.meshgrid(np.arange(ni - 1), np.arange(nj - 1), indexing="ij")
        # e_i x e_j = +e_k
        n = np.stack([nid(i, j, kk), nid(i + 1, j, kk), nid(i + 1, j + 1, kk), nid(i, j + 1, kk)], -1)
        c = cid(i, j, kc)
        ab = (i, j)
    return n.reshape(-1, 4), c.reshape(-1), (ab[0].reshape(-1), ab[1].reshape(-1))


def _interior(ni, nj, nk):
    def nid(i, j, k):
        return 1 + i + ni * (j + nj * k)

    def cid(i, j, k):
        return 1 + i + (ni - 1) * (j + (nj - 1) * k)

    out = []
    # caras i interiores: normal +i, celda "+" = (i), celda "-" = (i-1)
    i, j, k = np.meshgrid(np.arange(1, ni - 1), np.arange(nj - 1), np.arange(nk - 1), indexing="ij")
    out.append((np.stack([nid(i, j, k), nid(i, j + 1, k), nid(i, j + 1, k + 1), nid(i, j, k + 1)], -1),
                cid(i, j, k), cid(i - 1, j, k)))
    i, j, k = np.meshgrid(np.arange(ni - 1), np.arange(1, nj - 1), np.arange(nk - 1), indexing="ij")
    out.append((np.stack([nid(i, j, k), nid(i, j, k + 1), nid(i + 1, j, k + 1), nid(i + 1, j, k)], -1),
                cid(i, j, k), cid(i, j - 1, k)))
    i, j, k = np.meshgrid(np.arange(ni - 1), np.arange(nj - 1), np.arange(1, nk - 1), indexing="ij")
    out.append((np.stack([nid(i, j, k), nid(i + 1, j, k), nid(i + 1, j + 1, k), nid(i, j + 1, k)], -1),
                cid(i, j, k), cid(i, j, k - 1)))
    n = np.concatenate([o[0].reshape(-1, 4) for o in out])
    cp = np.concatenate([o[1].reshape(-1) for o in out])
    cm = np.concatenate([o[2].reshape(-1) for o in out])
    return n, cp, cm


def write_structured(path, X, Y, Z, bc, normal_to_c0=True, title="msh_writer"):
    ni, nj, nk = X.shape
    nn = ni * nj * nk
    nc = (ni - 1) * (nj - 1) * (nk - 1)
    # Si el sistema (i,j,k) es levogiro en el espacio, invertir el sentido de todas las caras
    d = np.linalg.det(np.array([
        [X[1, 0, 0] - X[0, 0, 0], Y[1, 0, 0] - Y[0, 0, 0], Z[1, 0, 0] - Z[0, 0, 0]],
        [X[0, 1, 0] - X[0, 0, 0], Y[0, 1, 0] - Y[0, 0, 0], Z[0, 1, 0] - Z[0, 0, 0]],
        [X[0, 0, 1] - X[0, 0, 0], Y[0, 0, 1] - Y[0, 0, 0], Z[0, 0, 1] - Z[0, 0, 0]]]))
    flip_all = d < 0

    zones = []  # (nombre, tipo, nodos, c0, c1)
    n, cp, cm = _interior(ni, nj, nk)
    # normal geometrica apunta a cp (celda "+"), salvo sistema levogiro
    to_plus = normal_to_c0 != flip_all
    if to_plus:
        zones.append(("interior-fluid", "interior", n, cp, cm))
    else:
        zones.append(("interior-fluid", "interior", n, cm, cp))

    groups = {}
    for side in ("imin", "imax", "jmin", "jmax", "kmin", "kmax"):
        q, c, (a, b) = _quads(ni, nj, nk, side)
        # la normal geometrica de q apunta a +eje; en "min" eso es hacia la celda
        into_cell = side.endswith("min") != flip_all
        want_into = normal_to_c0
        if into_cell != want_into:
            q = q[:, ::-1]
        spec = bc[side]
        if callable(spec):
            labels = [spec(int(x), int(y)) for x, y in zip(a, b)]
        else:
            labels = [spec] * len(c)
        for idx, lab in enumerate(labels):
            groups.setdefault(lab, ([], []))
            groups[lab][0].append(q[idx])
            groups[lab][1].append(c[idx])
    for (name, typ), (qs, cs) in groups.items():
        cs = np.array(cs)
        zones.append((name, typ, np.array(qs), cs, np.zeros_like(cs)))

    nf = sum(len(z[3]) for z in zones)
    with open(path, "w", newline="\n") as f:
        f.write(f'(0 "{title}")\n(2 3)\n')
        f.write(f"(10 (0 1 {nn:x} 0 3))\n")
        f.write(f"(12 (0 1 {nc:x} 0))\n")
        f.write(f"(13 (0 1 {nf:x} 0))\n")
        f.write(f"(10 (1 1 {nn:x} 1 3)(\n")
        P = np.stack([X.ravel(order="F"), Y.ravel(order="F"), Z.ravel(order="F")], -1)
        np.savetxt(f, P, fmt="%.10e")
        f.write("))\n")
        f.write(f"(12 (2 1 {nc:x} 1 4))\n")
        first = 1
        zid = 3
        zone_ids = []
        for name, typ, q, c0, c1 in zones:
            last = first + len(c0) - 1
            f.write(f"(13 ({zid:x} {first:x} {last:x} {BC_HEX[typ]:x} 4)(\n")
            np.savetxt(f, np.column_stack([q, c0, c1]), fmt="%x")
            f.write("))\n")
            zone_ids.append((zid, typ, name))
            first = last + 1
            zid += 1
        f.write("(45 (2 fluid fluid)())\n")
        for zid_, typ, name in zone_ids:
            f.write(f"(45 ({zid_} {typ} {name})())\n")
    return {"nodos": nn, "celdas": nc, "caras": nf, "zonas": [z[2] for z in zone_ids]}


def caja(path, L, N, normal_to_c0=True, bc=None):
    """Caja [0,Lx]x[0,Ly]x[0,Lz] con N=(nx,ny,nz) celdas."""
    x = np.linspace(0, L[0], N[0] + 1)
    y = np.linspace(0, L[1], N[1] + 1)
    z = np.linspace(0, L[2], N[2] + 1)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    if bc is None:
        bc = {s: (s, "wall") for s in ("imin", "imax", "jmin", "jmax", "kmin")}
        bc["kmax"] = ("kmax", "pressure-outlet")
    return write_structured(path, X, Y, Z, bc, normal_to_c0=normal_to_c0)


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "caja.msh"
    print(caja(out, (1.0, 0.5, 0.25), (8, 6, 4)))


# ---------------------------------------------------------------------------
# Escritor generico: lista de hexaedros (orden VTK) -> .msh
# Orden VTK: 0-1-2-3 cara inferior (antihorario visto desde arriba), 4-5-6-7 superior.
# Caras con normal SALIENTE (regla de la mano derecha):
_HEX_FACES = np.array([[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4],
                       [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])


def write_hex_cells(path, nodes, cells, classify, zone_types, title="msh_writer"):
    """
    nodes: (N,3) float; cells: (M,8) int, indices 0-based en orden VTK, volumen positivo.
    classify(centros (K,3), normales_salientes (K,3)) -> array de K nombres de zona de frontera.
    zone_types: dict nombre -> tipo ('wall', 'pressure-outlet', ...).
    Convencion Fluent verificada en F4: la normal por mano derecha apunta hacia c0;
    en frontera c1 = 0 y la normal apunta hacia el interior.
    """
    nodes = np.asarray(nodes, float)
    cells = np.asarray(cells, np.int64)
    M = len(cells)
    F = cells[:, _HEX_FACES].reshape(-1, 4)          # (6M,4) salientes de su celda
    owner = np.repeat(np.arange(M), 6)
    key = np.sort(F, axis=1)
    order = np.lexsort(key.T[::-1])
    ks = key[order]
    same = np.all(ks[1:] == ks[:-1], axis=1)
    first = np.zeros(len(ks), bool)
    first[:-1] = same
    # pares (a,b): a = order[i], b = order[i+1] cuando same[i]
    ia = order[:-1][same]
    ib = order[1:][same]
    paired = np.zeros(len(F), bool)
    paired[ia] = True
    paired[ib] = True
    if np.bincount(np.concatenate([ia, ib]), minlength=len(F)).max() > 1:
        raise ValueError("cara compartida por mas de 2 celdas")
    # interior: nodos de la cara vistos desde a (normal saliente de a -> hacia b) => c0 = b, c1 = a
    int_nodes = F[ia]
    int_c0 = owner[ib] + 1
    int_c1 = owner[ia] + 1
    # frontera: invertir para que la normal apunte hacia la celda (c0)
    bidx = np.where(~paired)[0]
    b_nodes = F[bidx]
    P = nodes[b_nodes]                                # (K,4,3)
    cen = P.mean(1)
    nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 1]) + np.cross(P[:, 3] - P[:, 2], P[:, 0] - P[:, 3])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    names = np.asarray(classify(cen, nrm))
    b_nodes = b_nodes[:, ::-1]
    b_c0 = owner[bidx] + 1

    zones = [("interior-fluid", "interior", int_nodes, int_c0, int_c1)]
    for nm in sorted(set(names.tolist())):
        s = names == nm
        zones.append((nm, zone_types[nm], b_nodes[s], b_c0[s], np.zeros(s.sum(), np.int64)))
    nn, nc = len(nodes), M
    nf = sum(len(z[3]) for z in zones)
    with open(path, "w", newline="\n") as f:
        f.write(f'(0 "{title}")\n(2 3)\n')
        f.write(f"(10 (0 1 {nn:x} 0 3))\n(12 (0 1 {nc:x} 0))\n(13 (0 1 {nf:x} 0))\n")
        f.write(f"(10 (1 1 {nn:x} 1 3)(\n")
        np.savetxt(f, nodes, fmt="%.10e")
        f.write("))\n")
        f.write(f"(12 (2 1 {nc:x} 1 4))\n")
        first_f, zid, ids = 1, 3, []
        for name, typ, q, c0, c1 in zones:
            last = first_f + len(c0) - 1
            f.write(f"(13 ({zid:x} {first_f:x} {last:x} {BC_HEX[typ]:x} 4)(\n")
            np.savetxt(f, np.column_stack([q + 1, c0, c1]), fmt="%x")
            f.write("))\n")
            ids.append((zid, typ, name))
            first_f = last + 1
            zid += 1
        f.write("(45 (2 fluid fluid)())\n")
        for z_, t_, n_ in ids:
            f.write(f"(45 ({z_} {t_} {n_})())\n")
    return {"nodos": nn, "celdas": nc, "caras": nf,
            "zonas": {n_: int(len(z[3])) for (_, _, n_), z in zip(ids, zones)}}
