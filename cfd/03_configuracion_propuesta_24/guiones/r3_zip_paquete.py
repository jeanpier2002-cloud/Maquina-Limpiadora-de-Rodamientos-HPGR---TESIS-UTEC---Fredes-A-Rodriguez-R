#!/usr/bin/env python3
"""
CORRIDA 3 · T12 · Comprime 06_PAQUETE_ISMAEL en un ZIP (para subirlo a Drive: supera el limite de 25 MB de Gmail) y
copia el ZIP y el PDF de resultados a la carpeta de Drive que Ismael ya puede leer:
  G:/Mi unidad/Semestre X/TESIS II/Sistema de aspersión/CFD03_casos_para_Ismael/CORRIDA_3_O7C2_2026-10-26/
Escribe el SHA-256 del ZIP junto a el. No borra ni sobrescribe nada.
Uso: python -I -B r3_zip_paquete.py
"""
import hashlib
import os
import shutil
import zipfile

B = "D:/CFD_Redosado/CORRIDA_3_O7C2"
P = B + "/06_PAQUETE_ISMAEL"
Z = B + "/CORRIDA_3_O7C2_para_Ismael_2026-10-26.zip"
DRIVE = "G:/Mi unidad/Semestre X/TESIS II/Sistema de aspersión/CFD03_casos_para_Ismael/CORRIDA_3_O7C2_2026-10-26"
if os.path.exists(Z) or os.path.exists(DRIVE):
    raise SystemExit("ya existe el ZIP o la carpeta de Drive: no se sobrescribe")
with zipfile.ZipFile(Z, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
    for root, _, files in os.walk(P):
        for f in sorted(files):
            p = os.path.join(root, f)
            zf.write(p, os.path.join("CORRIDA_3_O7C2_para_Ismael", os.path.relpath(p, P)))
h = hashlib.sha256(open(Z, "rb").read()).hexdigest().upper()
open(Z + ".sha256", "w", encoding="utf-8").write("%s  %s\n" % (h, os.path.basename(Z)))
with zipfile.ZipFile(Z) as zf:
    assert zf.testzip() is None
    n = len(zf.namelist())
os.makedirs(DRIVE)
for src in (Z, Z + ".sha256", B + "/04_REDACCION/RESULTADOS_R3_para_Jean.pdf"):
    shutil.copy2(src, DRIVE)
print("ZIP %s: %d archivos, %.1f MB, SHA-256 %s" % (Z, n, os.path.getsize(Z) / 1e6, h))
print("copiado a", DRIVE, os.listdir(DRIVE))
