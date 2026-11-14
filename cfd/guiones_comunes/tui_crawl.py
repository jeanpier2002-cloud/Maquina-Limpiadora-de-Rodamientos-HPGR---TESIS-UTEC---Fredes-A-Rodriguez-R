#!/usr/bin/env python3
"""
Rastreo de menus de la TUI de Fluent en la instalacion (procedimiento anti-invencion,
sustituto de la grabacion GUI de PROMPT_MAESTRO §4.1 paso 4, ver D5 de MODO_AUTONOMO).

En la TUI, escribir una ruta absoluta de menu y luego una linea vacia lista su
contenido (verificado en F4, t0/t1). Las entradas terminadas en '/' son submenus.
Este script genera journals por niveles, lanza Fluent y parsea la transcripcion.

Uso: python tui_crawl.py <carpeta_trabajo> <caso_previo_o_-> <salida.json> raiz1 [raiz2 ...]
     [--prejournal archivo]  comandos a ejecutar antes del rastreo (p. ej. activar DPM)
     [--niveles 4]
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

ap = argparse.ArgumentParser()
ap.add_argument("cwd")
ap.add_argument("caso")
ap.add_argument("salida")
ap.add_argument("raices", nargs="+")
ap.add_argument("--prejournal")
ap.add_argument("--niveles", type=int, default=4)
a = ap.parse_args()

tree = {}
pend = list(a.raices)
for nivel in range(a.niveles):
    if not pend:
        break
    tag = f"crawl_{os.path.basename(a.salida).split('.')[0]}_{nivel}"
    tr = f"{a.cwd}/{tag}_transcript.txt"
    if os.path.exists(tr):
        os.remove(tr)
    with open(f"{a.cwd}/{tag}.jou", "w", newline="\n") as f:
        f.write(f'/file/start-transcript "{tr}"\n')
        if a.caso != "-":
            f.write(f'/file/read-case "{a.caso}"\n')
        if a.prejournal:
            f.write(open(a.prejournal).read().rstrip("\n") + "\n")
        for pth in pend:
            f.write(f"{pth}\n\n")
        f.write("/exit\nyes\n")
    subprocess.call([sys.executable, os.path.join(HERE, "run_fluent.py"), f"{a.cwd}/{tag}.jou", a.cwd,
                     "--t", "1", "--timeout", "600"])
    lines = open(tr, encoding="latin-1").read().splitlines()
    cur, collecting, buf = None, False, []
    for ln in lines:
        if "> " in ln or ln.endswith(">"):
            if collecting and cur is not None:
                tree[cur] = sorted(set(buf))
                cur, collecting, buf = None, False, []
            m = re.search(r">\s(/\S+)\s*$", ln)
            if m and m.group(1) in pend:
                cur = m.group(1)
            elif cur is not None and re.search(r">\s*$", ln):
                collecting = True
            continue
        if collecting:
            buf += ln.split()
    nuevos = []
    for pth in pend:
        for it in tree.get(pth, []):
            if it.endswith("/"):
                nuevos.append(pth.rstrip("/") + "/" + it.rstrip("/"))
    pend = [n for n in nuevos if n not in tree]
    print(f"nivel {nivel}: {len(tree)} menus listados, {len(pend)} pendientes")

json.dump(tree, open(a.salida, "w"), indent=1, sort_keys=True)
print("guardado", a.salida)
