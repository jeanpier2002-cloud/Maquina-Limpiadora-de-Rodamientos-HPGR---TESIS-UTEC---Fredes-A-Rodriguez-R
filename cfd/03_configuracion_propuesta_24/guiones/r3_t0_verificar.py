#!/usr/bin/env python3
"""
CORRIDA 3 · T0 · Verificacion de integridad antes de correr (solo lectura de las fuentes).
  1. MANIFIESTO.txt del kit de Ismael (SHA-256 de cada archivo listado).
  2. Mallas de D:/CFD03_run/mallas contra HASHES_mallas.sha256 (L_A_base, L_A_gruesa, L_A_fina, L_B_base, L_A_dominio)
     y la copia L_A_base.msh del kit.
  3. Version de Python y de Fluent (cabecera del transcript de la Corrida 2: misma instalacion).
Salida: 00_ADMIN/T0_hashes.txt (y resumen en pantalla).
Uso: python -I -B r3_t0_verificar.py
"""
import hashlib
import os
import platform
import re
import sys

BASE = "D:/CFD_Redosado/CORRIDA_3_O7C2"
KIT = "D:/CFD_Redosado/Diseño actual/PAQUETE_JEAN_O7C2_v2_2026-10-25/01_KIT_G3_A_O7_O4"
MALLAS = "D:/CFD03_run/mallas"
TRN_C2 = "D:/CFD_Redosado/CORRIDA_2_desde24oct/03_FLUENT/casos/F1_G3_gruesa_Co/F1_G3_gruesa_Co_transcript.txt"
FLUENT = r"D:\Ansys\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\fluent.exe"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest().upper()


out = []
# 1. manifiesto del kit
ok = bad = 0
for ln in open(KIT + "/MANIFIESTO.txt", encoding="utf-8", errors="replace"):
    m = re.match(r"^([0-9A-F]{64})\s+(.+?)\s*$", ln.strip())
    if not m:
        continue
    p = os.path.join(KIT, m.group(2))
    if not os.path.exists(p):
        out.append("KIT FALTA      %s" % m.group(2)); bad += 1
        continue
    h = sha(p)
    if h == m.group(1):
        ok += 1
    else:
        out.append("KIT DISTINTO   %s  esperado %s  real %s" % (m.group(2), m.group(1), h)); bad += 1
out.insert(0, "1. MANIFIESTO del kit: %d archivos identicos, %d con problema" % (ok, bad))
# 2. mallas
esper = {}
for ln in open(MALLAS + "/HASHES_mallas.sha256"):
    if ln.strip():
        h, n = ln.split()
        esper[n.lstrip("*")] = h.upper()
out.append("2. Mallas (D:/CFD03_run/mallas, solo lectura):")
for n in ("L_A_base.msh", "L_A_gruesa.msh", "L_A_fina.msh", "L_B_base.msh", "L_A_dominio.msh"):
    h = sha(MALLAS + "/" + n)
    out.append("   %-16s %s  %s" % (n, h, "IDENTICO" if h == esper.get(n) else "DISTINTO (esperado %s)" % esper.get(n)))
h = sha(KIT + "/malla/L_A_base.msh")
out.append("   kit/malla/L_A_base.msh %s  %s" % (h, "IDENTICO a CFD03" if h == esper["L_A_base.msh"] else "DISTINTO"))
# 3. versiones
out.append("3. Python %s (%s) en %s" % (platform.python_version(), platform.architecture()[0], sys.executable))
cab = open(TRN_C2, errors="replace").read(3000)
bt = re.search(r"Build Time:.*?Build Id:\s*\d+", cab)
out.append("   Fluent: %s | %s | ejecutable %s (existe: %s)" % (
    "ANSYS Fluent 2026 R1 Student (v261)", bt.group(0) if bt else "[VERIFICAR]", FLUENT, os.path.exists(FLUENT)))
out.append("   (la cabecera de cada transcript de esta tanda repite Build Time/Build Id: se comprueba en el humo)")
txt = "\n".join(out) + "\n"
open(BASE + "/00_ADMIN/T0_hashes.txt", "w", encoding="utf-8").write(txt)
print(txt)
