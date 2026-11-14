#!/usr/bin/env python3
"""
CORRIDA 3 · T12 · Paquete para Ismael (NO se envia: lo envia Jean). Copia lo ligero a 06_PAQUETE_ISMAEL/ y escribe
MANIFIESTO_SHA256.txt con el hash de cada archivo copiado y, aparte, el hash y la ruta de los .cas.h5/.dat.h5 de cada
corrida (pesados: no se copian; quedan en 03_FLUENT/casos/<caso>/). Los .dpm de impactos (hasta 2 GB) solo se listan.
Contenido: LEEME, PDF de resultados, DECISIONES_PARA_REGISTRAR.md, journals corregidos, tablas .dpm de entrada,
mascaras del Caso 2, CSV de KPI y figuras, run_log.csv, CAMBIOS_R3.md, aviso del journal del kit.
Uso: python -I -B r3_paquete_ismael.py
"""
import glob
import hashlib
import os
import shutil

B = "D:/CFD_Redosado/CORRIDA_3_O7C2"
FL = B + "/03_FLUENT"
P = B + "/06_PAQUETE_ISMAEL"
CASOS = ["R3_00_humo", "R3_02_caso2", "R3_01_kit", "R3_03_B_caso2", "R3_04_gruesa", "R3_05_fina", "R3_06_np050", "R3_07_np200"]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest().upper()


def cp(src, rel):
    dst = os.path.join(P, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


if os.path.exists(P):
    raise SystemExit("ya existe %s: no se sobrescribe" % P)
cp(B + "/04_REDACCION/RESULTADOS_R3_para_Jean.pdf", "RESULTADOS_R3_para_Jean.pdf")
cp(B + "/00_ADMIN/DECISIONES_PARA_REGISTRAR.md", "DECISIONES_PARA_REGISTRAR.md")
cp(B + "/00_ADMIN/run_log.csv", "run_log.csv")
cp(B + "/CAMBIOS_R3.md", "CAMBIOS_R3.md")
cp(B + "/01_ENTRADA/boquillas_O7_C2_LAT1m4.json", "entradas/boquillas_O7_C2_LAT1m4.json")
cp(B + "/01_ENTRADA/inyecciones/VERIFICACION_T2.csv", "entradas/VERIFICACION_T2.csv")
cp(B + "/01_ENTRADA/mascaras/K1_O7C2_Caso2_mascaras.npz", "entradas/K1_O7C2_Caso2_mascaras.npz")
cp(B + "/01_ENTRADA/mascaras/T3_log.txt", "entradas/T3_log.txt")
for c in CASOS:
    d = "%s/casos/%s" % (FL, c)
    cp("%s/%s.jou" % (d, c), "casos/%s/%s.jou" % (c, c))
    for f in glob.glob(d + "/*.dpm"):
        n = os.path.basename(f)
        if n.split(".")[0].upper() == n.split(".")[0]:          # tablas de inyeccion (LAT_1_A.dpm...), no impactos
            cp(f, "casos/%s/inyecciones/%s" % (c, n))
    cp("%s/%s_transcript.txt" % (d, c), "casos/%s/%s_transcript.txt" % (c, c))
cp("%s/casos/R3_00_humo/_fallo1/R3_00_humo_transcript.txt" % FL, "casos/R3_00_humo/_fallo1_transcript_sin_muestras.txt")
for f in glob.glob(FL + "/resultados/*.csv") + glob.glob(FL + "/resultados/*.md") + glob.glob(FL + "/resultados/*.txt"):
    cp(f, "resultados/" + os.path.basename(f))
for f in glob.glob(FL + "/resultados/R3/*.csv"):
    cp(f, "resultados/R3/" + os.path.basename(f))
for f in glob.glob(FL + "/resultados/KPI/*/*"):
    cp(f, "resultados/KPI/%s/%s" % (os.path.basename(os.path.dirname(f)), os.path.basename(f)))
for f in glob.glob(FL + "/figuras/*"):
    cp(f, "figuras/" + os.path.basename(f))
open(P + "/LEEME.txt", "w", encoding="utf-8").write(
    "CORRIDA 3 (diseno O7+C2) - paquete para Ismael preparado el 26/10/2026 (Jean lo revisa y lo envia).\n"
    "Empezar por RESULTADOS_R3_para_Jean.pdf y DECISIONES_PARA_REGISTRAR.md (incluye el aviso del journal del kit).\n"
    "casos/<caso>/: journal (corregido: 8 lineas en blanco en el primer /report/dpm-sample), transcript, tablas .dpm.\n"
    "resultados/KPI/<caso>/: KPI con obstaculos (r3_post.py); R3_02_03_AB = valor final del Caso 2 (A+B explicito).\n"
    "Los .cas.h5/.dat.h5 y los .dpm de impactos no se copian (pesados): ver su SHA-256 y ruta en MANIFIESTO_SHA256.txt.\n"
    "Estados: CFD EJECUTADO y verificado (balance, malla, parcelas); NO validado. Abanico 16,8 grados = HIPOTESIS.\n")
lin = ["MANIFIESTO SHA-256 - 06_PAQUETE_ISMAEL (CORRIDA 3). Formato: SHA-256  ruta relativa", ""]
for root, _, files in os.walk(P):
    for f in sorted(files):
        if f == "MANIFIESTO_SHA256.txt":
            continue
        p = os.path.join(root, f)
        lin.append("%s  %s" % (sha(p), os.path.relpath(p, P).replace("\\", "/")))
lin += ["", "Archivos pesados NO copiados (quedan en D:/CFD_Redosado/CORRIDA_3_O7C2/03_FLUENT/casos/):"]
for c in CASOS:
    for ext in ("_fin.cas.h5", "_fin.dat.h5"):
        p = "%s/casos/%s/%s%s" % (FL, c, c, ext)
        if os.path.exists(p):
            lin.append("%s  %s  (%.1f MB)" % (sha(p), p, os.path.getsize(p) / 1e6))
    for z in ("od", "cara_inf"):
        p = "%s/casos/%s/%s.dpm" % (FL, c, z)
        if os.path.exists(p):
            lin.append("(sin hash)  %s  (%.1f MB)" % (p, os.path.getsize(p) / 1e6))
open(P + "/MANIFIESTO_SHA256.txt", "w", encoding="utf-8").write("\n".join(lin) + "\n")
tot = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(P) for f in fs)
print("paquete %s: %d archivos, %.1f MB" % (P, sum(len(fs) for _, _, fs in os.walk(P)), tot / 1e6))
