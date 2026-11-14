#!/usr/bin/env python3
"""
CFD03 - Lectura eficiente en memoria de los CSV de impactos (salida de dpm2csv.py), para archivos de varios GB
(S18: hasta ~8 millones de impactos por zona). Lee fila a fila con csv.reader y guarda cada columna en un
array('d') (8 bytes por valor). Las columnas de texto (boquilla) se codifican como enteros con su tabla.
No cambia ningun valor: es la misma conversion float() que hacian los lectores anteriores.
"""
import csv
from array import array

import numpy as np


def leer(path, numericas, texto=("boquilla",), filtro_t=None):
    """Devuelve {col: np.ndarray} para las columnas pedidas y, para cada columna de texto, (codigos, tabla).
    filtro_t=(t0, t1) descarta al leer las filas fuera de la ventana (columna 't'), para ahorrar memoria."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rd = csv.reader(f)
        cab = next(rd)
        ix = {c: i for i, c in enumerate(cab)}
        num = {c: array("d") for c in numericas if c in ix}
        txt = {c: (array("i"), {}) for c in texto if c in ix}
        it = ix.get("t")
        for r in rd:
            if filtro_t is not None:
                tv = float(r[it])
                if not (filtro_t[0] <= tv < filtro_t[1]):
                    continue
            for c, arr in num.items():
                arr.append(float(r[ix[c]]))
            for c, (cod, tabla) in txt.items():
                v = r[ix[c]]
                k = tabla.get(v)
                if k is None:
                    k = tabla[v] = len(tabla)
                cod.append(k)
    out = {c: np.frombuffer(a, dtype=np.float64).copy() if len(a) else np.zeros(0) for c, a in num.items()}
    for c, (cod, tabla) in txt.items():
        inv = np.array(sorted(tabla, key=tabla.get), dtype=object)
        out[c] = inv[np.frombuffer(cod, dtype=np.int32)] if len(cod) else np.array([], dtype=object)
    out["_columnas"] = cab
    return out
